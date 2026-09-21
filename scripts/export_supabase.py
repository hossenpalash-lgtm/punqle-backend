#!/usr/bin/env python3
"""Free, logical backup of the Punqle Supabase database (the Free plan has NO built-in backups).
Writes every table (+ the auth user list) as JSON to iCloud Drive, keeping the last 5 daily copies.
Secrets are dropped: any column whose name contains token / secret / password is NOT exported (users simply
reconnect Facebook / YouTube / TikTok / Shopify after a restore). actor_video_clips.video_base64 is skipped
(the clips live in actors_v2_approved_base_videos and are re-uploaded with scripts/upload_actor_clip.py).
Standard library only, so it also runs from the scheduled backup app.

  /usr/bin/python3 scripts/export_supabase.py
Restore notes are written next to the export (README.txt).
"""
import glob, json, os, re, shutil, sys, urllib.request, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST_ROOT = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/Punqle-BACKUP/supabase-export")
KEEP_DAYS = 5
SECRET = re.compile(r"token|secret|password", re.I)
SKIP_COLUMNS = {"actor_video_clips": {"video_base64"}}

env = {}
for line in open(os.path.join(ROOT, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
BASE = env["SUPABASE_URL"].rstrip("/")
KEY = env.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("SUPABASE_KEY")
HDR = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

def get(url, extra=None):
    req = urllib.request.Request(url, headers={**HDR, **(extra or {})})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

tables = []
for f in sorted(glob.glob(os.path.join(ROOT, "migrations", "*.sql"))):
    for m in re.finditer(r"create table(?: if not exists)?\s+(?:public\.)?([a-z_0-9]+)", open(f).read(), re.I):
        if m.group(1) not in tables:
            tables.append(m.group(1))

stamp = datetime.date.today().isoformat()
out_dir = os.path.join(DEST_ROOT, stamp)
os.makedirs(out_dir, exist_ok=True)
summary, dropped = [], set()
PAGE_SIZES = (25, 5, 1)   # image tables (~1.7MB a row) time out on big pages, so fall back to smaller ones

def fetch_page(table, start):
    last = None
    for size in PAGE_SIZES:
        try:
            return get(f"{BASE}/rest/v1/{table}?select=*", {"Range-Unit": "items", "Range": f"{start}-{start + size - 1}"}), size
        except Exception as e:
            last = e
    raise last

for t in tables:
    rows, start, failed = [], 0, False
    while True:
        try:
            chunk, size = fetch_page(t, start)
        except Exception as e:
            summary.append(f"{t}: FAILED after {len(rows)} rows ({type(e).__name__})"); failed = True
            break
        rows += chunk
        if len(chunk) < size:
            break
        start += len(chunk)
    if failed:
        continue
    clean = []
    for r in rows:
        keep = {}
        for k, v in r.items():
            if SECRET.search(k):
                dropped.add(f"{t}.{k}"); continue
            if k in SKIP_COLUMNS.get(t, ()):
                continue
            keep[k] = v
        clean.append(keep)
    json.dump(clean, open(os.path.join(out_dir, f"{t}.json"), "w"), ensure_ascii=False)
    summary.append(f"{t}: {len(clean)} rows")

try:
    users, page = [], 1
    while True:
        data = get(f"{BASE}/auth/v1/admin/users?page={page}&per_page=200")
        batch = data.get("users", [])
        users += [{k: u.get(k) for k in ("id", "email", "phone", "created_at", "last_sign_in_at", "app_metadata", "user_metadata")} for u in batch]
        if len(batch) < 200:
            break
        page += 1
    json.dump(users, open(os.path.join(out_dir, "_auth_users.json"), "w"), ensure_ascii=False)
    summary.append(f"_auth_users: {len(users)} users")
except Exception as e:
    summary.append(f"_auth_users: FAILED ({type(e).__name__})")

open(os.path.join(out_dir, "README.txt"), "w").write(
    "Punqle Supabase logical backup, " + stamp + "\n\n" + "\n".join(summary) +
    "\n\nNOT included: columns with token/secret/password in the name (" + ", ".join(sorted(dropped)) + "),"
    " actor_video_clips.video_base64, auth password hashes.\n"
    "Restore: re-create tables from migrations/*.sql, then upsert each JSON file through the REST API with the service key;"
    " users must reset passwords / sign in again and reconnect Facebook, YouTube, TikTok and Shopify.\n")

# keep only the last KEEP_DAYS daily folders
days = sorted(d for d in os.listdir(DEST_ROOT) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d))
for old in days[:-KEEP_DAYS]:
    shutil.rmtree(os.path.join(DEST_ROOT, old), ignore_errors=True)
print("Supabase export ->", out_dir)
print("\n".join(summary))
size = sum(os.path.getsize(os.path.join(out_dir, f)) for f in os.listdir(out_dir))
print(f"export size: {size/1e6:.1f} MB")
