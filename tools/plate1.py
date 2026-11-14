import torch, numpy as np, sys, time
from PIL import Image, ImageFilter
from diffusers import StableDiffusionInpaintPipeline
S=sys.argv[1]; seed=int(sys.argv[2]) if len(sys.argv)>2 else 7
torch.set_num_threads(4)
# full-res plate geometry
PW,PH,X0,Y0=3542,1984,1231,32
ref=Image.open(S+'/src/0161.jpg').convert('RGB')
canvas=Image.new('RGB',(PW,PH),(128,128,128)); canvas.paste(ref,(X0,Y0))
# init fill: stretch edge columns so the noise starts near correct colours
a=np.array(canvas)
a[:, :X0]=np.array(ref)[:, :1].mean(axis=1,keepdims=True).astype(np.uint8).repeat(1,1)[:, :1].repeat(X0,1) if False else a[:, :X0]
canvas=Image.fromarray(a)
mask=Image.new('L',(PW,PH),255); mask.paste(0,(X0+6,Y0+6,X0+1080-6,Y0+1920-6))
W,H=1072,600
img=canvas.resize((W,H),Image.LANCZOS); m=mask.resize((W,H),Image.NEAREST)
pipe=StableDiffusionInpaintPipeline.from_pretrained('stable-diffusion-v1-5/stable-diffusion-inpainting',torch_dtype=torch.float32,variant='fp16',safety_checker=None)
prompt=("wide angle photo inside a bright modern shopping mall, dark ceiling with rows of round recessed spotlights, "
        "red storefront on the left, food court seating with tables and chairs, striped pillars, shops in the distance, "
        "young woman in navy shirt and grey hijab in foreground holding a shopping bag, iphone photo, realistic, sharp, natural indoor lighting")
neg="text, letters, words, writing, logo, signage text, watermark, border, frame, black bars, blurry, distorted, deformed, duplicate, extra limbs, cartoon, painting, lowres"
t=time.time()
out=pipe(prompt=prompt,negative_prompt=neg,image=img,mask_image=m,width=W,height=H,num_inference_steps=30,guidance_scale=7.0,
         generator=torch.Generator().manual_seed(seed)).images[0]
print('secs',time.time()-t)
out.save(S+f'/plate_lo_{seed}.png')
