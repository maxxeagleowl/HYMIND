"""OpenAI client wrapper for HYMIND with validation, retry, and timeout."""

import logging
import os
import sys
from typing import Optional

from openai import OpenAI, APITimeoutError, RateLimitError, APIError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from hymind.utils.logger import get_logger

logger = get_logger(__name__)

_TIMEOUT: int = 30
_MAX_RETRIES: int = 3
_DEFAULT_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Return the shared OpenAI client, initialising it on first call.

    Exits with a clear message if OPENAI_API_KEY is not configured.
    """
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.error(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env and add your OpenAI key, "
            "then re-run the application."
        )
        sys.exit(1)

    _client = OpenAI(api_key=api_key, timeout=_TIMEOUT)
    logger.debug("OpenAI client initialised | default_model=%s | timeout=%ds", _DEFAULT_MODEL, _TIMEOUT)
    return _client


@retry(
    retry=retry_if_exception_type((APITimeoutError, RateLimitError)),
    stop=stop_after_attempt(_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _call_api(
    client: OpenAI,
    model: str,
    messages: list[dict],
    max_tokens: int,
    temperature: float,
) -> str:
    """Execute the chat completion call. Retried by tenacity on timeout / rate limit."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    tokens_used = response.usage.total_tokens if response.usage else 0
    logger.debug("OpenAI tokens used | total=%d", tokens_used)
    return response.choices[0].message.content or ""


def complete(
    prompt: str,
    system: str = "You are an expert hydrogen industry analyst.",
    model: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> str:
    """Send a prompt to OpenAI and return the response text.

    Retries up to 3 times with exponential back-off on timeout and rate limit
    errors. All other API errors are raised immediately after logging.

    Args:
        prompt: User message to send.
        system: System instruction for the assistant role.
        model: OpenAI model ID. Defaults to OPENAI_MODEL env var or gpt-4o-mini.
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature (0.0 = deterministic).

    Returns:
        Response text from the model.

    Raises:
        openai.APIError: On non-retryable API failures.
        SystemExit: If OPENAI_API_KEY is not configured.
    """
    client = _get_client()
    active_model = model or _DEFAULT_MODEL
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    logger.info(
        "OpenAI request | model=%s | prompt_chars=%d | max_tokens=%d",
        active_model,
        len(prompt),
        max_tokens,
    )

    try:
        result = _call_api(client, active_model, messages, max_tokens, temperature)
    except (APITimeoutError, RateLimitError) as exc:
        logger.error(
            "OpenAI request failed after %d retries | error=%s",
            _MAX_RETRIES,
            exc,
        )
        raise
    except APIError as exc:
        logger.error("OpenAI API error | status=%s | error=%s", exc.status_code, exc)
        raise

    logger.info(
        "OpenAI response received | model=%s | response_chars=%d",
        active_model,
        len(result),
    )
    return result


def synthesize(context: str, topic: str = "hydrogen industry") -> str:
    """Transform collected research context into executive intelligence.

    This is the primary entry point used by report generation workflows.
    It wraps complete() with a synthesis-focused system prompt.

    Args:
        context: Raw research text gathered from multiple sources.
        topic: Domain topic label used to frame the synthesis request.

    Returns:
        Structured synthesis text suitable for executive report sections.
    """
    system = (
        "You are an expert hydrogen industry analyst producing executive intelligence reports. "
        "Synthesize the provided research into concise, structured, professional insights. "
        "Lead with business impact. Separate confirmed facts from interpretation. "
        "Preserve source references where available. "
        "Avoid generic AI phrasing. Write in a clear, professional, executive tone."
    )
    prompt = (
        f"Topic: {topic}\n\n"
        f"Research:\n{context}\n\n"
        "Produce a structured synthesis suitable for an executive intelligence report. "
        "Use clear section headings. Prioritise relevance and strategic significance."
    )
    logger.info("Synthesis request | topic=%s | context_chars=%d", topic, len(context))
    return complete(prompt=prompt, system=system, max_tokens=2000, temperature=0.3)
