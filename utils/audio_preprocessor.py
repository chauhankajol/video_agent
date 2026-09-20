import os
import glob
import subprocess
import yt_dlp

DOWNLOAD_DIR = "downloads"
CHUNK_DIR = "chunks"
COOKIE_PATH = "cookies.txt"

# Netscape HTTP Cookie Content for YouTube Authentication
YOUTUBE_COOKIES = """# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1806922005	LOGIN_INFO	AFmmF2swRgIhAPKL-h-j9-Kn3g2jMKLigpmmWpbJL3I9s728lyRQMLHBAiEA31ycNliSSLMTOme8Jj7YmuA1vZBAmMCcBltK9047qdc:QUQ3MjNmeTcyMFhvQUJXeW1ZZnk0SmNRV2d3UU1wdHU5S2MtRWt0b21FYnMxdzVmcGZCNFgyc3dGRGl6UmtRXzZIUjBSanIyZDFFN05xVE5VdEJYWmtpOUUzR1c4S1AtcXBzLUpFSTdUcUh0V0ZvMW1VbjN5cVdjeE1RSXF6azFYMU1yU1FUcHJ5bTFhUlE5dmc3V0poNVZMWUJoZDdYWTNR
.youtube.com	TRUE	/	TRUE	1791167931	__Secure-BUCKET	CEI
.youtube.com	TRUE	/	FALSE	1822991135	HSID	Ad3PlrRvWVfQ6TqhU
.youtube.com	TRUE	/	TRUE	1822991135	SSID	Ag23DR2GKo01J8V10
.youtube.com	TRUE	/	FALSE	1822991135	APISID	p5w9V1qI-lX_JqNm/AyA1OPaXvmb8XAF3_
.youtube.com	TRUE	/	TRUE	1822991135	SAPISID	nkreIcLPKOegZV9u/A7EoBU_qmfdCDxbta
.youtube.com	TRUE	/	TRUE	1822991135	__Secure-1PAPISID	nkreIcLPKOegZV9u/A7EoBU_qmfdCDxbta
.youtube.com	TRUE	/	TRUE	1822991135	__Secure-3PAPISID	nkreIcLPKOegZV9u/A7EoBU_qmfdCDxbta
.youtube.com	TRUE	/	FALSE	1822991135	SID	g.a000CAnXFwL92xzXBcsze1mJmMSoAjIdRm8eJEc-rf_gxnZ7gALz8PmrBVis2DDvoK1M6ptxvgACgYKAYoSARMSFQHGX2MiK1rCIY7qsQsEc7k-xQCYvBoVAUF8yKrJrzn5h3-EI-Yj0cI4F9N30076
.youtube.com	TRUE	/	TRUE	1822991135	__Secure-1PSID	g.a000CAnXFwL92xzXBcsze1mJmMSoAjIdRm8eJEc-rf_gxnZ7gALzJfiQSkMdILakD2xug33OcgACgYKAeQSARMSFQHGX2MiehIlbzUkAbvtXv-zT0L6pBoVAUF8yKr4uWv3Wydh3wk27MHipPff0076
.youtube.com	TRUE	/	TRUE	1822991135	__Secure-3PSID	g.a000CAnXFwL92xzXBcsze1mJmMSoAjIdRm8eJEc-rf_gxnZ7gALz1P8RJ3s9CDV7ZrH9bdZRoAACgYKAewSARMSFQHGX2Mi0wCdafX0d4_f1SaWlghmQRoVAUF8yKo77jDklqyCzaI9rEPGJ5Hj0076
.youtube.com	TRUE	/	TRUE	1824470727	PREF	tz=Asia.Calcutta&f5=30000&f7=100&f4=4000000
.youtube.com	TRUE	/	TRUE	1821447422	__Secure-1PSIDTS	sidts-CjUBXMw41ShqFPl6iV7aHdaP8ArW2iq3zowvsIf_0zdOJK8Ndt7_P74MpasQKQlrUMtPb3lSkBAA
.youtube.com	TRUE	/	TRUE	1821447422	__Secure-3PSIDTS	sidts-CjUBXMw41ShqFPl6iV7aHdaP8ArW2iq3zowvsIf_0zdOJK8Ndt7_P74MpasQKQlrUMtPb3lSkBAA
.youtube.com	TRUE	/	FALSE	1821447422	SIDCC	AKEyXzXePVB1AEcBpf_CvqPQaf2RGURUYRzFCmZdDUY_K5PWjbTbL1axSp7j55mrhBqNAFa2p8gl
.youtube.com	TRUE	/	TRUE	1821447422	__Secure-1PSIDCC	AKEyXzVjM4F4ijrCHQI-6-NnH7OgOLGlL9HxJXv7IB_cF-dhGS5LBh1YhwnxN3iZ1pqdpHRtKg6f
.youtube.com	TRUE	/	TRUE	1821447422	__Secure-3PSIDCC	AKEyXzWtr2N_woygaiFU62YTwyoxmsS79vDgmR4P7-UG3T5wYkHEj_V0qA14m9jDFGsTEEeIATdS
.youtube.com	TRUE	/	TRUE	1805462709	VISITOR_INFO1_LIVE	sqXcYv8GlG0
.youtube.com	TRUE	/	TRUE	1805462709	VISITOR_PRIVACY_METADATA	CgJJThIEGgAgPA%3D%3D
.youtube.com	TRUE	/	TRUE	0	YSC	Hfew4Dl2E2Y
.youtube.com	TRUE	/	TRUE	1805462702	__Secure-YNID	21.YT=a7IuV46I3XCqOF63Zzw2MZHQPtZCJgOJhWnNsYrQc-hJYd36r5VbbXVO6Vh1G86jjYAK9Y2roNjGu1Oa9mRaRi0hoepWhcHqzgh4JFR0wy0mLHCLuY2G89MBqK3etmNxpo82z9DvPLcEWN1jv7XjYrO50OLHqp-Zl1_cNdtmAupWw4iPiLr0LcBRTxkH60BmT255eku2HI20hfk19fKCVRq82Y8TfOzuErv1UyHe7pS72HO2MuhH5rNyH-dbBX5zJ8i1VWx__Uc0WwgOA97n7foO9bn4KdbBK9kW-4Ltr-btfOKhuHV0kJd60eGTjXmrDMJojYMYXuwPIZp8YAfLAg
.youtube.com	TRUE	/	TRUE	1805462702	__Secure-ROLLOUT_TOKEN	CL7Ymc_3x66wSRCCo43-wv6SAxjH8qr8oP2WAw%3D%3D
"""

# Ensure working directories exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CHUNK_DIR, exist_ok=True)


def ensure_cookie_file() -> str:
    """Writes the Netscape cookie content to cookies.txt if it doesn't already exist."""
    with open(COOKIE_PATH, "w", encoding="utf-8") as f:
        f.write(YOUTUBE_COOKIES.strip())
    return COOKIE_PATH


def download_youtube_audio(url: str) -> str:
    """
    Downloads audio from YouTube and converts it to 16kHz mono WAV using yt-dlp + FFmpeg.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    cookie_file = ensure_cookie_file()

    output_template = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "ba/b/bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "force_ipv4": True,
        "cookiefile": cookie_file,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb", "web"],
            }
        },
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
    Splits a WAV file into fixed-duration WAV chunks with valid PCM headers.
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
        "-c:a", "pcm_s16le",  # Re-encodes PCM headers cleanly for each chunk
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