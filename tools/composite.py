# Composite: original frame (untouched) in centre + generated plate on the sides,
# moved with camera motion, with edge-motion propagation, seam colour matching and grain.
import cv2, numpy as np, json, sys, subprocess
S, plate_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
nmax = int(sys.argv[4]) if len(sys.argv)>4 else 10**9
SRC="/root/.claude/uploads/f2f4d021-6eab-5a67-bdbb-2039f9f4a52a/ec142bfe-IMG_1337.mov"
FW,FH=1080,1920; OW,OH=3414,1920; OX=(OW-FW)//2      # output canvas, frame offset
PX0,PY0=1231,32                                      # ref frame offset inside plate
plate=cv2.imread(plate_path).astype(np.float32)
Ms=[np.array(m) for m in json.load(open(S+'/motion.json'))]
ref=cv2.imread(S+'/src/0161.jpg'); refg=cv2.resize(cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY),(540,960))
dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
uu,vv=np.meshgrid(np.arange(OW,dtype=np.float32),np.arange(OH,dtype=np.float32))
fx=uu-OX; fy=vv                                       # output -> frame coords
dl=np.clip(-fx,0,None); dr=np.clip(fx-(FW-1),0,None)  # distance outside seam
wL=np.exp(-dl/260.0)*(fx<0); wR=np.exp(-dr/260.0)*(fx>FW-1)
cL=np.exp(-dl/30.0)*(fx<0);  cR=np.exp(-dr/30.0)*(fx>FW-1)
side=((fx<0)|(fx>FW-1))
rng=np.random.default_rng(0)
# grain level of original (high-pass std in flat-ish areas)
g=ref.astype(np.float32); hp=g-cv2.GaussianBlur(g,(0,0),1.2); grain=float(np.median(np.abs(hp)))*1.25
print('grain',grain)
def edge_profile(img,cols):
    p=img[:,cols].astype(np.float32).mean(axis=1)
    return cv2.GaussianBlur(p.reshape(-1,1,p.shape[-1]) if p.ndim==2 else p,(1,0),sigmaX=0.1,sigmaY=18).reshape(FH,-1)
dec=subprocess.Popen(['ffmpeg','-v','error','-i',SRC,'-map','0:v:0','-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{OW}x{OH}','-r','60000/1001','-i','-',
     '-c:v','libx264','-preset','medium','-crf','12','-pix_fmt','yuv444p',out_path],stdin=subprocess.PIPE)
refmean=ref[:800].reshape(-1,3).mean(0)
for i in range(min(len(Ms),nmax)):
    buf=dec.stdout.read(FW*FH*3)
    if len(buf)<FW*FH*3: break
    fr=np.frombuffer(buf,np.uint8).reshape(FH,FW,3)
    M=Ms[i]
    # global camera mapping: frame coords -> ref coords
    rx=M[0,0]*fx+M[0,1]*fy+M[0,2]; ry=M[1,0]*fx+M[1,1]*fy+M[1,2]
    # local edge motion residual (flow frame->ref along each edge), propagated outward with decay
    fg=cv2.resize(cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY),(540,960))
    fl=cv2.resize(dis.calc(fg,refg,None),(FW,FH))*2.0
    ys=np.arange(FH,dtype=np.float32)
    for cols,w in ((slice(0,24),wL),(slice(FW-24,FW),wR)):
        xs=np.arange(FW)[cols].mean()
        res=fl[:,cols].mean(axis=1)-np.stack([M[0,0]*xs+M[0,1]*ys+M[0,2]-xs, M[1,0]*xs+M[1,1]*ys+M[1,2]-ys],1)
        res=cv2.GaussianBlur(res.reshape(FH,1,2),(1,0),sigmaX=0.1,sigmaY=40).reshape(FH,2)
        res=np.clip(res,-60,60)
        rx+=w*res[:,0:1]; ry+=w*res[:,1:2]
    ext=cv2.remap(plate,(rx+PX0).astype(np.float32),(ry+PY0).astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
    # exposure tracking
    gain=(fr[:800].reshape(-1,3).mean(0)+1)/(refmean+1); ext*=gain
    # seam colour matching
    for colsF,colE,w in ((slice(0,3),OX-1,cL),(slice(FW-3,FW),OX+FW,cR)):
        a=fr[:,colsF].astype(np.float32).mean(1); b=ext[:,colE-1:colE+2].mean(1) if colE>OX else ext[:,colE-2:colE+1].mean(1)
        d=cv2.GaussianBlur((a-b).reshape(FH,1,3),(1,0),sigmaX=0.1,sigmaY=6).reshape(FH,1,3)
        d=18.0*np.tanh(d/18.0)                      # soft clamp: avoid ghost smears from moving objects
        ext+=w[...,None]*d
    ext+=rng.normal(0,grain,ext.shape).astype(np.float32)*side[...,None]
    out=np.clip(ext,0,255).astype(np.uint8)
    out[:,OX:OX+FW]=fr                                  # original pixels untouched
    enc.stdin.write(out.tobytes())
    if i%40==0: print(i,flush=True)
enc.stdin.close(); enc.wait(); dec.kill()
