# Tiled detail pass at higher resolution over the generated side areas only.
import torch, numpy as np, sys, time
from PIL import Image
from diffusers import StableDiffusionInpaintPipeline
S, lo, outp = sys.argv[1], sys.argv[2], sys.argv[3]
torch.set_num_threads(4)
PW,PH,X0,Y0=3542,1984,1231,32
sc=0.6; W,H=int(PW*sc)//8*8, int(PH*sc)//8*8          # ~2120x1184
base=Image.open(lo).convert('RGB').resize((W,H),Image.LANCZOS)
ref=Image.open(S+'/src/0161.jpg').convert('RGB')
fw,fh=round(1080*W/PW),round(1920*H/PH); fx0,fy0=round(X0*W/PW),round(Y0*H/PH)
base.paste(ref.resize((fw,fh),Image.LANCZOS),(fx0,fy0))
B=np.array(base).astype(np.float32)
known=np.zeros((H,W),np.float32); known[fy0+4:fy0+fh-4,fx0+4:fx0+fw-4]=1
pipe=StableDiffusionInpaintPipeline.from_pretrained('stable-diffusion-v1-5/stable-diffusion-inpainting',torch_dtype=torch.float32,variant='fp16',safety_checker=None)
pipe.set_progress_bar_config(disable=True)
prompt="photo inside a modern shopping mall, recessed ceiling lights, shops, people, shopping bag, sharp focus, highly detailed, realistic, iphone photo"
neg="text, letters, words, logo, watermark, blurry, soft, painting, cartoon, deformed, distorted face"
T,O=512,96
acc=np.zeros_like(B); wsum=np.zeros((H,W,1),np.float32)
xs=list(range(0,W-T,T-O))+[W-T]; ys=list(range(0,H-T,T-O))+[H-T]
win=np.outer(np.hanning(T+2)[1:-1],np.hanning(T+2)[1:-1]).astype(np.float32)[...,None]+1e-3
t=time.time(); n=0
for y in ys:
  for x in xs:
    k=known[y:y+T,x:x+T]
    if k.min()>0.5: continue
    tile=Image.fromarray(B[y:y+T,x:x+T].astype(np.uint8)); m=Image.fromarray(((1-k)*255).astype(np.uint8))
    o=pipe(prompt=prompt,negative_prompt=neg,image=tile,mask_image=m,width=T,height=T,strength=0.42,num_inference_steps=36,
           guidance_scale=6.0,generator=torch.Generator().manual_seed(100+n)).images[0]
    acc[y:y+T,x:x+T]+=np.array(o,np.float32)*win; wsum[y:y+T,x:x+T]+=win; n+=1
    print('tile',n,round(time.time()-t),flush=True)
R=np.where(wsum>0,acc/np.maximum(wsum,1e-6),B)
R=np.where(known[...,None]>0.5,B,R)
full=Image.fromarray(np.clip(R,0,255).astype(np.uint8)).resize((PW,PH),Image.LANCZOS)
full.save(outp)
