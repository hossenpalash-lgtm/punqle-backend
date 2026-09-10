"""One-off / re-runnable script that generates real Veo 3.1 Lite base
clips for Punqle Actors v2 (see the "B" architecture plan) and stores
them in the actor_video_clips table. Not part of the FastAPI app -- run
manually:

    ./venv/bin/python3 scripts/populate_actor_video_clips.py [actor_id ...]

With no args, fills in every actor below that doesn't already have a row
for its assigned situation (safe to re-run -- skips what's already
there). Pass specific actor ids to (re)generate just those.

Each clip is an 8-second Veo 3.1 Lite generation (Veo's own hard cap --
confirmed live: durationSeconds must be 4-8) using that actor's own
bundled reference photo as the starting frame. Framing is deliberately
front-facing/direct-to-camera throughout -- confirmed via a real,
founder-judged side-by-side that this reads as more natural and more
Arcads-like than an over-the-shoulder angle. Lite (not Standard) was
chosen after a real, founder-judged side-by-side found no visible
quality difference worth Standard's 8x cost for this use case.

16 actors (8 female, 8 male), each assigned one distinct real situation
(from Arcads' own published "Situation" tag list, per the founder's own
screenshot -- excluding pure camera-move tags like Dolly/Crane/Arc,
which aren't settings) so the library reads as varied, not repetitive,
across the range of businesses that will use it."""
import base64
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types as genai_types
from supabase import create_client

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _getenv(name: str) -> str:
    env_text = open(os.path.join(_ROOT, ".env")).read()
    m = re.search(rf"^{name}=(.+)$", env_text, re.M)
    if not m:
        raise RuntimeError(f"{name} not found in .env")
    return m.group(1).strip()


GEMINI_API_KEY = _getenv("GEMINI_API_KEY")
SUPABASE_URL = _getenv("SUPABASE_URL")
SUPABASE_KEY = _getenv("SUPABASE_KEY")
VEO_MODEL = "veo-3.1-lite-generate-preview"

client = genai.Client(api_key=GEMINI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

_IMAGE_ACTORS_DIR = os.path.join(_ROOT, "assets", "actors")

# actor_id -> (description [must match _IMAGE_AD_ACTORS in main.py],
#              situation_id, setting description for the Veo prompt)
_ACTOR_SITUATIONS = {
    "maya": (
        "a warm, friendly woman in her early 30s with long wavy brown hair, light olive skin, wearing a soft cream knit sweater, natural everyday makeup",
        "coffee_shop", "sitting at a small table in a cozy, warmly-lit coffee shop, a coffee cup nearby",
    ),
    "liam": (
        "a friendly young man in his mid-20s with short dark brown hair, light stubble, tan skin, wearing a relaxed denim jacket over a white t-shirt",
        "car", "sitting in the driver's seat of a car, parked, natural daylight through the windows, one hand on the wheel",
    ),
    "sofia": (
        "a confident professional woman in her late 30s with sleek straight black hair, fair skin, wearing a tailored charcoal blazer over a white blouse",
        "office", "standing in a bright, modern office space, confident posture",
    ),
    "noah": (
        "a polished professional man in his 40s with short greying dark hair, a neatly trimmed beard, medium skin tone, wearing a navy blue blazer over a light shirt",
        "airport", "standing in a bright, modern airport terminal, a travel bag over one shoulder, wide windows with daylight behind",
    ),
    "ava": (
        "an energetic athletic woman in her mid-20s with a blonde ponytail, fair freckled skin, wearing a fitted grey athletic top, healthy outdoorsy glow",
        "beach", "standing on a sunny beach, ocean softly out of focus behind, light breeze in her hair",
    ),
    "ethan": (
        "a rugged outdoorsy man in his early 30s with short wavy brown hair, a light beard, tan weathered skin, wearing a rolled-sleeve flannel shirt",
        "park", "standing outdoors in natural daylight, a park setting with soft green background",
    ),
    "zara": (
        "an elegant woman in her late 20s with voluminous curly dark hair, deep brown skin, wearing a simple elegant neutral-toned top, soft glam makeup",
        "balcony", "standing on a balcony at golden hour, warm soft light, a soft blurred city or skyline behind",
    ),
    "marcus": (
        "a stylish young man in his early 20s with short curly black hair, dark skin, wearing a relaxed graphic t-shirt, friendly approachable smile",
        "kitchen", "standing in a bright home kitchen, countertop visible behind, casual and relaxed",
    ),
    "priya": (
        "a bright, energetic woman in her mid-20s with a dark high ponytail, warm brown skin, wearing a fitted coral athletic top, natural dewy glow",
        "gym", "standing in a bright, modern gym space, energetic posture, soft blurred equipment behind",
    ),
    "elena": (
        "a poised professional woman in her early 30s with shoulder-length wavy auburn hair, warm tan skin, wearing a fitted emerald green blouse, subtle gold jewelry",
        "restaurant", "seated at a table in a warmly-lit, upscale restaurant, soft ambient background",
    ),
    "hannah": (
        "a cheerful woman in her late 20s with a sleek black bob haircut, fair skin, wearing an oversized soft grey hoodie, fresh natural makeup",
        "bedroom", "sitting comfortably on a bed in a bright, cozy bedroom, soft natural morning light",
    ),
    "grace": (
        "a warm, graceful woman in her mid-40s with shoulder-length silver-streaked brown hair, light tan skin, wearing a relaxed linen button-up shirt, kind confident smile",
        "garden", "standing in a lush green garden, soft natural daylight, plants softly out of focus behind",
    ),
    "diego": (
        "an athletic man in his mid-30s with short black wavy hair, a light beard, warm brown skin, wearing a fitted navy performance polo, easygoing confident smile",
        "boat", "standing on the deck of a boat, open water softly out of focus behind, natural daylight",
    ),
    "kwame": (
        "a sharp professional man in his late 20s with a short fade haircut, deep brown skin, wearing a fitted grey suit jacket over a black t-shirt, confident modern style",
        "rooftop", "standing on a rooftop terrace at golden hour, city skyline softly out of focus behind",
    ),
    "ravi": (
        "a friendly man in his early 30s with short black hair and thin-framed glasses, medium brown skin, wearing a plain heather-grey crewneck sweatshirt, approachable smile",
        "living_room", "sitting comfortably in a cozy, softly-lit living room, leaning slightly toward the camera",
    ),
    "james": (
        "a warm, distinguished man in his mid-50s with short greying hair and a trimmed grey beard, fair skin, wearing a casual open-collar denim shirt, friendly confident expression",
        "bathroom", "standing in front of a bright bathroom mirror/vanity area, clean and well-lit, casual morning routine feel",
    ),
}


def _build_prompt(description: str, setting_desc: str) -> str:
    return (
        "Strict front-facing shot, looking directly at the camera (like a phone held "
        "at arm's length or propped up facing the subject head-on) -- NOT an "
        "over-the-shoulder or three-quarter angle. "
        f"{description}, {setting_desc}, talking directly and warmly to the "
        "camera with natural hand gestures, occasional small idle movements (a slight "
        "head tilt, a natural blink), subtle natural motion in the background. "
        'They say, "Hi, let me tell you about something I think you will love." '
        "in a warm, natural, conversational voice. "
        "Realistic, professional lighting, shallow depth of field, natural skin tones."
    )


def _existing_situation_ids(actor_id: str) -> set:
    res = supabase.table("actor_video_clips").select("situation_id").eq("actor_id", actor_id).execute()
    return {row["situation_id"] for row in (res.data or [])}


def generate_one(actor_id: str) -> None:
    description, situation_id, setting_desc = _ACTOR_SITUATIONS[actor_id]
    if situation_id in _existing_situation_ids(actor_id):
        print(f"[skip] {actor_id}/{situation_id} already exists")
        return

    photo_path = os.path.join(_IMAGE_ACTORS_DIR, f"{actor_id}.jpg")
    with open(photo_path, "rb") as f:
        photo_bytes = f.read()

    prompt = _build_prompt(description, setting_desc)
    print(f"[start] {actor_id}/{situation_id}")
    operation = client.models.generate_videos(
        model=VEO_MODEL,
        prompt=prompt,
        image=genai_types.Image(image_bytes=photo_bytes, mime_type="image/jpeg"),
        config=genai_types.GenerateVideosConfig(
            aspect_ratio="9:16",
            resolution="720p",
            duration_seconds="8",
        ),
    )

    deadline = time.time() + 400
    while not operation.done and time.time() < deadline:
        time.sleep(10)
        operation = client.operations.get(operation)

    if not operation.done:
        print(f"[timeout] {actor_id}/{situation_id} still running after 400s, skipping")
        return
    if operation.error:
        print(f"[error] {actor_id}/{situation_id}: {operation.error}")
        return

    result = operation.result or operation.response
    if not result or not result.generated_videos:
        print(f"[error] {actor_id}/{situation_id}: no video returned")
        return

    video = result.generated_videos[0].video
    video_bytes = client.files.download(file=video)
    video_b64 = base64.b64encode(video_bytes).decode("ascii")

    supabase.table("actor_video_clips").insert({
        "actor_id": actor_id,
        "situation_id": situation_id,
        "video_base64": video_b64,
    }).execute()
    print(f"[done] {actor_id}/{situation_id} -- {len(video_bytes)} bytes stored")


def main() -> None:
    requested_ids = set(sys.argv[1:]) or None
    for actor_id in _ACTOR_SITUATIONS:
        if requested_ids and actor_id not in requested_ids:
            continue
        generate_one(actor_id)


if __name__ == "__main__":
    main()
