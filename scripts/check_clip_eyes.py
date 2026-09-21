#!/usr/bin/env python3
"""Eye check for a Punqle Actors v2 base clip: how often the eyes close, for how long, and how steady the eyes are.
Blink proxy = frames where a face is found but NO eye is found in its upper half (OpenCV Haar, so it is a rough
screen, not a medical measurement: a head turned down or a hand over the face also reads as 'closed').

  python3 scripts/check_clip_eyes.py <clip.mp4> [<source_footage.mp4> ...]

Reference values (people at rest blink ~15-20 times a minute, each ~0.1-0.4s; long closures >0.5s look odd on a base clip
that gets reused for every ad). Comparing the swap against the source footage shows whether the swap ADDED eye trouble.
"""
import sys, cv2, numpy as np

FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
EYE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

def analyse(path):
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    states = []  # 1 = eyes seen, 0 = face seen but no eyes, None = no face
    last = None
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        faces = FACE.detectMultiScale(g, 1.1, 4, minSize=(28, 28))
        if len(faces):
            last = max(faces, key=lambda r: r[2] * r[3])
        elif last is None:
            states.append(None); continue
        x, y, w, h = last
        roi = g[y + int(h * .12): y + int(h * .58), x: x + w]
        eyes = EYE.detectMultiScale(roi, 1.08, 5, minSize=(max(8, w // 10), max(8, w // 10)))
        states.append(1 if len(eyes) else (0 if len(faces) else None))
    # runs of 'closed'
    runs, cur = [], 0
    for s in states + [1]:
        if s == 0: cur += 1
        else:
            if cur: runs.append(cur)
            cur = 0
    secs = len(states) / fps
    blinks = [r / fps for r in runs if 2 <= r <= 12]
    longs = [r / fps for r in runs if r > 12]
    flips = sum(1 for a, b in zip(states, states[1:]) if a is not None and b is not None and a != b)
    known = [s for s in states if s is not None]
    return {
        "seconds": secs, "faces_found": len(known) / max(1, len(states)),
        "blinks_per_min": len(blinks) / secs * 60 if secs else 0,
        "avg_blink_s": float(np.mean(blinks)) if blinks else 0.0,
        "long_closures": [round(x, 2) for x in longs],
        "flicker_per_s": flips / secs if secs else 0,
    }

def show(label, r):
    lc = ", ".join(f"{x}s" for x in r["long_closures"]) or "none"
    print(f"{label:<34} {r['seconds']:5.1f}s | face found {r['faces_found']*100:3.0f}% | blinks {r['blinks_per_min']:5.1f}/min (avg {r['avg_blink_s']:.2f}s) | closures >0.5s: {lc} | eye flicker {r['flicker_per_s']:.1f}/s")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    show(sys.argv[1].split("/")[-1], analyse(sys.argv[1]))
    for extra in sys.argv[2:]:
        show("  source: " + extra.split("/")[-1], analyse(extra))
