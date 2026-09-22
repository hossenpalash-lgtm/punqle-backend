#!/usr/bin/env python3
"""Picker thumbnail for a live Talking Actor: a still frame from their OWN base video (face + a hint of the
real situation — kitchen counter, car interior, bedroom), not the isolated studio-style persona photo.

Why a separate file: assets/actors/{id}.jpg is also the reference photo fed into Image Ad's actor-compositing
calls (AdCreationForm's actor picker, the home page's Product and Show Your App actor pickers) — those want a
clean, plain-background portrait, so they keep using assets/actors/{id}.jpg unchanged. This script writes
assets/actors/{id}_situation.jpg instead, which ImageActorOut.situation_preview_base64 serves ONLY to the
Talking Actors pickers.

Picks the first candidate (after --after seconds) where a face AND both eyes are detected (eyes-open proxy),
scored by eye size (bigger = more open/closer) minus a motion-blur penalty (Laplacian variance, higher = sharper).

  python3 scripts/make_situation_thumbnail.py --actor maya --video actors_v2_approved_base_videos/kitchen/final_base_video.mp4
  add --at 4.2 to force one exact timestamp instead of auto-picking
"""
import argparse, os, cv2, numpy as np

FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
EYE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def score_frame(frame):
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = FACE.detectMultiScale(g, 1.1, 5, minSize=(60, 60))
    if not len(faces):
        return None
    x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
    roi = g[y + int(h * .12): y + int(h * .58), x: x + w]
    eyes = EYE.detectMultiScale(roi, 1.08, 6, minSize=(max(10, w // 9), max(10, w // 9)))
    if len(eyes) < 2:
        return None
    sharp = cv2.Laplacian(g[y:y + h, x:x + w], cv2.CV_64F).var()
    eye_area = sum(e[2] * e[3] for e in eyes)
    return (eye_area * 0.5 + sharp * 0.02), (x, y, w, h)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--actor", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--after", type=float, default=0.6)
    ap.add_argument("--at", type=float, default=None)
    ap.add_argument("--zoom", type=float, default=2.5, help="crop side = max(face_w,face_h) * zoom; higher = looser crop, more situation visible")
    ap.add_argument("--y-bias", type=float, default=0.42, help="face-height fraction below face top used as the crop's vertical center; lower = more room shown below the face")
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    best = None
    frames = []
    idx = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        t = idx / fps
        frames.append((t, f))
        idx += 1

    candidates = [a.at] if a.at is not None else [t for t, _ in frames if t >= a.after]
    for t in candidates:
        f = min(frames, key=lambda tf: abs(tf[0] - t))[1]
        r = score_frame(f)
        if r is None:
            continue
        score, box = r
        if best is None or score > best[0]:
            best = (score, t, f, box)
        if a.at is not None:
            break

    if best is None:
        raise SystemExit(f"No frame with an open-eyed face found in {a.video} after {a.after}s.")
    score, t, frame, (x, y, w, h) = best
    H, W = frame.shape[:2]
    cx, cy = x + w / 2, y + h * a.y_bias
    side = int(max(w, h) * a.zoom)
    x0, y0 = int(max(0, cx - side / 2)), int(max(0, cy - side / 2))
    x1, y1 = int(min(W, x0 + side)), int(min(H, y0 + side))
    x0, y0 = x1 - side if x1 - side >= 0 else 0, y1 - side if y1 - side >= 0 else 0
    crop = frame[max(0, y0):min(H, y1), max(0, x0):min(W, x1)]
    crop = cv2.resize(crop, (400, 400), interpolation=cv2.INTER_AREA)
    out = os.path.join(ROOT, "assets", "actors", f"{a.actor}_situation.jpg")
    cv2.imwrite(out, crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"actor={a.actor} picked t={t:.2f}s score={score:.0f} -> {out}")

if __name__ == "__main__":
    main()
