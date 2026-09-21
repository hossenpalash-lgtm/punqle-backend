#!/usr/bin/env python3
"""Remove actors' base clips from `actor_video_clips` (the actors then stop being selectable in Talking Actors).
Dry run by default. With --apply it first saves each clip to actors_v2_approved_base_videos/_replaced_old_clips/, then deletes the rows.
Does NOT touch the actor roster, photos or descriptions — only the clips.

  python3 scripts/remove_actor_clips.py --actors sofia,noah,zara [--apply]
"""
import argparse, base64, os, sys, requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(ROOT, "actors_v2_approved_base_videos", "_replaced_old_clips")

env = {}
for line in open(os.path.join(ROOT, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
URL = env["SUPABASE_URL"].rstrip("/") + "/rest/v1/actor_video_clips"
KEY = env.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("SUPABASE_KEY")
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

ap = argparse.ArgumentParser()
ap.add_argument("--actors", required=True)
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()
ids = [x.strip() for x in a.actors.split(",") if x.strip()]

rows = []
for actor in ids:
    r = requests.get(f"{URL}?actor_id=eq.{actor}&select=id,actor_id,situation_id,created_at,video_base64", headers=H, timeout=180)
    r.raise_for_status()
    rows += r.json()
print("clips found:", ", ".join(f"{r['actor_id']}/{r['situation_id']} ({r['created_at'][:10]})" for r in rows) or "none")
if not a.apply:
    print(f"DRY RUN — would back up and delete {len(rows)} clip(s). Add --apply to do it.")
    sys.exit(0)
os.makedirs(BACKUP_DIR, exist_ok=True)
for r in rows:
    p = os.path.join(BACKUP_DIR, f"{r['actor_id']}_{r['situation_id']}_{r['created_at'][:10]}.mp4")
    open(p, "wb").write(base64.b64decode(r["video_base64"]))
missing = [r for r in rows if not os.path.exists(os.path.join(BACKUP_DIR, f"{r['actor_id']}_{r['situation_id']}_{r['created_at'][:10]}.mp4"))]
if missing:
    sys.exit("Backup failed for some clips — nothing deleted.")
for r in rows:
    d = requests.delete(f"{URL}?id=eq.{r['id']}", headers=H, timeout=60)
    print(f"  deleted {r['actor_id']}/{r['situation_id']}: HTTP {d.status_code}")
print("done.")
