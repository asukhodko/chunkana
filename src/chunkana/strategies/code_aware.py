"""
Code-aware strategy for markdown_chunker v2.

For documents with code blocks or tables.
Consolidates CodeStrategy + MixedStrategy + TableStrategy.
"""

from ..code_context import CodeBlockRole, CodeContext, CodeContextBinder
from ..config import ChunkConfig
from ..types import Chunk, ContentAnalysis, FencedBlock, LatexType
from .base import BaseStrategy


class CodeAwareStrategy(BaseStrategy):
    """
    Strategy for documents with code blocks or tables.

    Preserves atomic blocks (code, tables) intact.
    Splits text around atomic blocks.

    Priority: 1 (highest - used when document has code or tables)
    """

    @property
    def name(self) -> str:
        return "code_aware"

    @property
    def priority(self) -> int:
        return 1

    def can_handle(self, analysis: ContentAnalysis, config: ChunkConfig) -> bool:
        """
        Can handle if document has code blocks or tables.
        """
        return (
            analysis.code_block_count >= 1
            or analysis.table_count >= 1
            or analysis.code_ratio >= config.code_threshold
        )

    def apply(self, md_text: str, analysis: ContentAnalysis, config: ChunkConfig) -> list[Chunk]:
        """
        Apply code-aware strategy.

        1. Identify atomic blocks (code, tables)
        2. Optionally bind code blocks to context (if enabled)
        3. Group related code blocks
        4. Split document around atomic blocks
        5. Create chunks preserving atomic blocks with metadata
        """
        if not md_text.strip():
            return []

        # Check if code-context binding is enabled
        if config.enable_code_context_binding and analysis.code_blocks:
            return self._apply_with_context_binding(md_text, analysis, config)
        else:
            return self._apply_without_context_binding(md_text, analysis, config)

    def _apply_without_context_binding(
        self, md_text: str, analysis: ContentAnalysis, config: ChunkConfig
    ) -> list[Chunk]:
        """
        Original apply logic without code-context binding.

        Preserves backward compatibility when feature is disabled.
        """
        # O1: Use cached lines from analysis (fallback for backward compatibility)
        lines = analysis.get_lines()
        if lines is None:
            lines = md_text.split("\n")

        # Get atomic block ranges
        atomic_ranges = self._get_atomic_ranges(analysis)

        if not atomic_ranges:
            # No atomic blocks - use simple splitting
            return self._split_text_to_size(md_text, 1, config)

        chunks = []
        current_line = 1

        for block_start, block_end, block_type in atomic_ranges:
            # Handle text before atomic block
            chunks.extend(self._process_text_before_block(lines, current_line, block_start, config))

            # Handle atomic block
            atomic_chunk = self._process_atomic_block(
                lines, block_start, block_end, block_type, config
            )
            if atomic_chunk:
                chunks.append(atomic_chunk)

            current_line = block_end + 1

        # Handle text after last atomic block
        chunks.extend(self._process_text_after_blocks(lines, current_line, config))

        # Ensure fence balance
        chunks = self._ensure_fence_balance(chunks)

        return chunks

    def _process_text_before_block(
        self,
        lines: list[str],
        current_line: int,
        block_start: int,
        config: ChunkConfig,
    ) -> list[Chunk]:
        """Process text content before an atomic block."""
        if current_line >= block_start:
            return []

        text_lines = lines[current_line - 1 : block_start - 1]
        text_content = "\n".join(text_lines)

        if text_content.strip():
            return self._split_text_to_size(text_content, current_line, config)
        return []

    def _process_text_after_blocks(
        self, lines: list[str], current_line: int, config: ChunkConfig
    ) -> list[Chunk]:
        """Process text content after all atomic blocks."""
        if current_line > len(lines):
            return []

        text_lines = lines[current_line - 1 :]
        text_content = "\n".join(text_lines)

        if text_content.strip():
            return self._split_text_to_size(text_content, current_line, config)
        return []

    def _process_atomic_block(
        self,
        lines: list[str],
        block_start: int,
        block_end: int,
        block_type: str,
        config: ChunkConfig,
    ) -> Chunk | None:
        """Process a single atomic block (code, table, or LaTeX)."""
        block_lines = lines[block_start - 1 : block_end]
        block_content = "\n".join(block_lines)

        if not block_content.strip():
            return None

        chunk = self._create_chunk(
            block_content,
            block_start,
            block_end,
            content_type=block_type,
            is_atomic=True,
        )

        # Set oversize metadata if needed
        if chunk.size > config.max_chunk_size:
            reason = self._get_oversize_reason(block_type)
            self._set_oversize_metadata(chunk, reason, config)

        return chunk

    def _get_oversize_reason(self, block_type: str) -> str:
        """Get oversize reason based on block type."""
        if block_type == "code":
            return "code_block_integrity"
        elif block_type == "table":
            return "table_integrity"
        else:  # latex
            return "latex_integrity"

    def _apply_with_context_binding(
        self, md_text: str, analysis: ContentAnalysis, config: ChunkConfig
    ) -> list[Chunk]:
        """
        Enhanced apply logic with code-context binding.

        Binds code blocks to explanations and groups related blocks.
        """
        # O1: Use cached lines from analysis (fallback for backward compatibility)
        lines = analysis.get_lines()
        if lines is None:
            lines = md_text.split("\n")

        # Initialize context binder and bind all code blocks
        # O1: Pass lines to CodeContextBinder for optimization
        binder = CodeContextBinder(
            max_context_chars_before=config.max_context_chars_before,
            max_context_chars_after=config.max_context_chars_after,
            related_block_max_gap=config.related_block_max_gap,
            lines=lines,  # O1: Share line array
        )

        code_contexts = [
            binder.bind_context(block, md_text, analysis.code_blocks)
            for block in analysis.code_blocks
        ]

        # Group related contexts and create index mapping
        context_groups = self._group_related_contexts(code_contexts, config)
        context_to_group = self._build_context_to_group_map(code_contexts, context_groups)

        # Get atomic block ranges
        atomic_ranges = self._get_atomic_ranges(analysis)
        if not atomic_ranges:
            return self._split_text_to_size(md_text, 1, config)

        # Process atomic blocks and create chunks
        return self._process_atomic_blocks_with_context(
            lines,
            md_text,
            analysis,
            atomic_ranges,
            code_contexts,
            context_to_group,
            config,
        )

    def _build_context_to_group_map(
        self,
        code_contexts: list[CodeContext],
        context_groups: list[list[CodeContext]],
    ) -> dict[int, list[CodeContext]]:
        """Build mapping from context index to group."""
        context_to_group: dict[int, list[CodeContext]] = {}
        for group in context_groups:
            for ctx in group:
                idx = code_contexts.index(ctx)
                context_to_group[idx] = group
        return context_to_group

    def _process_atomic_blocks_with_context(
        self,
        lines: list[str],
        md_text: str,
        analysis: ContentAnalysis,
        atomic_ranges: list[tuple[int, int, str]],
        code_contexts: list[CodeContext],
        context_to_group: dict[int, list[CodeContext]],
        config: ChunkConfig,
    ) -> list[Chunk]:
        """Process atomic blocks and create chunks with context binding."""
        chunks = []
        current_line = 1
        processed_blocks: set[int] = set()
        processed_table_lines: set[int] = set()

        for block_start, block_end, block_type in atomic_ranges:
            # Handle text before atomic block
            chunks.extend(self._create_text_chunks_before(lines, current_line, block_start, config))

            # Handle atomic block
            if block_type == "code":
                new_chunks, new_line = self._process_code_block_with_context(
                    lines,
                    md_text,
                    analysis,
                    block_start,
                    block_end,
                    code_contexts,
                    context_to_group,
                    processed_blocks,
                    config,
                )
                chunks.extend(new_chunks)
                current_line = new_line
            elif block_type == "table":
                new_chunks, new_line = self._process_table_block(
                    lines,
                    block_start,
                    block_end,
                    config,
                    analysis,
                    processed_table_lines,
                )
                chunks.extend(new_chunks)
                current_line = new_line
            else:
                # LaTeX or other atomic blocks
                new_chunks, new_line = self._process_table_block(
                    lines, block_start, block_end, config
                )
                chunks.extend(new_chunks)
                current_line = new_line

        # Handle text after last atomic block
        chunks.extend(self._create_text_chunks_after(lines, current_line, config))

        return self._ensure_fence_balance(chunks)

    def _create_text_chunks_before(
        self,
        lines: list[str],
        current_line: int,
        block_start: int,
        config: ChunkConfig,
    ) -> list[Chunk]:
        """Create chunks from text before atomic block."""
        if current_line >= block_start:
            return []

        text_lines = lines[current_line - 1 : block_start - 1]
        text_content = "\n".join(text_lines)

        if text_content.strip():
            return self._split_text_to_size(text_content, current_line, config)
        return []

    def _create_text_chunks_after(
        self, lines: list[str], current_line: int, config: ChunkConfig
    ) -> list[Chunk]:
        """Create chunks from text after last atomic block."""
        if current_line > len(lines):
            return []

        text_lines = lines[current_line - 1 :]
        text_content = "\n".join(text_lines)

        if text_content.strip():
            return self._split_text_to_size(text_content, current_line, config)
        return []

    def _process_code_block_with_context(
        self,
        lines: list[str],
        md_text: str,
        analysis: ContentAnalysis,
        block_start: int,
        block_end: int,
        code_contexts: list[CodeContext],
        context_to_group: dict[int, list[CodeContext]],
        processed_blocks: set[int],
        config: ChunkConfig,
    ) -> tuple[list[Chunk], int]:
        """Process code block with context binding."""
        code_block_idx = self._find_code_block_index(analysis.code_blocks, block_start, block_end)

        if code_block_idx is None or code_block_idx in processed_blocks:
            return [], block_end + 1

        group = context_to_group.get(code_block_idx)

        if group and len(group) > 1:
            # Create grouped chunk
            chunk = self._create_grouped_code_chunk(group, code_contexts, lines, md_text, config)
            # Mark all blocks in group as processed
            for ctx in group:
                idx = code_contexts.index(ctx)
                processed_blocks.add(idx)
            last_block = group[-1].code_block
            return [chunk], last_block.end_line + 1
        else:
            # Create single block chunk
            context = code_contexts[code_block_idx]
            chunk = self._create_context_enhanced_chunk(context, lines, md_text, config)
            processed_blocks.add(code_block_idx)
            return [chunk], block_end + 1

    def _process_table_block(
        self,
        lines: list[str],
        block_start: int,
        block_end: int,
        config: ChunkConfig,
        analysis: ContentAnalysis | None = None,
        processed_table_lines: set[int] | None = None,
    ) -> tuple[list[Chunk], int]:
        """
        Process table block, with optional table grouping support.

        Args:
            lines: Document lines
            block_start: Table start line
            block_end: Table end line
            config: Chunking configuration
            analysis: Document analysis (for table grouping)
            processed_table_lines: Set of already processed table start lines

        Returns:
            Tuple of (chunks, next_line)
        """
        # Check if this table was already processed as part of a group
        if processed_table_lines is not None and block_start in processed_table_lines:
            return [], block_end + 1

        # Check if table grouping is enabled
        if config.group_related_tables and analysis is not None:
            return self._process_table_with_grouping(
                lines, block_start, block_end, config, analysis, processed_table_lines
            )

        # Standard single-table processing
        block_lines = lines[block_start - 1 : block_end]
        block_content = "\n".join(block_lines)

        if not block_content.strip():
            return [], block_end + 1

        chunk = self._create_chunk(
            block_content,
            block_start,
            block_end,
            content_type="table",
            is_atomic=True,
        )

        if chunk.size > config.max_chunk_size:
            self._set_oversize_metadata(chunk, "table_integrity", config)

        return [chunk], block_end + 1

    def _process_table_with_grouping(
        self,
        lines: list[str],
        block_start: int,
        block_end: int,
        config: ChunkConfig,
        analysis: ContentAnalysis,
        processed_table_lines: set[int] | None,
    ) -> tuple[list[Chunk], int]:
        """
        Process table with grouping enabled.

        Finds the group containing this table and processes entire group.
        """
        # Get table groups
        table_groups = self._get_table_groups(analysis, lines, config)

        # Find group containing this table
        for group in table_groups:
            for table in group.tables:
                if table.start_line == block_start:
                    # Found the group - mark all tables as processed
                    if processed_table_lines is not None:
                        for t in group.tables:
                            processed_table_lines.add(t.start_line)

                    # Create chunk for group
                    chunk = self._create_chunk(
                        group.content,
                        group.start_line,
                        group.end_line,
                        content_type="table",
                        is_atomic=True,
                    )

                    # Add table group metadata
                    if group.table_count > 1:
                        chunk.metadata["is_table_group"] = True
                        chunk.metadata["table_group_count"] = group.table_count

                    if chunk.size > config.max_chunk_size:
                        self._set_oversize_metadata(chunk, "table_integrity", config)

                    return [chunk], group.end_line + 1

        # Fallback to single table processing
        block_lines = lines[block_start - 1 : block_end]
        block_content = "\n".join(block_lines)

        if not block_content.strip():
            return [], block_end + 1

        chunk = self._create_chunk(
            block_content,
            block_start,
            block_end,
            content_type="table",
            is_atomic=True,
        )

        if chunk.size > config.max_chunk_size:
            self._set_oversize_metadata(chunk, "table_integrity", config)

        return [chunk], block_end + 1

    def _get_atomic_ranges(self, analysis: ContentAnalysis) -> list[tuple[int, int, str]]:
        """
        Get line ranges of atomic blocks.

        Returns list of (start_line, end_line, block_type) tuples,
        sorted by start_line.
        """
        ranges = []

        # Add code blocks
        for block in analysis.code_blocks:
            ranges.append((block.start_line, block.end_line, "code"))

        # Add tables
        for table in analysis.tables:
            ranges.append((table.start_line, table.end_line, "table"))

        # Add LaTeX blocks (only display and environment types)
        for latex in analysis.latex_blocks:
            if latex.latex_type in (LatexType.DISPLAY, LatexType.ENVIRONMENT):
                ranges.append((latex.start_line, latex.end_line, "latex"))

        # Sort by start line
        ranges.sort(key=lambda x: x[0])

        return ranges

    def _group_related_contexts(
        self, contexts: list[CodeContext], config: ChunkConfig
    ) -> list[list[CodeContext]]:
        """
        Group related code contexts based on relationships.

        Groups are formed when:
        - Before/After pairs (if preserve_before_after_pairs is enabled)
        - Code/Output pairs (if bind_output_blocks is enabled)
        - Related blocks with same language in close proximity

        Returns:
            List of context groups, each group is a list of related contexts
        """
        if not contexts:
            return []

        groups = []
        processed = set()

        for i, context in enumerate(contexts):
            if i in processed:
                continue

            # Start new group with current context
            group = [context]
            processed.add(i)

            # Look for related contexts
            for j, other_context in enumerate(contexts):
                if j in processed or i == j:
                    continue

                # Check if contexts are related
                if self._are_contexts_related(context, other_context, config):
                    group.append(other_context)
                    processed.add(j)

            groups.append(group)

        return groups

    def _are_contexts_related(
        self, ctx1: CodeContext, ctx2: CodeContext, config: ChunkConfig
    ) -> bool:
        """
        Check if two code contexts are related and should be grouped.

        Args:
            ctx1: First code context
            ctx2: Second code context
            config: Chunking configuration

        Returns:
            True if contexts are related
        """
        # Check Before/After pairing
        if config.preserve_before_after_pairs and (
            (ctx1.role == CodeBlockRole.BEFORE and ctx2.role == CodeBlockRole.AFTER)
            or (ctx1.role == CodeBlockRole.AFTER and ctx2.role == CodeBlockRole.BEFORE)
        ):
            # Check proximity
            gap = abs(ctx1.code_block.end_line - ctx2.code_block.start_line)
            if gap <= config.related_block_max_gap:
                return True

        # Check Code/Output pairing
        if config.bind_output_blocks:
            if ctx1.output_block == ctx2.code_block:
                return True
            if ctx2.output_block == ctx1.code_block:
                return True

        # Check if blocks are in each other's related_blocks list
        if ctx1.related_blocks and ctx2.code_block in ctx1.related_blocks:
            return True
        return bool(ctx2.related_blocks and ctx1.code_block in ctx2.related_blocks)

    def _find_code_block_index(
        self, code_blocks: list[FencedBlock], start_line: int, end_line: int
    ) -> int | None:
        """
        Find the index of a code block by its line range.

        Args:
            code_blocks: List of code blocks
            start_line: Start line to match
            end_line: End line to match

        Returns:
            Index of matching block, or None if not found
        """
        for i, block in enumerate(code_blocks):
            if block.start_line == start_line and block.end_line == end_line:
                return i
        return None

    def _create_context_enhanced_chunk(
        self,
        context: CodeContext,
        lines: list[str],
        md_text: str,
        config: ChunkConfig,
    ) -> Chunk:
        """
        Create a chunk for a single code block with context metadata.

        Args:
            context: Code context with role and explanations
            lines: Document lines
            md_text: Full markdown text
            config: Chunking configuration

        Returns:
            Chunk with enhanced metadata
        """
        block = context.code_block
        block_lines = lines[block.start_line - 1 : block.end_line]
        block_content = "\n".join(block_lines)

        chunk = self._create_chunk(
            block_content,
            block.start_line,
            block.end_line,
            content_type="code",
            is_atomic=True,
        )

        # Add context metadata
        chunk.metadata["code_role"] = context.role.value
        related_blocks = context.related_blocks or []
        chunk.metadata["has_related_code"] = len(related_blocks) > 0
        chunk.metadata["related_code_count"] = len(related_blocks)
        chunk.metadata["explanation_bound"] = bool(
            context.explanation_before or context.explanation_after
        )

        if context.explanation_before and context.explanation_after:
            chunk.metadata["context_scope"] = "both"
        elif context.explanation_before:
            chunk.metadata["context_scope"] = "before"
        elif context.explanation_after:
            chunk.metadata["context_scope"] = "after"
        else:
            chunk.metadata["context_scope"] = "none"

        if context.output_block:
            chunk.metadata["has_output_block"] = True

        # Set oversize metadata if needed
        if chunk.size > config.max_chunk_size:
            self._set_oversize_metadata(chunk, "code_block_integrity", config)

        return chunk

    def _create_grouped_code_chunk(
        self,
        group: list[CodeContext],
        all_contexts: list[CodeContext],
        lines: list[str],
        md_text: str,
        config: ChunkConfig,
    ) -> Chunk:
        """
        Create a single chunk from a group of related code contexts.

        Args:
            group: List of related code contexts
            all_contexts: All code contexts (for index tracking)
            lines: Document lines
            md_text: Full markdown text
            config: Chunking configuration

        Returns:
            Chunk containing all blocks in the group
        """
        if not group:
            raise ValueError("Cannot create chunk from empty group")

        # Get line range for entire group
        start_line = min(ctx.code_block.start_line for ctx in group)
        end_line = max(ctx.code_block.end_line for ctx in group)

        # Extract content for entire group
        group_lines = lines[start_line - 1 : end_line]
        group_content = "\n".join(group_lines)

        chunk = self._create_chunk(
            group_content,
            start_line,
            end_line,
            content_type="code",
            is_atomic=True,
        )

        # Determine relationship type
        relationship = self._determine_relationship_type(group)

        # Add group metadata
        chunk.metadata["has_related_code"] = True
        chunk.metadata["related_code_count"] = len(group)
        chunk.metadata["code_relationship"] = relationship
        chunk.metadata["explanation_bound"] = any(
            ctx.explanation_before or ctx.explanation_after for ctx in group
        )

        # Add role information
        roles = [ctx.role.value for ctx in group]
        chunk.metadata["code_role"] = roles[0] if len(set(roles)) == 1 else "mixed"
        chunk.metadata["code_roles"] = roles

        # Set oversize metadata if needed
        if chunk.size > config.max_chunk_size:
            self._set_oversize_metadata(chunk, "related_code_group", config)

        return chunk

    def _determine_relationship_type(self, group: list[CodeContext]) -> str:
        """
        Determine the type of relationship in a context group.

        Args:
            group: List of code contexts in the group

        Returns:
            Relationship type string
        """
        roles = [ctx.role for ctx in group]

        # Check for Before/After pattern
        if CodeBlockRole.BEFORE in roles and CodeBlockRole.AFTER in roles:
            return "before_after"

        # Check for Code/Output pattern
        has_output = any(ctx.output_block is not None for ctx in group)
        if has_output:
            return "code_output"

        # Check for same language (sequential examples)
        languages = [ctx.code_block.language for ctx in group]
        if len(set(languages)) == 1 and languages[0]:
            return "sequential"

        return "related"
