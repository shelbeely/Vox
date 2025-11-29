import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables from .env file
load_dotenv()


def get_client():
    """Get an AsyncOpenAI client configured for OpenRouter."""
    return AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", "dummy-key"),
        base_url=os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    )


async def generate_feedback(prompt: str) -> str:
    """
    Generate personalized feedback from the LLM given a prompt.
    """
    client = get_client()
    response = await client.chat.completions.create(
        model="google/gemini-2.0-flash-001",
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.7
    )
    choices = response.choices
    if not choices:
        return "No feedback generated."
    return choices[0].message.content.strip()


async def chat_with_llm(system_prompt: str, user_message: str) -> str:
    """
    Chat with the LLM given a system prompt and user message.
    """
    client = get_client()
    response = await client.chat.completions.create(
        model="google/gemini-2.0-flash-001",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7
    )
    choices = response.choices
    if not choices:
        return "No response from LLM."
    return choices[0].message.content.strip()
