"""Generate Malay voiceover lines with edge-tts and record word timings -> vo/lines/*.mp3 + src/vo_timing.js"""
import asyncio, json, os, subprocess, edge_tts
VOICES = {"Y": ("ms-MY-YasminNeural", "+16%", "+4Hz"), "O": ("ms-MY-OsmanNeural", "+12%", "+0Hz")}
here = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(here, "lines"), exist_ok=True)
script = json.load(open(os.path.join(here, "script.json")))

async def gen(i, line):
    for attempt in range(5):
        try:
            return await gen1(i, line)
        except Exception as e:
            print('retry', i, e); await asyncio.sleep(3 * (attempt + 1))
    raise RuntimeError(i)

async def gen1(i, line):
    voice, rate, pitch = VOICES[line["v"]]
    com = edge_tts.Communicate(line["text"], voice, rate=rate, pitch=pitch, boundary="WordBoundary", proxy=os.environ.get("HTTPS_PROXY"))
    path = os.path.join(here, "lines", f"{i:02d}.mp3")
    words = []
    with open(path, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"w": ch["text"], "s": ch["offset"] / 1e7, "e": (ch["offset"] + ch["duration"]) / 1e7})
    dur = words[-1]["e"] + 0.05
    return dict(line, i=i, dur=dur, words=words, file=f"vo/lines/{i:02d}.mp3")

async def main():
    out = [await gen(i, l) for i, l in enumerate(script)]
    for a, b in zip(out, out[1:]):
        end = a["t"] + a["dur"]
        flag = "  <-- OVERLAP" if end > b["t"] - 0.1 else ""
        print(f'{a["i"]:02d} {a["t"]:6.1f} -> {end:6.1f}  next {b["t"]:6.1f}{flag}')
    l = out[-1]; print(f'{l["i"]:02d} {l["t"]:6.1f} -> {l["t"] + l["dur"]:6.1f}')
    json.dump(out, open(os.path.join(here, "lines.json"), "w"), indent=1, ensure_ascii=False)
    with open(os.path.join(here, "..", "src", "vo_timing.js"), "w") as f:
        f.write("const VO = " + json.dumps([{k: x[k] for k in ("t", "v", "dur", "words", "hl")} for x in out], ensure_ascii=False) + ";\n")
asyncio.run(main())
