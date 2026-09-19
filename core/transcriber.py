import os
from faster_whisper import WhisperModel


# =========================================================
# WHISPER CONFIGURATION
# =========================================================

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")

_model = None


# =========================================================
# LOAD FASTER-WHISPER MODEL
# =========================================================

def load_model():
    global _model

    if _model is None:
        print(f"Loading Faster-Whisper model: {WHISPER_MODEL}...")

        _model = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type="int8"
        )

        print("Faster-Whisper model loaded successfully.")

    return _model


# =========================================================
# TRANSCRIBE ONE AUDIO CHUNK
# =========================================================

def transcribe_chunk(chunk_path: str, translate: bool = False) -> str:

    model = load_model()

    task = "translate" if translate else "transcribe"

    print(f"Processing: {chunk_path}")

    segments, info = model.transcribe(
        chunk_path,
        task=task
    )

    # Faster-Whisper returns segments as an iterator
    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    )

    return text.strip()


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