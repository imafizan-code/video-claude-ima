"""Light-makeup beautify for talking-head clips.

Per frame: MediaPipe FaceMesh landmarks (temporally smoothed) drive feathered masks for
skin, lips and cheeks. Skin gets a gentle edge-preserving smooth and a small lift, lips a
rose-red tint in LAB (texture kept, inner mouth excluded), cheeks a faint blush.

usage: beautify.py IN.mp4 OUT.mp4 [--preview frame.png --at SECONDS]
"""
import sys, subprocess, argparse
import numpy as np
import cv2
import mediapipe as mp

FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377,
             152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
LIPS_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
LIPS_INNER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
LEFT_BROW = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
RIGHT_BROW = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
NOSTRILS = [98, 97, 2, 326, 327, 294, 278, 344, 440, 275, 4, 45, 220, 115, 48, 64]
CHEEKS = [(205, 50), (425, 280)]

# Rose-red to sit with the red cardigan (#C0394E-ish), applied in LAB
LIP_RGB = np.array([[[192, 57, 78]]], np.uint8)
BLUSH_RGB = np.array([[[236, 128, 146]]], np.uint8)
LIP_LAB = cv2.cvtColor(LIP_RGB[..., ::-1], cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)
BLUSH_LAB = cv2.cvtColor(BLUSH_RGB[..., ::-1], cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32)


def poly(mask, pts, idx, val=1.0):
    cv2.fillPoly(mask, [pts[idx].astype(np.int32)], val)


def process(frame, pts, s):
    h, w = frame.shape[:2]
    x0, y0 = pts.min(0).astype(int)
    x1, y1 = pts.max(0).astype(int)
    fw = x1 - x0
    pad = int(fw * 0.25)
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(w, x1 + pad), min(h, y1 + pad)
    crop = frame[y0:y1, x0:x1]
    p = pts - np.array([x0, y0])
    ch, cw = crop.shape[:2]
    feather = max(3, int(fw * 0.02)) | 1

    skin = np.zeros((ch, cw), np.float32)
    poly(skin, p, FACE_OVAL)
    for idx in (LEFT_EYE, RIGHT_EYE, LEFT_BROW, RIGHT_BROW, LIPS_OUTER, NOSTRILS):
        cv2.fillPoly(skin, [cv2.convexHull(p[idx].astype(np.int32))], 0.0)
    skin = cv2.GaussianBlur(skin, (0, 0), feather)

    lips = np.zeros((ch, cw), np.float32)
    poly(lips, p, LIPS_OUTER)
    poly(lips, p, LIPS_INNER, 0.0)
    lips = cv2.GaussianBlur(lips, (0, 0), max(1.5, fw * 0.006))

    blush = np.zeros((ch, cw), np.float32)
    for a, b in CHEEKS:
        c = (p[a] * 0.6 + p[b] * 0.4).astype(int)
        cv2.circle(blush, tuple(c), int(fw * 0.11), 1.0, -1)
    blush = cv2.GaussianBlur(blush, (0, 0), fw * 0.07) * skin

    # Skin: edge-preserving smooth, keep a little fine texture so it never reads plastic
    smooth = cv2.bilateralFilter(crop, 0, 22, max(4, fw * 0.012))
    detail = crop.astype(np.float32) - cv2.GaussianBlur(crop, (0, 0), 1.2).astype(np.float32)
    smooth = smooth.astype(np.float32) + detail * 0.35
    out = crop.astype(np.float32)
    k = (skin * s["smooth"])[..., None]
    out = out * (1 - k) + smooth * k

    lab = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] += skin * s["lift"]
    wl = lips * s["lip"]
    lab[..., 0] = lab[..., 0] * (1 - wl * 0.06)
    lab[..., 1] = lab[..., 1] * (1 - wl) + LIP_LAB[1] * wl
    lab[..., 2] = lab[..., 2] * (1 - wl) + LIP_LAB[2] * wl
    wb = blush * s["blush"]
    lab[..., 1] = lab[..., 1] * (1 - wb) + BLUSH_LAB[1] * wb
    lab[..., 2] = lab[..., 2] * (1 - wb) + BLUSH_LAB[2] * wb
    res = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    frame = frame.copy()
    frame[y0:y1, x0:x1] = res
    return frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--preview")
    ap.add_argument("--at", type=float, default=0)
    ap.add_argument("--lip", type=float, default=0.55)
    ap.add_argument("--smooth", type=float, default=0.55)
    ap.add_argument("--blush", type=float, default=0.16)
    ap.add_argument("--lift", type=float, default=4.0)
    a = ap.parse_args()
    s = {"lip": a.lip, "smooth": a.smooth, "blush": a.blush, "lift": a.lift}

    cap = cv2.VideoCapture(a.inp)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w, h = int(cap.get(3)), int(cap.get(4))
    mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=False,
                                           min_detection_confidence=0.5, min_tracking_confidence=0.5)
    enc = None
    if not a.preview:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                                "-r", f"{fps}", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                                "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                                "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", a.out],
                               stdin=subprocess.PIPE)
    prev = None
    n = hits = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = n / fps
        n += 1
        if a.preview and t + 1e-6 < a.at - 1.0:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        r = mesh.process(rgb)
        if r.multi_face_landmarks:
            lm = r.multi_face_landmarks[0].landmark
            pts = np.array([[q.x * w, q.y * h] for q in lm], np.float32)
            # Temporal smoothing kills mask shimmer; reset on large jumps (cuts, fast moves)
            if prev is not None and np.abs(pts - prev).mean() < 25:
                pts = prev * 0.45 + pts * 0.55
            prev = pts
            frame = process(frame, pts, s)
            hits += 1
        else:
            prev = None
        if a.preview:
            if t + 1e-6 >= a.at:
                cv2.imwrite(a.preview, frame)
                break
            continue
        enc.stdin.write(frame.tobytes())
    if enc:
        enc.stdin.close()
        enc.wait()
    print(f"{a.inp}: {n} frames, face in {hits}")


if __name__ == "__main__":
    main()
