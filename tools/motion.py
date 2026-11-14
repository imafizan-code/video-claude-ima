import cv2, numpy as np, glob, sys, json
S=sys.argv[1]
fs=sorted(glob.glob(S+'/src/*.jpg'))
ref=cv2.imread(fs[160],0)
mask=np.zeros_like(ref); mask[:820,:]=255   # ceiling/background region
orb=cv2.ORB_create(4000)
kr,dr=orb.detectAndCompute(ref,mask)
bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True)
out=[]
for f in fs:
    im=cv2.imread(f,0)
    k,d=orb.detectAndCompute(im,mask)
    m=bf.match(d,dr)
    src=np.float32([k[x.queryIdx].pt for x in m]); dst=np.float32([kr[x.trainIdx].pt for x in m])
    M,inl=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=2.0)
    out.append(M.tolist())
s=[ (np.hypot(M[0][0],M[0][1]), M[0][2], M[1][2]) for M in out]
a=np.array(s); print('scale',a[:,0].min(),a[:,0].max(),'tx',a[:,1].min(),a[:,1].max(),'ty',a[:,2].min(),a[:,2].max())
json.dump(out,open(S+'/motion.json','w'))
