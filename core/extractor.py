from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import os


def get_llm():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        groq_api_key=os.getenv("GROQ_API_KEY")
    )


def build_chain(system_prompt: str):

    return (
        RunnableLambda(lambda x: {"text": x})
        | ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}")
        ])
        | get_llm()
        | StrOutputParser()
    )


def extract_action_items(transcript: str):
    chain = build_chain("""
    Extract all action items.

    For each item provide:
    - Task
    - Owner
    - Deadline

    If missing write Not specified.

    Format as numbered list.
    """)

    return chain.invoke(transcript)


def extract_key_decision(transcript: str):
    chain = build_chain("""
    Extract all key decisions.

    Format as numbered list.

    If none found write:
    No key decisions found.
    """)

    return chain.invoke(transcript)


def extract_question(transcript: str):
    chain = build_chain("""
    Extract all unresolved questions.

    Format as numbered list.

    If none found write:
    No open questions found.
    """)

    return chain.invoke(transcript)