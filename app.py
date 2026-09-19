"""
AI Video Assistant - Streamlit UI
Run from your project root (next to main.py):  streamlit run app.py
"""
import html
import math
import re
import tempfile
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from utils.audio_preprocessor import process_input
from core.transcriber import all_chunks
from core.summarizer import summarizer, generate_title
from core.extractor import extract_action_items, extract_key_decision, extract_question
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ----------------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

INK = "#0E2433"
AMBER = "#F5A524"
TEAL = "#1F8A8A"
PAPER = "#F1F5F7"
LINE = "#D9E2E7"
MUTED = "#5B7080"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Instrument+Sans:wght@400;500;600&display=swap');

.stApp, .stMarkdown, p, label, button, input, textarea, li {
    font-family: 'Instrument Sans', system-ui, sans-serif;
}
.stApp { background: #F1F5F7; color: #0E2433; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1100px; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #D9E2E7;
}
.brand { display:flex; align-items:center; gap:.65rem; margin: .25rem 0 1.25rem; }
.brand-mark {
    width: 38px; height: 38px; border-radius: 10px; background: #0E2433;
    display:flex; align-items:center; justify-content:center; font-size: 1.15rem;
}
.brand-name {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
    font-size: 1.15rem; line-height: 1.1; color: #0E2433;
}
.brand-sub { font-size: .8rem; color: #5B7080; }
.side-note { font-size: .82rem; color: #5B7080; line-height: 1.5; margin-top: .75rem; }

/* ---------- hero ---------- */
.hero {
    background: #0E2433; border-radius: 22px; padding: 2.4rem 2.6rem;
    display: flex; align-items: center; justify-content: space-between; gap: 2rem;
    margin-bottom: 1.6rem; overflow: hidden;
}
.hero h1 {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
    font-size: 2.35rem; line-height: 1.12; letter-spacing: -0.02em;
    color: #FFFFFF; margin: 0 0 .7rem 0; padding: 0;
}
.hero p { color: #A9BDC9; font-size: 1.02rem; line-height: 1.6; margin: 0; max-width: 46ch; }
.hero-text { flex: 1 1 auto; min-width: 0; }
.hero svg { flex: 0 0 auto; }
@media (max-width: 780px) { .hero svg { display: none; } .hero h1 { font-size: 1.8rem; } }

/* ---------- stats ---------- */
.stat { border-left: 3px solid #F5A524; padding: .1rem 0 .1rem .9rem; }
.stat.teal { border-color: #1F8A8A; }
.stat.ink { border-color: #0E2433; }
.stat-value {
    font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
    font-size: 1.9rem; line-height: 1.1; color: #0E2433;
}
.stat-label { font-size: .85rem; color: #5B7080; margin-top: .15rem; }

/* ---------- item lists ---------- */
.items { display: flex; flex-direction: column; gap: .65rem; }
.item {
    display: flex; gap: .9rem; align-items: flex-start; background: #FFFFFF;
    border: 1px solid #D9E2E7; border-radius: 12px; padding: .95rem 1.1rem;
    line-height: 1.55; color: #0E2433;
}
.item .mark {
    flex: 0 0 auto; width: 22px; height: 22px; border-radius: 50%;
    display:flex; align-items:center; justify-content:center;
    font-size: .8rem; font-weight: 700; margin-top: 2px;
}
.item.action .mark { background: #FDEBC8; color: #8A5A00; }
.item.decision .mark { background: #D6EEEE; color: #146060; }
.item.question .mark { background: #E3E9EE; color: #0E2433; }

/* ---------- bordered containers ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF; border-radius: 14px; border-color: #D9E2E7;
}

/* ---------- empty state ---------- */
.feature { border-top: 3px solid #F5A524; padding-top: .8rem; }
.feature.teal { border-color: #1F8A8A; }
.feature.ink { border-color: #0E2433; }
.feature h4 {
    font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.05rem;
    margin: 0 0 .35rem 0; color: #0E2433;
}
.feature p { color: #5B7080; font-size: .92rem; line-height: 1.55; margin: 0; }

/* ---------- buttons ---------- */
.stButton > button, .stDownloadButton > button {
    border-radius: 10px; border: 1px solid #D9E2E7; font-weight: 600;
    transition: border-color .15s ease, background .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #0E2433; color: #0E2433;
}
.stButton > button[kind="primary"] {
    background: #F5A524; border-color: #F5A524; color: #0E2433;
}
.stButton > button[kind="primary"]:hover { background: #E39511; border-color: #E39511; }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
    outline: 3px solid #1F8A8A; outline-offset: 2px;
}

/* ---------- misc ---------- */
[data-testid="stChatMessage"] { background: transparent; }
h3 { font-family: 'Bricolage Grotesque', sans-serif; letter-spacing: -0.01em; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def waveform_svg(width: int = 260, height: int = 120) -> str:
    """Decorative waveform used in the hero banner."""
    bars = []
    n = 26
    gap = width / n
    for i in range(n):
        h = 16 + 84 * abs(math.sin(i * 0.55) * math.cos(i * 0.21 + 0.6))
        x = i * gap + 3
        y = (height - h) / 2
        opacity = 0.35 + 0.65 * (h / 100)
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="6" height="{h:.1f}" rx="3" '
            f'fill="{AMBER}" opacity="{opacity:.2f}"/>'
        )
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{"".join(bars)}</svg>'
    )


def fmt(text: str) -> str:
    """Escape HTML, then support **bold** from LLM output."""
    safe = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)


def to_items(value) -> list:
    """Normalise LLM output (list or bulleted string) into a clean list of strings."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    items = []
    for line in str(value).splitlines():
        line = re.sub(r"^\s*([-*\u2022]|\d+[.)])\s*", "", line).strip()
        if line:
            items.append(line)
    return items


def render_items(items: list, kind: str, symbol: str, empty_msg: str) -> None:
    if not items:
        st.info(empty_msg)
        return
    rows = "".join(
        f'<div class="item {kind}"><span class="mark">{symbol}</span>'
        f"<div>{fmt(item)}</div></div>"
        for item in items
    )
    st.markdown(f'<div class="items">{rows}</div>', unsafe_allow_html=True)


def stat(value, label: str, tone: str = "") -> str:
    return (
        f'<div class="stat {tone}"><div class="stat-value">{value}</div>'
        f'<div class="stat-label">{label}</div></div>'
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        '<div class="hero"><div class="hero-text">'
        f"<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>"
        f"{waveform_svg()}</div>",
        unsafe_allow_html=True,
    )


def save_upload(uploaded) -> str:
    folder = Path(tempfile.gettempdir()) / "video_assistant"
    folder.mkdir(exist_ok=True)
    path = folder / f"{int(time.time())}{Path(uploaded.name).suffix}"
    path.write_bytes(uploaded.getbuffer())
    return str(path)


def build_report(r: dict) -> str:
    def bullets(v):
        return "\n".join(f"- {i}" for i in to_items(v)) or "_None found_"

    return (
        f"# {r['title']}\n\n"
        f"## Summary\n{r['summary']}\n\n"
        f"## Action items\n{bullets(r['action_items'])}\n\n"
        f"## Key decisions\n{bullets(r['key_decisions'])}\n\n"
        f"## Open questions\n{bullets(r['open_questions'])}\n\n"
        f"## Transcript\n{r['transcript']}\n"
    )


def run_with_progress(source: str) -> dict:
    """Same steps as run_pipeline(), with live progress in the UI."""
    with st.status("Processing your recording", expanded=True) as status:
        try:
            st.write("Preparing audio")
            chunks = process_input(source)

            st.write("Transcribing speech")
            transcript = all_chunks(chunks)
            if not transcript or not transcript.strip():
                raise ValueError("No speech was found in this recording.")

            st.write("Writing title and summary")
            title = generate_title(transcript)
            summary = summarizer(transcript)

            st.write("Finding action items, decisions and open questions")
            action_items = extract_action_items(transcript)
            decisions = extract_key_decision(transcript)
            questions = extract_question(transcript)

            st.write("Indexing the transcript for chat")
            rag_chain = build_rag_chain(transcript)

            status.update(label="Recap is ready", state="complete", expanded=False)
        except Exception as exc:
            status.update(label="Processing stopped", state="error", expanded=True)
            raise exc

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
st.session_state.setdefault("result", None)
st.session_state.setdefault("messages", [])

# ----------------------------------------------------------------------------
# Sidebar - input
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">🎙️</div><div>'
        '<div class="brand-name">AI Video Assistant</div>'
        '<div class="brand-sub">Recaps and answers from any recording</div>'
        "</div></div>",
        unsafe_allow_html=True,
    )

    input_mode = st.radio("Source", ["YouTube link", "Upload a file"], horizontal=True)

    source, ready = None, False
    if input_mode == "YouTube link":
        url = st.text_input("Video URL", placeholder="https://www.youtube.com/watch?v=...")
        ready = url.strip().startswith("http")
        source = url.strip()
    else:
        uploaded = st.file_uploader(
            "Recording",
            type=["mp3", "wav", "m4a", "mp4", "mov", "mkv", "webm"],
            help="Audio or video, up to your Streamlit upload limit.",
        )
        ready = uploaded is not None

    analyze = st.button(
        "Analyze recording", type="primary", use_container_width=True, disabled=not ready
    )

    if st.session_state.result is not None:
        if st.button("Start over", use_container_width=True):
            st.session_state.result = None
            st.session_state.messages = []
            st.rerun()

    st.markdown(
        '<div class="side-note">Long recordings can take a few minutes to transcribe. '
        "Keep this tab open while it runs.</div>",
        unsafe_allow_html=True,
    )

# ----------------------------------------------------------------------------
# Run pipeline
# ----------------------------------------------------------------------------
if analyze:
    st.session_state.messages = []
    st.session_state.result = None
    try:
        path_or_url = source if input_mode == "YouTube link" else save_upload(uploaded)
        st.session_state.result = run_with_progress(path_or_url)
        st.rerun()
    except Exception as exc:
        st.error(f"Could not process this recording: {exc}")

result = st.session_state.result

# ----------------------------------------------------------------------------
# Empty state
# ----------------------------------------------------------------------------
if result is None:
    hero(
        "Turn any recording into a clear recap",
        "Paste a YouTube link or upload a meeting. You get a summary, the tasks "
        "people agreed to, and a chat that answers from the transcript.",
    )
    c1, c2, c3 = st.columns(3, gap="large")
    c1.markdown(
        '<div class="feature"><h4>Summary and title</h4>'
        "<p>A short overview you can read in under a minute.</p></div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        '<div class="feature teal"><h4>Actions, decisions, questions</h4>'
        "<p>Who needs to do what, what was settled, and what is still open.</p></div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        '<div class="feature ink"><h4>Chat with the recording</h4>'
        "<p>Ask follow-up questions and get answers grounded in the transcript.</p></div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ----------------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------------
actions = to_items(result["action_items"])
decisions = to_items(result["key_decisions"])
questions = to_items(result["open_questions"])
word_count = len(result["transcript"].split())

hero(str(result["title"]).strip().strip('"'), "Here is everything pulled from your recording.")

m1, m2, m3, m4 = st.columns(4)
m1.markdown(stat(f"{word_count:,}", "Words transcribed", "ink"), unsafe_allow_html=True)
m2.markdown(stat(len(actions), "Action items"), unsafe_allow_html=True)
m3.markdown(stat(len(decisions), "Key decisions", "teal"), unsafe_allow_html=True)
m4.markdown(stat(len(questions), "Open questions", "ink"), unsafe_allow_html=True)

st.write("")

VIEWS = ["Summary", "Action items", "Decisions", "Open questions", "Transcript", "Chat"]
if hasattr(st, "segmented_control"):
    view = st.segmented_control("View", VIEWS, default="Summary", key="view", label_visibility="collapsed")
else:  # older Streamlit
    view = st.radio("View", VIEWS, horizontal=True, key="view", label_visibility="collapsed")
view = view or "Summary"

st.write("")

if view == "Summary":
    with st.container(border=True):
        st.markdown("### Summary")
        st.markdown(result["summary"])
    st.download_button(
        "Download full report (.md)",
        data=build_report(result),
        file_name="video-recap.md",
        mime="text/markdown",
    )

elif view == "Action items":
    st.markdown("### Action items")
    render_items(actions, "action", "\u2713", "No action items were found in this recording.")

elif view == "Decisions":
    st.markdown("### Key decisions")
    render_items(decisions, "decision", "\u2713", "No decisions were found in this recording.")

elif view == "Open questions":
    st.markdown("### Open questions")
    render_items(questions, "question", "?", "No open questions were found in this recording.")

elif view == "Transcript":
    st.markdown("### Transcript")
    st.text_area(
        "Full transcript",
        value=result["transcript"],
        height=460,
        label_visibility="collapsed",
    )
    st.download_button(
        "Download transcript (.txt)",
        data=result["transcript"],
        file_name="transcript.txt",
        mime="text/plain",
    )

elif view == "Chat":
    st.markdown("### Chat with this recording")
    pending = st.session_state.pop("pending_q", None)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.messages and not pending:
        st.caption("Try one of these, or type your own question below.")
        suggestions = [
            "What were the main takeaways?",
            "Who is responsible for what?",
            "Were any deadlines mentioned?",
        ]
        cols = st.columns(len(suggestions))
        for col, text in zip(cols, suggestions):
            if col.button(text, key=f"sugg_{text}", use_container_width=True):
                st.session_state.pending_q = text
                st.rerun()

    typed = st.chat_input("Ask anything about this recording")
    question = typed or pending

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching the transcript"):
                try:
                    answer = ask_question(result["rag_chain"], question)
                except Exception as exc:
                    answer = f"I couldn't answer that: {exc}"
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})