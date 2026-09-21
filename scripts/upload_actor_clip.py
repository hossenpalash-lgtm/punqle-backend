#!/usr/bin/env python3
"""Put an approved Punqle Actors v2 base video into the `actor_video_clips` table.

Dry run by default. With --apply it (1) saves every existing clip row of that actor to a backup
folder, (2) deletes the actor's OTHER rows (an actor must have exactly one clip: the identity in the
picker photo has to match the identity in the video, and the endpoint picks randomly among an
actor's rows), then (3) inserts/replaces the (actor, situation) row.

Usage:
  python3 scripts/upload_actor_clip.py --actor maya --situation kitchen \
      --video actors_v2_approved_base_videos/kitchen/final_base_video.mp4 [--apply]

Uses the service key from the backend .env (never printed). The clip is stored as base64 text.
"""
import argparse, base64, os, subprocess, sys, requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(ROOT, "actors_v2_approved_base_videos", "_replaced_old_clips")


def load_env():
    env = {}
    for line in open(os.path.join(ROOT, ".env")):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout
    kinds = [l.split(",")[0] for l in out.strip().splitlines() if l]
    dur = max([float(l.split(",")[1]) for l in out.strip().splitlines() if l and l.split(",")[1] not in ("", "N/A")] or [0])
    return kinds, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--actor", required=True)
    ap.add_argument("--situation", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    kinds, dur = probe(a.video)
    size = os.path.getsize(a.video)
    print(f"video: {a.video}\n  streams={kinds} duration={dur:.1f}s size={size/1e6:.1f}MB (base64 ≈ {size*4/3/1e6:.1f}MB)")
    if "audio" in kinds:
        sys.exit("Refusing: the clip still has an audio track (a real person's voice may be in it). Strip it with -an first.")
    if dur > 30.5:
        sys.exit("Refusing: longer than 30s.")

    env = load_env()
    url = env["SUPABASE_URL"].rstrip("/") + "/rest/v1/actor_video_clips"
    key = env.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("SUPABASE_KEY")
    H = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    rows = requests.get(f"{url}?actor_id=eq.{a.actor}&select=id,situation_id,created_at,video_base64", headers=H, timeout=180).json()
    print(f"existing rows for '{a.actor}': " + (", ".join(r['situation_id'] + " (" + r['created_at'][:10] + ")" for r in rows) or "none"))
    others = [r for r in rows if r["situation_id"] != a.situation]
    print(f"would delete {len(others)} other row(s); would upsert {a.actor}/{a.situation}")
    if not a.apply:
        print("DRY RUN — nothing changed. Add --apply to do it.")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    for r in rows:
        p = os.path.join(BACKUP_DIR, f"{a.actor}_{r['situation_id']}_{r['created_at'][:10]}.mp4")
        open(p, "wb").write(base64.b64decode(r["video_base64"]))
        print(f"  backed up old clip -> {p}")
    b64 = base64.b64encode(open(a.video, "rb").read()).decode("ascii")
    r = requests.post(url + "?on_conflict=actor_id,situation_id", timeout=600,
                      headers={**H, "Prefer": "resolution=merge-duplicates,return=minimal"},
                      json={"actor_id": a.actor, "situation_id": a.situation, "video_base64": b64})
    if not r.ok:
        sys.exit(f"Upsert failed: HTTP {r.status_code} {r.text[:300]} (old rows NOT deleted)")
    for o in others:
        d = requests.delete(f"{url}?id=eq.{o['id']}", headers=H, timeout=60)
        print(f"  deleted old row {o['situation_id']}: HTTP {d.status_code}")
    print("done.")


if __name__ == "__main__":
    main()
