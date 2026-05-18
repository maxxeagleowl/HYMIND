"""Shared pytest fixtures for the HYMIND test suite."""

import pytest
import hymind.tools.openai_client as _oai


@pytest.fixture(autouse=True)
def reset_openai_singleton():
    """Reset the OpenAI client singleton between tests to prevent cross-test state leakage."""
    original = _oai._client
    yield
    _oai._client = original
