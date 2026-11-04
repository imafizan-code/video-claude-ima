import sys, json, subprocess, numpy as np, cv2, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
src, dst, model, facejson = sys.argv[1:5]
PREVIEW = len(sys.argv) > 5   # optional: list of seconds -> write stills only
cap = cv2.VideoCapture(src); W=int(cap.get(3)); H=int(cap.get(4)); FPS=cap.get(5); N=int(cap.get(7))
lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model), running_mode=vision.RunningMode.VIDEO, num_faces=1))
OUT_LIP=[61,146,91,181,84,17,314,405,321,375,291,409,270,269,267,0,37,39,40,185]
IN_LIP=[78,95,88,178,87,14,317,402,318,324,308,415,310,311,312,13,82,81,80,191]
OVAL=[10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109]
LEYE=[33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246]
REYE=[263,249,390,373,374,380,381,382,362,398,384,385,386,387,388,466]
LBROW=[70,63,105,66,107,55,65,52,53,46]; RBROW=[300,293,334,296,336,285,295,282,283,276]
LIP_LAB=np.array([118,168,148],np.float32)  # soft rose (OpenCV LAB, 8-bit scale)
def poly(mask, pts, idx, val=255): cv2.fillPoly(mask,[pts[idx].astype(np.int32)],val)
if not PREVIEW:
    enc = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-i",src,"-map","0:v","-map","1:a","-c:v","libx264","-crf","16","-preset","medium","-g","30","-pix_fmt","yuv420p",
        "-c:a","copy","-movflags","+faststart",dst],stdin=subprocess.PIPE)
want = set(int(float(t)*FPS) for t in sys.argv[5].split(",")) if PREVIEW else None
import os
SKIP=[tuple(map(float,r.split('-'))) for r in os.environ.get('SKIP','').split(',') if r]
prev=None; faces=[]; i=0
while True:
    ok, fr = cap.read()
    if not ok: break
    res = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(fr,cv2.COLOR_BGR2RGB)), int(i*1000/FPS))
    out = fr
    skip = any(a*FPS<=i<b*FPS for a,b in SKIP)
    if res.face_landmarks:
        p = np.array([[q.x*W,q.y*H] for q in res.face_landmarks[0]],np.float32)
        if prev is not None and np.abs(p-prev).mean()<25: p = 0.55*p+0.45*prev   # smooth jitter, reset on cuts
        prev = p
        x0,y0=np.maximum(p.min(0)-60,0).astype(int); x1,y1=np.minimum(p.max(0)+60,[W,H]).astype(int)
        faces.append({"f":i,"top":float(p[10,1]),"chin":float(p[152,1]),"x0":float(p[234,0]),"x1":float(p[454,0])})
        if skip: pass
        else:
          crop = fr[y0:y1,x0:x1].copy(); q = p-[x0,y0]; h,w = crop.shape[:2]
          fw = np.linalg.norm(p[454]-p[234])
          # --- masks ---
          skin=np.zeros((h,w),np.uint8); poly(skin,q,OVAL)
          for idx in (LEYE,REYE,LBROW,RBROW,OUT_LIP): poly(skin,q,idx,0)
          skin=cv2.GaussianBlur(skin,(0,0),fw*0.03).astype(np.float32)/255
          lip=np.zeros((h,w),np.uint8); poly(lip,q,OUT_LIP); poly(lip,q,IN_LIP,0)
          lip=cv2.GaussianBlur(lip,(0,0),max(1.5,fw*0.006)).astype(np.float32)/255
          hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV)
          notmic = 1-((hsv[...,1]>165)&(hsv[...,2]>140)).astype(np.float32)   # skip the hot-pink mic
          lip*=cv2.GaussianBlur(notmic,(0,0),2)
          # --- light makeup: smoothing + gentle lift ---
          sm=cv2.bilateralFilter(crop,9,38,9).astype(np.float32)
          f=crop.astype(np.float32); a=(skin*0.5)[...,None]
          f=f*(1-a)+sm*a
          lab=cv2.cvtColor(np.clip(f,0,255).astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
          lab[...,0]+=skin*5           # brighten skin a touch
          # blush on cheeks
          bl=np.zeros((h,w),np.float32)
          for c in (q[205],q[425]): cv2.circle(bl,tuple(int(v) for v in c),int(fw*0.11),1.0,-1)
          bl=cv2.GaussianBlur(bl,(0,0),fw*0.07)*skin
          lab[...,1]+=bl*6; lab[...,2]+=bl*1.5
          # lipstick: pull lip chroma toward soft rose, keep texture (luminance)
          la=lip*0.6
          lab[...,1]=lab[...,1]*(1-la)+LIP_LAB[1]*la
          lab[...,2]=lab[...,2]*(1-la)+LIP_LAB[2]*la
          lab[...,0]-=lip*4
          crop=cv2.cvtColor(np.clip(lab,0,255).astype(np.uint8),cv2.COLOR_LAB2BGR)
          out=fr.copy(); out[y0:y1,x0:x1]=crop
    else: faces.append({"f":i,"top":None,"chin":None})
    if PREVIEW:
        if i in want: cv2.imwrite(f"{dst}_{i}.jpg", np.hstack([fr,out])[400:1300:,].copy())
    else: enc.stdin.write(out.tobytes())
    i+=1
if not PREVIEW: enc.stdin.close(); enc.wait()
json.dump({"fps":FPS,"faces":faces},open(facejson,"w"))
print("frames",i,"with face",sum(1 for x in faces if x["chin"]))
