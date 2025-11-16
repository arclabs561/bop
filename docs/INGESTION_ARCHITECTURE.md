# BOP Ingestion Architecture Design

## Overview

This document outlines architectural options for integrating chat archive ingestion capabilities into BOP, enabling it to process, organize, and query chat archives directly.

## Current State

**BOP's Content Loading:**
- `load_content()` in `research.py` - simple markdown file loader
- `KnowledgeAgent.knowledge_base` - Dict[str, str] mapping filename → content
- `_get_relevant_context()` - simple keyword matching for relevance
- `search_knowledge_base()` - basic keyword search
- `--content-dir` CLI option - points to directory of markdown files

**Current Limitations:**
- Only loads `.md` files
- No format detection or parsing
- No metadata extraction
- No temporal organization
- Simple keyword matching (no semantic search)

## Architectural Options

### Option 1: Extend BOP's Content Loading (Recommended)

**Approach:** Enhance `load_content()` and add ingestion capabilities directly to BOP.

**Components:**
```
src/bop/
├── ingestion/
│   ├── __init__.py
│   ├── loader.py          # Enhanced content loader (replaces load_content)
│   ├── parsers/           # Format parsers (JSON, markdown, text)
│   │   ├── __init__.py
│   │   ├── json_parser.py
│   │   ├── markdown_parser.py
│   │   └── text_parser.py
│   ├── metadata.py        # Metadata extraction
│   └── indexer.py         # Indexing for better search
├── research.py            # Updated to use new loader
└── agent.py               # Enhanced knowledge base with metadata
```

**Flow:**
```
User: bop ingest ./chat-archives/
  ↓
IngestionEngine.ingest_directory()
  ↓
├─→ Parse files (JSON, markdown, text)
├─→ Extract metadata (dates, participants, topics)
├─→ Normalize to markdown format
└─→ Save to content_dir with metadata.json
  ↓
KnowledgeAgent loads enhanced content
  ↓
Enhanced search with metadata filtering
```

**CLI Commands:**
```bash
# Ingest chat archives
bop ingest ./chat-archives/ --output ./content/

# Ingest and immediately query
bop ingest ./chat-archives/ && bop chat --content-dir ./content/

# Ingest with metadata extraction
bop ingest ./chat-archives/ --extract-metadata

# Query with temporal filters
bop chat --content-dir ./content/ --after 2023-01-01 --before 2023-12-31
```

**Pros:**
- ✅ Single tool for ingestion + query
- ✅ Leverages BOP's existing knowledge base infrastructure
- ✅ Can use BOP's structured reasoning for ingestion tasks
- ✅ Unified CLI experience
- ✅ Metadata available for enhanced search

**Cons:**
- ❌ Adds complexity to BOP core
- ❌ Mixes ingestion concerns with research concerns
- ❌ Harder to reuse ingestion logic elsewhere

---

### Option 2: BOP Calls HOP Programmatically

**Approach:** Keep HOP separate, but BOP can call it programmatically.

**Components:**
```
bop/
└── src/bop/
    └── ingestion.py       # Thin wrapper around HOP

hop/                       # Separate project
└── src/hop/
    └── (existing HOP code)
```

**Flow:**
```
User: bop ingest ./chat-archives/
  ↓
BOP.ingestion.ingest() calls HOP programmatically
  ↓
HOP processes and saves to content_dir
  ↓
BOP reloads knowledge base
  ↓
Normal BOP query flow
```

**Implementation:**
```python
# src/bop/ingestion.py
from pathlib import Path
from typing import Optional

# Option A: Import HOP as library
try:
    from hop.ingest import IngestEngine
    from hop.output import OutputFormatter
    HOP_AVAILABLE = True
except ImportError:
    HOP_AVAILABLE = False

# Option B: Call HOP as subprocess
import subprocess

def ingest_with_hop(archive_path: Path, output_dir: Path) -> None:
    """Ingest archives using HOP."""
    if not HOP_AVAILABLE:
        # Fallback: call HOP CLI
        subprocess.run([
            "hop", "ingest", str(archive_path),
            "--output", str(output_dir)
        ])
    else:
        # Use HOP library directly
        engine = IngestEngine()
        result = engine.ingest_directory(archive_path)
        formatter = OutputFormatter()
        formatter.save(result, output_dir)
```

**CLI Commands:**
```bash
# BOP CLI delegates to HOP
bop ingest ./chat-archives/ --output ./content/

# Or use HOP directly, then BOP
hop ingest ./chat-archives/ --output ./content/
bop chat --content-dir ./content/
```

**Pros:**
- ✅ Separation of concerns (ingestion vs. research)
- ✅ HOP can be used standalone
- ✅ BOP stays focused on research/query
- ✅ Can swap ingestion implementations

**Cons:**
- ❌ Requires HOP as dependency (or subprocess)
- ❌ Two tools to maintain
- ❌ Less integrated experience

---

### Option 3: Hybrid - BOP with Optional Ingestion

**Approach:** BOP has basic ingestion, can use HOP for advanced features.

**Components:**
```
bop/
└── src/bop/
    ├── ingestion/
    │   ├── basic_loader.py    # Basic markdown/JSON loader
    │   └── advanced.py         # Optional HOP integration
    └── research.py
```

**Flow:**
```
User: bop ingest ./chat-archives/
  ↓
Check if HOP available
  ↓
├─→ If HOP: Use HOP for full-featured ingestion
└─→ Else: Use basic BOP loader (markdown only)
  ↓
Save to content_dir
  ↓
BOP query flow
```

**Implementation:**
```python
# src/bop/ingestion/basic_loader.py
def load_basic(archive_path: Path) -> Dict[str, str]:
    """Basic loader - markdown and simple JSON only."""
    # Simple implementation
    pass

# src/bop/ingestion/advanced.py
def load_advanced(archive_path: Path) -> Dict[str, Any]:
    """Advanced loader - uses HOP if available."""
    try:
        from hop.ingest import IngestEngine
        # Use HOP
    except ImportError:
        # Fallback to basic
        return load_basic(archive_path)
```

**CLI Commands:**
```bash
# Basic ingestion (always available)
bop ingest ./chat-archives/ --basic

# Advanced ingestion (requires HOP)
bop ingest ./chat-archives/ --advanced

# Auto-detect best available
bop ingest ./chat-archives/  # Uses HOP if available, else basic
```

**Pros:**
- ✅ Works without HOP (basic mode)
- ✅ Enhanced features if HOP available
- ✅ Graceful degradation
- ✅ Single CLI entry point

**Cons:**
- ❌ More complex implementation
- ❌ Two code paths to maintain
- ❌ Potential confusion about which mode is active

---

## Recommended Architecture: Option 1 (Extended BOP)

### Rationale

1. **Unified Experience:** Single tool for ingestion → query workflow
2. **Leverage Existing Infrastructure:** BOP already has knowledge base, search, metadata concepts
3. **Structured Reasoning for Ingestion:** Can use BOP's schemas for:
   - Topic extraction from conversations
   - Temporal organization
   - Participant analysis
   - Decision/conclusion extraction
4. **Enhanced Search:** Metadata enables temporal, participant, topic filtering
5. **Progressive Enhancement:** Start simple, add features incrementally

### Implementation Plan

**Phase 1: Basic Ingestion (MVP)**
- Add `src/bop/ingestion/` module
- Format parsers (JSON, markdown, text)
- Basic metadata extraction (dates, participants)
- Enhanced `load_content()` that handles multiple formats
- CLI command: `bop ingest <path>`

**Phase 2: Enhanced Search**
- Metadata-aware `search_knowledge_base()`
- Temporal filtering (`--after`, `--before`)
- Participant filtering (`--participant`)
- Topic-based search

**Phase 3: Structured Reasoning for Ingestion**
- Use `decompose_and_synthesize` schema for:
  - Topic extraction
  - Decision/conclusion identification
  - Theme extraction
- Temporal organization using structured reasoning

**Phase 4: Advanced Features**
- Semantic search (embeddings)
- Conversation threading
- Cross-reference detection
- External source extraction

### Data Structure Evolution

**Current:**
```python
knowledge_base: Dict[str, str]  # filename → content
```

**Enhanced:**
```python
knowledge_base: Dict[str, Document]  # filename → Document

class Document:
    content: str
    metadata: Dict[str, Any]
    # dates, participants, topics, source_file, etc.
```

**Search Enhancement:**
```python
def search_knowledge_base(
    self,
    query: str,
    after: Optional[datetime] = None,
    before: Optional[datetime] = None,
    participants: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Enhanced search with metadata filtering."""
```

### Integration Points

1. **KnowledgeAgent.__init__()**: Load enhanced content with metadata
2. **KnowledgeAgent._get_relevant_context()**: Use metadata for filtering
3. **KnowledgeAgent.search_knowledge_base()**: Enhanced with metadata filters
4. **CLI**: Add `bop ingest` command
5. **ResearchAgent**: Can search ingested archives + web sources

### Example Usage

```bash
# Ingest chat archives
bop ingest ./chat-archives/ --output ./content/

# Query with temporal filter
bop chat --content-dir ./content/
> What did we discuss about authentication in March 2023?

# Query with participant filter
bop chat --content-dir ./content/
> What did Alice say about the architecture?

# Combined research (archives + web)
bop chat --content-dir ./content/ --research
> How does our team's approach to microservices compare to industry best practices?
```

## Migration Path

If we choose Option 1:

1. **Create ingestion module** in BOP
2. **Enhance load_content()** to handle multiple formats
3. **Add metadata extraction** (dates, participants)
4. **Update KnowledgeAgent** to use enhanced documents
5. **Add CLI command** `bop ingest`
6. **Enhance search** with metadata filtering
7. **Add structured reasoning** for topic extraction

**Backward Compatibility:**
- Existing `load_content()` still works (markdown only)
- New `load_content_enhanced()` for multi-format
- `--content-dir` works with both old and new formats

## Comparison with HOP

**If we extend BOP (Option 1):**
- HOP becomes redundant OR
- HOP becomes a standalone tool for preprocessing
- BOP can optionally use HOP for advanced parsing

**If we keep HOP separate (Option 2):**
- HOP handles all ingestion
- BOP focuses on research/query
- Clear separation of concerns
- Two tools to maintain

## Recommendation

**Go with Option 1 (Extended BOP)** because:
1. Unified user experience
2. Leverages BOP's existing infrastructure
3. Can use structured reasoning for ingestion tasks
4. Metadata enables powerful search features
5. Progressive enhancement path

**Keep HOP as:**
- Reference implementation
- Standalone tool for preprocessing
- Testing ground for new ingestion features

