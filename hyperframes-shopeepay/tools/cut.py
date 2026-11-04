import json, subprocess, sys
S=sys.argv[1]
# (clip, in, out, label)
SEG=[
 ("IMG_1248",5.30,9.68,"hook"),
 ("IMG_1242",0.60,5.20,"intro"),
 ("IMG_1248",1.84,4.12,"settle"),
 ("IMG_1253",1.00,4.62,"scan"),
 ("IMG_1256",0.46,4.13,"bil"),
 ("IMG_1259",1.00,5.10,"coins"),
 ("IMG_1259",5.33,5.86,"senang"),
 ("IMG_1287",0.68,4.93,"cara1"),
 ("IMG_1287",5.10,6.28,"cara2"),
 ("IMG_1287",6.56,7.60,"cara3"),
 ("IMG_1287",7.84,11.24,"cara4"),
 ("IMG_1289",0.36,2.36,"cta"),
]
parts=[]
for i,(c,a,b,l) in enumerate(SEG):
    o=f"{S}/build/p{i:02d}.mp4"; d=b-a
    vf="scale=1080:1920:flags=lanczos,setsar=1,fps=30,format=yuv420p"
    # punch-in zoom on alternate segments for energy (same clip back-to-back)
    if l in ("senang","cara2","cara4","settle"):
        vf="scale=1188:2112:flags=lanczos,crop=1080:1920:54:110,setsar=1,fps=30,format=yuv420p"
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(a),"-t",f"{d:.3f}","-i",f"{S}/src/{c}.MOV",
      "-vf",vf,"-af",f"aresample=48000,afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03",
      "-c:v","libx264","-crf","17","-preset","fast","-c:a","aac","-b:a","192k","-ac","2",o],check=True)
    dur=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",o]))
    parts.append((c,a,b,l,o,dur))
open(f"{S}/build/list.txt","w").write("".join(f"file '{p[4]}'\n" for p in parts))
subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",f"{S}/build/list.txt",
  "-af","loudnorm=I=-14:TP=-1.5:LRA=11","-c:v","libx264","-crf","17","-preset","medium","-c:a","aac","-b:a","192k","-ar","48000",
  "-movflags","+faststart",f"{S}/build/talk.mp4"],check=True)
# map words into output timeline
W=json.load(open(f"{S}/words.json")); t=0; out=[]
for c,a,b,l,o,dur in parts:
    for s in W[c]:
        for ws,we,w in s["w"]:
            mid=(ws+we)/2
            if a<=mid<=b: out.append({"w":w.strip(),"s":round(t+max(ws,a)-a,3),"e":round(t+min(we,b)-a,3),"seg":l})
    print(f"{l:8s} {t:6.2f} -> {t+dur:6.2f}"); t+=dur
json.dump(out,open(f"{S}/build/timeline_words.json","w"),indent=0)
print("TOTAL",round(t,2))
