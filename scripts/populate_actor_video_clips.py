"""One-off / re-runnable script that generates real Veo 3.1 Standard base
clips for Punqle Actors v2 (see the "B" architecture plan) and stores
them in the actor_video_clips table. Not part of the FastAPI app -- run
manually:

    ./venv/bin/python3 scripts/populate_actor_video_clips.py [actor_id ...]

With no args, fills in every actor below that doesn't already have a row
for its assigned situation (safe to re-run -- skips what's already
there). Pass specific actor ids to (re)generate just those -- re-running
an actor_id that already has a row does NOT delete the old row first, so
delete it manually in Supabase before re-running if the goal is to
replace it.

Each clip is an 8-second Veo 3.1 STANDARD generation (Veo's own hard cap
on duration -- confirmed live: durationSeconds must be 4-8) using TWO
real reference photos via the `reference_images` field: the actor's own
persona photo (ASSET) and a real, license-safe photo of the actual
situation/location (ASSET, from Pexels or the founder's own photo for
kitchen). This replaced an earlier single-`image=`-starting-frame,
Lite-tier approach after a real, founder-judged side-by-side (grounding
Marcus's kitchen scene in a real photo of the founder's own kitchen vs.
a text-only prompt) found the reference-image result dramatically more
convincing -- "reference image version-tai bhalo laglo... amra ei rokom
shob base video banaite hobe." `reference_images` only works on
Standard (veo-3.1-generate-preview), not Lite -- confirmed live, Lite
rejects it outright ("referenceImages isn't supported by this model")
-- and cannot be combined with a separate `image=` starting frame at
all (400 INVALID_ARGUMENT). Standard is also ~8x Lite's cost
(~$0.40/sec vs ~$0.05/sec); the founder explicitly accepted this for
the quality gain.

Framing is deliberately front-facing/direct-to-camera throughout --
confirmed via a real, founder-judged side-by-side that this reads as
more natural and more Arcads-like than an over-the-shoulder angle.

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
VEO_MODEL = "veo-3.1-generate-preview"  # Standard tier -- required for reference_images

client = genai.Client(api_key=GEMINI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

_IMAGE_ACTORS_DIR = os.path.join(_ROOT, "assets", "actors")

# Real, license-safe location reference photos the founder hand-picked
# from Pexels (commercial use permitted, no attribution required --
# verified against pexels.com/license), one per situation, plus the
# founder's own real kitchen photo for Marcus. Not committed to the
# repo -- these live in the scratchpad and get copied in during
# implementation; swap this dict's paths if they move.
_LOCATION_REFS_DIR = "/tmp/punqle_test/selected_refs"
_KITCHEN_REF_PATH = "/tmp/punqle_test/kitchen_real.jpg"

# actor_id -> (description [must match _IMAGE_AD_ACTORS in main.py],
#              situation_id, setting description for the Veo prompt)
# setting_desc for each includes a genuine, real activity tied to the
# place -- not just "standing/sitting in X location" -- per real founder
# feedback (2026-09-11) comparing against Arcads' own examples: their
# actors are genuinely doing something in their setting (petting a dog,
# hands on a steering wheel), not just posed in front of a swapped
# background.
_ACTOR_SITUATIONS = {
    "maya": (
        "a warm, friendly woman in her early 30s with long wavy brown hair, light olive skin, wearing a soft cream knit sweater, natural everyday makeup",
        "coffee_shop",
        "She is seated naturally at a small cafe table, her body angled slightly rather than "
        "squared straight to the camera, framed as a relaxed medium-close shot roughly "
        "at her eye level -- as if a phone rests on the table in front of her, or a "
        "friend across the table is holding it, not a professional presenter setup. "
        "One hand rests casually around a real ceramic coffee cup on the table -- just "
        "resting there as a natural anchor for her hand, not drinking from it -- while "
        "her other hand moves naturally in small, easy conversational gestures as she "
        "talks, warm but measured, not big or attention-grabbing. Her expression stays "
        "even and constant across the entire clip -- the same gentle, closed-mouth "
        "warm smile from the first frame to the last, with no big laugh, no widening "
        "or dropping of the smile, and no single standout expression at any point -- "
        "just steady natural blinking and the faintest natural micro-movement around "
        "her eyes and mouth as she speaks. No hair touch, no head tilt, no single "
        "distinct gesture that only happens once -- only continuous, repeatable "
        "motion: small ongoing hand movement, tiny shifts in posture, weight settling "
        "slightly. Behind her, the cafe has its own "
        "independent life -- a barista "
        "moving behind the counter, another customer passing in the soft-focus "
        "background -- happening on its own, not staged around her.",
    ),
    "liam": (
        "a friendly young man in his mid-20s with short dark brown hair, light stubble, tan skin, wearing a relaxed denim jacket over a white t-shirt",
        "car", "sitting in the driver's seat of a car, parked, natural daylight through the windows, the steering wheel clearly visible in frame low in shot, one hand resting on top of the wheel and gesturing naturally with the other while talking, genuinely looking like he is about to drive, not just sitting in the back seat",
    ),
    "sofia": (
        "a confident professional woman in her late 30s with sleek straight black hair, fair skin, wearing a tailored charcoal blazer over a white blouse",
        "office", "standing beside a real desk in a bright, modern office, one hand resting on an open laptop on the desk, occasionally glancing down at it then back up to camera while talking",
    ),
    "noah": (
        "a polished professional man in his 40s with short greying dark hair, a neatly trimmed beard, medium skin tone, wearing a navy blue blazer over a light shirt",
        "airport", "standing in a bright airport terminal, a real travel bag strap over one shoulder, one hand resting on the strap and occasionally adjusting it slightly, wide windows with daylight behind",
    ),
    "ava": (
        "an energetic athletic woman in her mid-20s with a blonde ponytail, fair freckled skin, wearing a fitted grey athletic top, healthy outdoorsy glow",
        "beach", "standing barefoot on a sunny beach, sand visible underfoot, holding a pair of sandals loosely in one hand, ocean softly out of focus behind, light breeze moving her hair and clothing",
    ),
    "ethan": (
        "a rugged outdoorsy man in his early 30s with short wavy brown hair, a light beard, tan weathered skin, wearing a rolled-sleeve flannel shirt",
        "park", "standing on a park path with one hand resting on a wooden railing beside the path, natural daylight, soft green trees and grass in the background",
    ),
    "zara": (
        "an elegant woman in her late 20s with voluminous curly dark hair, deep brown skin, wearing a simple elegant neutral-toned top, soft glam makeup",
        "balcony", "standing at a balcony railing at golden hour, one hand resting on the railing itself, a warm drink in the other hand she occasionally sips from, a soft blurred city skyline behind",
    ),
    "marcus": (
        "a stylish young man in his early 20s with short curly black hair, dark skin, wearing a relaxed graphic t-shirt, friendly approachable smile",
        "kitchen", "standing at a kitchen countertop, both hands resting on the counter edge in front of him, a mug on the counter he occasionally picks up and sets back down, bright home kitchen visible behind",
    ),
    "priya": (
        "a bright, energetic woman in her mid-20s with a dark high ponytail, warm brown skin, wearing a fitted coral athletic top, natural dewy glow",
        "gym", "standing in a bright modern gym with one hand resting on a piece of gym equipment beside her (a rack or bench), a water bottle in the other hand, real gym equipment visible in soft focus behind",
    ),
    "elena": (
        "a poised professional woman in her early 30s with shoulder-length wavy auburn hair, warm tan skin, wearing a fitted emerald green blouse, subtle gold jewelry",
        "restaurant", "seated at a restaurant table, one hand resting near a water glass on the table which she occasionally touches or lifts slightly, warmly-lit upscale restaurant softly visible behind",
    ),
    "hannah": (
        "a cheerful woman in her late 20s with a sleek black bob haircut, fair skin, wearing an oversized soft grey hoodie, fresh natural makeup",
        "bedroom", "sitting cross-legged on a bed, a phone held loosely in one hand resting in her lap that she glances at briefly, bright cozy bedroom with soft morning light behind",
    ),
    "grace": (
        "a warm, graceful woman in her mid-40s with shoulder-length silver-streaked brown hair, light tan skin, wearing a relaxed linen button-up shirt, kind confident smile",
        "garden", "standing in a lush green garden, one hand gently touching the leaves of a nearby plant as she talks, soft natural daylight, more greenery out of focus behind",
    ),
    "diego": (
        "an athletic man in his mid-30s with short black wavy hair, a light beard, warm brown skin, wearing a fitted navy performance polo, easygoing confident smile",
        "boat", "standing on the deck of a boat, one hand gripping the boat's railing, open water visible softly out of focus behind, natural daylight, slight natural sway",
    ),
    "kwame": (
        "a sharp professional man in his late 20s with a short fade haircut, deep brown skin, wearing a fitted grey suit jacket over a black t-shirt, confident modern style",
        "rooftop", "standing at the ledge of a rooftop terrace at golden hour, one hand resting on the ledge itself, city skyline softly out of focus behind",
    ),
    "ravi": (
        "a friendly man in his early 30s with short black hair and thin-framed glasses, medium brown skin, wearing a plain heather-grey crewneck sweatshirt, approachable smile",
        "living_room", "sitting comfortably on a sofa, a mug held in one hand resting on his knee that he occasionally sips from, cozy softly-lit living room behind, leaning slightly toward the camera",
    ),
    "james": (
        "a warm, distinguished man in his mid-50s with short greying hair and a trimmed grey beard, fair skin, wearing a casual open-collar denim shirt, friendly confident expression",
        "bathroom", "standing at a bathroom vanity, one hand resting on the edge of the sink in front of him, a bright well-lit mirror and vanity visible behind, casual morning-routine feel",
    ),
}


def _location_ref_path(situation_id: str) -> str:
    if situation_id == "kitchen":
        return _KITCHEN_REF_PATH
    return os.path.join(_LOCATION_REFS_DIR, f"{situation_id}.jpg")


def _build_prompt(description: str, setting_desc: str) -> str:
    # Shared rules only cover what's genuinely universal across all 16 --
    # camera distance/angle/position, posture, and behavior are each
    # actor's own choice, carried entirely in setting_desc, precisely
    # because forcing one fixed composition ("front-facing shot, talking
    # directly to camera") on every actor was found to flatten all 16
    # into the same generic AI-talking-head feel regardless of situation
    # (real founder feedback, 2026-09-11/12) -- a coffee-shop chat, a
    # restaurant table, a boat deck, and a bedroom should each carry
    # their own distance, angle, and body language, not one template.
    return (
        "This is authentic, casual UGC-style footage -- not a professional "
        "advertisement being performed for a camera crew. The camera itself does "
        "not move during the shot (no push-in, pan, zoom, or handheld sway), but "
        "its distance, angle, and the person's position are specific to this scene, "
        "not a generic fixed composition. "
        "The person from the first reference photo, "
        f"{description}, is genuinely present in the real place shown in the "
        "second reference photo. Preserve that real location exactly as shown -- its "
        "architecture, furniture, materials, colors, lighting direction, depth, and "
        "spatial layout. Do not redesign, beautify, replace, or reinterpret the "
        "location into a generic or more polished version of it. "
        f"{setting_desc} "
        "Their attention returns naturally and warmly to the camera between moments "
        "of the scene, like mid-conversation with whoever is holding the phone -- "
        "never a fixed, unblinking stare at the lens, and never a performance for an "
        "audience. Movement stays subtle and spontaneous: small head shifts, "
        "occasional posture changes -- never a sequence of instructed actions or "
        "deliberate choreography. This clip's audio will later be fully replaced with "
        "different narration for a different ad script, so avoid any single, specific "
        "action whose meaning is tied to this placeholder line -- no eating, drinking, "
        "checking a phone, or other action that only makes sense with particular "
        "words. Physical behavior stays generic and continuous throughout, not a "
        "performance synced to what is being said, since different future dialogue "
        "will play over this exact same movement. Blinks are normal, complete human "
        "blinks -- natural eyelid closure and reopening at a relaxed, ordinary rate -- "
        "never a rolled, rotated, distorted, or repositioned eye, and never rapid or "
        "repeated blinking. "
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

    persona_photo_path = os.path.join(_IMAGE_ACTORS_DIR, f"{actor_id}.jpg")
    with open(persona_photo_path, "rb") as f:
        persona_photo_bytes = f.read()

    location_ref_path = _location_ref_path(situation_id)
    with open(location_ref_path, "rb") as f:
        location_ref_bytes = f.read()

    prompt = _build_prompt(description, setting_desc)
    print(f"[start] {actor_id}/{situation_id}")
    operation = client.models.generate_videos(
        model=VEO_MODEL,
        prompt=prompt,
        config=genai_types.GenerateVideosConfig(
            aspect_ratio="9:16",
            resolution="720p",
            duration_seconds="8",
            reference_images=[
                genai_types.VideoGenerationReferenceImage(
                    image=genai_types.Image(image_bytes=persona_photo_bytes, mime_type="image/jpeg"),
                    reference_type="ASSET",
                ),
                genai_types.VideoGenerationReferenceImage(
                    image=genai_types.Image(image_bytes=location_ref_bytes, mime_type="image/jpeg"),
                    reference_type="ASSET",
                ),
            ],
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
