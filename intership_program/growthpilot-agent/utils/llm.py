from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

try:
    from openai import OpenAI
except ImportError:
    OpenAI: Any = None


load_dotenv()


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: str | None
    model: str


def load_llm_config() -> LLMConfig:
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    return LLMConfig(
        api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        base_url=base_url,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
    )


def call_llm(prompt: str, system_prompt: str | None = None) -> str:
    """Call an OpenAI-compatible chat completion endpoint.

    Returns an empty string when the API key is missing or the request fails, so
    agents can safely fall back to deterministic mock output.
    """
    config = load_llm_config()
    if not config.api_key or config.api_key == "your_api_key_here":
        return ""
    if OpenAI is None:
        return ""

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        client_kwargs: dict[str, str] = {"api_key": config.api_key}
        if config.base_url:
            client_kwargs["base_url"] = config.base_url

        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=0.4,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except Exception:
        return ""
