"""OpenAI chat completion client."""
from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.openai_api_key)


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    response = _client.chat.completions.create(
        model=settings.openai_chat_model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""
