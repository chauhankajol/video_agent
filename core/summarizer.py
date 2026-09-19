from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os


# =========================================================
# LLM
# =========================================================

def get_llm():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not found")

    return ChatGroq(
        model="openai/gpt-oss-120b",
        groq_api_key=api_key,
        temperature=0.3,
        max_retries=5
    )


# =========================================================
# SPLIT TRANSCRIPT
# =========================================================

def split_transcript(transcript: str):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )

    return splitter.split_text(transcript)


# =========================================================
# SUMMARY
# =========================================================

def summarizer(transcript: str) -> str:

    try:

        llm = get_llm()

        chunks = split_transcript(transcript)

        map_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are an expert meeting summarizer.

                Summarize the transcript chunk.

                Keep:
                - Important discussions
                - Decisions
                - Action items
                - Key insights

                Be concise.
                """
            ),
            ("human", "{text}")
        ])

        map_chain = map_prompt | llm | StrOutputParser()

        chunk_summaries = []

        for i, chunk in enumerate(chunks):

            print(
                f"Summarizing chunk {i+1}/{len(chunks)}"
            )

            summary = map_chain.invoke(
                {"text": chunk}
            )

            chunk_summaries.append(summary)

        combined_summary = "\n\n".join(
            chunk_summaries
        )

        reduce_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are an expert meeting summarizer.

                Combine all chunk summaries into one
                professional summary.

                Format:

                ## Overview

                ## Key Discussion Points

                ## Decisions

                ## Action Items

                Use bullet points.
                """
            ),
            ("human", "{text}")
        ])

        reduce_chain = (
            reduce_prompt
            | llm
            | StrOutputParser()
        )

        final_summary = reduce_chain.invoke(
            {"text": combined_summary}
        )

        return final_summary

    except Exception as e:

        print(
            f"\n[!] Summarization Error: {e}"
        )

        return (
            "Summarization Failed\n\n"
            + transcript[:1500]
        )


# =========================================================
# TITLE GENERATOR
# =========================================================

def generate_title(transcript: str) -> str:

    try:

        llm = get_llm()

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                Generate a short title
                for this transcript.

                Rules:
                - Maximum 8 words
                - Professional
                - Return title only
                """
            ),
            ("human", "{text}")
        ])

        chain = (
            prompt
            | llm
            | StrOutputParser()
        )

        return chain.invoke(
            {
                "text": transcript[:2000]
            }
        )

    except Exception as e:

        print(
            f"\n[!] Title Generation Error: {e}"
        )

        words = transcript.split()[:6]

        if words:
            return " ".join(words).title()

        return "Meeting Transcript"