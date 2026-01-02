"""
Table grouping module for markdown_chunker v2.

Groups related tables based on proximity and section boundaries
to improve retrieval quality for table-heavy documents.
"""

from dataclasses import dataclass
from typing import List, Optional

from .types import Header, TableBlock


@dataclass
class TableGroupingConfig:
    """
    Configuration for table grouping behavior.

    Attributes:
        max_distance_lines: Maximum lines between tables to consider them related.
            Tables further apart will not be grouped. Default: 10
        max_grouped_tables: Maximum number of tables in a single group.
            Prevents overly large groups. Default: 5
        max_group_size: Maximum combined size (chars) for grouped tables.
            Groups exceeding this will be split. Default: 5000
        require_same_section: Only group tables within the same header section.
            If True, tables separated by headers will not be grouped. Default: True
    """

    max_distance_lines: int = 10
    max_grouped_tables: int = 5
    max_group_size: int = 5000
    require_same_section: bool = True

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_distance_lines < 0:
            raise ValueError(
                f"max_distance_lines must be non-negative, "
                f"got {self.max_distance_lines}"
            )

        if self.max_grouped_tables < 1:
            raise ValueError(
                f"max_grouped_tables must be >= 1, got {self.max_grouped_tables}"
            )

        if self.max_group_size < 100:
            raise ValueError(
                f"max_group_size must be >= 100, got {self.max_group_size}"
            )


@dataclass
class TableGroup:
    """
    A group of related tables.

    Attributes:
        tables: Tables in this group
        start_line: First line of the group (1-indexed)
        end_line: Last line of the group (1-indexed)
        content: Combined content including tables and text between them
    """

    tables: List[TableBlock]
    start_line: int
    end_line: int
    content: str

    @property
    def table_count(self) -> int:
        """Number of tables in group."""
        return len(self.tables)

    @property
    def size(self) -> int:
        """Total size in characters."""
        return len(self.content)


class TableGrouper:
    """
    Groups related tables based on proximity and section boundaries.

    Tables are grouped when:
    - They are within max_distance_lines of each other
    - No header separates them (if require_same_section is True)
    - Combined size doesn't exceed max_group_size
    - Group doesn't exceed max_grouped_tables
    """

    def __init__(self, config: Optional[TableGroupingConfig] = None):
        """
        Initialize TableGrouper.

        Args:
            config: Grouping configuration. Uses defaults if None.
        """
        self.config = config or TableGroupingConfig()

    def group_tables(
        self,
        tables: List[TableBlock],
        lines: List[str],
        headers: List[Header],
    ) -> List[TableGroup]:
        """
        Group related tables.

        Args:
            tables: List of tables from parser (sorted by start_line)
            lines: Document lines array
            headers: List of headers from parser

        Returns:
            List of TableGroup objects
        """
        if not tables:
            return []

        if len(tables) == 1:
            return [self._create_single_table_group(tables[0], lines)]

        groups: List[TableGroup] = []
        current_tables: List[TableBlock] = [tables[0]]
        current_size = len(tables[0].content)

        for i in range(1, len(tables)):
            table = tables[i]
            prev_table = tables[i - 1]

            if self._should_group(
                prev_table, table, headers, current_size, len(current_tables)
            ):
                current_tables.append(table)
                current_size += len(table.content)
            else:
                groups.append(self._create_group(current_tables, lines))
                current_tables = [table]
                current_size = len(table.content)

        # Add last group
        if current_tables:
            groups.append(self._create_group(current_tables, lines))

        return groups

    def _create_single_table_group(
        self, table: TableBlock, lines: List[str]
    ) -> TableGroup:
        """Create a group with a single table."""
        content = self._extract_content(table.start_line, table.end_line, lines)
        return TableGroup(
            tables=[table],
            start_line=table.start_line,
            end_line=table.end_line,
            content=content,
        )

    def _create_group(self, tables: List[TableBlock], lines: List[str]) -> TableGroup:
        """Create a group from multiple tables."""
        start_line = tables[0].start_line
        end_line = tables[-1].end_line
        content = self._extract_group_content(tables, lines)
        return TableGroup(
            tables=tables,
            start_line=start_line,
            end_line=end_line,
            content=content,
        )

    def _should_group(
        self,
        prev_table: TableBlock,
        table: TableBlock,
        headers: List[Header],
        current_size: int,
        current_count: int,
    ) -> bool:
        """
        Check if table should be grouped with previous.

        Uses early returns to keep complexity low.
        """
        if not self._check_count_limit(current_count):
            return False

        if not self._check_size_limit(current_size, table):
            return False

        if not self._check_distance(prev_table, table):
            return False

        if not self._check_section_boundary(prev_table, table, headers):
            return False

        return True

    def _check_count_limit(self, current_count: int) -> bool:
        """Check if adding another table would exceed max_grouped_tables."""
        return current_count < self.config.max_grouped_tables

    def _check_size_limit(self, current_size: int, table: TableBlock) -> bool:
        """Check if adding table would exceed max_group_size."""
        return current_size + len(table.content) <= self.config.max_group_size

    def _check_distance(self, prev_table: TableBlock, table: TableBlock) -> bool:
        """Check if tables are within max_distance_lines."""
        distance = table.start_line - prev_table.end_line
        return distance <= self.config.max_distance_lines

    def _check_section_boundary(
        self,
        prev_table: TableBlock,
        table: TableBlock,
        headers: List[Header],
    ) -> bool:
        """Check if there's no header between tables (if require_same_section)."""
        if not self.config.require_same_section:
            return True

        return not self._has_header_between(
            prev_table.end_line, table.start_line, headers
        )

    def _has_header_between(
        self, start_line: int, end_line: int, headers: List[Header]
    ) -> bool:
        """Check if there's a header between two lines."""
        for header in headers:
            if start_line < header.line < end_line:
                return True
        return False

    def _extract_content(self, start_line: int, end_line: int, lines: List[str]) -> str:
        """
        Extract content for a line range.

        Args:
            start_line: Start line (1-indexed)
            end_line: End line (1-indexed)
            lines: Document lines array

        Returns:
            Content string
        """
        return "\n".join(lines[start_line - 1 : end_line])

    def _extract_group_content(self, tables: List[TableBlock], lines: List[str]) -> str:
        """
        Extract content for a table group including text between tables.

        Includes all tables and any text between them.
        Normalizes whitespace between tables to single blank line.

        Args:
            tables: Tables in the group (sorted by start_line)
            lines: Document lines array

        Returns:
            Combined content string

        Requirements: 6.1, 6.2, 6.3
        """
        if not tables:
            return ""

        if len(tables) == 1:
            return self._extract_content(
                tables[0].start_line, tables[0].end_line, lines
            )

        parts: List[str] = []

        for i, table in enumerate(tables):
            # Add table content
            table_content = self._extract_content(
                table.start_line, table.end_line, lines
            )
            parts.append(table_content)

            # Add text between this table and next (if not last)
            if i < len(tables) - 1:
                next_table = tables[i + 1]
                between_content = self._get_text_between_tables(
                    table, next_table, lines
                )
                parts.append(between_content)

        return "\n".join(parts)

    def _get_text_between_tables(
        self,
        table1: TableBlock,
        table2: TableBlock,
        lines: List[str],
    ) -> str:
        """
        Get normalized text between two tables.

        If text is only whitespace, returns single blank line.
        Otherwise returns the text with leading/trailing whitespace trimmed.

        Args:
            table1: First table
            table2: Second table
            lines: Document lines array

        Returns:
            Text between tables (normalized)

        Requirements: 6.3
        """
        # Lines between tables (exclusive)
        start_idx = table1.end_line  # 0-indexed: end_line is 1-indexed
        end_idx = table2.start_line - 1  # 0-indexed: start_line - 1

        if start_idx >= end_idx:
            # No lines between - just add blank line separator
            return ""

        between_lines = lines[start_idx:end_idx]
        between_text = "\n".join(between_lines)

        # Normalize: if only whitespace, return single blank line
        if not between_text.strip():
            return ""

        # Return trimmed content
        return between_text.strip()
