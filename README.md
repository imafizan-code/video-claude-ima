# Merci Studio – Customer Journey Promo

16:9 (1920x1080, 30 fps, ~106 s) animated promo showing a customer's visit to Merci Studio,
in the outlined-cartoon style of the reference clip (HUD timer panel, time pill, wall clock,
word-by-word captions with yellow keywords).

Final video: `out/merci_studio_promo.mp4`

| Time  | Scene | Story clock |
|-------|-------|-------------|
| 0:00  | Arrival outside (storefront photo) | 12:00 PM |
| 0:07  | Up the stairs (stairway photo) | 12:00 PM |
| 0:13  | Warm welcome at reception | 12:00 PM |
| 0:21  | Package A photoshoot, 15 min | 12:00 → 12:15 |
| 0:39  | Session done, customer waits in lounge | 12:15 |
| 0:46  | Owner downloads photos, 5 min | 12:15 → 12:20 |
| 0:56  | Customer picks favourites on iPad, 10 min | 12:20 → 12:30 |
| 1:08  | Printing + quality check, 10 min | 12:30 → 12:40 |
| 1:21  | Prints handed over + Google Drive softcopy link | 12:40 |
| 1:32  | Thank-you & goodbye | 12:40 |
| 1:38  | End card: "Thank You for Choosing Us!" / "Your Memories, Beautifully Captured." | |

The two reference photos (`assets/photos/`) are displayed whole and unedited inside photo frames.

## Rebuild
```
node render/render.js video 4                       # frames -> out/video_noaudio.mp4 + out/sfx.json
python3 render/make_audio.py out/sfx.json out/audio.wav 106
ffmpeg -i out/video_noaudio.mp4 -i out/audio.wav -c:v copy -c:a aac -b:a 192k -shortest out/merci_studio_promo.mp4
```
Preview stills: `node render/render.js stills 12 30 75`. Live preview: serve the repo and open `src/index.html?play`.

## TikTok version (9:16, Bahasa Melayu + voiceover)

Final video: `out/merci_studio_tiktok.mp4` (1080x1920, 30 fps, ~107 s). All on-screen text is in BM,
with a casual Malay voiceover (neural TTS: customer = ms-MY-YasminNeural, owner = ms-MY-OsmanNeural).
The opening shop building is a cartoon redraw; the studio is shown as self-photo (customer uses a remote, no photographer).

```
SSL_CERT_FILE=/root/.ccr/ca-bundle.crt python3 vo/make_vo.py          # edit vo/script.json first; writes vo/lines + src/vo_timing.js
PAGE=tiktok.html OUTDIR=out/tiktok node render/render.js video 4
python3 render/make_audio.py out/tiktok/sfx.json out/tiktok/audio.wav 107.5 vo/lines.json
ffmpeg -i out/tiktok/video_noaudio.mp4 -i out/tiktok/audio.wav -c:v copy -c:a aac -b:a 192k -shortest out/merci_studio_tiktok.mp4
```
