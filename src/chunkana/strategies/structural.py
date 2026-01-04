"""
Structural strategy for markdown_chunker v2.

For documents with hierarchical headers.
Simplified from 1720 lines to ~150 lines.
"""

import re

from ..config import ChunkConfig
from ..types import Chunk, ContentAnalysis, Header
from .base import BaseStrategy


class StructuralStrategy(BaseStrategy):
    """
    Strategy for structured documents with headers.

    Splits document by headers, maintaining header hierarchy.

    Priority: 2 (used when document has headers but no code/tables)

    Attributes:
        max_structural_level: Maximum header level that can appear in header_path
            as structural context. Headers with level > max_structural_level are
            always considered local sections and go into section_tags.
            Default: 2 (H1 and H2 are structural, H3+ are local)
    """

    def __init__(self, max_structural_level: int = 2):
        """
        Initialize StructuralStrategy.

        Args:
            max_structural_level: Maximum header level for structural context.
                Headers with level <= max_structural_level can appear in header_path.
                Headers with level > max_structural_level always go to section_tags.
                Default: 2 (H1, H2 structural; H3, H4, H5, H6 local)
        """
        self.max_structural_level = max_structural_level
        # O4: Header stack cache for performance optimization
        self._header_stack_cache: dict[int, list[Header]] = {}

    @property
    def name(self) -> str:
        return "structural"

    @property
    def priority(self) -> int:
        return 3

    def can_handle(self, analysis: ContentAnalysis, config: ChunkConfig) -> bool:
        """
        Can handle if document has enough headers and hierarchy.
        """
        return analysis.header_count >= config.structure_threshold and analysis.max_header_depth > 1

    def apply(self, md_text: str, analysis: ContentAnalysis, config: ChunkConfig) -> list[Chunk]:
        """
        Apply structural strategy.

        Splits document by headers into sections.
        """
        if not md_text.strip():
            return []

        # O1: Use cached lines from analysis (fallback for backward compatibility)
        lines = analysis.get_lines()
        if lines is None:
            lines = md_text.split("\n")

        headers = analysis.headers

        if not headers:
            # No headers - use fallback behavior
            return self._split_text_to_size(md_text, 1, config)

        chunks = []

        # Handle preamble (content before first header)
        # Preamble gets special header_path "/__preamble__" to distinguish
        # from structural content
        first_header_line = headers[0].line if headers else len(lines) + 1
        if first_header_line > 1:
            preamble_lines = lines[: first_header_line - 1]
            preamble_content = "\n".join(preamble_lines)
            if preamble_content.strip():
                chunks.append(
                    self._create_chunk(
                        preamble_content,
                        1,
                        first_header_line - 1,
                        content_type="preamble",
                        header_path="/__preamble__",
                        section_tags=[],  # NEW: always present, empty for preamble
                        header_level=0,  # NEW: 0 for preamble (no structural context)
                    )
                )

        # Filter to structural headers only (level <= max_structural_level)
        # H3+ headers don't create new sections - they stay inside parent section
        structural_headers = [h for h in headers if h.level <= self.max_structural_level]

        # Process sections between STRUCTURAL headers only
        for i, header in enumerate(structural_headers):
            # Determine section boundaries
            start_line = header.line

            if i + 1 < len(structural_headers):
                end_line = structural_headers[i + 1].line - 1
            else:
                end_line = len(lines)

            # Extract section content
            section_lines = lines[start_line - 1 : end_line]
            section_content = "\n".join(section_lines)

            if not section_content.strip():
                continue

            # Check if section fits in one chunk
            if len(section_content) <= config.max_chunk_size:
                # Build header_path and section_tags with new semantics
                header_path, section_tags, header_level = self._build_header_path_for_chunk(
                    section_content, headers, start_line
                )

                chunk_meta = {
                    "content_type": "section",
                    "header_path": header_path,
                    "header_level": header_level,
                    "section_tags": section_tags,  # NEW: always present
                }

                chunks.append(
                    self._create_chunk(
                        section_content,
                        start_line,
                        end_line,
                        **chunk_meta,
                    )
                )
            else:
                # Split large section into sub-chunks
                section_chunks = self._split_large_section(
                    section_content, start_line, end_line, headers, analysis, config
                )
                chunks.extend(section_chunks)

        return chunks

    def _split_large_section(
        self,
        section_content: str,
        start_line: int,
        end_line: int,
        headers: list[Header],
        analysis: ContentAnalysis,
        config: ChunkConfig,
    ) -> list[Chunk]:
        """Split large section, preserving atomic blocks if present.

        Args:
            section_content: Content of the section
            start_line: Starting line of section
            end_line: Ending line of section
            headers: All document headers
            analysis: Document analysis (for atomic blocks)
            config: Chunking configuration

        Returns:
            List of chunks with metadata
        """
        # Check for atomic blocks (code, tables, LaTeX) in section
        atomic_blocks = self._get_atomic_blocks_in_range(start_line, end_line, analysis)

        if atomic_blocks:
            # Split preserving atomic blocks
            section_chunks = self._split_section_preserving_atomic(
                section_content, start_line, atomic_blocks, config
            )
        else:
            # No atomic blocks - simple split
            section_chunks = self._split_text_to_size(section_content, start_line, config)

        # Build section's header_path ONCE - all sub-chunks inherit it
        section_header_path, _, section_header_level = self._build_header_path_for_chunk(
            section_content, headers, start_line
        )

        for chunk in section_chunks:
            # Sub-chunks inherit header_path from parent section
            chunk.metadata["header_path"] = section_header_path
            chunk.metadata["header_level"] = section_header_level
            chunk.metadata["content_type"] = "section"
            # section_tags = all H3+ headers inside THIS sub-chunk
            chunk_headers = self._find_headers_in_content(chunk.content)
            chunk.metadata["section_tags"] = [
                text for level, text in chunk_headers if level > section_header_level
            ]

        return section_chunks

    def _build_header_path(self, headers: list[Header]) -> str:
        """
        Build header path from header hierarchy.

        Example: "/Chapter 1/Section 1.1/Subsection"
        """
        if not headers:
            return "/"

        # Build path maintaining hierarchy
        path_parts = []
        current_level = 0

        for header in headers:
            if header.level > current_level:
                path_parts.append(header.text)
            elif header.level == current_level:
                if path_parts:
                    path_parts[-1] = header.text
                else:
                    path_parts.append(header.text)
            else:
                # Going up in hierarchy
                while len(path_parts) > header.level - 1:
                    path_parts.pop()
                path_parts.append(header.text)

            current_level = header.level

        return "/" + "/".join(path_parts)

    def _get_contextual_header_stack(
        self,
        chunk_start_line: int,
        all_headers: list[Header],
    ) -> list[Header]:
        """
        Get the active header stack at the start of a chunk.

        This is the stack of headers that define the structural context
        of the chunk - where it sits in the document tree.

        IMPORTANT: Stack is built from ALL headers before chunk start,
        regardless of their level. This ensures header_path reflects
        the true document hierarchy.

        max_structural_level only affects CHUNK BOUNDARIES (where to split),
        NOT which headers appear in header_path.

        O4 Optimization: Results are cached to avoid redundant computation
        when consecutive chunks share the same header context.

        Args:
            chunk_start_line: First line of the chunk (1-indexed)
            all_headers: All headers in the document

        Returns:
            List of headers forming the contextual stack (ancestors)
        """
        # O4: Check cache first
        if chunk_start_line in self._header_stack_cache:
            return self._header_stack_cache[chunk_start_line]

        stack: list[Header] = []

        for header in all_headers:
            # Only consider headers BEFORE chunk start
            if header.line >= chunk_start_line:
                break

            # Build hierarchy: new header replaces same/higher levels
            # NO filtering by max_structural_level - all headers can be in path
            while stack and stack[-1].level >= header.level:
                stack.pop()
            stack.append(header)

        # O4: Cache the result before returning
        self._header_stack_cache[chunk_start_line] = stack
        return stack

    def _get_contextual_level(self, header_stack: list[Header]) -> int:
        """
        Get the contextual level from header stack.

        Contextual level is the level of the deepest header in the
        ALREADY FILTERED contextual stack (stack doesn't contain
        levels > max_structural_level).

        Args:
            header_stack: The contextual header stack (already filtered)

        Returns:
            The contextual level (1 to max_structural_level), or 0 if stack is empty
        """
        if not header_stack:
            return 0
        return header_stack[-1].level

    def _build_header_path_from_stack(self, header_stack: list[Header]) -> str:
        """
        Build header_path from contextual header stack.

        Args:
            header_stack: List of ancestor headers

        Returns:
            Header path string like "/Level1/Level2", or empty string if stack is empty
        """
        if not header_stack:
            return ""
        return "/" + "/".join(h.text for h in header_stack)

    def _build_section_tags(
        self,
        chunk_content: str,
        contextual_level: int,
        header_stack: list[Header],
        first_header_in_path: tuple[int, str] | None = None,
    ) -> list[str]:
        """
        Build section_tags from headers inside the chunk.

        section_tags contains ALL headers that are children of the root
        section (last header in header_path). This is determined by:
        1. All headers with level > contextual_level (deeper than root
           section)
        2. Headers with level == contextual_level, whose TEXT does not
           match the root section header (siblings of root, not root
           itself)

        IMPORTANT:
        - max_structural_level is NOT used in section_tags rules
        - Everything is relative to contextual_level (level of root
          section)
        - If root section is H4, then H5/H6 go to section_tags
        - If root section is H2, then H3/H4/H5/H6 go to section_tags

        Args:
            chunk_content: The text content of the chunk
            contextual_level: The level of the root section (last header
                in header_path)
            header_stack: The contextual header stack (to identify root
                section)
            first_header_in_path: Optional (level, text) of first header
                that was added to path from this chunk - should be
                excluded from section_tags

        Returns:
            List of header texts (deduplicated, order preserved)
        """
        # Get text of the root section (last header in stack) for exclusion
        root_section_text = header_stack[-1].text if header_stack else None

        # Also exclude the first header if it was added to path from this chunk
        excluded_texts: set[str] = set()
        if root_section_text:
            excluded_texts.add(root_section_text)
        if first_header_in_path:
            excluded_texts.add(first_header_in_path[1])

        # Find headers in chunk content
        chunk_headers = self._find_headers_in_content(chunk_content)

        section_tags: list[str] = []
        seen_texts: set[str] = set()

        for level, text in chunk_headers:
            # Skip if already added (deduplication)
            if text in seen_texts:
                continue

            # Skip if this is the root section header itself
            if text in excluded_texts:
                continue

            # Add if level > contextual_level (child of root section)
            # This works for ANY contextual_level, not just max_structural_level
            if level > contextual_level or level == contextual_level:
                section_tags.append(text)
                seen_texts.add(text)

        return section_tags

    def _find_headers_in_range(
        self, headers: list[Header], start_line: int, end_line: int
    ) -> list[Header]:
        """
        Find all headers within a line range.

        Args:
            headers: List of all headers in document
            start_line: Start line (1-indexed, inclusive)
            end_line: End line (1-indexed, inclusive)

        Returns:
            List of headers within the range
        """
        return [h for h in headers if start_line <= h.line <= end_line]

    def _find_headers_in_content(self, content: str) -> list[tuple[int, str]]:
        """
        Find headers directly in chunk content.

        Args:
            content: Chunk text content

        Returns:
            List of (level, text) tuples for each header found
        """
        headers = []
        in_code_block = False

        for line in content.split("\n"):
            # Track code blocks to skip headers inside them
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Check for ATX header
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headers.append((level, text))

        return headers

    def _build_header_path_for_chunk(
        self, chunk_content: str, all_headers: list[Header], chunk_start_line: int
    ) -> tuple[str, list[str], int]:
        """
        Build header_path and section_tags for a chunk.

        New semantics:
        - header_path = structural context (where in document tree)
        - section_tags = local sections inside chunk (children of root section)

        Algorithm:
        1. Build contextual stack from headers BEFORE chunk start
           (only levels <= max_structural_level for CHUNK BOUNDARIES)
        2. Find first non-empty line of chunk
        3. If it's a header with level <= max_structural_level, add to stack
        4. If it's a header with level > max_structural_level, DON'T add to stack
        5. Build header_path from final stack
        6. Build section_tags from ALL headers deeper than contextual_level
           (relative logic, not absolute max_structural_level)

        IMPORTANT: section_tags uses RELATIVE logic based on contextual_level,
        not absolute max_structural_level. If header_path ends with H3,
        then H4/H5/H6 go to section_tags.

        Args:
            chunk_content: The text content of the chunk
            all_headers: All headers in the document (for building hierarchy)
            chunk_start_line: Starting line of the chunk (1-indexed)

        Returns:
            Tuple of (header_path, section_tags, header_level)
        """
        # Step 1: Get contextual header stack (headers BEFORE chunk,
        # filtered by max_structural_level)
        header_stack = self._get_contextual_header_stack(chunk_start_line, all_headers)

        # Step 2-4: Find headers in chunk content and process first header
        chunk_headers = self._find_headers_in_content(chunk_content)

        # Check for single-header-only chunk special case
        is_single_header_only = (
            len(chunk_headers) == 1
            and chunk_content.strip() == f"{'#' * chunk_headers[0][0]} {chunk_headers[0][1]}"
        )

        # Track if we added a header from this chunk to the path
        first_header_added_to_path: tuple[int, str] | None = None

        if chunk_headers:
            first_level, first_text = chunk_headers[0]

            # ONLY add first header to stack if it's a STRUCTURAL header
            # (level <= max_structural_level)
            # Headers deeper than max_structural_level stay in
            # section_tags, NOT in header_path
            # This ensures all chunks within a section (e.g., DEV-4)
            # have the SAME header_path
            if first_level <= self.max_structural_level:
                # Build hierarchy: new header replaces same/higher levels
                while header_stack and header_stack[-1].level >= first_level:
                    header_stack.pop()
                # Create a temporary Header object for the first header
                first_header = Header(
                    level=first_level,
                    text=first_text,
                    line=chunk_start_line,  # Approximate line
                )
                header_stack.append(first_header)
                first_header_added_to_path = (first_level, first_text)
            # If first header is H3+ (level > max_structural_level),
            # it goes to section_tags
            # header_path stays at the parent section level (e.g., DEV-4)

        # Step 5: Build header_path from stack
        header_path = self._build_header_path_from_stack(header_stack)

        # Step 6: Get contextual level and build section_tags
        # contextual_level is the level of the ROOT SECTION (last header in path)
        # section_tags will contain ALL headers with level > contextual_level
        contextual_level = self._get_contextual_level(header_stack)
        section_tags = self._build_section_tags(
            chunk_content, contextual_level, header_stack, first_header_added_to_path
        )

        # For single-header-only chunks, section_tags should be empty
        # (the header is in header_path, not section_tags)
        if is_single_header_only:
            section_tags = []

        # Calculate header_level (level of deepest header in header_path)
        header_level = contextual_level if header_stack else 0

        return header_path, section_tags, header_level

    def _split_section_preserving_atomic(
        self,
        section_content: str,
        section_start_line: int,
        atomic_blocks: list[tuple[int, int, str]],
        config: ChunkConfig,
    ) -> list[Chunk]:
        """Split section while preserving atomic blocks (code, tables, LaTeX).

        Args:
            section_content: Content of the section
            section_start_line: Starting line of section
            atomic_blocks: List of (start, end, type) for atomic blocks
            config: Chunking configuration

        Returns:
            List of chunks with atomic blocks preserved
        """
        lines = section_content.split("\n")
        chunks = []
        current_line = section_start_line

        for block_start, block_end, block_type in atomic_blocks:
            # Handle text before atomic block
            if current_line < block_start:
                text_lines = lines[
                    current_line - section_start_line : block_start - section_start_line
                ]
                text_content = "\n".join(text_lines)
                if text_content.strip():
                    text_chunks = self._split_text_to_size(text_content, current_line, config)
                    chunks.extend(text_chunks)

            # Handle atomic block
            block_lines = lines[
                block_start - section_start_line : block_end - section_start_line + 1
            ]
            block_content = "\n".join(block_lines)
            if block_content.strip():
                chunk = self._create_chunk(
                    block_content,
                    block_start,
                    block_end,
                    content_type=block_type,
                    is_atomic=True,
                )
                # Set oversize metadata if needed
                if chunk.size > config.max_chunk_size:
                    reason = (
                        "code_block_integrity"
                        if block_type == "code"
                        else ("table_integrity" if block_type == "table" else "latex_integrity")
                    )
                    self._set_oversize_metadata(chunk, reason, config)
                chunks.append(chunk)

            current_line = block_end + 1

        # Handle text after last atomic block
        section_end_line = section_start_line + len(lines) - 1
        if current_line <= section_end_line:
            text_lines = lines[current_line - section_start_line :]
            text_content = "\n".join(text_lines)
            if text_content.strip():
                text_chunks = self._split_text_to_size(text_content, current_line, config)
                chunks.extend(text_chunks)

        return chunks
