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

    ydl_opts = {
        "format": "bestaudio/best",

        "outtmpl": os.path.join(
            DOWNLOAD_DIR,
            "%(title)s.%(ext)s"
        ),

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],

        "postprocessor_args": [
            "-ar", "16000",
            "-ac", "1"
        ],

        "noplaylist": True,
        "quiet": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        audio_file = (
            os.path.splitext(
                ydl.prepare_filename(info)
            )[0]
            + ".wav"
        )

    return audio_file


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

        wav_path,

        "-y"
    ]

    subprocess.run(
        command,
        check=True
    )

    return wav_path


# =========================================================
# 3. CHUNK AUDIO
# =========================================================

def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:

    # Create chunks folder if it doesn't exist
    os.makedirs("chunks", exist_ok=True)

    command = [
        "ffmpeg",
        "-i", wav_path,
        "-f", "segment",
        "-segment_time", str(chunk_minutes * 60),
        "-ar", "16000",
        "-ac", "1",
        "chunks/chunk_%03d.wav",
        "-y"
    ]

    subprocess.run(
        command,
        check=True
    )

    chunks = sorted(
        glob.glob("chunks/chunk_*.wav")
    )

    return chunks


# =========================================================
# 4. PROCESS INPUT
# =========================================================

def process_input(source: str) -> list:

    # -----------------------------------------
    # YouTube URL
    # -----------------------------------------

    if source.startswith(("http://", "https://")):

        print("Detected YouTube URL.")
        print("Downloading audio...")

        wav_path = download_youtube_audio(source)

    # -----------------------------------------
    # Local file
    # -----------------------------------------

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

        # MP3 / MP4 / other format
        else:

            print("Converting local file to WAV...")

            wav_path = convert_to_wav(source)

    # -----------------------------------------
    # Chunk the WAV
    # -----------------------------------------

    print("WAV Path:", wav_path)

    chunks = chunk_audio(
        wav_path,
        chunk_minutes=10
    )

    return chunks


# # =========================================================
# # TESTING
# # =========================================================

# if __name__ == "__main__":

#     source = "https://youtu.be/x63HCoDfAhQ"

#     chunks = process_input(source)

#     print("\nChunks created:")

#     for chunk in chunks:

#         print(chunk)