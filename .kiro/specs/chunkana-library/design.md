# Design Document: Chunkana Library

## Overview

Chunkana — это Python-библиотека для интеллектуального разбиения Markdown-документов на семантически осмысленные фрагменты (chunks). Библиотека переносит "магию" из dify-markdown-chunker в самостоятельный пакет с чистым API, готовый к публикации на PyPI.

### Design Goals

1. **Простота использования**: 3-10 строк кода для базового сценария
2. **Совместимость алгоритма chunking**: Границы чанков и metadata идентичны v2 (подтверждается baseline). API — упрощён. Это НЕ "полная совместимость" — output formatting и Dify-specific параметры не гарантируются 1:1.
3. **Расширяемость**: Модульная архитектура для добавления стратегий и рендереров
4. **Производительность**: Streaming для файлов >10MB, O(n) парсинг
5. **Тестируемость**: Property-based тесты для всех инвариантов

### Non-Goals

- CLI интерфейс (может быть добавлен позже как extras)
- Интеграция с конкретными SDK (Dify, n8n) — только рендереры
- Поддержка форматов кроме Markdown (RST, AsciiDoc)

### Implementation Approach: Port 1:1

Для обеспечения полной совместимости с dify-markdown-chunker v2:

1. **Step 0**: Зафиксировать baseline (commit hash + fixtures + golden outputs)
2. **Step 1**: Скопировать `markdown_chunker_v2/` целиком в `src/chunkana/`
3. **Step 2**: Минимальные правки: убрать Dify SDK импорты, добавить `ChunkerConfig` как алиас для `ChunkConfig`
4. **Step 3**: Добавить тонкий слой `api.py` с convenience функциями
5. **Step 4**: Прогнать baseline тесты — убедиться что output идентичен
6. **Step 5**: Только после прохождения baseline — допускать внутренние улучшения

**Важно про ChunkConfig**: Оригинальное имя `ChunkConfig` сохраняется для совместимости. `ChunkerConfig` добавляется как алиас: `ChunkerConfig = ChunkConfig`.

**Критически важно**: НЕ реорганизовывать структуру модулей до прохождения baseline тестов.


## Responsibility Matrix (A3)

Чёткое разделение ответственности между библиотекой и плагином:

### Библиотека Chunkana отвечает за:
- Парсинг и анализ Markdown документов
- Выбор и применение стратегий чанкинга
- Определение границ чанков (start_line, end_line)
- Расчёт overlap (previous_content, next_content в metadata)
- Enrichment metadata (header_path, content_type, strategy, etc.)
- Сериализация Chunk/ChunkerConfig (to_dict, from_dict, to_json, from_json)
- Renderers как чистые функции форматирования
- Валидация результатов (coverage, ordering)

### Плагин dify-markdown-chunker отвечает за:
- Маппинг входных параметров Dify → ChunkerConfig
- Выбор renderer'а по `include_metadata` и другим Dify-настройкам
- Упаковка Dify plugin SDK, manifest, tool schema
- Dify-специфичные defaults/валидации
- Форматирование вывода для Dify UI

### Ключевые границы:
- `include_metadata` — параметр **плагина**, не библиотеки
- Embedded overlap в content — это **renderer-level**, не chunking-level
- `chunk.content` всегда canonical (без дублей overlap)


## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Public API                               │
│  chunk_markdown() | MarkdownChunker | iter_chunks()             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Core Pipeline                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Parser  │→ │ Analyzer │→ │ Strategy │→ │ Postproc │        │
│  └──────────┘  └──────────┘  │ Selector │  └──────────┘        │
│                              └──────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Strategies  │    │  Renderers   │    │  Hierarchy   │
│  - CodeAware │    │  - JSON      │    │  Builder     │
│  - ListAware │    │  - Inline    │    │              │
│  - Structural│    │  - Dify      │    │              │
│  - Fallback  │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Data Flow

1. **Input**: Raw Markdown text + ChunkerConfig
2. **Parse**: Extract headers, code blocks, tables, lists, LaTeX → ContentAnalysis
3. **Select**: Choose strategy based on ContentAnalysis + config thresholds
4. **Apply**: Strategy produces initial chunks
5. **Postprocess**: Merge small chunks, apply overlap, enrich metadata
6. **Validate**: Check coverage and ordering invariants
7. **Output**: List[Chunk] with full metadata

## Module Structure (Port 1:1 from v2)

Структура модулей копируется из `markdown_chunker_v2/` с минимальными изменениями:

```
src/chunkana/
├── __init__.py           # Public exports
├── api.py                # Convenience functions (NEW)
├── config.py             # ChunkConfig (сохраняется) + ChunkerConfig (алиас)
├── types.py              # Chunk, ContentAnalysis, FencedBlock, etc.
├── parser.py             # MarkdownParser
├── chunker.py            # MarkdownChunker
├── hierarchy.py          # HierarchicalChunkingResult, HierarchyBuilder
├── adaptive_sizing.py    # AdaptiveSizeConfig
├── table_grouping.py     # TableGroupingConfig, TableGrouper
├── strategies/
│   ├── __init__.py
│   ├── base.py
│   ├── selector.py
│   ├── code_aware.py
│   ├── list_aware.py
│   ├── structural.py
│   └── fallback.py
├── streaming/            # Существует в v2 - портировать как есть
│   ├── __init__.py
│   ├── config.py         # StreamingConfig
│   └── processor.py      # StreamingProcessor
└── renderers/            # (NEW - тонкий слой)
    ├── __init__.py
    └── inline_metadata.py
```

**Примечание**: Структура `models/`, `parsing/`, `postprocess/` — это Phase 2 рефакторинг, ПОСЛЕ прохождения baseline.


## Components and Interfaces

### 1. Public API (`chunkana/api.py`) — NEW thin layer

**Design Decision (A1)**: `chunk()` и `chunk_markdown()` всегда возвращают `List[Chunk]`. Расширенные результаты — через отдельные методы.

```python
from typing import Iterator
from .chunker import MarkdownChunker
from .config import ChunkerConfig
from .types import Chunk, ChunkingMetrics, ChunkingResult, ContentAnalysis

def chunk_markdown(
    text: str,
    config: ChunkerConfig | None = None
) -> list[Chunk]:
    """Chunk markdown text. Always returns List[Chunk]."""
    chunker = MarkdownChunker(config or ChunkerConfig.default())
    return chunker.chunk(text)

def analyze_markdown(
    text: str,
    config: ChunkerConfig | None = None
) -> ContentAnalysis:
    """Analyze markdown without chunking."""
    chunker = MarkdownChunker(config or ChunkerConfig.default())
    return chunker.analyze(text)

def chunk_with_analysis(
    text: str,
    config: ChunkerConfig | None = None
) -> ChunkingResult:
    """Chunk and return structured result with analysis."""
    chunker = MarkdownChunker(config or ChunkerConfig.default())
    return chunker.chunk_with_analysis(text)

def chunk_with_metrics(
    text: str,
    config: ChunkerConfig | None = None
) -> tuple[list[Chunk], ChunkingMetrics]:
    """Chunk text and return metrics."""
    chunker = MarkdownChunker(config or ChunkerConfig.default())
    chunks = chunker.chunk(text)
    cfg = config or ChunkerConfig.default()
    metrics = ChunkingMetrics.from_chunks(chunks, cfg.min_chunk_size, cfg.max_chunk_size)
    return chunks, metrics

def iter_chunks(
    text: str,
    config: ChunkerConfig | None = None
) -> Iterator[Chunk]:
    """Yield chunks one at a time for memory efficiency."""
    chunker = MarkdownChunker(config or ChunkerConfig.default())
    yield from chunker._chunk_iterator(text)
```

### 2. Configuration (`chunkana/config.py`) — Port from v2

```python
# Портируется из markdown_chunker_v2/config.py
# ChunkConfig сохраняется как есть, ChunkerConfig добавляется как алиас

from dataclasses import dataclass
from typing import Optional
from .adaptive_sizing import AdaptiveSizeConfig

@dataclass
class ChunkConfig:
    """Configuration for markdown chunking. Original name preserved for compatibility."""
    
    # Size parameters
    max_chunk_size: int = 4096
    min_chunk_size: int = 512
    overlap_size: int = 200
    
    # Behavior parameters
    preserve_atomic_blocks: bool = True
    extract_preamble: bool = True
    
    # Strategy selection thresholds
    code_threshold: float = 0.3
    structure_threshold: int = 3
    list_ratio_threshold: float = 0.4
    list_count_threshold: int = 5
    
    # Override
    strategy_override: Optional[str] = None
    
    # Code-context binding parameters (from v2)
    enable_code_context_binding: bool = True
    max_context_chars_before: int = 500
    max_context_chars_after: int = 300
    related_block_max_gap: int = 5
    bind_output_blocks: bool = True
    preserve_before_after_pairs: bool = True
    
    # Adaptive sizing parameters
    use_adaptive_sizing: bool = False
    adaptive_config: Optional[AdaptiveSizeConfig] = None
    
    # Hierarchical chunking parameters
    include_document_summary: bool = True
    
    # Content preprocessing parameters
    strip_obsidian_block_ids: bool = False
    
    # LaTeX formula handling parameters
    preserve_latex_blocks: bool = True
    latex_display_only: bool = True
    latex_max_context_chars: int = 300
    
    # Table grouping parameters
    group_related_tables: bool = False
    table_grouping_config: Optional["TableGroupingConfig"] = None
    
    # Overlap cap (from v2 behavior)
    overlap_cap_ratio: float = 0.35
    
    def __post_init__(self):
        """Validate configuration - same logic as v2."""
        # ... validation logic from v2 ...
    
    @classmethod
    def default(cls) -> "ChunkerConfig":
        return cls()
    
    @classmethod
    def for_code_heavy(cls) -> "ChunkerConfig":
        return cls(max_chunk_size=8192, min_chunk_size=1024, overlap_size=100, code_threshold=0.2)
    
    # ... other factory methods from v2 ...
    
    def to_dict(self) -> dict:
        """Serialize config - same as v2."""
        # ... from v2 ...
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChunkerConfig":
        """Deserialize config - same as v2."""
        # ... from v2 ...

# Алиас для публичного API (ChunkConfig — оригинальное имя из v2)
ChunkerConfig = ChunkConfig
```


### 3. Data Models (`chunkana/types.py`) — Port from v2

```python
# Портируется из markdown_chunker_v2/types.py БЕЗ ИЗМЕНЕНИЙ
# Все dataclass'ы сохраняют структуру и поведение v2

@dataclass
class Chunk:
    """A chunk of markdown content. Ported from v2."""
    content: str
    start_line: int  # 1-indexed
    end_line: int    # 1-indexed
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate chunk on creation - same as v2."""
        if self.start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {self.start_line}")
        if self.end_line < self.start_line:
            raise ValueError(f"end_line ({self.end_line}) must be >= start_line ({self.start_line})")
        if not self.content.strip():
            raise ValueError("Chunk content cannot be empty or whitespace-only")
    
    @property
    def size(self) -> int:
        return len(self.content)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization - same as v2."""
        return {
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "size": self.size,
            "line_count": self.end_line - self.start_line + 1,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        """Create from dictionary - same as v2."""
        return cls(
            content=data["content"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            metadata=data.get("metadata", {}),
        )
    
    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Chunk":
        import json
        return cls.from_dict(json.loads(json_str))

@dataclass
class FencedBlock:
    """Fenced code block - same as v2."""
    language: Optional[str]
    content: str
    start_line: int
    end_line: int
    start_pos: int = 0
    end_pos: int = 0
    fence_char: str = "`"
    fence_length: int = 3
    is_closed: bool = True
    # Code-context binding fields (from v2)
    context_role: Optional[str] = None
    has_explanation_before: bool = False
    has_explanation_after: bool = False

@dataclass
class ContentAnalysis:
    """Result of analyzing a markdown document - same as v2."""
    total_chars: int
    total_lines: int
    code_ratio: float
    code_block_count: int
    header_count: int
    max_header_depth: int
    table_count: int
    list_count: int = 0
    list_item_count: int = 0
    code_blocks: list[FencedBlock] = field(default_factory=list)
    headers: list["Header"] = field(default_factory=list)
    tables: list["TableBlock"] = field(default_factory=list)
    list_blocks: list["ListBlock"] = field(default_factory=list)
    latex_blocks: list["LatexBlock"] = field(default_factory=list)
    has_preamble: bool = False
    preamble_end_line: int = 0
    list_ratio: float = 0.0
    max_list_depth: int = 0
    has_checkbox_lists: bool = False
    avg_sentence_length: float = 0.0
    latex_block_count: int = 0
    latex_ratio: float = 0.0
    _lines: Optional[list[str]] = field(default=None, repr=False)

# ... остальные dataclass'ы из v2: Header, TableBlock, ListBlock, LatexBlock, ChunkingMetrics, ChunkingResult
```


### 4. Renderers (`chunkana/renderers/`) — NEW thin layer

**Design Decision**: Renderers — это форматирование, не chunking. Они НЕ влияют на границы чанков и НЕ модифицируют Chunk объекты. `render_with_embedded_overlap` склеивает строки для вывода — это view-level операция.

```python
# chunkana/renderers/inline_metadata.py
# Это НОВЫЙ код, не из v2 — тонкий слой для форматирования

import json
from ..types import Chunk

def render_json(chunks: list[Chunk]) -> list[dict]:
    """Convert chunks to list of dictionaries. Does not modify chunks."""
    return [chunk.to_dict() for chunk in chunks]

def render_inline_metadata(chunks: list[Chunk]) -> list[str]:
    """Render chunks with inline JSON metadata tags. Does not modify chunks."""
    result = []
    for chunk in chunks:
        metadata_json = json.dumps(chunk.metadata, ensure_ascii=False, indent=2, sort_keys=True)
        result.append(f"<metadata>\n{metadata_json}\n</metadata>\n\n{chunk.content}")
    return result

def render_dify_style(chunks: list[Chunk]) -> list[str]:
    """Render chunks in Dify-compatible format with <metadata> block.
    
    Includes chunk.metadata + start_line + end_line in the metadata block.
    """
    result = []
    for chunk in chunks:
        output_metadata = chunk.metadata.copy()
        output_metadata['start_line'] = chunk.start_line
        output_metadata['end_line'] = chunk.end_line
        metadata_json = json.dumps(output_metadata, ensure_ascii=False, indent=2, sort_keys=True)
        result.append(f"<metadata>\n{metadata_json}\n</metadata>\n\n{chunk.content}")
    return result

def render_with_embedded_overlap(chunks: list[Chunk]) -> list[str]:
    """Render chunks with bidirectional overlap embedded into content string.
    
    This is a VIEW operation — it does NOT modify chunk.content.
    Produces: previous_content + "\\n" + content + "\\n" + next_content
    
    Use case: for compatibility mode selected by MIGRATION_GUIDE/BASELINE.
    Whether this matches v2 include_metadata=False is determined by BASELINE.md
    and renderer golden outputs — not hardcoded.
    """
    result = []
    for chunk in chunks:
        parts = []
        prev = chunk.metadata.get("previous_content", "")
        next_ = chunk.metadata.get("next_content", "")
        if prev:
            parts.append(prev)
        parts.append(chunk.content)
        if next_:
            parts.append(next_)
        result.append("\n".join(parts))
    return result

def render_with_prev_overlap(chunks: list[Chunk]) -> list[str]:
    """Render chunks with only previous overlap embedded (sliding window).
    
    This is a VIEW operation — it does NOT modify chunk.content.
    Produces: previous_content + "\\n" + content
    
    Use case: for compatibility mode selected by MIGRATION_GUIDE/BASELINE.
    Whether this matches v2 include_metadata=False is determined by BASELINE.md
    and renderer golden outputs — not hardcoded.
    """
    result = []
    for chunk in chunks:
        parts = []
        prev = chunk.metadata.get("previous_content", "")
        if prev:
            parts.append(prev)
        parts.append(chunk.content)
        result.append("\n".join(parts))
    return result
```

### 5. Hierarchy Builder (`chunkana/hierarchy.py`) — Port from v2

```python
# Портируется из markdown_chunker_v2/hierarchy.py ЦЕЛИКОМ
# Включает HierarchicalChunkingResult и HierarchyBuilder

import hashlib
from dataclasses import dataclass, field

@dataclass
class HierarchicalChunkingResult:
    """Result of hierarchical chunking with navigation methods."""
    
    chunks: list[Chunk]
    root_id: str
    strategy_used: str
    _index: dict[str, Chunk] = field(default_factory=dict, repr=False, init=False)
    
    def __post_init__(self):
        """Build index for O(1) lookups."""
        self._index = {
            c.metadata.get("chunk_id"): c
            for c in self.chunks
            if c.metadata.get("chunk_id")
        }
    
    def get_chunk(self, chunk_id: str) -> Chunk | None:
        return self._index.get(chunk_id)
    
    def get_children(self, chunk_id: str) -> list[Chunk]:
        chunk = self.get_chunk(chunk_id)
        if not chunk:
            return []
        children_ids = chunk.metadata.get("children_ids", [])
        return [self.get_chunk(cid) for cid in children_ids if self.get_chunk(cid)]
    
    def get_parent(self, chunk_id: str) -> Chunk | None:
        chunk = self.get_chunk(chunk_id)
        if not chunk:
            return None
        parent_id = chunk.metadata.get("parent_id")
        return self.get_chunk(parent_id) if parent_id else None
    
    def get_ancestors(self, chunk_id: str) -> list[Chunk]:
        """Get all ancestors from chunk to root (breadcrumb)."""
        ancestors = []
        current = self.get_chunk(chunk_id)
        while current:
            parent_id = current.metadata.get("parent_id")
            if not parent_id:
                break
            parent = self.get_chunk(parent_id)
            if parent:
                ancestors.append(parent)
            current = parent
        return ancestors
    
    def get_flat_chunks(self) -> list[Chunk]:
        """Get only leaf chunks for backward-compatible retrieval."""
        return [c for c in self.chunks if c.metadata.get("is_leaf", True)]
    
    def get_siblings(self, chunk_id: str) -> list[Chunk]:
        """Get all sibling chunks (including self)."""
        chunk = self.get_chunk(chunk_id)
        if not chunk:
            return []
        parent_id = chunk.metadata.get("parent_id")
        if not parent_id:
            return [chunk]  # Root has no siblings
        return self.get_children(parent_id)
    
    def get_by_level(self, level: int) -> list[Chunk]:
        """Get all chunks at specific hierarchy level (0=document, 1=section, etc.)."""
        return [c for c in self.chunks if c.metadata.get("hierarchy_level") == level]
    
    def to_tree_dict(self) -> dict:
        """Convert hierarchy to tree dictionary for serialization."""
        def build_node(chunk_id: str) -> dict:
            chunk = self.get_chunk(chunk_id)
            if not chunk:
                return {}
            content_preview = chunk.content[:100] + ("..." if len(chunk.content) > 100 else "")
            return {
                "id": chunk_id,
                "content_preview": content_preview,
                "header_path": chunk.metadata.get("header_path", ""),
                "level": chunk.metadata.get("hierarchy_level", 0),
                "children": [build_node(cid) for cid in chunk.metadata.get("children_ids", [])],
            }
        return build_node(self.root_id)


class HierarchyBuilder:
    """Builds hierarchical relationships between chunks."""
    
    def _generate_id(self, content: str, index: int) -> str:
        """Generate 8-char SHA256 hash ID (same as v2)."""
        data = f"{content[:50]}:{index}".encode()
        return hashlib.sha256(data).hexdigest()[:8]
    
    # ... остальные методы из v2 hierarchy.py ...
```

**Важно**: `chunk_id` генерируется как 8-символьный SHA256 хеш, НЕ как позиционный идентификатор.


## Chunk Metadata Schema

Metadata schema идентична v2 для обеспечения совместимости:

```python
from typing_extensions import NotRequired, TypedDict

class ChunkMetadata(TypedDict):
    # Required (from v2)
    chunk_index: int        # Sequential number (0-based)
    content_type: str       # "text" | "code" | "list" | "table" | "mixed" | "preamble" | "section"
                            # - "text": plain text content
                            # - "code": code block dominant
                            # - "list": list-heavy content (bullet/numbered lists)
                            # - "table": table dominant
                            # - "mixed": combination of types
                            # - "preamble": document preamble before first header
                            # - "section": hierarchy node (summary/container chunks)
    strategy: str           # Strategy name
    header_path: str        # "/Level1/Level2" (string format from v2)
    
    # Optional (from v2)
    header_level: NotRequired[int]      # 1-6
    has_code: NotRequired[bool]
    allow_oversize: NotRequired[bool]
    oversize_reason: NotRequired[str]
    small_chunk: NotRequired[bool]
    small_chunk_reason: NotRequired[str]
    sub_headers: NotRequired[list[str]]
    
    # Hierarchy (from v2 HierarchyBuilder)
    chunk_id: NotRequired[str]          # 8-char SHA256 hash
    parent_id: NotRequired[str]         # Parent chunk ID
    children_ids: NotRequired[list[str]] # Child chunk IDs
    prev_sibling_id: NotRequired[str]   # Previous sibling ID
    next_sibling_id: NotRequired[str]   # Next sibling ID
    hierarchy_level: NotRequired[int]   # Tree depth (0=root, 1=section, etc.)
    is_leaf: NotRequired[bool]          # True if no children or has own content
    is_root: NotRequired[bool]          # True for document root chunk
    
    # Overlap (from v2)
    previous_content: NotRequired[str]
    next_content: NotRequired[str]
    overlap_size: NotRequired[int]
    
    # Code-context binding (from v2)
    code_role: NotRequired[str]         # "example", "output", "standalone"
    code_relationship: NotRequired[str]
    related_code_count: NotRequired[int]
    
    # Adaptive sizing (from v2)
    adaptive_size: NotRequired[int]
    content_complexity: NotRequired[float]
    size_scale_factor: NotRequired[float]
    
    # Table grouping (from v2)
    is_table_group: NotRequired[bool]
    table_group_count: NotRequired[int]
    
    # Streaming
    stream_window_index: NotRequired[int]
```

**Важно**: `header_path` в v2 — это строка формата "/Level1/Level2", НЕ list[str]. Для удобства можно добавить `header_path_list` как дополнительное поле, но основной формат должен совпадать с v2.

## Error Handling

```python
class ChunkanaError(Exception):
    """Base exception for Chunkana."""
    pass

class ConfigValidationError(ChunkanaError, ValueError):
    """Invalid configuration parameters. Inherits from ValueError for compatibility."""
    pass

class ChunkValidationError(ChunkanaError):
    """Invalid chunk state."""
    pass

class ParseError(ChunkanaError):
    """Failed to parse markdown."""
    pass
```

### Error Recovery (same as v2)

1. **Unclosed fences**: Mark `is_closed=False`, include rest of document in block
2. **Oversize atomic blocks**: Create chunk with `allow_oversize=True`, `oversize_reason`
3. **Empty content**: Skip, don't create empty chunks
4. **Invalid line numbers**: Auto-correct to valid range


## Packaging & CI Plan

### Package Structure (src-layout)

```
chunkana/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── src/
│   └── chunkana/
│       ├── __init__.py
│       ├── api.py              # NEW: convenience functions
│       ├── config.py           # from v2: ChunkConfig → ChunkerConfig
│       ├── types.py            # from v2: all dataclasses
│       ├── parser.py           # from v2
│       ├── chunker.py          # from v2
│       ├── hierarchy.py        # from v2 or new
│       ├── adaptive_sizing.py  # from v2
│       ├── table_grouping.py   # from v2
│       ├── strategies/         # from v2
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── selector.py
│       │   ├── code_aware.py
│       │   ├── list_aware.py
│       │   ├── structural.py
│       │   └── fallback.py
│       └── renderers/          # NEW
│           ├── __init__.py
│           └── inline_metadata.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── property/
│   ├── baseline/               # Comparison with v2
│   │   ├── fixtures/           # Markdown files
│   │   ├── golden/             # Expected outputs from v2
│   │   └── test_baseline.py
│   └── examples/
└── docs/
    ├── quickstart.md
    ├── config.md
    ├── strategies.md
    ├── renderers.md
    └── integrations/
        ├── dify.md
        ├── n8n.md
        └── windmill.md
```

### Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    # Только то, что использует v2 (без Dify SDK)
    # Проверить requirements.txt плагина
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "hypothesis>=6.0",
    "mypy>=1.0",
    "ruff>=0.1",
    "build",
    "twine",
]
docs = [
    "mkdocs",
    "mkdocs-material",
]
```

### CI Workflow (.github/workflows/ci.yml)

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12"]  # Match python_requires
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=chunkana
      - run: mypy src/chunkana
      - run: ruff check src/chunkana
      - run: python -m build
      - run: twine check dist/*
```

### Publish Workflow (.github/workflows/publish.yml)

```yaml
name: Publish
on:
  push:
    tags: ["v*"]
permissions:
  contents: read
  id-token: write
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Chunk Round-Trip (Dict)

*For any* valid Chunk object, serializing to dict and deserializing back should produce an equivalent Chunk with identical content, line numbers, and metadata.

```python
# Pseudocode
for all chunk in valid_chunks:
    restored = Chunk.from_dict(chunk.to_dict())
    assert restored.content == chunk.content
    assert restored.start_line == chunk.start_line
    assert restored.end_line == chunk.end_line
    assert restored.metadata == chunk.metadata
```

**Validates: Requirements 1.5, 1.7, 14.1**

### Property 2: Chunk Round-Trip (JSON)

*For any* valid Chunk object, serializing to JSON string and deserializing back should produce an equivalent Chunk.

```python
# Pseudocode
for all chunk in valid_chunks:
    restored = Chunk.from_json(chunk.to_json())
    assert restored.content == chunk.content
    assert restored.start_line == chunk.start_line
    assert restored.end_line == chunk.end_line
    assert restored.metadata == chunk.metadata
```

**Validates: Requirements 1.6, 1.8, 14.2**

### Property 3: ChunkerConfig Round-Trip

*For any* valid ChunkerConfig object, serializing to dict and deserializing back should produce an equivalent config with identical parameters.

```python
# Pseudocode
for all config in valid_configs:
    restored = ChunkerConfig.from_dict(config.to_dict())
    assert restored.max_chunk_size == config.max_chunk_size
    assert restored.min_chunk_size == config.min_chunk_size
    # ... all other fields
```

**Validates: Requirements 2.8, 14.3**

### Property 4: Atomic Block Integrity

*For any* markdown document containing fenced code blocks, tables, or LaTeX formulas, no chunk should contain a partial atomic block (unclosed fence, partial table, or unclosed LaTeX delimiter).

```python
# Pseudocode
for all markdown in documents_with_atomic_blocks:
    chunks = chunk_markdown(markdown)
    for chunk in chunks:
        assert not contains_partial_fence(chunk.content)
        assert not contains_partial_table(chunk.content)
        assert not contains_partial_latex(chunk.content)
```

**Validates: Requirements 4.1, 4.2, 4.3, 4.5**

### Property 5: Strategy Selection Correctness

*For any* markdown document and config, the selected strategy should match the content analysis criteria:
- CodeAware when code_ratio >= threshold OR code_blocks > 0 OR tables > 0
- ListAware when list criteria met (AND for structural, OR for non-structural)
- Structural when headers >= threshold and no code/list criteria
- Fallback otherwise

```python
# Pseudocode
for all (markdown, config) in valid_inputs:
    analysis = parse(markdown)
    chunks = chunk_markdown(markdown, config)
    expected_strategy = determine_expected_strategy(analysis, config)
    assert all(c.metadata["strategy"] == expected_strategy for c in chunks)
```

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**


### Property 6: Required Metadata Presence

*For any* chunking result, every chunk should have all required metadata fields: chunk_index, content_type, strategy, header_path.

```python
# Pseudocode
for all markdown in valid_documents:
    chunks = chunk_markdown(markdown)
    for chunk in chunks:
        assert "chunk_index" in chunk.metadata
        assert "content_type" in chunk.metadata
        assert "strategy" in chunk.metadata
        assert "header_path" in chunk.metadata
```

**Validates: Requirements 5.1, 5.2, 5.4, 5.5**

### Property 7: Overlap Metadata Mode

*For any* markdown document chunked with overlap_size > 0, the overlap context should be stored in metadata fields (previous_content, next_content) and NOT duplicated in chunk.content.

```python
# Pseudocode
for all markdown in valid_documents:
    config = ChunkerConfig(overlap_size=200)
    chunks = chunk_markdown(markdown, config)
    for i, chunk in enumerate(chunks):
        if i > 0 and "previous_content" in chunk.metadata:
            prev_content = chunk.metadata["previous_content"]
            # Check directly against the stored previous_content from metadata
            # (not computed from adjacent chunk tail)
            if prev_content:
                # chunk.content should NOT start with the stored previous_content
                # (i.e., overlap is metadata-only, not embedded in content)
                assert not chunk.content.startswith(prev_content), (
                    f"Overlap should be in metadata, not embedded in content. "
                    f"chunk.metadata['previous_content'] = {repr(prev_content[:50])}"
                )
```

**Validates: Requirements 5.8, 5.9, 5.10**

### Property 8: Overlap Cap Ratio

*For any* markdown document chunked with overlap_size > 0, the actual overlap size should not exceed overlap_cap_ratio (default 0.35) of the adjacent chunk size.

```python
# Pseudocode
for all markdown in valid_documents:
    config = ChunkerConfig(overlap_size=200, overlap_cap_ratio=0.35)
    chunks = chunk_markdown(markdown, config)
    for i, chunk in enumerate(chunks):
        if i > 0 and "previous_content" in chunk.metadata:
            prev_size = len(chunks[i-1].content)
            overlap_size = len(chunk.metadata["previous_content"])
            assert overlap_size <= prev_size * config.overlap_cap_ratio
```

**Validates: Requirements 5.11**

### Property 9: Line Coverage

*For any* markdown document, the union of all chunk line ranges (start_line to end_line) should cover at least 99% of the source document lines.

```python
# Pseudocode
for all markdown in valid_documents:
    chunks = chunk_markdown(markdown)
    total_lines = len(markdown.split("\n"))
    covered_lines = set()
    for chunk in chunks:
        covered_lines.update(range(chunk.start_line, chunk.end_line + 1))
    coverage = len(covered_lines) / total_lines
    assert coverage >= 0.99
```

**Validates: Requirements 9.1**

### Property 10: Monotonic Ordering

*For any* chunking result with multiple chunks, the start_line values should be monotonically increasing.

```python
# Pseudocode
for all markdown in valid_documents:
    chunks = chunk_markdown(markdown)
    for i in range(1, len(chunks)):
        assert chunks[i].start_line >= chunks[i-1].start_line
```

**Validates: Requirements 9.2**


### Property 11: Small Chunk Handling

*For any* chunk smaller than min_chunk_size that cannot be merged, it should be flagged with small_chunk=True and small_chunk_reason in metadata.

```python
# Pseudocode
for all markdown in valid_documents:
    config = ChunkerConfig(min_chunk_size=512)
    chunks = chunk_markdown(markdown, config)
    for chunk in chunks:
        if chunk.size < config.min_chunk_size:
            assert chunk.metadata.get("small_chunk") == True
            assert "small_chunk_reason" in chunk.metadata
```

**Validates: Requirements 17.3, 17.4**

### Property 12: Hierarchy Navigation Consistency

*For any* hierarchical chunking result, the navigation methods should be consistent: get_parent(child_id) should return a chunk whose get_children includes child_id.

```python
# Pseudocode
for all markdown in valid_documents:
    result = chunk_hierarchical(markdown)
    for chunk in result.chunks:
        chunk_id = chunk.metadata.get("chunk_id")
        if chunk_id:
            parent = result.get_parent(chunk_id)
            if parent:
                parent_id = parent.metadata.get("chunk_id")
                children = result.get_children(parent_id)
                assert chunk in children
```

**Validates: Requirements 7.2, 7.3**

## Testing Strategy

### Dual Testing Approach

Chunkana uses both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across randomly generated inputs
- **Baseline tests**: Verify output matches dify-markdown-chunker v2

### Baseline Testing (Critical for Port 1:1)

```python
# tests/baseline/test_baseline.py
import json
from pathlib import Path
from chunkana import chunk_markdown

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_DIR = Path(__file__).parent / "golden"

def test_baseline_compatibility():
    """Ensure chunkana output matches v2 golden outputs."""
    for fixture_path in FIXTURES_DIR.glob("*.md"):
        golden_path = GOLDEN_DIR / f"{fixture_path.stem}.json"
        
        markdown = fixture_path.read_text()
        chunks = chunk_markdown(markdown)
        
        expected = json.loads(golden_path.read_text())
        actual = [c.to_dict() for c in chunks]
        
        # Structural comparison (not bit-for-bit)
        assert len(actual) == len(expected["chunks"])
        for a, e in zip(actual, expected["chunks"]):
            assert a["start_line"] == e["start_line"]
            assert a["end_line"] == e["end_line"]
            assert a["metadata"]["strategy"] == e["metadata"]["strategy"]
            # Content comparison: normalize line endings only, NO .strip()
            # Using .strip() hides whitespace bugs — don't do it
            actual_content = a["content"].replace("\r\n", "\n")
            expected_content = e["content"].replace("\r\n", "\n")
            assert actual_content == expected_content, (
                f"Content mismatch in {fixture_path.name}:\n"
                f"Expected: {repr(expected_content[:100])}\n"
                f"Actual: {repr(actual_content[:100])}"
            )
```

### Property-Based Testing Configuration

- **Library**: hypothesis (Python)
- **Minimum iterations**: 100 per property test
- **Tag format**: `# Feature: chunkana-library, Property N: {property_text}`

### Test Directory Structure

```
tests/
├── conftest.py
├── unit/
│   ├── test_chunk.py           # Chunk dataclass tests
│   ├── test_config.py          # ChunkerConfig tests
│   ├── test_parser.py          # Parser tests
│   ├── test_strategies.py      # Strategy tests
│   ├── test_renderers.py       # Renderer tests
│   └── test_hierarchy.py       # Hierarchy tests
├── property/
│   ├── test_roundtrip.py       # Properties 1, 2, 3
│   ├── test_atomic_blocks.py   # Property 4
│   ├── test_strategy.py        # Property 5
│   ├── test_metadata.py        # Property 6
│   ├── test_overlap.py         # Properties 7, 8
│   ├── test_coverage.py        # Properties 9, 10
│   ├── test_small_chunks.py    # Property 11
│   └── test_hierarchy.py       # Property 12
├── baseline/
│   ├── fixtures/               # Markdown files from v2 tests
│   │   ├── nested_fences.md
│   │   ├── large_tables.md
│   │   ├── complex_lists.md
│   │   └── code_context.md
│   ├── golden/                 # Expected outputs from v2
│   │   ├── nested_fences.json
│   │   ├── large_tables.json
│   │   └── ...
│   └── test_baseline.py
└── examples/
    ├── test_quickstart.py      # Documentation examples
    └── test_integrations.py    # Integration examples
```

### Coverage Requirements

- Overall code coverage: >= 80%
- Critical paths (parser, strategies): >= 90%
- Property tests: 100 iterations minimum
- Baseline tests: All v2 fixtures must pass

