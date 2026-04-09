# 🎙️ AI Grandparent Voice Scam Simulator

Given 15 seconds of audio from any public source, the app clones that voice and synthesizes a realistic grandparent phone scam — entirely locally, with zero API costs.

> ⚠️ **This tool is for educational purposes only.** It was created to show how accessible AI voice cloning has become.

---

## Demo

A step-by-step walkthrough:
1. Paste a YouTube URL (any video with clear speech — a news clip, TED talk, etc.)
2. The app extracts 15 seconds of reference audio using `yt-dlp`
3. A pre-written scam script is personalized with the victim/grandchild names you provide
4. Coqui XTTS v2 synthesizes the script in the cloned voice — fully locally
5. An iPhone-style call UI plays back the result with a live transcript

**Total cost: $0.00. No API keys. No cloud.**

---

## System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| OS | macOS 12+ / Ubuntu 20.04+ | macOS (Apple Silicon) |
| Python | 3.10 | 3.11 |
| RAM | 8 GB | 16 GB |
| Disk | 5 GB free | 10 GB free |
| GPU | Not required | Apple Silicon MPS or NVIDIA CUDA |

> ⏱️ Generation time: ~2–5 min on CPU, ~30–60s on Apple Silicon MPS, ~15s on NVIDIA GPU.

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/grandparent-scam-demo
cd grandparent-scam-demo
```

### 2. Install system dependencies

**macOS:**
```bash
brew install ffmpeg python@3.11
```


### 3. Create a virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate       
```

### 4. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```



### 5. Apply the XTTS v2 / transformers compatibility patch

Coqui XTTS v2 uses an API removed in `transformers>=5.0`. Patch it with one command:

```bash
sed -i '' \
  's/from transformers.pytorch_utils import isin_mps_friendly as isin/import torch; isin = torch.isin/' \
  venv/lib/python3.11/site-packages/TTS/tts/layers/tortoise/autoregressive.py
```

**Linux:**
```bash
sed -i \
  's/from transformers.pytorch_utils import isin_mps_friendly as isin/import torch; isin = torch.isin/' \
  venv/lib/python3.11/site-packages/TTS/tts/layers/tortoise/autoregressive.py
```

### 6. Verify the installation

```bash
python -c "
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
import torch
from TTS.api import TTS
print('PyTorch:', torch.__version__)
print('MPS available:', torch.backends.mps.is_available())
print('TTS import: OK')
"
```

Expected output:
```
PyTorch: 2.5.1
MPS available: True      ← True on Apple Silicon, False on CPU-only
TTS import: OK
```

---

## Pre-generating Demo Audio

Pre-generate audio clips before any live presentation so synthesis never blocks the demo.

### Step 1 — Get a reference voice clip

```bash
# Download audio from any YouTube video with clear speech
yt-dlp -x --audio-format wav \
  -o "reference_audio/demo_ref.%(ext)s" \
  "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"

# Trim and normalize for XTTS v2
ffmpeg -i reference_audio/demo_ref.wav \
  -ss 5 -t 15 \
  -ar 22050 -ac 1 \
  -af loudnorm \
  reference_audio/demo_trimmed.wav -y
```

### Step 2 — Run the pre-generation script

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 python pregenerate_demo.py
```

This generates two pre-baked audio files in `audio_files/`:
- `preset_car_accident.wav`
- `preset_arrested.wav`

---

## Running the App

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at **http://localhost:8000**

---

## Project Structure

```
grandparent-scam-demo/
├── main.py                    # FastAPI backend — audio extraction, synthesis routes
├── pregenerate_demo.py        # One-time script to pre-bake demo audio clips
├── requirements.txt
├── Modelfile                  # Ollama modelfile
├── frontend/
│   └── index.html             # Full demo UI — iPhone call mockup, transcript, pipeline
├── reference_audio/           # Reference voice clips (gitignored)
│   ├── demo_ref.wav
│   └── demo_trimmed.wav
└── audio_files/               # Generated output audio (gitignored)
    ├── preset_car_accident.wav
    └── preset_arrested.wav
```

---

## Demo Presentation

The app is most effective when presented without narration:

| Time | Action |
|---|---|
| 0–15s | Open the app. Show the YouTube URL field. Say: *"This is all the attacker needs — 15 seconds from any public video."* Paste a URL and click **Extract Audio**. |
| 15–35s | Fill in victim/grandchild names. Select scenario. Click **Generate Script**. Let the transcript appear. Stay silent. |
| 35–65s | Click **▶ Play** on the iPhone UI. Let the audio play while the transcript scrolls. Do not narrate. |
| 65–90s | Point to the stats bar: *"Cost: $0.00. Generation time: Xs. Source audio needed: 15 seconds. The FBI reports grandparent scams cost Americans $74M last year — before AI voice cloning existed."* |

---

## Tech Stack

| Component | Technology |
|---|---|
| Voice Cloning | Coqui XTTS v2 (local, open-source) |
| Audio Extraction | yt-dlp |
| Audio Processing | FFmpeg + pydub |
| Backend | Python / FastAPI |
| Frontend | Vanilla HTML/CSS/JS |
| Cost | $0.00 |

---


**Synthesis sounds robotic / low quality**  
The reference audio clip needs to be clean speech with minimal background noise. Use a clip where the speaker is close to the microphone. Avoid clips with music, crowds, or reverb.

---

## Ethical Notice

This tool demonstrates real capabilities that are accessible to malicious actors today. 
