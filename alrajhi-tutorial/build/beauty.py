"""Light makeup + sun-kissed key light, baked into the talking-head footage.

python3 build/beauty.py <model.task> <in.mp4> <out.mp4> [--still t out.png]
Per frame: MediaPipe face landmarks -> soft skin smoothing (texture kept), blush, lip tint gated to
real lip pixels (so a finger or the mic near the mouth is never painted), then a warm directional
"sun" from the upper left. Audio is copied untouched.
"""
import sys, subprocess, json
import numpy as np, cv2
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

W, H = 1080, 1920
LIPS_OUT = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
LIPS_IN = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149,
        150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
EYE_L = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
EYE_R = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
BROW_L = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
BROW_R = [336, 296, 334, 293, 300, 276, 283, 282, 295, 285]
CHEEK_L, CHEEK_R = 205, 425

LIP_LAB = np.array([120, 168, 137], np.float32)     # rose-pink lipstick target (OpenCV 8-bit Lab)
BLUSH_BGR = np.array([150, 150, 255], np.float32)   # peachy pink

# sun: warm key from the upper left, falling off across the frame
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx + 250) / 1500) ** 2 + ((yy + 200) / 1700) ** 2)
SUN = np.clip(1.15 - d, 0, 1) ** 1.6                   # 0..1
SUN_COL = np.array([90, 180, 255], np.float32) / 255   # golden (BGR)


def poly(mask, pts, val=255):
    cv2.fillPoly(mask, [pts.astype(np.int32)], val)


def process(img, lm):
    out = img.astype(np.float32)
    if lm is not None:
        P = lm
        fw = np.linalg.norm(P[454] - P[234])            # face width in px
        x0, y0 = np.maximum(P.min(0) - fw * 0.25, 0).astype(int)
        x1, y1 = np.minimum(P.max(0) + fw * 0.25, [W - 1, H - 1]).astype(int)
        roi = img[y0:y1, x0:x1]
        Q = P - [x0, y0]
        h, w = roi.shape[:2]

        # ---- skin: smooth, keep 35% of the fine texture so it doesn't look plastic
        skin = np.zeros((h, w), np.uint8); poly(skin, Q[OVAL])
        for part in (EYE_L, EYE_R, BROW_L, BROW_R, LIPS_OUT):
            m = np.zeros((h, w), np.uint8); poly(m, Q[part]); m = cv2.dilate(m, None, iterations=int(fw * 0.02) + 1)
            skin[m > 0] = 0
        skin = cv2.GaussianBlur(skin, (0, 0), fw * 0.03).astype(np.float32) / 255
        small = cv2.resize(roi, (w // 2, h // 2))
        smooth = cv2.bilateralFilter(small, 9, 28, 9)
        smooth = cv2.resize(smooth, (w, h)).astype(np.float32)
        r = roi.astype(np.float32)
        detail = r - cv2.GaussianBlur(r, (0, 0), 1.2)
        soft = smooth + detail * 0.35
        r = r * (1 - skin[..., None] * 0.6) + soft * (skin[..., None] * 0.6)

        # ---- tone: brighter, more even skin; lift the darker patches round the mouth corners
        lab = cv2.cvtColor(np.clip(r, 0, 255).astype(np.uint8), cv2.COLOR_BGR2Lab).astype(np.float32)
        L, A, Bc = lab[..., 0], lab[..., 1], lab[..., 2]
        core = skin > 0.6
        if core.sum() > 50:
            Lm, Am, Bm = np.median(L[core]), np.median(A[core]), np.median(Bc[core])
            Lbig = cv2.GaussianBlur(L, (0, 0), fw * 0.06)
            Le = L - (Lbig - Lm) * 0.45                               # flatten blotches / uneven shading
            Le = Le + 13 * np.clip(1.25 - L / 255, 0, 1)              # brighten, more in the darker tones
            Ae = A + (Am - A) * 0.35; Be = Bc + (Bm - Bc) * 0.35 - 2  # even out redness and sallowness
            k = skin
            L = L * (1 - k) + Le * k; A = A * (1 - k) + Ae * k; Bc = Bc * (1 - k) + Be * k
            lipm = np.zeros((h, w), np.uint8); poly(lipm, Q[LIPS_OUT])
            ring = cv2.dilate(lipm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(fw * 0.14) | 1,) * 2))
            for c in (61, 291):
                cv2.circle(ring, tuple(Q[c].astype(int)), int(fw * 0.06), 255, -1)
            ring[lipm > 0] = 0
            ring = cv2.GaussianBlur(ring.astype(np.float32) / 255, (0, 0), fw * 0.02)
            dark = np.clip((Lm + 6 - L) / 18, 0, 1) * ring
            L = L + (Lm + 6 - L) * 0.75 * dark
            A = A + (Am - A) * 0.5 * dark; Bc = Bc + (Bm - Bc) * 0.5 * dark
            lab = np.dstack([L, A, Bc])
            r = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_Lab2BGR).astype(np.float32)

        # ---- blush
        blush = np.zeros((h, w), np.float32)
        for c in (CHEEK_L, CHEEK_R):
            cv2.circle(blush, tuple(Q[c].astype(int)), int(fw * 0.11), 1.0, -1)
        blush = cv2.GaussianBlur(blush, (0, 0), fw * 0.07) * skin * 0.16
        r = r * (1 - blush[..., None]) + (r * 0.55 + BLUSH_BGR * 0.45) * blush[..., None]

        # ---- lips: mask from landmarks, then gate to lip-coloured pixels only
        lips = np.zeros((h, w), np.uint8); poly(lips, Q[LIPS_OUT])
        inner = np.zeros((h, w), np.uint8); poly(inner, Q[LIPS_IN]); lips[inner > 0] = 0
        lab = cv2.cvtColor(np.clip(r, 0, 255).astype(np.uint8), cv2.COLOR_BGR2Lab).astype(np.float32)
        sk = lab[skin > 0.6]
        ref_a = np.median(sk[:, 1]) if len(sk) else 150
        gate = np.clip((lab[..., 1] - ref_a - 1) / 8, 0, 1) * np.clip((lab[..., 0] - 40) / 30, 0, 1)
        lm_ = cv2.GaussianBlur(lips.astype(np.float32) / 255, (0, 0), fw * 0.006) * gate * 0.62
        tgt = lab.copy()
        tgt[..., 0] = lab[..., 0] * 0.9 + LIP_LAB[0] * 0.1
        tgt[..., 1] = LIP_LAB[1] + (lab[..., 1] - ref_a) * 0.3
        tgt[..., 2] = LIP_LAB[2] + (lab[..., 2] - np.median(sk[:, 2]) if len(sk) else 0) * 0.3
        lab = lab * (1 - lm_[..., None]) + tgt * lm_[..., None]
        r = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_Lab2BGR).astype(np.float32)
        out[y0:y1, x0:x1] = r

    # ---- sun-kissed key: screen a warm light in from the upper left, warm the mids a touch
    lightc = SUN[..., None] * SUN_COL * 255 * 0.30
    out = 255 - (255 - out) * (255 - lightc) / 255
    out[..., 2] *= 1.035; out[..., 0] *= 0.965
    return np.clip(out, 0, 255).astype(np.uint8)


def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)


def main():
    model, src, dst = sys.argv[1:4]
    still = sys.argv[sys.argv.index("--still") + 1:] if "--still" in sys.argv else None
    opts = vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=model),
                                        running_mode=vision.RunningMode.VIDEO, num_faces=1)
    det = vision.FaceLandmarker.create_from_options(opts)
    fps = 30
    enc = None if still else subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
         "-i", src, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-g", "30",
         "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    ema, n = None, 0
    want = int(float(still[0]) * fps) if still else None
    for i, f in enumerate(frames(src)):
        small = cv2.cvtColor(cv2.resize(f, (540, 960)), cv2.COLOR_BGR2RGB)
        res = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=small), int(i * 1000 / fps))
        lm = None
        if res.face_landmarks:
            pts = np.array([[p.x * W, p.y * H] for p in res.face_landmarks[0]], np.float32)
            ema = pts if ema is None else ema * 0.45 + pts * 0.55       # steady the landmarks between frames
            lm = ema
        if still:
            if i == want:
                cv2.imwrite(still[1], np.hstack([f, process(f, lm)])); return
            continue
        enc.stdin.write(process(f, lm).tobytes()); n += 1
    enc.stdin.close(); enc.wait()
    print(dst, n, "frames")


if __name__ == "__main__":
    main()
