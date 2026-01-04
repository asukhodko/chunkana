import re

from .types import (
    ContentAnalysis,
    FencedBlock,
    Header,
    LatexBlock,
    LatexType,
    ListBlock,
    ListItem,
    ListType,
    TableBlock,
)


class Parser:
    """
    Markdown document parser.

    Extracts:
    - Code blocks (fenced)
    - LaTeX formulas (display and environments)
    - Headers
    - Tables
    - Lists
    - Content metrics

    All line endings are normalized to Unix-style (\\n) before processing.
    """

    # Regex patterns
    CODE_BLOCK_PATTERN = re.compile(r"^(`{3,})(\w*)\n(.*?)\n\1", re.MULTILINE | re.DOTALL)

    HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    # O1b: Pre-compiled fence detection pattern for performance
    FENCE_PATTERN = re.compile(r"^(\s*)(`{3,}|~{3,})(\w*)\s*$")

    # O3: Pre-compiled list item patterns (early termination)
    CHECKBOX_PATTERN = re.compile(r"^(\s*)([-*+])\s+\[([ xX])\]\s+(.+)$")
    NUMBERED_PATTERN = re.compile(r"^(\s*)(\d+\.)\s+(.+)$")
    BULLET_PATTERN = re.compile(r"^(\s*)([-*+])\s+(.+)$")

    def analyze(self, md_text: str) -> ContentAnalysis:
        """
        Analyze a markdown document.

        Args:
            md_text: Raw markdown text

        Returns:
            ContentAnalysis with metrics and extracted elements
        """
        # 1. Normalize line endings (CRITICAL - must be first)
        md_text = self._normalize_line_endings(md_text)

        # O1: Single split operation for entire pipeline
        lines = md_text.split("\n") if md_text else []
        positions = self._build_position_index(lines)

        # 2. Extract elements using shared line array and position index
        code_blocks = self._extract_code_blocks(lines, positions)
        latex_blocks = self._extract_latex_blocks(lines, positions, code_blocks)
        headers = self._extract_headers(lines, positions)
        tables = self._extract_tables(lines, positions)
        list_blocks = self._extract_lists(lines, positions)

        # 3. Calculate metrics
        total_chars = len(md_text)
        total_lines = len(lines) if md_text else 0

        code_chars = sum(len(b.content) for b in code_blocks)
        code_ratio = code_chars / total_chars if total_chars > 0 else 0.0

        max_header_depth = max((h.level for h in headers), default=0)

        # Calculate list metrics
        list_chars = sum(len(item.content) for block in list_blocks for item in block.items)
        list_ratio = list_chars / total_chars if total_chars > 0 else 0.0
        list_item_count = sum(block.item_count for block in list_blocks)
        max_list_depth = max((block.max_depth for block in list_blocks), default=0)
        has_checkbox_lists = any(
            any(item.list_type == ListType.CHECKBOX for item in block.items)
            for block in list_blocks
        )

        # Calculate LaTeX metrics
        latex_chars = sum(len(block.content) for block in latex_blocks)
        latex_ratio = latex_chars / total_chars if total_chars > 0 else 0.0

        # 4. Detect preamble using shared line array
        has_preamble, preamble_end = self._detect_preamble(lines, positions, headers)

        # 5. Calculate average sentence length using shared line array
        avg_sent_length = self._calculate_avg_sentence_length(lines)

        return ContentAnalysis(
            total_chars=total_chars,
            total_lines=total_lines,
            code_ratio=code_ratio,
            code_block_count=len(code_blocks),
            header_count=len(headers),
            max_header_depth=max_header_depth,
            table_count=len(tables),
            list_count=len(list_blocks),
            list_item_count=list_item_count,
            code_blocks=code_blocks,
            headers=headers,
            tables=tables,
            list_blocks=list_blocks,
            latex_blocks=latex_blocks,
            has_preamble=has_preamble,
            preamble_end_line=preamble_end,
            list_ratio=list_ratio,
            max_list_depth=max_list_depth,
            has_checkbox_lists=has_checkbox_lists,
            avg_sentence_length=avg_sent_length,
            latex_block_count=len(latex_blocks),
            latex_ratio=latex_ratio,
            _lines=lines,  # O1: Store line array for strategy optimization
        )

    def _normalize_line_endings(self, text: str) -> str:
        """
        Normalize all line endings to Unix-style (\\n).

        Handles:
        - Windows: \\r\\n -> \\n
        - Old Mac: \\r -> \\n

        Performance optimization: Fast-path detection skips normalization
        when text contains no \\r characters (Unix-formatted files).

        This MUST be called before any other processing.
        """
        # Fast path: skip normalization if no \r present (Unix line endings)
        if "\r" not in text:
            return text

        # Normalize: First convert CRLF to LF, then convert remaining CR to LF
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _build_position_index(self, lines: list[str]) -> list[int]:
        """
        Build cumulative position index for O(1) position lookups.

        O0 Optimization: Replaces O(n×m) position calculations with O(1) array lookups.

        Args:
            lines: Array of text lines from document

        Returns:
            Array where index i gives character position of line i in document.
            Position includes all preceding lines plus newline characters.

        Example:
            For document "hello\nworld\n":
            lines = ["hello", "world"]
            positions = [0, 6]  # "hello" starts at 0, "world" starts at 6
        """
        positions = [0]
        cumulative = 0
        for line in lines:
            cumulative += len(line) + 1  # +1 for newline character
            positions.append(cumulative)
        return positions

    def _is_fence_opening(self, line: str) -> tuple[str, int, str] | None:
        """
        Check if line is a fence opening.

        Args:
            line: Line to check

        Returns:
            Tuple of (fence_char, fence_length, language) if fence opening,
            None otherwise.

        Examples:
            >>> parser._is_fence_opening("```python")
            ('`', 3, 'python')
            >>> parser._is_fence_opening("~~~~")
            ('~', 4, '')
            >>> parser._is_fence_opening("regular text")
            None
        """
        # O1b: Use pre-compiled pattern for performance
        match = self.FENCE_PATTERN.match(line)
        if not match:
            return None

        fence_chars = match.group(2)
        fence_char = fence_chars[0]
        fence_length = len(fence_chars)
        language = match.group(3) or ""

        return (fence_char, fence_length, language)

    def _is_fence_closing(self, line: str, fence_char: str, fence_length: int) -> bool:
        """
        Check if line is a valid closing fence.

        Args:
            line: Line to check
            fence_char: Expected fence character ('`' or '~')
            fence_length: Minimum fence length required

        Returns:
            True if line closes fence, False otherwise.

        Examples:
            >>> parser._is_fence_closing("```", '`', 3)
            True
            >>> parser._is_fence_closing("````", '`', 3)
            True
            >>> parser._is_fence_closing("```", '`', 4)
            False
            >>> parser._is_fence_closing("~~~", '`', 3)
            False
        """
        # Closing fence must:
        # 1. Start with same fence character
        # 2. Have equal or greater length
        # 3. Contain only fence characters and whitespace
        pattern = rf"^(\s*)({re.escape(fence_char)}{{{fence_length},}})\s*$"
        return bool(re.match(pattern, line))

    def _extract_code_blocks(self, lines: list[str], positions: list[int]) -> list[FencedBlock]:
        """
        Extract fenced code blocks with nested fencing support.

        Handles:
        - Standard ``` fences
        - Quadruple ````, quintuple ````` fences
        - Tilde fencing (~~~, ~~~~, ~~~~~)
        - Mixed fence types (backticks containing tildes and vice versa)
        - Unclosed fences (extend to end of document)
        - Indented fences

        Args:
            lines: Pre-split document lines (O1 optimization)
            positions: Pre-computed position index (O0 optimization)

        Returns:
            List of FencedBlock objects with complete metadata.
        """
        blocks = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for fence opening
            fence_info = self._is_fence_opening(line)
            if fence_info:
                fence_char, fence_length, language = fence_info
                start_line = i + 1  # 1-indexed
                start_pos = positions[i]  # O0: O(1) lookup instead of O(i) sum

                # Collect fence content
                content_lines = []
                i += 1
                is_closed = False

                while i < len(lines):
                    if self._is_fence_closing(lines[i], fence_char, fence_length):
                        is_closed = True
                        break
                    content_lines.append(lines[i])
                    i += 1

                # Calculate end position
                end_line = min(i + 1, len(lines))  # 1-indexed
                end_pos = positions[min(i + 1, len(lines))]  # O0: O(1) lookup

                blocks.append(
                    FencedBlock(
                        language=language if language else None,
                        content="\n".join(content_lines),
                        start_line=start_line,
                        end_line=end_line,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        fence_char=fence_char,
                        fence_length=fence_length,
                        is_closed=is_closed,
                    )
                )

            i += 1

        return blocks

    def _is_display_delimiter(self, line: str) -> bool:
        """
        Check if line contains display math delimiter ($$).

        Args:
            line: Line to check

        Returns:
            True if line contains $$, False otherwise
        """
        return "$$" in line.strip()

    def _is_environment_start(self, line: str) -> str | None:
        """
        Check if line starts a LaTeX environment.

        Args:
            line: Line to check

        Returns:
            Environment name if found, None otherwise
        """
        pattern = r"^\\begin\{(equation|align|gather|multline|eqnarray)\*?\}"
        match = re.match(pattern, line.strip())
        if match:
            return match.group(1)
        return None

    def _is_environment_end(self, line: str, env_name: str) -> bool:
        """
        Check if line ends a LaTeX environment.

        Args:
            line: Line to check
            env_name: Expected environment name

        Returns:
            True if line ends the specified environment
        """
        pattern = rf"^\\end\{{{re.escape(env_name)}\*?\}}"
        return bool(re.match(pattern, line.strip()))

    def _create_latex_block(
        self,
        content: str,
        latex_type: LatexType,
        start_line: int,
        end_line: int,
        start_pos: int,
        end_pos: int,
        env_name: str | None = None,
    ) -> LatexBlock:
        """
        Create a LatexBlock instance.

        Args:
            content: Complete LaTeX content including delimiters
            latex_type: Type of LaTeX block
            start_line: Starting line (1-indexed)
            end_line: Ending line (1-indexed)
            start_pos: Character position in document
            end_pos: Character position in document
            env_name: Environment name (for ENVIRONMENT type)

        Returns:
            LatexBlock instance
        """
        return LatexBlock(
            content=content,
            latex_type=latex_type,
            start_line=start_line,
            end_line=end_line,
            start_pos=start_pos,
            end_pos=end_pos,
            environment_name=env_name,
        )

    def _extract_latex_blocks(
        self, lines: list[str], positions: list[int], code_blocks: list[FencedBlock]
    ) -> list[LatexBlock]:
        """
        Extract LaTeX formula blocks from markdown.

        Handles:
        - Display math: $$...$$
        - Equation environments: \\begin{equation}...\\end{equation}
        - Ignores LaTeX inside code blocks

        Args:
            lines: Pre-split document lines (O1 optimization)
            positions: Pre-computed position index (O0 optimization)
            code_blocks: Already extracted code blocks (to skip LaTeX inside them)

        Returns:
            List of LatexBlock objects
        """
        blocks = []

        # Build code block line ranges for quick lookup
        code_ranges = [(b.start_line, b.end_line) for b in code_blocks]

        i = 0
        while i < len(lines):
            line_num = i + 1  # 1-indexed

            # Skip if inside code block
            in_code = any(start <= line_num <= end for start, end in code_ranges)
            if in_code:
                i += 1
                continue

            # Check for display math delimiter
            if self._is_display_delimiter(lines[i]):
                start_line = line_num
                start_pos = positions[i]  # O0: O(1) lookup
                content_lines = [lines[i]]

                # Check if single-line or multi-line
                if lines[i].strip().count("$$") >= 2:
                    # Single line display math
                    end_line = line_num
                    end_pos = start_pos + len(lines[i])
                    blocks.append(
                        self._create_latex_block(
                            content=lines[i],
                            latex_type=LatexType.DISPLAY,
                            start_line=start_line,
                            end_line=end_line,
                            start_pos=start_pos,
                            end_pos=end_pos,
                        )
                    )
                    i += 1
                    continue

                # Multi-line display math - find closing $$
                i += 1
                while i < len(lines):
                    content_lines.append(lines[i])
                    if self._is_display_delimiter(lines[i]):
                        # Found closing delimiter
                        end_line = i + 1
                        end_pos = positions[i + 1]  # O0: O(1) lookup
                        blocks.append(
                            self._create_latex_block(
                                content="\n".join(content_lines),
                                latex_type=LatexType.DISPLAY,
                                start_line=start_line,
                                end_line=end_line,
                                start_pos=start_pos,
                                end_pos=end_pos,
                            )
                        )
                        i += 1
                        break
                    i += 1
                else:
                    # Unclosed display math - extends to end
                    end_line = len(lines)
                    end_pos = positions[-1] if positions else 0
                    blocks.append(
                        self._create_latex_block(
                            content="\n".join(content_lines),
                            latex_type=LatexType.DISPLAY,
                            start_line=start_line,
                            end_line=end_line,
                            start_pos=start_pos,
                            end_pos=end_pos,
                        )
                    )
                continue

            # Check for environment start
            env_name = self._is_environment_start(lines[i])
            if env_name:
                start_line = line_num
                start_pos = positions[i]  # O0: O(1) lookup
                content_lines = [lines[i]]

                # Find matching end
                i += 1
                while i < len(lines):
                    content_lines.append(lines[i])
                    if self._is_environment_end(lines[i], env_name):
                        end_line = i + 1
                        end_pos = positions[i + 1]  # O0: O(1) lookup
                        blocks.append(
                            self._create_latex_block(
                                content="\n".join(content_lines),
                                latex_type=LatexType.ENVIRONMENT,
                                start_line=start_line,
                                end_line=end_line,
                                start_pos=start_pos,
                                end_pos=end_pos,
                                env_name=env_name,
                            )
                        )
                        i += 1
                        break
                    i += 1
                else:
                    # Unclosed environment - extends to end
                    end_line = len(lines)
                    end_pos = positions[-1] if positions else 0
                    blocks.append(
                        self._create_latex_block(
                            content="\n".join(content_lines),
                            latex_type=LatexType.ENVIRONMENT,
                            start_line=start_line,
                            end_line=end_line,
                            start_pos=start_pos,
                            end_pos=end_pos,
                            env_name=env_name,
                        )
                    )
                continue

            i += 1

        return blocks

    def _extract_headers(self, lines: list[str], positions: list[int]) -> list[Header]:
        """
        Extract markdown headers.

        Handles:
        - ATX headers (# through ######)
        - Ignores headers inside code blocks
        - Supports nested fences and tilde fencing

        Args:
            lines: Pre-split document lines (O1 optimization)
            positions: Pre-computed position index (O0 optimization)

        Returns:
            List of extracted Header objects
        """
        headers = []

        # Track fence state with stack for nested fences
        fence_stack: list[tuple[str, int]] = []  # (char, length) tuples

        for i, line in enumerate(lines):
            # Check for fence closing FIRST (if inside fence)
            if fence_stack:
                current_fence_char, current_fence_length = fence_stack[-1]
                if self._is_fence_closing(line, current_fence_char, current_fence_length):
                    fence_stack.pop()
                    continue

            # Check for fence opening
            fence_info = self._is_fence_opening(line)
            if fence_info:
                fence_char, fence_length, _ = fence_info
                fence_stack.append((fence_char, fence_length))
                continue

            # Skip if inside fence
            if fence_stack:
                continue

            # Check for header
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2).strip()
                pos = positions[i]  # O0: O(1) lookup

                headers.append(
                    Header(
                        level=level,
                        text=text,
                        line=i + 1,  # 1-indexed
                        pos=pos,
                    )
                )

        return headers

    def _extract_tables(self, lines: list[str], positions: list[int]) -> list[TableBlock]:
        """
        Extract markdown tables.

        A table is identified by:
        - Row with | characters
        - Followed by separator row with |---|
        - Ignores tables inside code blocks
        - Supports nested fences and tilde fencing

        Args:
            lines: Pre-split document lines (O1 optimization)
            positions: Pre-computed position index (O0 optimization)

        Returns:
            List of extracted table blocks
        """
        tables = []

        # Track fence state with stack for nested fences
        fence_stack: list[tuple[str, int]] = []  # (char, length) tuples

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for fence closing FIRST (if inside fence)
            if fence_stack:
                current_fence_char, current_fence_length = fence_stack[-1]
                if self._is_fence_closing(line, current_fence_char, current_fence_length):
                    fence_stack.pop()
                    i += 1
                    continue

            # Check for fence opening
            fence_info = self._is_fence_opening(line)
            if fence_info:
                fence_char, fence_length, _ = fence_info
                fence_stack.append((fence_char, fence_length))
                i += 1
                continue

            # Skip if inside fence
            if fence_stack:
                i += 1
                continue

            # Check for table start: line with | followed by separator
            if "|" in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                if "|" in next_line and re.search(r"-{3,}", next_line):
                    # Found table
                    start_line = i + 1  # 1-indexed
                    table_lines = [line, next_line]

                    # Count columns from header
                    column_count = line.count("|") - 1
                    if line.startswith("|"):
                        column_count = line.count("|") - 1

                    # Collect remaining rows
                    i += 2
                    while i < len(lines) and "|" in lines[i]:
                        table_lines.append(lines[i])
                        i += 1

                    end_line = i  # 1-indexed (line after last table row)
                    row_count = len(table_lines) - 2  # Exclude header and separator

                    tables.append(
                        TableBlock(
                            content="\n".join(table_lines),
                            start_line=start_line,
                            end_line=end_line,
                            column_count=max(column_count, 1),
                            row_count=max(row_count, 0),
                        )
                    )
                    continue

            i += 1

        return tables

    def _detect_preamble(
        self, lines: list[str], positions: list[int], headers: list[Header]
    ) -> tuple[bool, int]:
        """
        Detect if document has preamble (content before first header).

        Args:
            lines: Pre-split document lines (O1 optimization)
            positions: Pre-computed position index (O0 optimization)
            headers: Extracted headers from document

        Returns:
            Tuple of (has_preamble, preamble_end_line)
        """
        if not headers:
            # No headers = entire document could be preamble
            return False, 0

        first_header_line = headers[0].line

        # Check if there's non-whitespace content before first header
        for i in range(first_header_line - 1):
            if lines[i].strip():
                return True, first_header_line - 1

        return False, 0

    def _extract_lists(self, lines: list[str], positions: list[int]) -> list[ListBlock]:
        """
        Extract list blocks from markdown.

        Handles:
        - Bullet lists (-, *, +)
        - Numbered lists (1., 2., etc.)
        - Checkbox lists (- [ ], - [x])
        - Nested lists
        - Continuation lines
        - Ignores lists inside code blocks
        - Supports nested fences and tilde fencing

        Args:
            lines: Pre-split document lines (O1 optimization)
            positions: Pre-computed position index (O0 optimization)

        Returns:
            List of extracted list blocks
        """
        blocks = []

        # Track fence state with stack for nested fences
        fence_stack: list[tuple[str, int]] = []  # (char, length) tuples

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for fence closing FIRST (if inside fence)
            if fence_stack:
                current_fence_char, current_fence_length = fence_stack[-1]
                if self._is_fence_closing(line, current_fence_char, current_fence_length):
                    fence_stack.pop()
                    i += 1
                    continue

            # Check for fence opening
            fence_info = self._is_fence_opening(line)
            if fence_info:
                fence_char, fence_length, _ = fence_info
                fence_stack.append((fence_char, fence_length))
                i += 1
                continue

            # Skip if inside fence
            if fence_stack:
                i += 1
                continue

            # Try to parse as list item
            item = self._try_parse_list_item(line, i + 1)
            if item:
                # Collect entire list block
                block, end_idx = self._collect_list_block(lines, i)
                blocks.append(block)
                i = end_idx + 1
            else:
                i += 1

        return blocks

    def _try_parse_list_item(self, line: str, line_number: int) -> ListItem | None:
        """
        Try to parse a line as a list item.

        Args:
            line: Line to parse
            line_number: Line number (1-indexed)

        Returns:
            ListItem if successful, None otherwise
        """
        # O3: Use pre-compiled patterns with early termination
        # Checkbox pattern (must check first as it's a subset of bullet)
        checkbox_match = self.CHECKBOX_PATTERN.match(line)
        if checkbox_match:
            indent, marker, checked, content = checkbox_match.groups()
            return ListItem(
                content=content,
                marker=f"{marker} [{checked}]",
                depth=len(indent) // 2,
                line_number=line_number,
                list_type=ListType.CHECKBOX,
                is_checked=(checked.lower() == "x"),
            )

        # Numbered list pattern
        numbered_match = self.NUMBERED_PATTERN.match(line)
        if numbered_match:
            indent, marker, content = numbered_match.groups()
            return ListItem(
                content=content,
                marker=marker,
                depth=len(indent) // 2,
                line_number=line_number,
                list_type=ListType.NUMBERED,
                is_checked=None,
            )

        # Bullet list pattern
        bullet_match = self.BULLET_PATTERN.match(line)
        if bullet_match:
            indent, marker, content = bullet_match.groups()
            return ListItem(
                content=content,
                marker=marker,
                depth=len(indent) // 2,
                line_number=line_number,
                list_type=ListType.BULLET,
                is_checked=None,
            )

        return None

    def _collect_list_block(self, lines: list[str], start_idx: int) -> tuple[ListBlock, int]:
        """Collect an entire list block starting from start_idx."""
        items = []
        max_depth = 0
        end_idx = start_idx
        first_item_type = None

        i = start_idx
        while i < len(lines):
            line = lines[i]

            # Empty line - check if list continues
            if not line.strip():
                should_continue, new_i = self._should_continue_list(lines, i, first_item_type)
                if should_continue:
                    i = new_i
                    continue
                break

            # Try to parse as list item
            item = self._try_parse_list_item(line, i + 1)
            if item:
                if first_item_type is None:
                    first_item_type = item.list_type
                elif item.list_type != first_item_type:
                    # Type changed - close this block
                    break

                items.append(item)
                max_depth = max(max_depth, item.depth)
                end_idx = i
                i += 1
            elif items:
                # Continuation line
                if line.strip():
                    items[-1].content += "\n" + line.strip()
                    end_idx = i
                i += 1
            else:
                break

        if not items:
            # Return a dummy block that will be filtered out
            dummy_block = ListBlock(
                items=[],
                start_line=start_idx + 1,
                end_line=start_idx + 1,
                list_type=ListType.BULLET,
                max_depth=0,
            )
            return dummy_block, start_idx

        primary_type = self._determine_primary_type(items)
        block = ListBlock(
            items=items,
            start_line=items[0].line_number,
            end_line=end_idx + 1,
            list_type=primary_type,
            max_depth=max_depth,
        )

        return block, end_idx

    def _should_continue_list(
        self, lines: list[str], current_idx: int, first_item_type: ListType | None
    ) -> tuple[bool, int]:
        """Check if list continues after empty line."""
        if current_idx + 1 >= len(lines):
            return False, current_idx

        next_item = self._try_parse_list_item(lines[current_idx + 1], current_idx + 2)
        if not next_item:
            return False, current_idx

        # Check if type changes
        if first_item_type and next_item.list_type != first_item_type:
            return False, current_idx

        # Continue past the empty line
        return True, current_idx + 1

    def _determine_primary_type(self, items: list[ListItem]) -> ListType:
        """Determine predominant list type from items."""
        type_counts: dict[ListType, int] = {}
        for item in items:
            type_counts[item.list_type] = type_counts.get(item.list_type, 0) + 1
        return max(type_counts.keys(), key=lambda k: type_counts[k])

    def get_line_at_position(self, md_text: str, pos: int) -> int:
        """
        Get line number (1-indexed) for character position.
        """
        return md_text[:pos].count("\n") + 1

    def get_position_at_line(self, md_text: str, line: int) -> int:
        """
        Get character position for start of line (1-indexed).
        """
        lines = md_text.split("\n")
        return sum(len(lines[i]) + 1 for i in range(line - 1))

    def _calculate_avg_sentence_length(self, lines: list[str]) -> float:
        """
        Calculate average sentence length in characters.

        Simple heuristic: split on periods followed by space or end of line.
        Filters out empty sentences and normalizes to typical technical writing.

        Args:
            lines: Pre-split document lines (O1 optimization)

        Returns:
            Average sentence length in characters, 0.0 if no sentences found
        """
        # Reconstruct text from lines for sentence analysis
        text = "\n".join(lines)
        if not text:
            return 0.0

        # Split on period followed by space/newline/end
        sentences = [s.strip() for s in text.split(".") if s.strip()]

        if not sentences:
            return 0.0

        total_length = sum(len(s) for s in sentences)
        return total_length / len(sentences)


# ============================================================================
# Module-Level Parser Singleton (Performance Optimization)
# ============================================================================
# Singleton parser instance to avoid repeated instantiation and regex compilation.
# Parser is stateless - all methods are pure functions safe for concurrent use.
# Estimated impact: 3-5 second reduction in test suite runtime.

_parser_singleton = None


def get_parser() -> Parser:
    """
    Get the singleton Parser instance.

    Returns:
        Shared Parser instance
    """
    global _parser_singleton
    if _parser_singleton is None:
        _parser_singleton = Parser()
    return _parser_singleton
