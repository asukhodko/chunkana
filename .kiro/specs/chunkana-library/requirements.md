# Requirements Document

## Introduction

Chunkana — это Python-библиотека для интеллектуального разбиения Markdown-документов на семантически осмысленные фрагменты (chunks). Библиотека выделяется из плагина dify-markdown-chunker как самостоятельный пакет для широкого применения в RAG-системах, n8n, windmill и других интеграциях.

Ключевые особенности:
- Сохранение целостности кода, таблиц, списков и LaTeX-формул
- Автоматический выбор стратегии на основе анализа контента
- Иерархическая структура с header_path для навигации
- Метаданные для контекстного overlap без дублирования текста
- Code-context binding для связывания кода с объяснениями
- Готовность к публикации на PyPI

**Подход к переносу**: Код переносится из dify-markdown-chunker v2 методом "port 1:1" — структура модулей и логика сохраняются максимально близко к оригиналу. При этом библиотека **намеренно упрощает API** для удобства внешних интеграций: `chunk()` всегда возвращает `List[Chunk]`, а расширенные результаты доступны через отдельные методы.

**Breaking changes vs v2**: Библиотека упрощает контракт возврата — см. MIGRATION_GUIDE.md для деталей миграции плагина.

## Glossary

- **Chunkana**: Библиотека для разбиения Markdown на chunks
- **Chunk**: Фрагмент документа с контентом, позицией и метаданными
- **ChunkerConfig**: Конфигурация параметров разбиения (аналог ChunkConfig из плагина)
- **Strategy**: Алгоритм разбиения (code_aware, list_aware, structural, fallback)
- **ContentAnalysis**: Результат анализа документа (code_ratio, headers, tables и т.д.)
- **header_path**: Иерархический путь к секции как строка ("/Level1/Level2")
- **Renderer**: Компонент для форматирования вывода (JSON, inline_metadata, dify_style)
- **Atomic_Block**: Неделимый блок (fenced code, table, LaTeX formula)
- **Overlap**: Контекст из соседних chunks (metadata-only, хранится в previous_content/next_content)
- **Code_Context_Binding**: Механизм связывания блоков кода с окружающими объяснениями
- **StreamingConfig**: Конфигурация потоковой обработки больших файлов
- **AdaptiveSizeConfig**: Конфигурация адаптивного размера чанков
- **TableGroupingConfig**: Конфигурация группировки связанных таблиц
- **Fenced_Block**: Блок кода, ограниченный fence-символами (``` или ~~~) длиной >= 3

## Requirements

### Requirement 1: Core Chunking API

**User Story:** As a developer, I want a simple API to chunk Markdown documents, so that I can integrate intelligent chunking into my applications.

**Design Decision (A1)**: Библиотека намеренно упрощает возврат `chunk()` до `List[Chunk]` — один метод, один тип результата. Это breaking change относительно v2, где мог возвращаться union-тип. Расширенные результаты доступны через отдельные методы.

#### Acceptance Criteria

1. THE Chunkana SHALL provide a `chunk_markdown(text: str, config: ChunkerConfig | None = None) -> list[Chunk]` function for basic chunking
2. THE Chunkana SHALL provide a `MarkdownChunker` class with `chunk(text) -> list[Chunk]` method (always returns List[Chunk], never union type)
3. WHEN config is None, THE Chunkana SHALL use defaults matching v2 (documented in BASELINE.md; current v2 defaults: max_chunk_size=4096, min_chunk_size=512, overlap_size=200)
4. THE Chunk dataclass SHALL include at minimum: content (str), start_line (int), end_line (int), metadata (dict)
5. THE Chunk SHALL provide `to_dict() -> dict` method for dictionary serialization
6. THE Chunk SHALL provide `to_json() -> str` method for JSON string serialization
7. THE Chunk SHALL provide `from_dict(data: dict) -> Chunk` class method for deserialization
8. THE Chunk SHALL provide `from_json(json_str: str) -> Chunk` class method for JSON deserialization
9. THE start_line and end_line SHALL always describe the unique (non-overlap) portion of the chunk in the source document

### Requirement 1a: Analysis API

**User Story:** As a developer, I want access to document analysis and extended chunking results, so that I can build advanced processing pipelines.

#### Acceptance Criteria

1. THE Chunkana SHALL provide `analyze_markdown(text: str, config: ChunkerConfig | None = None) -> ContentAnalysis` for document analysis without chunking
2. THE Chunkana SHALL provide `chunk_with_analysis(text: str, config: ChunkerConfig | None = None) -> ChunkingResult` returning chunks + analysis + strategy_used
3. THE ChunkingResult SHALL contain: chunks (list[Chunk]), strategy_used (str), analysis (ContentAnalysis)
4. THE Chunkana SHALL provide `chunk_with_metrics(text: str, config: ChunkerConfig | None = None) -> tuple[list[Chunk], ChunkingMetrics]`

### Requirement 2: Configuration System

**User Story:** As a developer, I want flexible configuration options, so that I can tune chunking behavior for different document types.

#### Acceptance Criteria

1. THE ChunkerConfig SHALL support size parameters: max_chunk_size, min_chunk_size, overlap_size
2. THE ChunkerConfig SHALL support strategy thresholds: code_threshold, structure_threshold, list_ratio_threshold, list_count_threshold
3. THE ChunkerConfig SHALL support behavior flags: preserve_atomic_blocks, extract_preamble, preserve_latex_blocks
4. THE ChunkerConfig SHALL support overlap control: overlap_cap_ratio (float, default 0.35)
5. THE ChunkerConfig SHALL support strategy_override to force specific strategy
6. THE ChunkerConfig SHALL provide factory methods: default(), for_code_heavy(), for_structured(), minimal(), for_changelogs(), with_adaptive_sizing()
7. THE ChunkerConfig SHALL validate parameters in __post_init__ and raise ValueError for invalid values (custom exceptions like ConfigValidationError SHALL inherit from ValueError for compatibility)
8. THE ChunkerConfig SHALL provide to_dict() and from_dict() methods for serialization

### Requirement 3: Strategy Selection

**User Story:** As a developer, I want automatic strategy selection based on content analysis, so that documents are chunked optimally without manual configuration.

#### Acceptance Criteria

1. WHEN code_ratio >= code_threshold OR code_block_count > 0 OR table_count > 0, THE StrategySelector SHALL select CodeAwareStrategy
2. WHEN document is structurally rich (header_count >= structure_threshold), THE StrategySelector SHALL select ListAwareStrategy if list_ratio >= list_ratio_threshold AND list_count >= list_count_threshold
3. WHEN document is NOT structurally rich, THE StrategySelector SHALL select ListAwareStrategy if list_ratio >= list_ratio_threshold OR list_count >= list_count_threshold
4. WHEN header_count >= structure_threshold AND no list criteria met AND no code criteria met, THE StrategySelector SHALL select StructuralStrategy
5. WHEN no specific criteria are met, THE StrategySelector SHALL select FallbackStrategy
6. WHEN strategy_override is set in config, THE StrategySelector SHALL use the specified strategy
7. THE ContentAnalysis SHALL provide: code_ratio, list_ratio, table_ratio, header_count, avg_sentence_length, code_block_count, table_count, code_blocks, headers, tables, list_blocks, latex_blocks

### Requirement 4: Atomic Block Preservation

**User Story:** As a developer, I want code blocks, tables, and LaTeX formulas to remain intact, so that semantic meaning is preserved.

#### Acceptance Criteria

1. WHEN preserve_atomic_blocks is True, THE Chunkana SHALL NOT split fenced code blocks (any fence of >= 3 backticks or tildes)
2. WHEN preserve_atomic_blocks is True, THE Chunkana SHALL NOT split Markdown tables
3. WHEN preserve_latex_blocks is True, THE Chunkana SHALL NOT split LaTeX display math (`$$...$$`) or environments (`\begin{equation}...\end{equation}`, `\begin{align}...\end{align}`, etc.)
4. IF an atomic block exceeds max_chunk_size, THEN THE Chunkana SHALL create an oversize chunk with allow_oversize=True and oversize_reason in metadata
5. THE Chunkana SHALL detect nested fenced blocks (e.g., ``` inside ~~~~) by tracking fence length and preserve them correctly
6. THE Chunkana SHALL correctly handle fences of different lengths (3, 4, 5+ characters)

### Requirement 5: Metadata Enrichment

**User Story:** As a developer, I want rich metadata on each chunk, so that I can build effective retrieval systems.

**Design Decision (A2)**: Overlap — это ответственность core chunking, но **не вшивается в content**. `chunk.content` всегда содержит canonical текст без дублей. Overlap хранится в metadata (`previous_content`, `next_content`). Вшивание overlap в content — это renderer-level операция.

#### Acceptance Criteria

1. THE Chunk metadata SHALL include chunk_index (sequential number, 0-based)
2. THE Chunk metadata SHALL include content_type ("text", "code", "list", "table", "mixed", "preamble", "section")
   - "text": plain text content
   - "code": code block dominant
   - "list": list-heavy content (bullet/numbered lists)
   - "table": table dominant
   - "mixed": combination of types
   - "preamble": document preamble before first header
   - "section": hierarchy node (used in hierarchical chunking for summary/container chunks)
3. THE Chunk metadata SHALL include has_code (boolean)
4. THE Chunk metadata SHALL include strategy (name of strategy used)
5. THE Chunk metadata SHALL include header_path as string (e.g., "/Level1/Level2") matching v2 format
6. THE Chunk metadata SHALL include header_level (1-6 for first header in chunk)
7. WHEN overlap is enabled (overlap_size > 0), THE Chunk metadata SHALL include previous_content and next_content from adjacent chunks
8. THE chunk.content SHALL NEVER contain embedded overlap text — overlap is metadata-only (canonical chunks)
9. WHEN overlap is enabled, THE Chunk metadata SHALL include overlap_size indicating context window size
10. THE overlap context size SHALL be capped at overlap_cap_ratio (default 0.35) of adjacent chunk size

### Requirement 6: Output Renderers

**User Story:** As a developer, I want multiple output formats, so that I can integrate with different systems (Dify, n8n, windmill, custom).

**Design Decision**: Renderers — это форматирование, не chunking. Они не влияют на границы чанков, только на представление. `render_with_embedded_overlap` склеивает строки для вывода, но это view-level операция.

#### Acceptance Criteria

1. THE Chunkana SHALL provide `render_json(chunks: list[Chunk]) -> list[dict]` renderer for dictionary output
2. THE Chunkana SHALL provide `render_inline_metadata(chunks: list[Chunk]) -> list[str]` renderer for inline metadata format
3. THE Chunkana SHALL provide `render_dify_style(chunks: list[Chunk]) -> list[str]` renderer for Dify-compatible format with `<metadata>` block containing: chunk.metadata fields (chunk_index, header_path, content_type, strategy, etc.) + start_line + end_line for traceability
4. THE Chunkana SHALL provide `render_with_embedded_overlap(chunks: list[Chunk]) -> list[str]` renderer that embeds bidirectional overlap context into content (previous_content + "\n" + content + "\n" + next_content) — "rich context" mode. Whether this matches v2 `include_metadata=False` is determined by BASELINE.md.
5. THE Chunkana SHALL provide `render_with_prev_overlap(chunks: list[Chunk]) -> list[str]` renderer that embeds only previous overlap (previous_content + "\n" + content) — "sliding window" mode. Whether this matches v2 `include_metadata=False` is determined by BASELINE.md.
6. THE renderers SHALL NOT modify Chunk objects — they produce formatted strings/dicts
7. THE renderers SHALL NOT import any external SDK (Dify, n8n, etc.)
8. THE renderers SHALL be pure functions operating on Chunk objects

### Requirement 7: Hierarchical Chunking

**User Story:** As a developer, I want to navigate chunk hierarchy, so that I can build tree-based retrieval systems.

#### Acceptance Criteria

1. THE Chunkana SHALL provide `chunk_hierarchical(text) -> HierarchicalChunkingResult` method
2. THE HierarchicalChunkingResult SHALL provide get_chunk(chunk_id), get_children(chunk_id), get_parent(chunk_id) methods
3. THE HierarchicalChunkingResult SHALL provide get_ancestors(chunk_id) method for breadcrumb navigation
4. THE HierarchicalChunkingResult SHALL provide get_flat_chunks() method for backward compatibility
5. THE HierarchicalChunkingResult SHALL provide root_id for document root
6. THE HierarchicalChunkingResult SHALL provide get_siblings(chunk_id) method for sibling navigation
7. THE HierarchicalChunkingResult SHALL provide get_by_level(level: int) method for level-based filtering
8. THE HierarchicalChunkingResult SHALL provide to_tree_dict() method for tree serialization
9. THE hierarchy SHALL be built from header_path metadata post-hoc

### Requirement 8: Streaming Support

**User Story:** As a developer, I want to process large files efficiently, so that I can handle documents >10MB without memory issues.

#### Acceptance Criteria

1. THE Chunkana SHALL provide `iter_chunks(text: str, config: ChunkerConfig | None = None) -> Iterator[Chunk]` for streaming
2. THE Chunkana SHALL provide `chunk_file_streaming(path: str, config: ChunkerConfig | None = None, streaming_config: StreamingConfig | None = None) -> Iterator[Chunk]` for file streaming
3. THE StreamingConfig SHALL support buffer_size (int, default 100_000) and max_memory_mb (int, default 50)
4. THE streaming mode SHOULD limit memory usage to approximately max_memory_mb (best effort — avoids loading entire file into memory)
5. THE streaming chunks SHALL include stream_window_index in metadata

### Requirement 9: Validation and Metrics

**User Story:** As a developer, I want to validate chunking results and get quality metrics, so that I can monitor and tune performance.

#### Acceptance Criteria

1. THE Chunkana SHALL validate that each source line (by start_line/end_line ranges) is covered by at least one chunk (union coverage >= 99%)
2. THE Chunkana SHALL validate monotonic ordering (start_line increases across chunks, based on unique portion)
3. THE Chunkana SHALL provide ChunkingMetrics with: total_chunks, avg_chunk_size, std_dev_size, min_size, max_size, undersize_count, oversize_count
4. THE Chunkana SHALL provide `chunk_with_metrics(text) -> tuple[list[Chunk], ChunkingMetrics]` method

### Requirement 10: PyPI Packaging

**User Story:** As a library maintainer, I want proper packaging, so that users can install via pip and the library is discoverable.

#### Acceptance Criteria

1. THE package SHALL use src-layout (src/chunkana/)
2. THE package SHALL have pyproject.toml with [build-system] and [project] sections
3. THE package SHALL specify python_requires >= "3.12" (matching dify-markdown-chunker v2)
4. THE package SHALL define optional extras: [dev] for testing, [docs] for documentation
5. THE package SHALL include README.md as readme in pyproject.toml
6. THE package SHALL include CHANGELOG.md
7. THE package SHALL include LICENSE file (MIT) and declare license metadata in pyproject.toml (Req 10.7)
8. THE package SHALL include proper classifiers and keywords for PyPI discovery

### Requirement 11: Testing Infrastructure

**User Story:** As a library maintainer, I want comprehensive tests, so that I can ensure correctness and prevent regressions.

#### Acceptance Criteria

1. THE package SHALL include unit tests in tests/unit/
2. THE package SHALL include property-based tests in tests/property/ using hypothesis
3. THE package SHALL include baseline tests in tests/baseline/ comparing output with dify-markdown-chunker v2
4. THE package SHALL include example tests in tests/examples/
5. THE tests SHALL achieve >= 80% code coverage
6. THE CI SHALL run pytest, type checking (mypy), and linting (ruff) on every PR
7. THE baseline tests SHALL use fixtures and golden outputs generated from dify-markdown-chunker v2

### Requirement 12: Documentation

**User Story:** As a developer, I want clear documentation, so that I can quickly understand and use the library.

#### Acceptance Criteria

1. THE package SHALL include README.md with quickstart (3-10 lines of code)
2. THE package SHALL include docs/ with: quickstart.md, config.md, strategies.md, renderers.md
3. THE package SHALL include docs/integrations/ with: dify.md, n8n.md, windmill.md
4. THE docstrings SHALL follow Google style for all public APIs
5. THE package SHALL include CONTRIBUTING.md with development setup instructions

### Requirement 13: CI/CD Pipeline

**User Story:** As a library maintainer, I want automated CI/CD, so that releases are reliable and consistent.

#### Acceptance Criteria

1. THE repository SHALL have .github/workflows/ci.yml for PR checks (pytest, mypy, ruff)
2. THE CI SHALL run `python -m build` to verify package builds correctly
3. THE CI SHALL run `twine check dist/*` to validate package metadata and README rendering
4. THE repository SHALL have .github/workflows/publish.yml for PyPI publishing on tag
5. THE publish workflow SHALL use Trusted Publishing (OIDC) without API tokens
6. THE publish workflow SHALL require permissions: id-token: write
7. THE CI SHALL run on Python 3.12 (matching python_requires)

### Requirement 14: Round-Trip Serialization

**User Story:** As a developer, I want reliable serialization, so that chunks can be stored and restored without data loss.

#### Acceptance Criteria

1. FOR ALL valid Chunk objects, `Chunk.from_dict(chunk.to_dict())` SHALL produce an equivalent Chunk
2. FOR ALL valid Chunk objects, `Chunk.from_json(chunk.to_json())` SHALL produce an equivalent Chunk
3. FOR ALL valid ChunkerConfig objects, `ChunkerConfig.from_dict(config.to_dict())` SHALL produce an equivalent config
4. THE serialization SHALL preserve all metadata fields including nested structures

### Requirement 15: Adaptive Chunk Sizing

**User Story:** As a developer, I want chunks sized based on content complexity, so that dense content gets smaller chunks and simple content gets larger chunks.

#### Acceptance Criteria

1. THE ChunkerConfig SHALL support use_adaptive_sizing (bool, default False) and adaptive_config (AdaptiveSizeConfig)
2. THE AdaptiveSizeConfig SHALL support: base_size, min_scale, max_scale, code_weight, table_weight, list_weight, sentence_length_weight
3. WHEN use_adaptive_sizing is True, THE Chunkana SHALL calculate optimal chunk size based on content complexity
4. THE Chunk metadata SHALL include adaptive_size, content_complexity, size_scale_factor when adaptive sizing is used
5. THE adaptive size SHALL be capped by max_chunk_size from config

### Requirement 16: Table Grouping

**User Story:** As a developer, I want related tables grouped together, so that retrieval quality improves for tabular data.

#### Acceptance Criteria

1. THE ChunkerConfig SHALL support group_related_tables (bool, default False) and table_grouping_config (TableGroupingConfig)
2. THE TableGroupingConfig SHALL support: max_distance_lines, require_same_section, max_group_size, max_grouped_tables
3. WHEN group_related_tables is True, THE Chunkana SHALL group tables within max_distance_lines into single chunks
4. WHEN require_same_section is True, THE Chunkana SHALL only group tables under the same header
5. THE Chunk metadata SHALL include is_table_group (bool) and table_group_count (int) for grouped table chunks

### Requirement 17: Small Chunk Handling

**User Story:** As a developer, I want undersize chunks handled gracefully, so that I don't get fragmented results.

#### Acceptance Criteria

1. WHEN a chunk is smaller than min_chunk_size, THE Chunkana SHALL attempt to merge it with the previous chunk
2. IF merging with previous chunk would exceed max_chunk_size, THE Chunkana SHALL attempt to merge with the next chunk
3. IF merging is blocked by atomic block boundaries, THE Chunkana SHALL keep the undersize chunk and mark it with small_chunk=True in metadata
4. THE Chunk metadata SHALL include small_chunk_reason when small_chunk is True

### Requirement 18: Code-Context Binding

**User Story:** As a developer, I want code blocks to be grouped with their surrounding explanations, so that retrieval returns complete context.

#### Acceptance Criteria

1. THE ChunkerConfig SHALL support enable_code_context_binding (bool, default True)
2. THE ChunkerConfig SHALL support max_context_chars_before (int, default 500) for backward explanation search
3. THE ChunkerConfig SHALL support max_context_chars_after (int, default 300) for forward explanation search
4. THE ChunkerConfig SHALL support related_block_max_gap (int, default 5) for maximum line gap between related blocks
5. THE ChunkerConfig SHALL support bind_output_blocks (bool, default True) to bind output blocks to code
6. THE ChunkerConfig SHALL support preserve_before_after_pairs (bool, default True) to keep Before/After examples together
7. WHEN enable_code_context_binding is True, THE Chunkana SHALL group code blocks with their surrounding explanatory text
8. THE Chunk metadata SHALL include code_role when code-context binding is active (e.g., "example", "output", "standalone")
9. THE Chunk metadata SHALL include has_explanation_before and has_explanation_after for code blocks

### Requirement 19: Migration Guide

**User Story:** As a plugin maintainer migrating from dify-markdown-chunker to Chunkana, I want clear migration documentation, so that I can update my code without breaking functionality.

#### Acceptance Criteria

1. THE repository SHALL include MIGRATION_GUIDE.md (or docs/migration-guide.md)
2. THE guide SHALL document breaking changes: `chunk()` always returns `List[Chunk]`, not union type
3. THE guide SHALL provide parameter mapping:
   - `include_metadata=True` → `render_dify_style()`
   - `include_metadata=False` → choose renderer according to BASELINE.md and renderer golden outputs:
     - v2 prev-only behavior → `render_with_prev_overlap()`
     - v2 bidirectional behavior → `render_with_embedded_overlap()`
4. THE guide SHALL include a decision tree for renderer selection:
   - Dify plugin (include_metadata=True) → `render_dify_style`
   - Dify plugin (include_metadata=False) → renderer per baseline (prev-only or bidirectional)
   - "More context than v2" → `render_with_embedded_overlap`
   - "Classic sliding window" → `render_with_prev_overlap`
5. THE guide SHALL include code snippets showing "before" (dify-markdown-chunker) and "after" (chunkana) usage
6. THE guide SHALL document compatibility guarantees: chunk boundaries, metadata schema
7. THE guide SHALL document what is NOT guaranteed 1:1: output formatting, Dify-specific parameters

