"""OpenAI embeddings client for HYMIND RAG layer.

Uses dependency injection for the OpenAI client so that tests can pass a mock
without patching the openai module globally.
"""

import os
from typing import Any, Optional

from hymind.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"


def get_embedding_model() -> str:
    """Return the configured embedding model name."""
    return os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def create_embeddings(
    texts: list[str],
    client: Optional[Any] = None,
) -> list[list[float]]:
    """Create embeddings for a list of texts using OpenAI.

    Args:
        texts: Text strings to embed. Empty list returns [] without API call.
        client: Optional injected OpenAI client. If None, one is created from env.

    Returns:
        List of embedding vectors, one per input text.

    Raises:
        ValueError: If OPENAI_API_KEY is not set.
        openai.APIError: On non-retryable OpenAI failures.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set — embeddings require OpenAI. "
            "Add it to your .env file."
        )

    if not texts:
        logger.debug("create_embeddings: empty input — returning []")
        return []

    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

    model = get_embedding_model()
    logger.debug("create_embeddings | model=%s | texts=%d", model, len(texts))

    try:
        response = client.embeddings.create(input=texts, model=model)
        embeddings = [item.embedding for item in response.data]
        logger.info(
            "create_embeddings complete | model=%s | count=%d",
            model,
            len(embeddings),
        )
        return embeddings
    except Exception as exc:
        logger.error("create_embeddings failed | model=%s | error=%s", model, exc)
        raise
