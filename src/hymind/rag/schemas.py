"""Data schemas for the HYMIND RAG layer."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StoredFinding:
    """A normalized research finding ready for Pinecone ingestion."""

    title: str
    url: str
    source: str
    source_type: str
    published_at: Optional[str]
    snippet: str
    content: str
    topic: str
    category: Optional[str] = None
    collected_at: Optional[str] = None


@dataclass
class RetrievedFinding:
    """A finding retrieved from Pinecone with its similarity score."""

    title: str
    url: str
    source: str
    source_type: str
    published_at: Optional[str]
    snippet: str
    score: float
    metadata: dict = field(default_factory=dict)
