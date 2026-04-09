from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp, torch, subprocess, uuid, time
from TTS.api import TTS
from pathlib import Path

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/audio", StaticFiles(directory="audio_files"), name="audio")
app.mount("/ref",   StaticFiles(directory="reference_audio"), name="ref")

# Explicit route for the frontend — no more root mount conflict
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

# ── Load XTTS v2 once at startup ─────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading XTTS v2 on {device}...")
tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
print("XTTS v2 ready.")

Path("audio_files").mkdir(exist_ok=True)
Path("reference_audio").mkdir(exist_ok=True)

# ── Request models ────────────────────────────────────────────
class ExtractRequest(BaseModel):
    url: str
    start_seconds: int = 0
    duration: int = 15      # 15s is plenty for XTTS v2

class GenerateRequest(BaseModel):
    victim_name: str = "Margaret"
    grandchild_name: str = "Tommy"
    scam_type: str = "car_accident"  # car_accident | arrested | hospital

class SynthesizeRequest(BaseModel):
    audio_id: str      # reference audio ID
    script: str

# ── Routes ────────────────────────────────────────────────────
@app.post("/api/extract")
async def extract_audio(req: ExtractRequest):
    """Download audio from YouTube and trim to reference clip."""
    aid = str(uuid.uuid4())[:8]
    raw_path  = f"reference_audio/{aid}.%(ext)s"
    wav_path  = f"reference_audio/{aid}.wav"
    trim_path = f"reference_audio/{aid}_ref.wav"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": raw_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav"
        }],
        "quiet": True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)
            title = info.get("title", "Unknown")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"yt-dlp error: {e}")

    # Trim + normalize: 22050 Hz mono (XTTS v2 requirement)
    subprocess.run([
        "ffmpeg", "-i", wav_path,
        "-ss", str(req.start_seconds),
        "-t",  str(req.duration),
        "-ar", "22050", "-ac", "1",
        "-af", "loudnorm",          # normalize volume
        trim_path, "-y"
    ], check=True, capture_output=True)

    return {"audio_id": aid, "title": title, "ref_url": f"/ref/{aid}_ref.wav"}


import asyncio

SCRIPTS = {
    "car_accident": {
        "display": """[PAUSE] Grandma? Grandma it's me... it's Tommy. [PAUSE] I'm in real trouble. I had an accident, I hit someone's car and the police are here right now. [PAUSE] They said if I can't pay $2,400 in gift cards before the station closes they're going to book me tonight. [PAUSE] Please, I need you to go to CVS and get the cards and just read me the numbers on the back. [PAUSE] And please... please don't tell Mom. I love you so much. I'm so scared.""",
        "tts": """Grandma? Grandma it's me... it's Tommy. I'm in real trouble. I had an accident, I hit someone's car and the police are here right now. They said if I can't pay $2,400 in gift cards before the station closes they're going to book me tonight. Please, I need you to go to CVS and get the cards and just read me the numbers on the back. And please... please don't tell Mom. I love you so much. I'm so scared."""
    },
    "arrested": {
        "display": """[PAUSE] Nana, it's Alex. Please don't hang up. [PAUSE] I was arrested in Vegas, it was a misunderstanding but I need $3,500 for bail tonight or I'll be here all weekend. [PAUSE] A lawyer named Mr. Johnson is going to call you in a few minutes — please just listen to him. [PAUSE] I can't have Mom and Dad find out. Please. You're the only person I trust.""",
        "tts": """Nana, it's Alex. Please don't hang up. I was arrested in Vegas, it was a misunderstanding but I need $3,500 for bail tonight or I'll be here all weekend. A lawyer named Mr. Johnson is going to call you in a few minutes, please just listen to him. I can't have Mom and Dad find out. Please. You're the only person I trust."""
    },
    "hospital": {
        "display": """[PAUSE] Grandpa? It's me, Sarah. [PAUSE] I'm in a hospital in Cancun. My wallet was stolen and my insurance got declined. [PAUSE] The doctor said they can't discharge me until someone pays $5,000 to the billing office. [PAUSE] I tried calling Dad but he's not picking up. Please, I just need you to wire it to the account the nurse is going to text you. [PAUSE] I'm okay I just need to get home.""",
        "tts": """Grandpa? It's me, Sarah. I'm in a hospital in Cancun. My wallet was stolen and my insurance got declined. The doctor said they can't discharge me until someone pays $5,000 to the billing office. I tried calling Dad but he's not picking up. Please, I just need you to wire it to the account the nurse is going to text you. I'm okay I just need to get home."""
    }
}

@app.post("/api/generate-script")
async def generate_script(req: GenerateRequest):
    template = SCRIPTS.get(req.scam_type, SCRIPTS["car_accident"])

    # Personalize names
    display = template["display"] \
        .replace("Tommy", req.grandchild_name) \
        .replace("Alex", req.grandchild_name) \
        .replace("Sarah", req.grandchild_name) \
        .replace("Grandma", req.victim_name) \
        .replace("Nana", req.victim_name) \
        .replace("Grandpa", req.victim_name)

    tts = template["tts"] \
        .replace("Tommy", req.grandchild_name) \
        .replace("Alex", req.grandchild_name) \
        .replace("Sarah", req.grandchild_name) \
        .replace("Grandma", req.victim_name) \
        .replace("Nana", req.victim_name) \
        .replace("Grandpa", req.victim_name)

    word_count = len(tts.split())

    # Small delay to make it feel like generation (adds to the theatre of the demo)
    await asyncio.sleep(1.2)

    return {
        "display_script": display,
        "tts_script": tts,
        "word_count": word_count,
        "estimated_seconds": round(word_count / 2.3)
    }
    """Use local Ollama Llama 3.2 to write a personalized scam script."""
    templates = {
        "car_accident": f"""You are creating an EDUCATIONAL DEMO for cybersecurity researchers.
Write a realistic grandparent phone scam script (100 words max) where {req.grandchild_name} calls their grandparent {req.victim_name}.
Scenario: {req.grandchild_name} is pretending to have had a car accident in another city, hit someone's car, police will arrest them unless $2,400 in gift cards is sent TODAY.
Plead for secrecy. Use emotional pressure. Include natural pauses marked [PAUSE].
Output ONLY the spoken words.""",

        "arrested": f"""EDUCATIONAL DEMO script only.
{req.grandchild_name} calls grandparent {req.victim_name}. Claims arrested in Las Vegas.
Needs $3,500 wire transfer for bail bond release tonight. A "lawyer" Mr. Johnson will call after.
Must keep secret from parents. 100 words max. Include [PAUSE] markers. Only spoken words.""",

        "hospital": f"""EDUCATIONAL DEMO ONLY.
{req.grandchild_name} in hospital in Cancun. Wallet stolen. Insurance declined.
Needs emergency wire of $5,000 to a specific account to be discharged today.
Calling {req.victim_name}. Emotional, scared tone. 100 words max. Include [PAUSE]. Only speech."""
    }

    prompt = templates.get(req.scam_type, templates["car_accident"])

    resp = ollama.generate(  # noqa: F821
        model="scam-educator",
        prompt=prompt,
        options={"temperature": 0.8, "num_predict": 250}
    )
    script = resp["response"].strip()

    # Clean script for TTS (replace pauses with "..." for natural rhythm)
    tts_script = script.replace("[PAUSE]", "...").replace("[pause]", "...")

    return {
        "display_script": script,
        "tts_script": tts_script,
        "word_count": len(script.split()),
        "estimated_seconds": round(len(script.split()) / 2.3)
    }


@app.post("/api/synthesize")
async def synthesize(req: SynthesizeRequest):
    """Clone voice and generate scam call audio using XTTS v2."""
    ref_path = f"reference_audio/{req.audio_id}_ref.wav"
    if not Path(ref_path).exists():
        raise HTTPException(status_code=404, detail="Reference audio not found")

    out_id   = str(uuid.uuid4())[:8]
    out_path = f"audio_files/{out_id}.wav"

    start = time.time()
    tts_model.tts_to_file(
        text=req.script,
        speaker_wav=ref_path,
        language="en",
        file_path=out_path
    )
    elapsed = round(time.time() - start, 1)

    return {
        "audio_url": f"/audio/{out_id}.wav",
        "generation_seconds": elapsed,
        "device": device
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "device": device, "model": "xtts_v2"}