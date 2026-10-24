"""Build the Hook C cartoon-hybrid video.

Usage: python3 build.py <work_dir> <out.mp4>
Expects trimmed voice clips at <work_dir>/vo/voNN.wav (one per entry in vo.json).
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
work, out = sys.argv[1], sys.argv[2]
FPS, LEAD, GAP, TAIL = 30, 0.25, 0.45, 1.6

vo = json.load(open(os.path.join(HERE, "vo.json")))
dur = lambda f: float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))

timeline, t = [], 0.0
for i, v in enumerate(vo):
    d = dur(f"{work}/vo/vo{i:02d}.wav")
    end = t + LEAD + d + GAP + (TAIL if i == len(vo) - 1 else 0)
    timeline.append({"start": round(t, 3), "end": round(end, 3), "voStart": round(t + LEAD, 3),
                     "voDur": round(d, 3), "sub": v["sub"]})
    t = end
total = t
json.dump(timeline, open(f"{work}/timeline.json", "w"), indent=1)
print(f"total {total:.2f}s")

# voice track: each clip delayed to its scene's voStart
inputs, filt = [], []
for i, s in enumerate(timeline):
    inputs += ["-i", f"{work}/vo/vo{i:02d}.wav"]
    ms = int(s["voStart"] * 1000)
    filt.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
mix = "".join(f"[a{i}]" for i in range(len(timeline)))
filt.append(f"{mix}amix=inputs={len(timeline)}:normalize=0,apad,atrim=0:{total:.3f},loudnorm=I=-15:TP=-1.5[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt),
                "-map", "[out]", "-ar", "44100", f"{work}/voice.wav"], check=True)

os.makedirs(f"{work}/frames", exist_ok=True)
subprocess.run(["node", os.path.join(HERE, "render.js"), os.path.join(HERE, "scene.html"),
                f"{work}/timeline.json", f"{work}/frames", str(FPS), f"{total:.3f}"], check=True)

subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{work}/frames/%05d.jpg",
                "-i", f"{work}/voice.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
               check=True)
print("wrote", out)
