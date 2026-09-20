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
    """
    Verify that FFmpeg is available in PATH.
    """

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
    """
    Download the best available audio from YouTube.

    Pipeline:

        YouTube URL
            ↓
        yt-dlp
            ↓
        downloaded source
            ↓
        FFmpeg
            ↓
        16 kHz mono WAV
    """

    check_ffmpeg()

    # -----------------------------------------------------
    # Clean URL
    # -----------------------------------------------------

    url = url.strip()

    if not url:
        raise ValueError(
            "YouTube URL cannot be empty."
        )

    print("Starting YouTube audio download...")

    # -----------------------------------------------------
    # Output template
    #
    # Example:
    #
    # downloads/JWMizuT_A8E.webm
    # downloads/JWMizuT_A8E.m4a
    # -----------------------------------------------------

    output_template = str(
        DOWNLOAD_DIR / "%(id)s.%(ext)s"
    )

    # -----------------------------------------------------
    # yt-dlp configuration
    # -----------------------------------------------------

    ydl_opts = {

        # -------------------------------------------------
        # FORMAT
        # -------------------------------------------------

        "format": "bestaudio/best",

        "outtmpl": output_template,

        "noplaylist": True,

        # -------------------------------------------------
        # NETWORK RELIABILITY
        # -------------------------------------------------

        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 3,
        "socket_timeout": 30,

        # IPv4
        "force_ipv4": True,

        # -------------------------------------------------
        # DENO / EJS
        #
        # Deno is already in Windows PATH.
        #
        # IMPORTANT:
        # For the Python API, yt-dlp expects:
        #
        # "deno": {}
        #
        # NOT:
        #
        # "deno": "deno"
        # -------------------------------------------------

        "js_runtimes": {
            "deno": {},
        },

        # -------------------------------------------------
        # EJS CHALLENGE SOLVER
        # -------------------------------------------------

        "remote_components": {
            "ejs": ["github"],
        },

        # -------------------------------------------------
        # WINDOWS
        # -------------------------------------------------

        "windowsfilenames": True,

        # -------------------------------------------------
        # LOGGING
        # -------------------------------------------------

        "quiet": False,
        "no_warnings": False,
    }

    # -----------------------------------------------------
    # OPTIONAL COOKIES
    # -----------------------------------------------------

    cookie_file = Path("cookies.txt")

    if cookie_file.exists():

        print("Using cookies.txt")

        ydl_opts["cookiefile"] = str(cookie_file)

    else:

        print(
            "No cookies.txt found. "
            "Continuing without cookies."
        )

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            # ---------------------------------------------
            # Get video ID
            # ---------------------------------------------

            video_id = info.get("id")

            if not video_id:

                raise RuntimeError(
                    "Could not determine YouTube video ID."
                )

            # ---------------------------------------------
            # Get actual downloaded filename
            # ---------------------------------------------

            downloaded_file = Path(
                ydl.prepare_filename(info)
            )

    except Exception as e:

        raise RuntimeError(
            f"YouTube download failed: {e}"
        ) from e

    # -----------------------------------------------------
    # VERIFY DOWNLOADED FILE
    # -----------------------------------------------------

    if not downloaded_file.exists():

        print(
            "Prepared filename was not found. "
            "Searching downloads folder..."
        )

        possible_files = list(
            DOWNLOAD_DIR.glob(f"{video_id}.*")
        )

        # Ignore temporary files
        possible_files = [
            p
            for p in possible_files
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

    # -----------------------------------------------------
    # CONVERT TO FINAL WAV
    # -----------------------------------------------------

    wav_file = DOWNLOAD_DIR / f"{video_id}.wav"

    convert_to_wav(
        str(downloaded_file),
        str(wav_file)
    )

    # -----------------------------------------------------
    # VERIFY WAV
    # -----------------------------------------------------

    if not wav_file.exists():

        raise FileNotFoundError(
            f"FFmpeg failed to create WAV: {wav_file}"
        )

    # -----------------------------------------------------
    # REMOVE ORIGINAL DOWNLOADED FILE
    # -----------------------------------------------------

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


# =========================================================
# CONVERT TO WAV
# =========================================================

def convert_to_wav(
    input_file: str,
    output_file: str | None = None
) -> str:
    """
    Convert audio/video to:

        WAV
        16 kHz
        Mono
        PCM 16-bit
    """

    check_ffmpeg()

    input_path = Path(input_file)

    if not input_path.exists():

        raise FileNotFoundError(
            f"Input file does not exist: {input_file}"
        )

    # -----------------------------------------------------
    # Default output path
    # -----------------------------------------------------

    if output_file is None:

        output_file = str(
            input_path.with_name(
                input_path.stem + "_16k.wav"
            )
        )

    print(
        f"Converting to 16kHz mono WAV: "
        f"{output_file}"
    )

    # -----------------------------------------------------
    # FFmpeg command
    # -----------------------------------------------------

    command = [
        "ffmpeg",

        "-hide_banner",
        "-loglevel", "error",

        "-i",
        str(input_path),

        # Ignore video stream
        "-vn",

        # 16 kHz
        "-ar",
        "16000",

        # Mono
        "-ac",
        "1",

        # PCM 16-bit
        "-c:a",
        "pcm_s16le",

        # Overwrite
        "-y",

        output_file
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=600
    )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg conversion failed:\n"
            + result.stderr
        )

    return output_file


# =========================================================
# CLEAN OLD CHUNKS
# =========================================================

def clean_chunks():
    """
    Remove previously generated audio chunks.
    """

    CHUNK_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for old_chunk in CHUNK_DIR.glob(
        "chunk_*.wav"
    ):

        try:

            old_chunk.unlink()

        except OSError as e:

            print(
                f"Warning: could not remove "
                f"{old_chunk}: {e}"
            )


# =========================================================
# CHUNK AUDIO
# =========================================================

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list[str]:
    """
    Split WAV into fixed-duration chunks.

    Example:

        35 minute audio

        ↓

        chunk_000.wav
        chunk_001.wav
        chunk_002.wav
        chunk_003.wav
    """

    check_ffmpeg()

    wav_path = Path(wav_path)

    # -----------------------------------------------------
    # Validate WAV
    # -----------------------------------------------------

    if not wav_path.exists():

        raise FileNotFoundError(
            f"WAV file not found: {wav_path}"
        )

    if chunk_minutes <= 0:

        raise ValueError(
            "chunk_minutes must be greater than 0."
        )

    # -----------------------------------------------------
    # Remove previous chunks
    # -----------------------------------------------------

    clean_chunks()

    # -----------------------------------------------------
    # Output pattern
    # -----------------------------------------------------

    output_pattern = str(
        CHUNK_DIR / "chunk_%03d.wav"
    )

    # -----------------------------------------------------
    # FFmpeg command
    # -----------------------------------------------------

    command = [
        "ffmpeg",

        "-hide_banner",
        "-loglevel", "error",

        "-i",
        str(wav_path),

        # Segment muxer
        "-f",
        "segment",

        # 10 minutes by default
        "-segment_time",
        str(chunk_minutes * 60),

        # Reset timestamps
        "-reset_timestamps",
        "1",

        # PCM 16-bit
        "-c:a",
        "pcm_s16le",

        # 16 kHz
        "-ar",
        "16000",

        # Mono
        "-ac",
        "1",

        # Overwrite
        "-y",

        output_pattern
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=1200
    )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg chunking failed:\n"
            + result.stderr
        )

    # -----------------------------------------------------
    # Find chunks
    # -----------------------------------------------------

    chunks = sorted(
        str(p)
        for p in CHUNK_DIR.glob(
            "chunk_*.wav"
        )
    )

    if not chunks:

        raise RuntimeError(
            "FFmpeg did not create "
            "any audio chunks."
        )

    print(
        f"Created {len(chunks)} audio chunk(s)."
    )

    for chunk in chunks:

        print(
            f"  → {chunk}"
        )

    return chunks


# =========================================================
# MAIN INPUT PROCESSOR
# =========================================================

def process_input(
    source: str,
    chunk_minutes: int = 10
) -> list[str]:
    """
    Main entry point.

    Supports:

    1. YouTube URL
    2. Other supported URL
    3. Local audio/video file
    """

    source = source.strip()

    if not source:

        raise ValueError(
            "Source cannot be empty."
        )

    # -----------------------------------------------------
    # URL
    # -----------------------------------------------------

    if source.startswith(
        ("http://", "https://")
    ):

        print(
            "Detected YouTube / Web URL."
        )

        wav_path = download_youtube_audio(
            source
        )

    # -----------------------------------------------------
    # LOCAL FILE
    # -----------------------------------------------------

    else:

        print(
            "Detected local audio/video file."
        )

        if not os.path.exists(source):

            raise FileNotFoundError(
                f"File not found: {source}"
            )

        wav_path = convert_to_wav(
            source
        )

    # -----------------------------------------------------
    # Split audio
    # -----------------------------------------------------

    chunks = chunk_audio(
        wav_path,
        chunk_minutes=chunk_minutes
    )

    return chunks


# ### One important thing

# Your previous pasted code had this:

# ```python
# ydl_opts = {
#     ...
# }
# ```

# at the **top level**, while the following code was still indented as though it were inside `download_youtube_audio()`.

# That causes multiple problems, including:

# ```text
# output_template is not defined
# url is not defined
# ```

# The corrected version above puts the entire YouTube workflow back inside:

# ```python
# def download_youtube_audio(url: str) -> str:
# ```

# ### Now test it

# Make sure you are here:

# ```powershell
# cd "C:\Users\India\Desktop\video Agent"
# ```

# and your environment is active:

# ```text
# (video Agent)
# ```

# Then run:

# ```powershell
# python test.py
# ```

# For your YouTube URL, the flow should now be:

# ```text
# Detected YouTube / Web URL.
#         ↓
# Starting YouTube audio download...
#         ↓
# Deno + EJS
#         ↓
# Downloaded source
#         ↓
# FFmpeg conversion
#         ↓
# Final WAV created
#         ↓
# Created N audio chunk(s)
# ```

# **Don't modify your Whisper code yet.** First get this stage working completely.
