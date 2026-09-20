import os
import glob
import subprocess
import yt_dlp

DOWNLOAD_DIR = "downloads"
CHUNK_DIR = "chunks"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CHUNK_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """
    Downloads audio from YouTube and converts it to 16kHz mono WAV using yt-dlp + FFmpeg.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # We output directly as .wav using outtmpl
    output_template = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "ba/b/bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "force_ipv4": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb", "web"],
            }
        },
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
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
    }

    print("Starting YouTube download and audio extraction...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id")
        wav_file = os.path.join(DOWNLOAD_DIR, f"{video_id}.wav")

    if not os.path.exists(wav_file):
        raise FileNotFoundError(f"Failed to generate WAV file at: {wav_file}")

    print("WAV created:", wav_file)
    return wav_file


def convert_to_wav(input_file: str) -> str:
    """
    Converts a local audio/video file to 16kHz mono WAV.
    """
    wav_path = os.path.splitext(input_file)[0] + "_16k.wav"

    command = [
        "ffmpeg",
        "-i", input_file,
        "-ar", "16000",
        "-ac", "1",
        "-y", wav_path
    ]

    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """
    Splits a WAV file into fixed-duration WAV chunks with valid headers.
    """
    os.makedirs(CHUNK_DIR, exist_ok=True)

    # Clean up previous chunks before splitting
    for old_chunk in glob.glob(os.path.join(CHUNK_DIR, "chunk_*.wav")):
        try:
            os.remove(old_chunk)
        except OSError:
            pass

    output_pattern = os.path.join(CHUNK_DIR, "chunk_%03d.wav")

    command = [
        "ffmpeg",
        "-i", wav_path,
        "-f", "segment",
        "-segment_time", str(chunk_minutes * 60),
        "-c:a", "pcm_s16le",  # Ensure each chunk gets a valid WAV header
        "-ar", "16000",
        "-ac", "1",
        "-y", output_pattern
    ]

    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    chunks = sorted(glob.glob(os.path.join(CHUNK_DIR, "chunk_*.wav")))
    print(f"Created {len(chunks)} audio chunk(s).")
    return chunks


def process_input(source: str, chunk_minutes: int = 10) -> list:
    """
    Main entry point: Handles YouTube/Web URLs or local audio/video files.
    """
    if source.startswith(("http://", "https://")):
        print("Detected YouTube / Web URL.")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file.")
        if not os.path.exists(source):
            raise FileNotFoundError(f"File not found: {source}")
        
        wav_path = convert_to_wav(source)

    chunks = chunk_audio(wav_path, chunk_minutes=chunk_minutes)
    return chunks