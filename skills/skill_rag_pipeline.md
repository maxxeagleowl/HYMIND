# Skill - RAG Pipeline Standards

# skill_rag_pipeline.md

---

# Purpose

This skill defines the Retrieval Augmented Generation (RAG) architecture standards for the HYMIND project.

The goal is to ensure that long term memory, retrieval quality, contextual analysis, and historical intelligence remain reliable and maintainable.

This skill applies to:

- Vector databases
- Document chunking
- Embedding generation
- Retrieval workflows
- Metadata handling
- Context assembly
- Historical report memory

---

# Core Philosophy

RAG is treated as a long term intelligence layer.

The purpose of RAG inside HYMIND is not simple document search.

The system uses RAG to support:

- Historical context retention
- Trend analysis
- Strategic memory
- Executive continuity
- Cross report comparison
- Long term market intelligence

The architecture should prioritize retrieval quality over retrieval quantity.

---

# Initial Vector Database Philosophy

The MVP should remain lightweight.

Preferred MVP vector options:

- ChromaDB
- FAISS

Pinecone may be added later if scaling requirements increase.

---

# RAG Workflow Philosophy

Preferred high level workflow:

```text
Research Collection
    ↓
Content Cleaning
    ↓
Chunking
    ↓
Embedding Generation
    ↓
Metadata Enrichment
    ↓
Vector Storage
    ↓
Context Retrieval
    ↓
LLM Analysis
```

---

# Chunking Standards

Chunking should preserve semantic meaning.

The system should avoid:

- Extremely small chunks
- Excessively large chunks
- Broken sentences
- Context fragmentation

---

# Recommended Chunk Size

Preferred starting range:

```text
500 to 1200 characters
```

This may evolve based on retrieval quality testing.

---

# Chunk Overlap Standards

Chunk overlap should support continuity.

Recommended overlap:

```text
50 to 150 characters
```

Overlap should remain minimal but useful.

---

# Chunking Philosophy

Chunks should represent meaningful information units.

Preferred chunk boundaries:

- Paragraphs
- Sections
- Logical article segments
- Topic changes

Blind character splitting should be minimized.

---

# Embedding Standards

Embeddings should remain:

- Consistent
- Reproducible
- Cost aware
- Retrieval optimized

Preferred embedding model:

```text
text-embedding-3-small
```

Possible future upgrade:

```text
text-embedding-3-large
```

---

# Metadata Standards

All stored chunks should include metadata.

Preferred metadata structure:

```python
{
    "source": "",
    "title": "",
    "url": "",
    "published_at": "",
    "topic": "",
    "source_type": "",
    "retrieved_at": ""
}
```

---

# Metadata Philosophy

Metadata is critical for:

- Source traceability
- Report citations
- Historical filtering
- Trend analysis
- Context relevance
- Duplicate detection

Unlabeled chunks should be avoided.

---

# Retrieval Standards

Retrieval should prioritize:

- Relevance
- Diversity
- Strategic usefulness
- Temporal relevance

The goal is contextual intelligence, not maximum retrieval volume.

---

# Recommended Retrieval Strategy

Preferred initial retrieval flow:

```text
Query
    ↓
Embedding
    ↓
Similarity Search
    ↓
Top K Retrieval
    ↓
Context Assembly
```

---

# Retrieval Quality Rules

Retrieved context should:

- Remain relevant
- Avoid duplicates
- Avoid low quality sources
- Preserve diversity of information
- Support executive level synthesis

Low quality retrieval degrades report quality significantly.

---

# Context Assembly Standards

Retrieved chunks should be assembled carefully.

The system should avoid:

- Excessive context length
- Duplicate chunks
- Redundant information
- Contradictory context without explanation

---

# Historical Intelligence Philosophy

Historical retrieval is a strategic capability.

The system should eventually support:

- Market trend comparison
- Competitor history tracking
- Technology evolution tracking
- Funding trend analysis
- Policy development tracking

The memory system should improve report quality over time.

---

# Duplicate Handling Standards

Duplicate content should be minimized.

Duplicate detection may use:

- URL comparison
- Semantic similarity
- Title similarity
- Hash comparison

Duplicate storage wastes retrieval quality and increases costs.

---

# Source Quality Standards

Not all retrieved information should enter vector memory.

Low quality content should be filtered.

Examples of poor sources:

- Extremely short content
- Spam style articles
- Duplicate news copies
- Irrelevant announcements
- Low relevance social content

---

# Retrieval Logging Standards

The system should log:

- Retrieved chunk count
- Similarity scores
- Retrieval failures
- Empty retrieval events
- Vector storage operations

The RAG system must remain observable.

---

# Future RAG Expansion Possibilities

Future enhancements may include:

- Hybrid search
- Semantic reranking
- Time weighted retrieval
- Multi vector retrieval
- Graph based retrieval
- Internal enterprise documents
- Patent intelligence memory
- Strategic market memory

The architecture should remain extensible.

---

# Reliability Philosophy

RAG quality directly impacts executive report quality.

The system prioritizes:

- Retrieval relevance
- Source quality
- Metadata quality
- Traceability
- Historical continuity

over raw vector database size.

---

# Operational Engineering Principle

The RAG layer is treated as the persistent intelligence memory of the HYMIND platform.

The system should continuously improve contextual understanding and strategic report generation through reliable long term retrieval architecture.