Fast PDF → Audiobook (Python + Streamlit) 🎧

Turn long PDFs into clean, listenable MP3s—fast.
This Streamlit app extracts text, detects chapters, converts to speech via your preferred TTS engine, and exports either per-chapter files or a single merged audiobook.

Live write-up: Fast PDF → Audiobook in Minutes with Python + Streamlit

✨ Features

Drag & drop PDF → quick text extraction (optimized for digital PDFs)

Chapter detection (e.g., “Chapter 1”, “Chapter 2”…), with multi-select UI

Multiple TTS engines (pick one per run):

Edge TTS (neural, natural prosody)

gTTS (simple baseline, multilingual)

pyttsx3 (fully offline, adjustable rate)

Coqui XTTS v2 (optional integration)

Chunked synthesis (~5k chars) for stability and speed

Loudness alignment so chapters sound consistent

One-click merge to produce a single MP3 with tasteful pauses

Timestamped filenames saved next to the script for easy sharing

🖥️ Requirements

Python ≥ 3.9

FFmpeg (required by pydub for reading/writing audio)

For optional OCR (scanned PDFs): Tesseract + PyMuPDF (fitz)

📦 Installation
# Create & activate a virtual environment (recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Core deps
pip install streamlit PyPDF2 gTTS pyttsx3 pydub pillow numpy requests

# Optional: better neural voices
pip install edge-tts

# Optional: OCR stack (if you need to read scanned PDFs)
pip install pymupdf pytesseract
# Also install Tesseract binary on your OS (e.g., apt/brew/choco)

# Optional: Coqui XTTS v2 (integration snippet below)
pip install TTS


FFmpeg:

macOS: brew install ffmpeg

Ubuntu/Debian: sudo apt-get install ffmpeg

Windows (scoop): scoop install ffmpeg (or download from ffmpeg.org and add to PATH)

🚀 Run
streamlit run book_voice_studio.py


Then open the local URL Streamlit prints (usually http://localhost:8501).

🧭 Usage (in the app)

Upload PDF (and optionally a short voice sample if you plan to use volume matching).

Click Extract Text → chapters appear in the right panel.

Select chapters you want to render.

Pick a TTS engine (Edge TTS / gTTS / pyttsx3 / Coqui XTTS v2, if added).

Click Generate → the app synthesizes by chunks, then stitches into chapters.

Download per-chapter MP3s and/or a merged audiobook. 🎧

🗣️ TTS Engines

Edge TTS — Neural voices with natural prosody (internet required).

gTTS — Simple baseline, multilingual (internet required).

pyttsx3 — Fully offline; control speaking rate locally.

Coqui XTTS v2 — (Optional) multilingual, expressive; supports short-sample voice adaptation.

Choose one in the UI each time you render. You can switch engines between runs.

🧩 Optional: Add Coqui XTTS v2 Integration

This repo’s core script focuses on Edge TTS, gTTS, and pyttsx3.
If you want Coqui XTTS v2, you can add it with the following minimal snippet.

Install:

pip install TTS pydub


Add this helper to book_voice_studio.py (near your other TTS methods):

def generate_with_coqui_xtts(self, text, output_path, speaker_wav=None, language="en"):
    """
    Coqui XTTS v2 synthesis to MP3.
    Requires: pip install TTS pydub
    """
    from TTS.api import TTS
    from pydub import AudioSegment
    import os
    # Load the multilingual XTTS v2 model (downloads on first use)
    model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts = TTS(model_name)

    # Generate a wav first (XTTS outputs wav)
    tmp_wav = output_path.replace(".mp3", ".wav")
    tts.tts_to_file(
        text=text,
        file_path=tmp_wav,
        speaker_wav=speaker_wav,   # Optional: path to a short reference voice sample
        language=language          # e.g., "en", "hi", "ur", etc.
    )

    # Convert wav → mp3 for consistency with the rest of the app
    AudioSegment.from_wav(tmp_wav).export(output_path, format="mp3", bitrate="192k")
    try:
        os.remove(tmp_wav)
    except OSError:
        pass


Wire it into your engine selector, e.g.:

if selected_engine == "Coqui XTTS v2":
    success = self.generate_with_coqui_xtts(chunk, temp_audio.name, speaker_wav=voice_sample_path, language=coqui_lang)


UI addition (example):

Add "Coqui XTTS v2" to your engine dropdown.

Add an optional language selector and an optional file uploader for speaker_wav.

🔧 Configuration Tips

Chunk size: default is ~5000 characters for speed/stability.

Rate & voice (pyttsx3): adjustable; behavior varies by OS TTS backend.

Loudness alignment: keeps chapters’ perceived volume similar; it’s not “voice cloning.”

OCR: for scanned PDFs, enable a branch that uses PyMuPDF (fitz) for images + Tesseract for text.

📂 Project Structure
pdftoAudiobook/
├─ book_voice_studio.py        # Streamlit app
├─ README.md                   # This file
├─ requirements.txt            # (optional) pin your deps
└─ output/                     # (app writes MP3s here or alongside script)


(Your actual layout may differ; update as needed.)

⚠️ Known Limitations

No OCR by default → scanned PDFs need the optional OCR path.

Simple chapter regex → customize if your headings are nonstandard.

Network dependence → Edge TTS & gTTS require an internet connection.

FFmpeg required → pydub needs FFmpeg available on PATH.

🗺️ Roadmap

OCR fallback toggle (PyMuPDF + Tesseract)

SSML controls (pauses, emphasis) where supported

Per-section voices (dialogue vs. narration)

Export to M4B with chapter markers

🤝 Contributing

Issues and PRs are welcome!

Open an issue with steps to reproduce and environment details.

For new engines or features, keep the UI simple and default flows fast.

📜 License

Add a LICENSE file (e.g., MIT/Apache-2.0). If you’ve already chosen one, update this section to match.

🔗 Links

Medium blog: https://medium.com/@ameersultan0310/fast-pdf-audiobook-in-minutes-with-python-streamlit-13acce36f2a5

GitHub repo: https://github.com/Ameer3716/pdftoAudiobook
