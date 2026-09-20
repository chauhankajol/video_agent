import os
from dotenv import load_dotenv

from utils.audio_preprocessor import process_input
from core.transcriber import all_chunks
from core.summarizer import summarizer, generate_title
from core.extractor import extract_action_items, extract_key_decision, extract_question
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()


def run_pipeline(source: str) -> dict:
    print("Starting AI Video Assistant...")

    # Step 1: Preprocess input audio
    chunks = process_input(source)
    if not chunks:
        raise ValueError("Audio processing returned no chunks.")

    # Step 2: Transcribe chunks
    transcript = all_chunks(chunks)
    if not transcript or not transcript.strip():
        raise ValueError("Transcription generated an empty result.")

    print(f"Raw transcription (first 300 characters):\n{transcript[:300]}")

    # Step 3: Run LLM extractions
    title = generate_title(transcript)
    summary = summarizer(transcript)
    action_items = extract_action_items(transcript)
    decisions = extract_key_decision(transcript)
    questions = extract_question(transcript)

    # Step 4: Build RAG chain
    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


if __name__ == "__main__":
    # CLI entry point
    source = input("Enter YouTube URL or local file path: ").strip()

    if not source:
        print("Error: Source cannot be empty.")
        exit(1)

    try:
        result = run_pipeline(source)

        print("\n" + "=" * 60)
        print(f"📌 Title: {result['title']}")
        print(f"\n📋 Summary:\n{result['summary']}")
        print(f"\n✅ Action Items:\n{result['action_items']}")
        print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")
        print(f"\n❓ Open Questions:\n{result['open_questions']}")
        print("=" * 60)

        # Chat interface
        print("\n💬 Chat with your meeting (type 'exit' to quit)\n")
        rag_chain = result["rag_chain"]

        while True:
            question = input("You: ").strip()
            if question.lower() in ["exit", "quit", "q"]:
                print("👋 Goodbye!")
                break
            if not question:
                continue

            answer = ask_question(rag_chain, question)
            print(f"\n🤖 Assistant: {answer}\n")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")