import yt_dlp
import os
import subprocess
import glob


# =========================================================
# FOLDERS
# =========================================================

DOWNLOAD_DIR = "downloads"
CHUNK_DIR = "chunks"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CHUNK_DIR, exist_ok=True)


# =========================================================
# 1. DOWNLOAD YOUTUBE AUDIO
# =========================================================

def download_youtube_audio(url: str) -> str:

    output_template = os.path.join(
        DOWNLOAD_DIR,
        "%(title)s.%(ext)s"
    )

    ydl_opts = {
        # Prefer audio-only formats
        "format": "bestaudio[ext=m4a]/bestaudio/best",

        "outtmpl": output_template,

        "noplaylist": True,

        "quiet": False,

        "no_warnings": False,

        # Retry settings
        "retries": 3,
        "fragment_retries": 3,

        # Network timeout
        "socket_timeout": 30,

        # Browser-like headers
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        },
    }

    print("Starting YouTube download...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        downloaded_file = ydl.prepare_filename(info)

    print("Downloaded:", downloaded_file)

    # -----------------------------------------------------
    # Convert downloaded file to WAV
    # -----------------------------------------------------

    wav_file = os.path.splitext(downloaded_file)[0] + ".wav"

    command = [
        "ffmpeg",
        "-i",
        downloaded_file,
        "-ar",
        "16000",
        "-ac",
        "1",
        "-y",
        wav_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print("WAV created:", wav_file)

    return wav_file


# =========================================================
# 2. CONVERT LOCAL FILE TO WAV
# =========================================================

def convert_to_wav(input_file: str) -> str:

    wav_path = os.path.splitext(input_file)[0] + ".wav"

    command = [
        "ffmpeg",

        "-i",
        input_file,

        "-ar",
        "16000",

        "-ac",
        "1",

        "-y",

        wav_path
    ]

    subprocess.run(
        command,
        check=True
    )

    return wav_path


# =========================================================
# 3. CHUNK AUDIO
# =========================================================

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:

    os.makedirs(CHUNK_DIR, exist_ok=True)

    # Remove old chunks
    old_chunks = glob.glob(
        os.path.join(CHUNK_DIR, "chunk_*.wav")
    )

    for old_chunk in old_chunks:
        try:
            os.remove(old_chunk)
        except OSError:
            pass

    output_pattern = os.path.join(
        CHUNK_DIR,
        "chunk_%03d.wav"
    )

    command = [
        "ffmpeg",

        "-i",
        wav_path,

        "-f",
        "segment",

        "-segment_time",
        str(chunk_minutes * 60),

        "-ar",
        "16000",

        "-ac",
        "1",

        "-y",

        output_pattern
    ]

    subprocess.run(
        command,
        check=True
    )

    chunks = sorted(
        glob.glob(
            os.path.join(
                CHUNK_DIR,
                "chunk_*.wav"
            )
        )
    )

    print(f"Created {len(chunks)} audio chunks.")

    return chunks


# =========================================================
# 4. PROCESS INPUT
# =========================================================

def process_input(source: str) -> list:

    # =====================================================
    # YOUTUBE URL
    # =====================================================

    if source.startswith(
        ("http://", "https://")
    ):

        print("Detected YouTube URL.")
        print("Downloading audio...")

        wav_path = download_youtube_audio(source)

    # =====================================================
    # LOCAL FILE
    # =====================================================

    else:

        print("Detected local file.")

        if not os.path.exists(source):

            raise FileNotFoundError(
                f"File not found: {source}"
            )

        # Already WAV
        if source.lower().endswith(".wav"):

            print("File is already WAV.")

            wav_path = source

        # Other format
        else:

            print("Converting local file to WAV...")

            wav_path = convert_to_wav(source)

    # =====================================================
    # CHUNK WAV
    # =====================================================

    print("WAV Path:", wav_path)

    chunks = chunk_audio(
        wav_path,
        chunk_minutes=10
    )

    return chunks