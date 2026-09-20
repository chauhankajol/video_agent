import os
import subprocess

from pathlib import Path

import yt_dlp

# =========================================================
# CONFIGURATION
# =========================================================

DOWNLOAD_DIR = Path("downloads")
CHUNK_DIR = Path("chunks")

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHUNK_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# FFMPEG CHECK
# =========================================================

def check_ffmpeg():

    try:

        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise RuntimeError(
                "FFmpeg is installed but could not be executed."
            )

    except FileNotFoundError:

        raise RuntimeError(
            "FFmpeg was not found. "
            "Install FFmpeg and add it to PATH."
        )


# =========================================================
# DOWNLOAD YOUTUBE AUDIO
# =========================================================

def download_youtube_audio(url: str) -> str:

    check_ffmpeg()

    url = url.strip()

    if not url:
        raise ValueError(
            "YouTube URL cannot be empty."
        )

    print("Starting YouTube audio download...")

    output_template = str(
        DOWNLOAD_DIR / "%(id)s.%(ext)s"
    )

    # =====================================================
    # YT-DLP CONFIG
    # =====================================================

    ydl_opts = {

    "format": "bestaudio/best",

    "outtmpl": output_template,

    "noplaylist": True,

    "retries": 10,
    "fragment_retries": 10,
    "file_access_retries": 3,
    "socket_timeout": 30,

    "force_ipv4": True,

    "js_runtimes": {
        "deno": {},
    },

    "windowsfilenames": True,

    "quiet": False,
    "no_warnings": False,
   }
    # =====================================================
    # OPTIONAL COOKIES
    # =====================================================

    cookie_file = Path("cookies.txt")

    if cookie_file.exists():

        print("Using cookies.txt")

        ydl_opts["cookiefile"] = str(cookie_file)

    else:

        print(
            "No cookies.txt found. "
            "Continuing without cookies."
        )

    # =====================================================
    # DOWNLOAD
    # =====================================================

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            video_id = info.get("id")

            if not video_id:

                raise RuntimeError(
                    "Could not determine YouTube video ID."
                )

            downloaded_file = Path(
                ydl.prepare_filename(info)
            )

    except Exception as e:

        raise RuntimeError(
            f"YouTube download failed: {e}"
        ) from e

    # =====================================================
    # VERIFY DOWNLOAD
    # =====================================================

    if not downloaded_file.exists():

        print(
            "Prepared filename was not found. "
            "Searching downloads folder..."
        )

        possible_files = list(
            DOWNLOAD_DIR.glob(f"{video_id}.*")
        )

        possible_files = [
            p for p in possible_files
            if p.suffix.lower()
            not in [".part", ".ytdl", ".tmp"]
        ]

        if not possible_files:

            raise FileNotFoundError(
                f"Downloaded file was not found "
                f"for video {video_id}"
            )

        downloaded_file = possible_files[0]

    print(
        f"Downloaded source: {downloaded_file}"
    )

    # =====================================================
    # CONVERT TO WAV
    # =====================================================

    wav_file = DOWNLOAD_DIR / f"{video_id}.wav"

    convert_to_wav(
        str(downloaded_file),
        str(wav_file)
    )

    if not wav_file.exists():

        raise FileNotFoundError(
            f"FFmpeg failed to create WAV: {wav_file}"
        )

    # =====================================================
    # REMOVE ORIGINAL
    # =====================================================

    if (
        downloaded_file.exists()
        and downloaded_file.resolve()
        != wav_file.resolve()
    ):

        try:

            downloaded_file.unlink()

            print(
                f"Removed temporary source: "
                f"{downloaded_file}"
            )

        except OSError as e:

            print(
                f"Warning: could not remove "
                f"{downloaded_file}: {e}"
            )

    print(
        f"Final WAV created: {wav_file}"
    )

    return str(wav_file)