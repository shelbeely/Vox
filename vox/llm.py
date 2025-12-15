import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables from .env file
load_dotenv()


def get_client():
    """Get an AsyncOpenAI client configured for any OpenAI-compatible API."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_API_BASE", None)
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    if base_url:
        return AsyncOpenAI(api_key=api_key, base_url=base_url)
    else:
        return AsyncOpenAI(api_key=api_key)


async def generate_feedback(prompt: str) -> str:
    """
    Generate personalized feedback from the LLM given a prompt.
    """
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.7
        )
        choices = response.choices
        if not choices:
            return "No feedback generated."
        return choices[0].message.content.strip()
    except ValueError as e:
        return f"Error: {str(e)}. Please configure your OpenAI-compatible API key."
    except Exception as e:
        return f"Error generating feedback: {str(e)}"


async def chat_with_llm(system_prompt: str, user_message: str) -> str:
    """
    Chat with the LLM given a system prompt and user message.
    """
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model=model,
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
    except ValueError as e:
        return f"Error: {str(e)}. Please configure your OpenAI-compatible API key."
    except Exception as e:
        return f"Error: {str(e)}"
