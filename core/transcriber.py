import os
import whisper


# =========================================================
# WHISPER CONFIGURATION
# =========================================================

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")

_model = None


# =========================================================
# LOAD WHISPER MODEL
# =========================================================

def load_model():
    global _model

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL}...")

        _model = whisper.load_model(
            WHISPER_MODEL,
            device="cpu"
        )

        print("Whisper model loaded successfully.")

    return _model


# =========================================================
# TRANSCRIBE ONE AUDIO CHUNK
# =========================================================

def transcribe_chunk(chunk_path: str, translate: bool = False) -> str:

    model = load_model()

    task = "translate" if translate else "transcribe"

    print(f"Processing: {chunk_path}")

    result = model.transcribe(
        chunk_path,
        task=task,
        fp16=False
    )

    text = result.get("text", "").strip()

    return text


# =========================================================
# TRANSCRIBE ALL AUDIO CHUNKS
# =========================================================

def all_chunks(chunks: list, translate: bool = False) -> str:

    if not chunks:
        return ""

    full_transcript = []

    total_chunks = len(chunks)

    for i, chunk in enumerate(chunks):

        print(f"\nTranscribing chunk {i + 1}/{total_chunks}")

        text = transcribe_chunk(
            chunk,
            translate=translate
        )

        if text:
            full_transcript.append(text)

        print(f"Chunk {i + 1}/{total_chunks} completed")

    # Combine all chunks
    transcript = " ".join(full_transcript).strip()

    print("\nAll chunks transcribed successfully.")

    return transcript