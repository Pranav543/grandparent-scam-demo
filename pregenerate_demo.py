# pregenerate_demo.py  — run ONCE before your demo
import torch
from TTS.api import TTS
from pathlib import Path

Path("audio_files").mkdir(exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# You need a reference WAV first — download one manually via:
# yt-dlp -x --audio-format wav -o "reference_audio/demo_ref.%(ext)s" "YOUR_YOUTUBE_URL"
# Then run: ffmpeg -i reference_audio/demo_ref.wav -t 15 -ar 22050 -ac 1 reference_audio/demo_trimmed.wav

scripts = {
    "car_accident": "Grandma? Grandma it's me, Tommy. [pause] I'm in real trouble. I had an accident, I hit someone's car and the police are here. [pause] I need you to get $2,400 in gift cards from CVS right now or they're going to take me to jail. [pause] Please, please don't tell Mom. Just get the cards and scratch the back and read me the numbers. I love you.",
    "arrested":     "Nana, it's Alex. Please don't hang up. [pause] I was arrested in Vegas, it was a misunderstanding but I need $3,500 for bail tonight or I'll be here all weekend. [pause] A lawyer named Mr. Johnson is going to call you in a few minutes. Please just trust him. And please, please don't tell Dad. I'm so scared."
}

ref_wav = "reference_audio/demo_trimmed.wav"

for name, script in scripts.items():
    out = f"audio_files/preset_{name}.wav"
    print(f"Generating {name}...")
    tts.tts_to_file(text=script, speaker_wav=ref_wav, language="en", file_path=out)
    print(f"  ✓ Saved to {out}")

print("\nAll demo audio pre-generated. Ready for live demo!")