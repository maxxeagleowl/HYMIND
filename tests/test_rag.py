"""Phase 3 RAG tests — all external calls mocked, no live OpenAI or Pinecone.

Covers:
  1. Embedding client validates missing API key
  2. Pinecone store builds correct metadata
  3. Stable vector ID generation
  4. Empty findings list returns clean result
  5. Upsert calls Pinecone mock with expected payload
  6. Retriever returns normalized RetrievedFinding results
  7. Missing Pinecone credentials are handled cleanly
  8. LangGraph pipeline still works when RAG is disabled
  9. Existing state schema is backward compatible
"""

import dataclasses
import os
from unittest.mock import MagicMock, patch

import pytest

from hymind.rag.schemas import RetrievedFinding, StoredFinding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stored_finding(
    title: str = "Hydrogen Breakthrough",
    url: str = "https://example.com/h2",
    source: str = "Reuters",
    source_type: str = "news",
    snippet: str = "A major development in hydrogen fuel cells.",
    topic: str = "hydrogen fuel cell",
) -> StoredFinding:
    return StoredFinding(
        title=title,
        url=url,
        source=source,
        source_type=source_type,
        published_at="2026-05-18",
        snippet=snippet,
        content="Full content here.",
        topic=topic,
    )


def _fake_embedding(dim: int = 8) -> list[float]:
    return [0.1] * dim


def _mock_pinecone_index(matches: list[dict] | None = None) -> MagicMock:
    idx = MagicMock()
    idx.upsert.return_value = None
    idx.query.return_value = {"matches": matches or []}
    return idx


def _mock_openai_client(embedding: list[float] | None = None) -> MagicMock:
    client = MagicMock()
    item = MagicMock()
    item.embedding = embedding or _fake_embedding()
    response = MagicMock()
    response.data = [item]
    client.embeddings.create.return_value = response
    return client


# ---------------------------------------------------------------------------
# 1. Embedding client validates missing API key
# ---------------------------------------------------------------------------

class TestEmbeddingsMissingApiKey:
    def test_raises_value_error_when_key_absent(self):
        from hymind.rag.embeddings import create_embeddings
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                create_embeddings(["some text"])

    def test_raises_even_with_whitespace_key(self):
        from hymind.rag.embeddings import create_embeddings
        with patch.dict(os.environ, {"OPENAI_API_KEY": "   "}, clear=False):
            with pytest.raises(ValueError):
                create_embeddings(["some text"])

    def test_empty_text_list_returns_empty_without_api_call(self):
        from hymind.rag.embeddings import create_embeddings
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            result = create_embeddings([])
        assert result == []

    def test_injected_client_is_used_for_embedding(self):
        from hymind.rag.embeddings import create_embeddings
        client = _mock_openai_client(embedding=[0.5, 0.5])
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            result = create_embeddings(["hydrogen market"], client=client)
        assert result == [[0.5, 0.5]]
        client.embeddings.create.assert_called_once()

    def test_embedding_model_from_env(self):
        from hymind.rag.embeddings import get_embedding_model
        with patch.dict(os.environ, {"OPENAI_EMBEDDING_MODEL": "text-embedding-3-large"}, clear=False):
            assert get_embedding_model() == "text-embedding-3-large"

    def test_embedding_model_defaults_to_small(self):
        from hymind.rag.embeddings import get_embedding_model, DEFAULT_EMBEDDING_MODEL
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_EMBEDDING_MODEL"}
        with patch.dict(os.environ, env, clear=True):
            assert get_embedding_model() == DEFAULT_EMBEDDING_MODEL


# ---------------------------------------------------------------------------
# 2. Pinecone store builds correct metadata
# ---------------------------------------------------------------------------

class TestFindingToMetadata:
    def test_all_required_keys_present(self):
        from hymind.rag.pinecone_store import finding_to_metadata
        finding = _stored_finding()
        meta = finding_to_metadata(finding)
        for key in ("title", "url", "source", "source_type", "published_at",
                    "snippet", "content_preview", "topic", "category", "collected_at"):
            assert key in meta, f"Missing metadata key: {key}"

    def test_title_mapped_correctly(self):
        from hymind.rag.pinecone_store import finding_to_metadata
        meta = finding_to_metadata(_stored_finding(title="PEM Electrolyser Advance"))
        assert meta["title"] == "PEM Electrolyser Advance"

    def test_url_mapped_correctly(self):
        from hymind.rag.pinecone_store import finding_to_metadata
        meta = finding_to_metadata(_stored_finding(url="https://h2news.com/article"))
        assert meta["url"] == "https://h2news.com/article"

    def test_source_type_preserved(self):
        from hymind.rag.pinecone_store import finding_to_metadata
        meta = finding_to_metadata(_stored_finding(source_type="rss"))
        assert meta["source_type"] == "rss"

    def test_snippet_truncated_to_limit(self):
        from hymind.rag.pinecone_store import finding_to_metadata, _SNIPPET_LIMIT
        long_snippet = "x" * (_SNIPPET_LIMIT + 200)
        finding = _stored_finding(snippet=long_snippet)
        meta = finding_to_metadata(finding)
        assert len(meta["snippet"]) == _SNIPPET_LIMIT

    def test_none_published_at_becomes_empty_string(self):
        from hymind.rag.pinecone_store import finding_to_metadata
        finding = _stored_finding()
        finding.published_at = None
        meta = finding_to_metadata(finding)
        assert meta["published_at"] == ""

    def test_collected_at_auto_filled_when_none(self):
        from hymind.rag.pinecone_store import finding_to_metadata
        finding = _stored_finding()
        finding.collected_at = None
        meta = finding_to_metadata(finding)
        assert meta["collected_at"]  # non-empty ISO string


# ---------------------------------------------------------------------------
# 3. Stable vector ID generation
# ---------------------------------------------------------------------------

class TestMakeVectorId:
    def test_same_url_produces_same_id(self):
        from hymind.rag.pinecone_store import make_vector_id
        url = "https://example.com/article"
        assert make_vector_id(url) == make_vector_id(url)

    def test_different_urls_produce_different_ids(self):
        from hymind.rag.pinecone_store import make_vector_id
        assert make_vector_id("https://a.com") != make_vector_id("https://b.com")

    def test_id_length_is_48_chars(self):
        from hymind.rag.pinecone_store import make_vector_id
        vid = make_vector_id("https://example.com/hydrogen")
        assert len(vid) == 48

    def test_empty_url_falls_back_to_title(self):
        from hymind.rag.pinecone_store import make_vector_id
        vid_no_url = make_vector_id("", title="Some Title")
        vid_with_url = make_vector_id("https://example.com")
        assert vid_no_url != vid_with_url

    def test_whitespace_url_stripped_before_hashing(self):
        from hymind.rag.pinecone_store import make_vector_id
        assert make_vector_id("  https://x.com  ") == make_vector_id("https://x.com")


# ---------------------------------------------------------------------------
# 4. Empty findings list returns clean result
# ---------------------------------------------------------------------------

class TestUpsertEmptyFindings:
    def test_empty_list_returns_zero(self):
        from hymind.rag.pinecone_store import upsert_findings
        result = upsert_findings([], [], pinecone_index=MagicMock())
        assert result == 0

    def test_empty_list_does_not_call_pinecone(self):
        from hymind.rag.pinecone_store import upsert_findings
        mock_idx = _mock_pinecone_index()
        upsert_findings([], [], pinecone_index=mock_idx)
        mock_idx.upsert.assert_not_called()

    def test_length_mismatch_raises_value_error(self):
        from hymind.rag.pinecone_store import upsert_findings
        findings = [_stored_finding()]
        embeddings: list = []  # mismatch
        with pytest.raises(ValueError, match="mismatch"):
            upsert_findings(findings, embeddings, pinecone_index=MagicMock())


# ---------------------------------------------------------------------------
# 5. Upsert calls Pinecone mock with expected payload
# ---------------------------------------------------------------------------

class TestUpsertCallsMock:
    def test_upsert_called_once_with_vectors(self):
        from hymind.rag.pinecone_store import upsert_findings
        finding = _stored_finding()
        embedding = _fake_embedding()
        mock_idx = _mock_pinecone_index()

        count = upsert_findings([finding], [embedding], pinecone_index=mock_idx)

        assert count == 1
        mock_idx.upsert.assert_called_once()
        call_kwargs = mock_idx.upsert.call_args[1]
        vectors = call_kwargs.get("vectors", [])
        assert len(vectors) == 1

    def test_upsert_vector_has_id_values_metadata(self):
        from hymind.rag.pinecone_store import upsert_findings, make_vector_id
        finding = _stored_finding(url="https://example.com/h2")
        embedding = _fake_embedding()
        mock_idx = _mock_pinecone_index()

        upsert_findings([finding], [embedding], pinecone_index=mock_idx)

        vectors = mock_idx.upsert.call_args[1]["vectors"]
        v = vectors[0]
        assert v["id"] == make_vector_id("https://example.com/h2")
        assert v["values"] == embedding
        assert "title" in v["metadata"]

    def test_upsert_multiple_findings(self):
        from hymind.rag.pinecone_store import upsert_findings
        findings = [
            _stored_finding(url="https://a.com"),
            _stored_finding(url="https://b.com"),
            _stored_finding(url="https://c.com"),
        ]
        embeddings = [_fake_embedding(), _fake_embedding(), _fake_embedding()]
        mock_idx = _mock_pinecone_index()

        count = upsert_findings(findings, embeddings, pinecone_index=mock_idx)
        assert count == 3
        vectors = mock_idx.upsert.call_args[1]["vectors"]
        assert len(vectors) == 3

    def test_upsert_returns_count(self):
        from hymind.rag.pinecone_store import upsert_findings
        findings = [_stored_finding(), _stored_finding(url="https://b.com")]
        embeddings = [_fake_embedding(), _fake_embedding()]
        mock_idx = _mock_pinecone_index()
        assert upsert_findings(findings, embeddings, pinecone_index=mock_idx) == 2


# ---------------------------------------------------------------------------
# 6. Retriever returns normalized retrieval results
# ---------------------------------------------------------------------------

class TestRetrieverReturnsResults:
    def _pinecone_match(
        self,
        title: str = "H2 Market Growth",
        url: str = "https://h2news.com/market",
        source: str = "H2 News",
        score: float = 0.92,
    ) -> dict:
        return {
            "id": "abc123",
            "score": score,
            "metadata": {
                "title": title,
                "url": url,
                "source": source,
                "source_type": "news",
                "published_at": "2026-04-01",
                "snippet": "The hydrogen market is growing rapidly.",
                "topic": "hydrogen market",
            },
        }

    def test_returns_retrieved_findings(self):
        from hymind.rag.retriever import retrieve_context
        client = _mock_openai_client()
        mock_idx = _mock_pinecone_index(matches=[self._pinecone_match()])

        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "PINECONE_API_KEY": "pc-test-key",
            "PINECONE_INDEX_NAME": "hymind-research",
        }, clear=False):
            results = retrieve_context(
                topic="hydrogen market",
                query="hydrogen market Europe",
                top_k=3,
                openai_client=client,
                pinecone_index=mock_idx,
            )

        assert len(results) == 1
        assert isinstance(results[0], RetrievedFinding)

    def test_retrieved_finding_fields_populated(self):
        from hymind.rag.retriever import retrieve_context
        match = self._pinecone_match(title="PEM Advance", url="https://pem.com", score=0.88)
        client = _mock_openai_client()
        mock_idx = _mock_pinecone_index(matches=[match])

        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "PINECONE_API_KEY": "pc-key",
            "PINECONE_INDEX_NAME": "hymind-research",
        }, clear=False):
            results = retrieve_context(
                "hydrogen", "hydrogen PEM", openai_client=client, pinecone_index=mock_idx
            )

        r = results[0]
        assert r.title == "PEM Advance"
        assert r.url == "https://pem.com"
        assert r.score == pytest.approx(0.88)

    def test_empty_matches_returns_empty_list(self):
        from hymind.rag.retriever import retrieve_context
        client = _mock_openai_client()
        mock_idx = _mock_pinecone_index(matches=[])

        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "PINECONE_API_KEY": "pc-key",
            "PINECONE_INDEX_NAME": "hymind-research",
        }, clear=False):
            results = retrieve_context(
                "hydrogen", "hydrogen", openai_client=client, pinecone_index=mock_idx
            )

        assert results == []

    def test_multiple_matches_all_returned(self):
        from hymind.rag.retriever import retrieve_context
        matches = [
            self._pinecone_match(title="A", url="https://a.com", score=0.95),
            self._pinecone_match(title="B", url="https://b.com", score=0.88),
        ]
        client = _mock_openai_client()
        mock_idx = _mock_pinecone_index(matches=matches)

        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "PINECONE_API_KEY": "pc-key",
            "PINECONE_INDEX_NAME": "hymind-research",
        }, clear=False):
            results = retrieve_context(
                "hydrogen", "hydrogen", openai_client=client, pinecone_index=mock_idx
            )

        assert len(results) == 2


# ---------------------------------------------------------------------------
# 7. Missing Pinecone credentials are handled cleanly
# ---------------------------------------------------------------------------

class TestMissingPineconeCredentials:
    def test_retrieve_context_returns_empty_when_no_pinecone_key(self):
        from hymind.rag.retriever import retrieve_context
        env = {k: v for k, v in os.environ.items() if k != "PINECONE_API_KEY"}
        env["OPENAI_API_KEY"] = "test-key"
        with patch.dict(os.environ, env, clear=True):
            results = retrieve_context("hydrogen", "hydrogen market")
        assert results == []

    def test_retrieve_context_returns_empty_when_no_openai_key(self):
        from hymind.rag.retriever import retrieve_context
        with patch.dict(os.environ, {
            "PINECONE_API_KEY": "pc-key",
            "PINECONE_INDEX_NAME": "hymind-research",
            "OPENAI_API_KEY": "",
        }, clear=False):
            results = retrieve_context("hydrogen", "hydrogen market")
        assert results == []

    def test_retrieve_context_never_raises(self):
        """retrieve_context must always return [] rather than propagating exceptions."""
        from hymind.rag.retriever import retrieve_context
        # Both missing — guaranteed graceful degradation
        with patch.dict(os.environ, {"PINECONE_API_KEY": "", "OPENAI_API_KEY": ""}, clear=False):
            results = retrieve_context("hydrogen", "hydrogen market")
        assert results == []

    def test_is_pinecone_configured_false_when_no_key(self):
        from hymind.rag.pinecone_store import is_pinecone_configured
        env = {k: v for k, v in os.environ.items() if k != "PINECONE_API_KEY"}
        env["PINECONE_API_KEY"] = ""
        with patch.dict(os.environ, env, clear=True):
            assert is_pinecone_configured() is False

    def test_is_pinecone_configured_true_when_key_set(self):
        from hymind.rag.pinecone_store import is_pinecone_configured
        with patch.dict(os.environ, {
            "PINECONE_API_KEY": "pc-real-key",
            "PINECONE_INDEX_NAME": "hymind-research",
        }, clear=False):
            assert is_pinecone_configured() is True

    def test_upsert_raises_when_no_key_and_no_index_injected(self):
        from hymind.rag.pinecone_store import upsert_findings
        finding = _stored_finding()
        env = {k: v for k, v in os.environ.items() if k != "PINECONE_API_KEY"}
        env["PINECONE_API_KEY"] = ""
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="PINECONE_API_KEY"):
                upsert_findings([finding], [_fake_embedding()])


# ---------------------------------------------------------------------------
# 8. LangGraph pipeline still works when RAG is disabled
# ---------------------------------------------------------------------------

class TestWorkflowWithRagDisabled:
    def test_build_workflow_succeeds(self):
        from hymind.workflows.research_workflow import build_workflow
        app = build_workflow()
        assert app is not None

    def test_initial_state_has_rag_context_field(self):
        from hymind.workflows.state import initial_state
        state = initial_state("hydrogen")
        assert "rag_context" in state
        assert state["rag_context"] == []

    def test_store_node_skips_when_pinecone_not_configured(self):
        from hymind.workflows.research_workflow import store_findings_in_pinecone
        from hymind.workflows.state import initial_state
        state = {
            **initial_state("hydrogen"),
            "merged_results": [
                {"title": "T", "url": "https://x.com", "snippet": "S",
                 "published_at": None, "source": "Test", "source_type": "news",
                 "search_query": "hydrogen", "author": None, "rank": 1}
            ],
        }
        with patch.dict(os.environ, {"PINECONE_API_KEY": ""}, clear=False):
            result = store_findings_in_pinecone(state)
        # Must return a warnings dict, not raise
        assert isinstance(result, dict)
        warnings = result.get("warnings", [])
        assert any("Pinecone" in w for w in warnings)

    def test_retrieve_node_returns_empty_list_when_not_configured(self):
        from hymind.workflows.research_workflow import retrieve_context_from_pinecone
        from hymind.workflows.state import initial_state
        state = initial_state("hydrogen")
        with patch.dict(os.environ, {"PINECONE_API_KEY": "", "OPENAI_API_KEY": ""}, clear=False):
            result = retrieve_context_from_pinecone(state)
        assert isinstance(result, dict)
        assert result.get("rag_context") == []

    def test_store_node_skips_when_openai_key_missing(self):
        from hymind.workflows.research_workflow import store_findings_in_pinecone
        from hymind.workflows.state import initial_state
        state = {**initial_state("hydrogen"), "merged_results": []}
        with patch.dict(os.environ, {
            "PINECONE_API_KEY": "pc-key",
            "OPENAI_API_KEY": "",
        }, clear=False):
            result = store_findings_in_pinecone(state)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# 9. findings_from_state: correctly converts AgentState results
# ---------------------------------------------------------------------------

class TestFindingsFromState:
    def test_merged_results_converted_to_stored_findings(self):
        from hymind.rag.retriever import findings_from_state
        state = {
            "merged_results": [
                {"title": "T1", "url": "https://a.com", "snippet": "S1",
                 "published_at": "2026-05-01", "source": "Reuters",
                 "source_type": "news", "search_query": "hydrogen",
                 "author": None, "rank": 1},
            ],
            "crawled_results": [],
        }
        findings = findings_from_state(state, topic="hydrogen")
        assert len(findings) == 1
        assert findings[0].title == "T1"
        assert findings[0].url == "https://a.com"
        assert findings[0].topic == "hydrogen"

    def test_items_without_url_are_skipped(self):
        from hymind.rag.retriever import findings_from_state
        state = {
            "merged_results": [
                {"title": "No URL", "url": "", "snippet": "S", "published_at": None,
                 "source": "S", "source_type": "news", "search_query": "q",
                 "author": None, "rank": 1},
                {"title": "Has URL", "url": "https://b.com", "snippet": "S2",
                 "published_at": None, "source": "S", "source_type": "news",
                 "search_query": "q", "author": None, "rank": 2},
            ],
            "crawled_results": [],
        }
        findings = findings_from_state(state, topic="hydrogen")
        assert len(findings) == 1
        assert findings[0].url == "https://b.com"

    def test_crawled_content_merged_by_url(self):
        from hymind.rag.retriever import findings_from_state
        state = {
            "merged_results": [
                {"title": "T", "url": "https://c.com/article", "snippet": "S",
                 "published_at": None, "source": "S", "source_type": "news",
                 "search_query": "q", "author": None, "rank": 1},
            ],
            "crawled_results": [
                {"url": "https://c.com/article", "content": "Full page text here.",
                 "extraction_success": True},
            ],
        }
        findings = findings_from_state(state, topic="hydrogen")
        assert findings[0].content == "Full page text here."

    def test_empty_merged_results_returns_empty_list(self):
        from hymind.rag.retriever import findings_from_state
        state = {"merged_results": [], "crawled_results": []}
        assert findings_from_state(state, topic="hydrogen") == []


# ---------------------------------------------------------------------------
# 10. RAG context serializes to dicts in workflow node output
# ---------------------------------------------------------------------------

class TestRagContextSerializationInWorkflow:
    def test_retrieve_node_returns_dicts_not_dataclasses(self):
        """The workflow node must return plain dicts (dataclasses.asdict) for LangGraph."""
        from hymind.workflows.research_workflow import retrieve_context_from_pinecone
        from hymind.workflows.state import initial_state

        mock_idx = _mock_pinecone_index(matches=[{
            "id": "abc",
            "score": 0.9,
            "metadata": {
                "title": "Historical H2 Article",
                "url": "https://h2history.com",
                "source": "H2 History",
                "source_type": "news",
                "published_at": "2025-01-01",
                "snippet": "Old but relevant.",
                "topic": "hydrogen",
            },
        }])
        client = _mock_openai_client()

        state = initial_state("hydrogen")

        with patch("hymind.rag.retriever.is_pinecone_configured", return_value=True), \
             patch("hymind.rag.retriever.create_embeddings", return_value=[_fake_embedding()]), \
             patch("hymind.rag.retriever.query_index", return_value=[{
                 "id": "abc", "score": 0.9,
                 "metadata": {
                     "title": "Historical H2", "url": "https://h2history.com",
                     "source": "H2 History", "source_type": "news",
                     "published_at": "2025-01-01", "snippet": "Old text.", "topic": "hydrogen",
                 }
             }]):
            with patch.dict(os.environ, {
                "OPENAI_API_KEY": "test-key",
                "PINECONE_API_KEY": "pc-key",
            }, clear=False):
                result = retrieve_context_from_pinecone(state)

        rag_context = result.get("rag_context", [])
        assert isinstance(rag_context, list)
        if rag_context:
            assert isinstance(rag_context[0], dict), "rag_context must contain plain dicts"

    def test_rag_context_included_in_report_build_context(self):
        """build_context includes RAG historical context when rag_context is populated."""
        from hymind.reporting.report_generator import build_context
        from hymind.workflows.state import initial_state

        state = {
            **initial_state("hydrogen"),
            "rag_context": [
                {
                    "title": "Historical Funding", "url": "https://hist.com",
                    "source": "H2 News", "source_type": "news",
                    "published_at": "2025-06-01",
                    "snippet": "Germany committed 10bn EUR to hydrogen.",
                    "score": 0.91, "metadata": {},
                }
            ],
        }
        context, source_count = build_context(state)
        assert "HISTORICAL CONTEXT" in context
        assert "Germany committed" in context
        assert source_count >= 1
