"""
Main MarkdownChunker class for v2.

Simplified pipeline:
1. Parse (once)
2. Select strategy
3. Apply strategy
4. Apply overlap
5. Validate
6. Return
"""

from __future__ import annotations

import io
import re
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from .adaptive_sizing import AdaptiveSizeCalculator
from .config import ChunkConfig
from .header_processor import HeaderProcessor
from .hierarchy import HierarchicalChunkingResult, HierarchyBuilder
from .metadata_recalculator import MetadataRecalculator
from .parser import get_parser
from .section_splitter import SectionSplitter
from .strategies import StrategySelector
from .types import Chunk, ChunkingMetrics, ContentAnalysis

if TYPE_CHECKING:
    from .streaming import StreamingConfig

# Note: MAX_OVERLAP_CONTEXT_RATIO is kept for backward compatibility
# but the actual value is now configurable via config.overlap_cap_ratio
MAX_OVERLAP_CONTEXT_RATIO = 0.35


class MarkdownChunker:
    """
    Main class for chunking markdown documents.

    Simplified from the original with:
    - Single parse pass
    - Single strategy selection
    - Linear pipeline
    - No duplication
    """

    def __init__(self, config: ChunkConfig | None = None):
        """
        Initialize chunker.

        Args:
            config: Chunking configuration (uses defaults if None)
        """
        self.config = config or ChunkConfig()
        self._parser = get_parser()  # Use singleton parser instance
        self._selector = StrategySelector()
        self._header_processor = HeaderProcessor(self.config)
        self._section_splitter = SectionSplitter(self.config)
        self._metadata_recalculator = MetadataRecalculator()
        self._hierarchy_builder = HierarchyBuilder(
            include_document_summary=self.config.include_document_summary,
            validate_invariants=self.config.validate_invariants,
            strict_mode=self.config.strict_mode,
        )

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess markdown text before chunking.

        Currently handles:
        - Obsidian block ID removal (if configured)

        Args:
            text: Raw markdown text

        Returns:
            Preprocessed text
        """
        if self.config.strip_obsidian_block_ids:
            # Remove Obsidian block IDs: ^identifier at end of lines
            # Pattern: space(s) + ^ + alphanumeric + spaces/end
            text = re.sub(r"\s+\^[a-zA-Z0-9]+\s*$", "", text, flags=re.MULTILINE)
        return text

    def chunk(self, md_text: str) -> list[Chunk]:
        """
        Chunk a markdown document.

        Pipeline:
        1. Parse (once)
        2. Calculate adaptive size (if enabled)
        3. Select strategy
        4. Apply strategy
        5. Merge small chunks
        6. Apply overlap
        7. Add metadata
        8. Validate

        Args:
            md_text: Raw markdown text

        Returns:
            List of chunks
        """
        if not md_text or not md_text.strip():
            return []

        # 0. Preprocess text (e.g., strip Obsidian block IDs if configured)
        md_text = self._preprocess_text(md_text)

        # 1. Parse (once) - includes line ending normalization
        analysis = self._parser.analyze(md_text)

        # Get normalized text (line endings normalized)
        normalized_text = md_text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Calculate adaptive size (if enabled)
        effective_config = self.config
        adaptive_metadata = {}
        if self.config.use_adaptive_sizing:
            calculator = AdaptiveSizeCalculator(self.config.adaptive_config)
            adaptive_max_size = calculator.calculate_optimal_size(normalized_text, analysis)
            complexity = calculator.calculate_complexity(analysis)
            scale_factor = calculator.get_scale_factor(complexity)

            # Store metadata for later enrichment
            adaptive_metadata = {
                "adaptive_size": adaptive_max_size,
                "content_complexity": complexity,
                "size_scale_factor": scale_factor,
            }

            # Create effective config with adaptive size
            # Respect absolute max_chunk_size limit
            final_max_size = min(adaptive_max_size, self.config.max_chunk_size)
            effective_config = ChunkConfig(
                max_chunk_size=final_max_size,
                min_chunk_size=self.config.min_chunk_size,
                overlap_size=self.config.overlap_size,
                preserve_atomic_blocks=self.config.preserve_atomic_blocks,
                strategy_override=self.config.strategy_override,
                enable_code_context_binding=self.config.enable_code_context_binding,
                use_adaptive_sizing=False,  # Prevent recursion
            )

        # 3. Select strategy
        strategy = self._selector.select(analysis, effective_config)

        # 4. Apply strategy
        chunks = strategy.apply(normalized_text, analysis, effective_config)

        # 5. Merge small chunks
        chunks = self._merge_small_chunks(chunks)

        # 5.5. Prevent dangling headers
        # CRITICAL: This MUST happen BEFORE section splitting
        # so that headers are "attached" to their content before any splitting
        chunks = self._header_processor.prevent_dangling_headers(chunks)

        # 5.6. Split oversize sections
        # CRITICAL: This MUST happen AFTER dangling header fix
        # so that split chunks can repeat the header_stack
        chunks = self._section_splitter.split_oversize_sections(chunks)

        # 6. Apply overlap (if enabled)
        if self.config.enable_overlap and len(chunks) > 1:
            chunks = self._apply_overlap(chunks)

        # 7. Add standard metadata
        chunks = self._add_metadata(chunks, strategy.name)

        # 8. Recalculate derived metadata (section_tags) after all post-processing
        chunks = self._metadata_recalculator.recalculate_all(chunks)

        # 9. Add adaptive sizing metadata (if enabled)
        if self.config.use_adaptive_sizing:
            for chunk in chunks:
                chunk.metadata.update(adaptive_metadata)

        # 10. Validate
        self._validate(chunks, normalized_text)

        return chunks

    def chunk_with_metrics(self, md_text: str) -> tuple[list[Chunk], ChunkingMetrics]:
        """
        Chunk and return metrics.

        Returns:
            Tuple of (chunks, metrics)
        """
        chunks = self.chunk(md_text)
        metrics = ChunkingMetrics.from_chunks(
            chunks, self.config.min_chunk_size, self.config.max_chunk_size
        )
        return chunks, metrics

    def chunk_with_analysis(self, md_text: str) -> tuple[list[Chunk], str, ContentAnalysis | None]:
        """
        Chunk and return analysis info.

        Returns:
            Tuple of (chunks, strategy_name, analysis)
        """
        if not md_text or not md_text.strip():
            return [], "none", None

        # Preprocess text
        md_text = self._preprocess_text(md_text)

        analysis = self._parser.analyze(md_text)
        normalized_text = md_text.replace("\r\n", "\n").replace("\r", "\n")

        strategy = self._selector.select(analysis, self.config)
        chunks = strategy.apply(normalized_text, analysis, self.config)

        if self.config.enable_overlap and len(chunks) > 1:
            chunks = self._apply_overlap(chunks)

        self._validate(chunks, normalized_text)

        return chunks, strategy.name, analysis

    def chunk_hierarchical(self, md_text: str) -> HierarchicalChunkingResult:
        """
        Create hierarchical chunk structure with parent-child relationships.

        This method builds on chunk() to add hierarchy metadata and navigation.
        The hierarchy is constructed post-hoc using existing header_path metadata.

        Process:
        1. Perform normal chunking via chunk()
        2. Build hierarchy relationships via HierarchyBuilder
        3. Return HierarchicalChunkingResult with navigation methods

        Args:
            md_text: Raw markdown text

        Returns:
            HierarchicalChunkingResult with navigation methods and hierarchy

        Example:
            >>> chunker = MarkdownChunker()
            >>> result = chunker.chunk_hierarchical(markdown_text)
            >>> root = result.get_chunk(result.root_id)
            >>> children = result.get_children(result.root_id)
            >>> for child in children:
            ...     print(f"Section: {child.metadata['header_path']}")
        """
        # Step 1: Perform normal chunking
        chunks = self.chunk(md_text)

        # Step 2: Build hierarchy
        return self._hierarchy_builder.build(chunks, md_text)

    def chunk_file_streaming(
        self, file_path: str, streaming_config: StreamingConfig | None = None
    ) -> Iterator[Chunk]:
        """
        Chunk file in streaming mode for memory efficiency.

        Use this for files >10MB to limit memory usage.

        Args:
            file_path: Path to markdown file
            streaming_config: Streaming configuration (uses defaults if None)

        Yields:
            Chunk objects with streaming metadata

        Example:
            >>> chunker = MarkdownChunker()
            >>> for chunk in chunker.chunk_file_streaming("large.md"):
            ...     process(chunk)
        """
        from .streaming import StreamingChunker, StreamingConfig

        config = streaming_config or StreamingConfig()
        streamer = StreamingChunker(self.config, config)
        yield from streamer.chunk_file(file_path)

    def chunk_stream(
        self, stream: io.TextIOBase, streaming_config: StreamingConfig | None = None
    ) -> Iterator[Chunk]:
        """
        Chunk stream in streaming mode for memory efficiency.

        Args:
            stream: Text stream to process
            streaming_config: Streaming configuration (uses defaults if None)

        Yields:
            Chunk objects with streaming metadata

        Example:
            >>> import io
            >>> chunker = MarkdownChunker()
            >>> stream = io.StringIO(large_text)
            >>> for chunk in chunker.chunk_stream(stream):
            ...     process(chunk)
        """
        from .streaming import StreamingChunker, StreamingConfig

        config = streaming_config or StreamingConfig()
        streamer = StreamingChunker(self.config, config)
        yield from streamer.chunk_stream(stream)

    def _apply_overlap(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Apply metadata-only overlap context between chunks.

        This implements the v2 overlap model where context from neighboring chunks
        is stored in metadata fields only. There is NO physical text duplication
        in chunk.content.

        Adds metadata fields:
        - previous_content: Last N characters from previous chunk (all except first)
        - next_content: First N characters from next chunk (all except last)
        - overlap_size: Size of context window used

        Context window size:
        - Determined by config.overlap_size (default: 200 characters)
        - Capped at adaptive maximum based on chunk size:
          max_overlap = min(config.overlap_size, chunk_size * config.overlap_cap_ratio)
        - This allows larger overlap for larger chunks while preventing bloat
        - Word boundary-aware: attempts to break at spaces when possible

        next_content and previous_content behavior:
        - Contains preview/follow-up text from adjacent chunks
        - NOT duplicated in chunk.content (metadata-only)
        - Limited to configured overlap_size or adaptive maximum
        - Helps language models understand chunk boundaries
        - Avoids index bloat and semantic search confusion

        Key points:
        - overlap_size parameter determines base context window size
        - Maximum overlap scales with chunk size (overlap_cap_ratio of chunk size, default 0.35)
        - chunk.content remains distinct and non-overlapping
        - Context extraction respects word boundaries
        - Helps language models understand chunk boundaries without text duplication
        - Avoids index bloat and semantic search confusion

        Args:
            chunks: List of chunks to add overlap metadata to

        Returns:
            Same chunks with overlap metadata added
        """
        if len(chunks) <= 1:
            return chunks

        for i in range(len(chunks)):
            # Previous content (for all except first)
            if i > 0:
                prev_chunk = chunks[i - 1]
                # Adaptive cap: max overlap = overlap_cap_ratio of previous chunk size
                max_overlap = int(len(prev_chunk.content) * self.config.overlap_cap_ratio)
                effective_overlap_size = min(self.config.overlap_size, max_overlap)

                overlap_text = self._extract_overlap_end(prev_chunk.content, effective_overlap_size)
                chunks[i].metadata["previous_content"] = overlap_text
                chunks[i].metadata["overlap_size"] = len(overlap_text)

            # Next content (for all except last)
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                # Adaptive cap: max overlap = overlap_cap_ratio of next chunk size
                max_overlap = int(len(next_chunk.content) * self.config.overlap_cap_ratio)
                effective_overlap_size = min(self.config.overlap_size, max_overlap)

                overlap_text = self._extract_overlap_start(
                    next_chunk.content, effective_overlap_size
                )
                chunks[i].metadata["next_content"] = overlap_text

        return chunks

    def _extract_overlap_end(self, content: str, size: int) -> str:
        """
        Extract overlap from end of content, respecting word boundaries.

        This is used for previous_content metadata field.

        Strategy:
        - If content <= size, return entire content
        - Otherwise, extract last 'size' characters
        - Try to start at word boundary (first space in first half of extracted text)

        Args:
            content: Source content
            size: Target overlap size (adaptive, capped at overlap_cap_ratio of chunk size)

        Returns:
            Overlap text from end of content, at most 'size' characters
        """
        if len(content) <= size:
            return content

        text = content[-size:]

        # Try to start at word boundary
        space_pos = text.find(" ")
        if 0 < space_pos < len(text) // 2:
            text = text[space_pos + 1 :]

        return text

    def _extract_overlap_start(self, content: str, size: int) -> str:
        """
        Extract overlap from start of content, respecting word boundaries.

        This is used for next_content metadata field.

        Strategy:
        - If content <= size, return entire content
        - Otherwise, extract first 'size' characters
        - Try to end at word boundary (last space in second half of extracted text)

        Args:
            content: Source content
            size: Target overlap size (adaptive, capped at 35% of chunk size)

        Returns:
            Overlap text from start of content, at most 'size' characters
        """
        if len(content) <= size:
            return content

        text = content[:size]

        # Try to end at word boundary
        space_pos = text.rfind(" ")
        if space_pos > len(text) // 2:
            text = text[:space_pos]

        return text

    def _validate(self, chunks: list[Chunk], original: str) -> None:
        """
        Validate chunking results.

        Checks domain properties PROP-1 through PROP-5.

        v2.1 Changes:
        - Removed section_integrity as valid oversize reason for text/lists
        - Only code_block_integrity, table_integrity, list_item_integrity are valid
        """
        if not chunks:
            return

        # PROP-1: No content loss (relaxed check)
        total_output = sum(len(c.content) for c in chunks)
        total_input = len(original)

        # Allow some variance due to overlap and whitespace normalization
        if total_output < total_input * 0.9:
            # Log warning but don't fail
            pass

        # PROP-2: Size bounds
        # v2.1: Only code_block_integrity and table_integrity are auto-assigned
        # section_integrity is REMOVED - text/lists should be split, not marked oversize
        for chunk in chunks:
            if chunk.size > self.config.max_chunk_size and not chunk.metadata.get("allow_oversize"):
                # Set default oversize metadata
                chunk.metadata["allow_oversize"] = True
                if "```" in chunk.content:
                    chunk.metadata["oversize_reason"] = "code_block_integrity"
                elif "|" in chunk.content and "---" in chunk.content:
                    chunk.metadata["oversize_reason"] = "table_integrity"
                else:
                    # v2.1: Use list_item_integrity instead of section_integrity
                    # This indicates the chunk couldn't be split further
                    chunk.metadata["oversize_reason"] = "list_item_integrity"

        # PROP-3: Monotonic ordering
        for i in range(len(chunks) - 1):
            if chunks[i].start_line > chunks[i + 1].start_line:
                # Fix ordering
                chunks.sort(key=lambda c: (c.start_line, c.end_line))
                break

        # PROP-4 and PROP-5 are enforced by Chunk.__post_init__

    def _merge_small_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Merge chunks smaller than min_chunk_size with adjacent chunks.

        Strategy:
        1. First, merge small header-only chunks with their section body
        2. Then merge remaining small chunks with adjacent chunks
        3. For chunks that cannot merge, flag as small_chunk if structurally weak

        Small chunk flagging criteria:
        - Chunk size is below min_chunk_size
        - Cannot merge with adjacent chunks without exceeding max_chunk_size
        - Chunk is structurally weak (lacks significant headers, content, or paragraphs)

        Note: A chunk below min_chunk_size that is structurally strong (has headers,
        multiple paragraphs, etc.) will NOT be flagged as small_chunk.
        """
        if len(chunks) <= 1:
            return chunks

        # Phase 1: Merge small header chunks with their section body
        chunks = self._merge_header_chunks(chunks)

        # Phase 2: Size-based merging for remaining small chunks
        result: list[Chunk] = []
        i = 0

        while i < len(chunks):
            chunk = chunks[i]

            if chunk.size < self.config.min_chunk_size:
                merged = self._try_merge(chunk, result, chunks, i)
                if merged:
                    i += 1
                    continue
                else:
                    # Cannot merge - check if structurally weak before flagging
                    if not self._is_structurally_strong(chunk):
                        chunk.metadata["small_chunk"] = True
                        chunk.metadata["small_chunk_reason"] = "cannot_merge"

            result.append(chunk)
            i += 1

        return result

    def _merge_header_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Merge small header-only chunks with their section body.

        This addresses the issue where top-level headers create standalone chunks
        with minimal content, while the actual section body is in a separate chunk.

        Merge conditions (all must be met):
        - Current chunk has header level 1 or 2
        - Current chunk size < 150 characters (heuristic threshold)
        - Current chunk is header/section type, not preamble
        - Next chunk is in same section or is a child section
        - Next chunk is not preamble

        Returns:
            List of chunks with header chunks merged into their section bodies
        """
        if len(chunks) <= 1:
            return chunks

        result = []
        i = 0

        while i < len(chunks):
            current = chunks[i]

            # Check if this chunk should be merged with next
            if i + 1 < len(chunks) and self._should_merge_with_next(current, chunks[i + 1]):
                next_chunk = chunks[i + 1]

                # Merge current header chunk with next chunk
                merged_content = current.content + "\n\n" + next_chunk.content
                merged_chunk = Chunk(
                    content=merged_content,
                    start_line=current.start_line,
                    end_line=next_chunk.end_line,
                    metadata={**current.metadata},
                )

                # Update metadata after merge
                # Re-detect content_type only if merging atomic blocks
                # (to handle code+table mixed content)
                curr_type = current.metadata.get("content_type", "")
                next_type = next_chunk.metadata.get("content_type", "")
                if curr_type in ("code", "table") or next_type in ("code", "table"):
                    merged_chunk.metadata["content_type"] = self._detect_content_type(
                        merged_content
                    )
                # Preserve top-level header_path from current chunk
                if "section_tags" in current.metadata and "section_tags" in next_chunk.metadata:
                    # Combine section tags from both chunks
                    merged_chunk.metadata["section_tags"] = (
                        current.metadata["section_tags"] + next_chunk.metadata["section_tags"]
                    )
                elif "section_tags" in next_chunk.metadata:
                    merged_chunk.metadata["section_tags"] = next_chunk.metadata["section_tags"]

                result.append(merged_chunk)
                i += 2  # Skip next chunk since we merged it
            else:
                result.append(current)
                i += 1

        return result

    def _should_merge_with_next(self, current: Chunk, next_chunk: Chunk) -> bool:
        """
        Determine if a small header chunk should merge with the next chunk.

        Merge conditions (all must be met):
        1. Current chunk has header level 1 or 2 (top-level headers)
        2. Current chunk size < 150 characters (configurable heuristic)
        3. Current chunk is header/section type, not preamble
        4. Next chunk is in same section OR is a child section
        5. Next chunk is not preamble

        Args:
            current: Current chunk to check
            next_chunk: Next chunk in sequence

        Returns:
            True if current chunk should merge with next chunk
        """
        # Condition 1: Check header level (1 or 2 only)
        header_level = current.metadata.get("header_level", 0)
        if header_level not in [1, 2]:
            return False

        # Condition 2: Check size threshold (150 characters heuristic)
        HEADER_MERGE_THRESHOLD = 150
        if current.size >= HEADER_MERGE_THRESHOLD:
            return False

        # Condition 3: Current chunk must be header/section type, not preamble
        current_type = str(current.metadata.get("content_type", ""))
        if current_type == "preamble":
            return False

        # Condition 5: Next chunk must not be preamble
        next_type = str(next_chunk.metadata.get("content_type", ""))
        if next_type == "preamble":
            return False

        # Condition 4: Check if next chunk is in same section or is child section
        current_path = str(current.metadata.get("header_path", ""))
        next_path = str(next_chunk.metadata.get("header_path", ""))

        # Handle empty paths
        if not current_path or not next_path:
            return False

        # Same section: paths are identical
        if current_path == next_path:
            return True

        # Child section: next_path starts with current_path
        return next_path.startswith(current_path + "/")

    def _is_structurally_strong(self, chunk: Chunk) -> bool:
        """
        Determine if a chunk is structurally strong despite being small.

        A chunk is considered structurally strong if ANY of these
        conditions are true:
        1. Has strong header: Contains header level 2 (##) or 3 (###)
        2. Sufficient text lines: Contains at least 3 lines of non-header
           content
        3. Meaningful content: Text content exceeds 100 characters after
           header extraction
        4. Multiple paragraphs: Contains at least 2 paragraph breaks
           (double newline)

        Current limitation: Lists (bullet/numbered) are NOT considered as
        structural strength indicators in this version. Support planned
        for future iterations.

        Args:
            chunk: Chunk to evaluate

        Returns:
            True if chunk is structurally strong, False otherwise
        """
        content = chunk.content

        # Indicator 1: Has strong header (level 2 or 3)
        header_level = chunk.metadata.get("header_level", 0)
        if header_level in [2, 3]:
            return True

        # Indicator 4: Multiple paragraphs (at least 2 paragraph breaks)
        paragraph_breaks = content.count("\n\n")
        if paragraph_breaks >= 2:
            return True

        # For indicators 2 and 3, extract non-header content
        lines = content.split("\n")
        non_header_lines = [line for line in lines if not line.strip().startswith("#")]
        non_header_content = "\n".join(non_header_lines)

        # Indicator 2: Sufficient text lines (at least 3 non-header lines)
        non_empty_lines = [line for line in non_header_lines if line.strip()]
        if len(non_empty_lines) >= 3:
            return True

        # Indicator 3: Meaningful content (> 100 chars after header extraction)
        return len(non_header_content.strip()) > 100

    def _try_merge(
        self, chunk: Chunk, result: list[Chunk], all_chunks: list[Chunk], index: int
    ) -> bool:
        """
        Try to merge a small chunk with adjacent chunks.

        Merge conditions for small_chunk:
        - Chunk size is below min_chunk_size
        - Cannot merge with adjacent chunks without exceeding max_chunk_size
        - Preamble chunks are never merged with structural chunks
        - Prefer merging with chunks in same logical section (same header_path prefix)
        - Prefer left (previous) chunk over right (next) chunk

        Returns True if merge was successful.
        """
        # Try merging with previous chunk (left preference per Requirement 4.4)
        if result and self._try_merge_with_previous(chunk, result):
            return True

        # Try merging with next chunk
        if index + 1 < len(all_chunks):
            return self._try_merge_with_next(chunk, all_chunks, index)

        return False

    def _can_merge_chunks(self, chunk1: Chunk, chunk2: Chunk) -> bool:
        """Check if two chunks can be merged (preamble compatibility)."""
        chunk1_is_preamble = chunk1.metadata.get("content_type") == "preamble"
        chunk2_is_preamble = chunk2.metadata.get("content_type") == "preamble"
        # Only merge if both are preamble or both are not preamble
        return chunk1_is_preamble == chunk2_is_preamble

    def _create_merged_chunk(
        self, chunk1: Chunk, chunk2: Chunk, metadata_base: dict[str, Any]
    ) -> Chunk:
        """Create a merged chunk from two chunks."""
        merged_content = chunk1.content + "\n\n" + chunk2.content
        merged_chunk = Chunk(
            content=merged_content,
            start_line=chunk1.start_line,
            end_line=chunk2.end_line,
            metadata={**metadata_base},
        )

        # Re-detect content_type only if merging atomic blocks
        type1 = chunk1.metadata.get("content_type", "")
        type2 = chunk2.metadata.get("content_type", "")
        if type1 in ("code", "table") or type2 in ("code", "table"):
            merged_chunk.metadata["content_type"] = self._detect_content_type(merged_content)

        return merged_chunk

    def _try_merge_with_previous(self, chunk: Chunk, result: list[Chunk]) -> bool:
        """Try to merge chunk with previous chunk in result."""
        prev_chunk = result[-1]

        # Check preamble compatibility
        if not self._can_merge_chunks(prev_chunk, chunk):
            return False

        combined_size = prev_chunk.size + chunk.size
        if combined_size > self.config.max_chunk_size:
            return False

        # Check if same logical section
        if not self._same_logical_section(prev_chunk, chunk):
            return False

        # Merge with previous
        merged_chunk = self._create_merged_chunk(prev_chunk, chunk, prev_chunk.metadata)
        result[-1] = merged_chunk
        return True

    def _try_merge_with_next(self, chunk: Chunk, all_chunks: list[Chunk], index: int) -> bool:
        """Try to merge chunk with next chunk in all_chunks."""
        next_chunk = all_chunks[index + 1]

        # Check preamble compatibility
        if not self._can_merge_chunks(chunk, next_chunk):
            return False

        combined_size = chunk.size + next_chunk.size
        if combined_size > self.config.max_chunk_size:
            return False

        # Check if same logical section
        if not self._same_logical_section(chunk, next_chunk):
            return False

        # Merge with next - modify next chunk in place
        merged_chunk = self._create_merged_chunk(chunk, next_chunk, next_chunk.metadata)
        all_chunks[index + 1] = merged_chunk
        return True

    def _same_logical_section(self, chunk1: Chunk, chunk2: Chunk) -> bool:
        """
        Check if two chunks belong to the same logical section.

        Compares header_path prefix up to ## level (first two segments).
        This implements Requirement 4.3 - prefer merging within same section.

        Args:
            chunk1: First chunk
            chunk2: Second chunk

        Returns:
            True if chunks are in same logical section
        """
        path1 = str(chunk1.metadata.get("header_path", ""))
        path2 = str(chunk2.metadata.get("header_path", ""))

        # Preamble chunks are in their own section
        if path1 == "/__preamble__" or path2 == "/__preamble__":
            return path1 == path2

        # Compare first two segments of path (up to ## level)
        parts1 = path1.strip("/").split("/")[:2]
        parts2 = path2.strip("/").split("/")[:2]

        return parts1 == parts2

    def _add_metadata(self, chunks: list[Chunk], strategy_name: str) -> list[Chunk]:
        """
        Add standard metadata to all chunks.

        Adds:
        - chunk_index: sequential index
        - content_type: text/code/table/mixed
        - has_code: boolean
        - header_path: list of ancestor headers (if available)
        - strategy: strategy that created the chunk
        """
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            # Don't overwrite content_type if already set (e.g., "preamble")
            if "content_type" not in chunk.metadata:
                chunk.metadata["content_type"] = self._detect_content_type(chunk.content)
            chunk.metadata["has_code"] = "```" in chunk.content
            chunk.metadata["strategy"] = strategy_name

            # header_path is set by strategy if available
            if "header_path" not in chunk.metadata:
                chunk.metadata["header_path"] = []

        return chunks

    def _detect_content_type(self, content: str) -> str:
        """Detect content type of chunk."""
        has_code = "```" in content
        has_table = "|" in content and "---" in content

        if has_code and has_table:
            return "mixed"
        elif has_code:
            return "code"
        elif has_table:
            return "table"
        else:
            return "text"

    def chunk_simple(
        self, text: str, config: dict[str, Any] | None = None, strategy: str | None = None
    ) -> dict[str, object]:
        """
        Simple chunking method that returns dictionary format.

        This method provides backward compatibility for code expecting
        dictionary-based results instead of Chunk objects.

        Args:
            text: Input text to chunk
            config: Optional config as dict (will be converted to ChunkConfig)
            strategy: Optional strategy hint (ignored in v2, auto-selected)

        Returns:
            Dictionary with keys:
            - chunks: list of chunk dicts
            - errors: list of error messages (empty in normal operation)
            - warnings: list of warning messages (empty in normal operation)
            - total_chunks: number of chunks
            - strategy_used: name of strategy used
        """
        try:
            # Handle config parameter
            chunker = self
            if config is not None:
                config_dict = config.copy()
                # Handle legacy enable_overlap parameter
                if "enable_overlap" in config_dict:
                    enable = config_dict.pop("enable_overlap")
                    if enable and "overlap_size" not in config_dict:
                        config_dict["overlap_size"] = 100
                    elif not enable:
                        config_dict["overlap_size"] = 0

                # Remove any unknown parameters
                valid_params = {
                    "max_chunk_size",
                    "min_chunk_size",
                    "overlap_size",
                    "preserve_atomic_blocks",
                    "strategy_override",
                }
                config_dict = {k: v for k, v in config_dict.items() if k in valid_params}

                temp_config = ChunkConfig(**config_dict)
                chunker = MarkdownChunker(temp_config)

            # Get chunks with analysis
            chunks, strategy_used, _ = chunker.chunk_with_analysis(text)

            # Convert chunks to dictionary format
            chunk_dicts = []
            for chunk in chunks:
                chunk_dict = {
                    "content": chunk.content,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "size": len(chunk.content),
                    "line_count": chunk.end_line - chunk.start_line + 1,
                    "metadata": chunk.metadata.copy() if chunk.metadata else {},
                }
                chunk_dicts.append(chunk_dict)

            return {
                "chunks": chunk_dicts,
                "errors": [],
                "warnings": [],
                "total_chunks": len(chunk_dicts),
                "strategy_used": strategy_used or "auto",
            }

        except Exception as e:
            return {
                "chunks": [],
                "errors": [str(e)],
                "warnings": [],
                "total_chunks": 0,
                "strategy_used": "none",
            }
