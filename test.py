print("START")
print("FILE IS RUNNING")
from dotenv import load_dotenv
load_dotenv()  

from utils.audio_preprocessor import process_input
from core.transcriber import all_chunks
from core.extractor import (
    extract_action_items,
    extract_key_decision,
    extract_question
)
from core.summarizer import summarizer, generate_title


source = "https://www.youtube.com/watch?v=eaHfex71yO0"
# language = "english"

# Step 1: Download + Convert + Chunk
chunks = process_input(source)

print("Chunks Created:")
print(chunks)

# Step 2: Transcription
transcript = all_chunks(chunks)

print("\n" + "=" * 60)
print("TRANSCRIPT")
print("=" * 60)
print(transcript[:500] + "..." if len(transcript) > 500 else transcript)

# Step 3: Title + Summary
title = generate_title(transcript)
summary = summarizer(transcript)

print("\n" + "=" * 60)
print(f"TITLE: {title}")
print("=" * 60)

print("\nSUMMARY")
print("-" * 60)
print(summary)

# Step 4: Insights
action_items = extract_action_items(transcript)
decisions = extract_key_decision(transcript)
questions = extract_question(transcript)

print("\n" + "=" * 60)
print("ACTION ITEMS")
print("=" * 60)
print(action_items)

print("\n" + "=" * 60)
print("KEY DECISIONS")
print("=" * 60)
print(decisions)

print("\n" + "=" * 60)
print("OPEN QUESTIONS")
print("=" * 60)
print(questions)