"""
Consolidated type definitions for markdown_chunker v2.

All types in one file - no duplication between parser and chunker.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ListType(Enum):
    """Type of markdown list."""

    BULLET = "bullet"  # -, *, + markers
    NUMBERED = "numbered"  # 1., 2., etc.
    CHECKBOX = "checkbox"  # - [ ], - [x]


class LatexType(Enum):
    """Type of LaTeX formula block."""

    DISPLAY = "display"  # $$...$$
    ENVIRONMENT = "environment"  # \begin{equation}...\end{equation}
    INLINE = "inline"  # $...$ (optional extraction)


@dataclass
class ListItem:
    """
    Represents a single item in a markdown list.

    Attributes:
        content: Item text without marker
        marker: Original markdown marker (e.g., '-', '*', '1.', '- [ ]')
        depth: Nesting level (0 = top-level)
        line_number: Line position in document (1-indexed)
        list_type: Type of list item
        is_checked: For checkbox items: True/False/None
    """

    content: str
    marker: str
    depth: int
    line_number: int
    list_type: ListType
    is_checked: bool | None = None


@dataclass
class ListBlock:
    """
    Represents a contiguous block of list items.

    Attributes:
        items: All items in this list block
        start_line: First line of block (1-indexed)
        end_line: Last line of block (1-indexed)
        list_type: Predominant type in block
        max_depth: Maximum nesting level in block
    """

    items: list[ListItem]
    start_line: int
    end_line: int
    list_type: ListType
    max_depth: int

    @property
    def item_count(self) -> int:
        """Total number of items in block."""
        return len(self.items)

    @property
    def has_nested(self) -> bool:
        """Whether block contains nested items."""
        return self.max_depth > 0


@dataclass
class FencedBlock:
    """
    Represents a fenced code block in markdown.

    Attributes:
        language: Programming language (e.g., 'python', 'javascript')
        content: The code content inside the fences
        start_line: Line number where block starts (1-indexed)
        end_line: Line number where block ends (1-indexed)
        start_pos: Character position in document
        end_pos: Character position in document
        fence_char: The fence character used ('`' for backtick, '~' for tilde)
        fence_length: Number of fence characters (3, 4, 5, etc.)
        is_closed: Whether the fence has a matching closing fence
        context_role: Cached role classification for code-context binding
            (optional, used by enhanced code-context binding feature)
        has_explanation_before: Whether preceding explanation exists
            (optional, used by enhanced code-context binding feature)
        has_explanation_after: Whether following explanation exists
            (optional, used by enhanced code-context binding feature)
    """

    language: str | None
    content: str
    start_line: int
    end_line: int
    start_pos: int = 0
    end_pos: int = 0
    fence_char: str = "`"
    fence_length: int = 3
    is_closed: bool = True
    # Optional fields for code-context binding (backward compatible)
    context_role: str | None = None
    has_explanation_before: bool = False
    has_explanation_after: bool = False


@dataclass
class TableBlock:
    """
    Represents a markdown table.

    Attributes:
        content: Full table content including header and rows
        start_line: Line number where table starts
        end_line: Line number where table ends
        column_count: Number of columns
        row_count: Number of data rows (excluding header)
    """

    content: str
    start_line: int
    end_line: int
    column_count: int = 0
    row_count: int = 0


@dataclass
class Header:
    """
    Represents a markdown header.

    Attributes:
        level: Header level (1-6)
        text: Header text content
        line: Line number (1-indexed)
        pos: Character position in document
    """

    level: int
    text: str
    line: int
    pos: int = 0


@dataclass
class LatexBlock:
    """
    Represents a LaTeX mathematical formula block.

    Attributes:
        content: Complete formula including delimiters
        latex_type: Type of LaTeX block (DISPLAY, ENVIRONMENT, INLINE)
        start_line: Line number where block starts (1-indexed)
        end_line: Line number where block ends (1-indexed)
        start_pos: Character position in document
        end_pos: Character position in document
        environment_name: For ENVIRONMENT type, the environment name
            (e.g., 'equation', 'align', 'gather')
    """

    content: str
    latex_type: LatexType
    start_line: int
    end_line: int
    start_pos: int = 0
    end_pos: int = 0
    environment_name: str | None = None


@dataclass
class ContentAnalysis:
    """
    Result of analyzing a markdown document.

    Contains metrics and extracted elements for strategy selection.
    """

    # Basic metrics
    total_chars: int
    total_lines: int

    # Content ratios
    code_ratio: float  # code_chars / total_chars

    # Element counts
    code_block_count: int
    header_count: int
    max_header_depth: int
    table_count: int
    list_count: int = 0
    list_item_count: int = 0

    # Extracted elements
    code_blocks: list[FencedBlock] = field(default_factory=list)
    headers: list[Header] = field(default_factory=list)
    tables: list[TableBlock] = field(default_factory=list)
    list_blocks: list[ListBlock] = field(default_factory=list)
    latex_blocks: list["LatexBlock"] = field(default_factory=list)

    # Additional metrics
    has_preamble: bool = False
    preamble_end_line: int = 0
    list_ratio: float = 0.0
    max_list_depth: int = 0
    has_checkbox_lists: bool = False
    avg_sentence_length: float = 0.0
    latex_block_count: int = 0
    latex_ratio: float = 0.0

    # O1: Line array optimization (optional, backward compatible)
    # Private field excluded from repr to avoid clutter in debug output
    _lines: list[str] | None = field(default=None, repr=False)

    def get_lines(self) -> list[str] | None:
        """
        Get cached line array if available.

        Returns:
            Cached line array from parser analysis, or None if not available.
            When present, enables strategies to avoid redundant split operations.

        Note:
            This is an internal optimization field. Strategies should fall back
            to splitting md_text if this returns None (backward compatibility).
        """
        return self._lines


@dataclass
class Chunk:
    """
    A chunk of markdown content.

    Attributes:
        content: The text content of the chunk
        start_line: Starting line number (1-indexed) - provides approximate location
            in source document. Line ranges may overlap between adjacent chunks.
            For precise chunk location, use the content text itself.
        end_line: Ending line number (1-indexed) - provides approximate location
            in source document. Line ranges may overlap between adjacent chunks.
            For precise chunk location, use the content text itself.
        metadata: Additional information about the chunk

    Metadata Fields:
        chunk_index (int): Sequential index of chunk in document
        content_type (str): "text" | "code" | "table" | "mixed" | "preamble"
        has_code (bool): Whether chunk contains code blocks
        strategy (str): Strategy name that created this chunk
        header_path (str): Hierarchical path to first header in chunk.
            Format: "/Level1/Level2/Level3" where each segment corresponds
            to a header level (# = 1st segment, ## = 2nd, etc.).
            Special value "/__preamble__" for preamble chunks.
            Empty string only if document has no headers.
        header_level (int): Level of first header in chunk (1-6)
        sub_headers (List[str], optional): Additional header texts within
            the chunk (excluding the first header used for header_path).
            Only present when chunk contains multiple headers.
        small_chunk (bool): True if chunk meets ALL conditions:
            - Size < min_chunk_size
            - Cannot merge with adjacent chunks without exceeding max_chunk_size
            - Chunk is structurally weak (lacks strong headers, multiple paragraphs,
              or sufficient meaningful content)
            Note: Chunks below min_chunk_size that are structurally strong
            (e.g., have level 2-3 headers, multiple paragraphs, or substantial text)
            will NOT be flagged as small_chunk.
        small_chunk_reason (str): Reason for small_chunk flag.
            Currently only "cannot_merge" is used.
        previous_content (str, optional): Last N characters from previous chunk.
            Size of context window determined by overlap_size configuration.
            This is metadata-only context; chunk.content does NOT contain
            duplicated text from previous chunk.
        next_content (str, optional): First N characters from next chunk.
            Size of context window determined by overlap_size configuration.
            This is metadata-only context; chunk.content does NOT contain
            duplicated text from next chunk.
        overlap_size (int, optional): Size of context window (in characters)
            used for previous_content/next_content metadata extraction.
            Does NOT indicate physical text overlap in chunk.content.
    """

    content: str
    start_line: int
    end_line: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate chunk on creation."""
        if self.start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {self.start_line}")
        if self.end_line < self.start_line:
            raise ValueError(
                f"end_line ({self.end_line}) must be >= start_line ({self.start_line})"
            )
        if not self.content.strip():
            raise ValueError("Chunk content cannot be empty or whitespace-only")

    @property
    def size(self) -> int:
        """Size of chunk in characters."""
        return len(self.content)

    @property
    def line_count(self) -> int:
        """Number of lines in chunk."""
        return self.content.count("\n") + 1

    @property
    def is_oversize(self) -> bool:
        """Whether chunk is marked as intentionally oversize."""
        return bool(self.metadata.get("allow_oversize", False))

    @property
    def strategy(self) -> str:
        """Strategy that created this chunk."""
        result = self.metadata.get("strategy", "unknown")
        return str(result) if result is not None else "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "size": self.size,
            "line_count": self.end_line - self.start_line + 1,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Chunk":
        """Create from dictionary."""
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data).__name__}")
        if "content" not in data:
            raise ValueError("Missing required field: content")
        if "start_line" not in data:
            raise ValueError("Missing required field: start_line")
        if "end_line" not in data:
            raise ValueError("Missing required field: end_line")

        return cls(
            content=data["content"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        """Serialize chunk to JSON string."""
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "Chunk":
        """Deserialize chunk from JSON string."""
        import json

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
        return cls.from_dict(data)


@dataclass
class ChunkingMetrics:
    """
    Statistics about chunking results.

    Provides quality metrics for monitoring and tuning.
    """

    total_chunks: int
    avg_chunk_size: float
    std_dev_size: float
    min_size: int
    max_size: int
    undersize_count: int  # chunks < min_chunk_size
    oversize_count: int  # chunks > max_chunk_size

    @classmethod
    def from_chunks(
        cls,
        chunks: list["Chunk"],
        min_chunk_size: int = 512,
        max_chunk_size: int = 4096,
    ) -> "ChunkingMetrics":
        """Calculate metrics from chunk list."""
        if not chunks:
            return cls(0, 0.0, 0.0, 0, 0, 0, 0)

        sizes = [c.size for c in chunks]
        avg = sum(sizes) / len(sizes)
        variance = sum((s - avg) ** 2 for s in sizes) / len(sizes)
        std_dev = variance**0.5

        return cls(
            total_chunks=len(chunks),
            avg_chunk_size=avg,
            std_dev_size=std_dev,
            min_size=min(sizes),
            max_size=max(sizes),
            undersize_count=sum(1 for s in sizes if s < min_chunk_size),
            oversize_count=sum(1 for s in sizes if s > max_chunk_size),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_chunks": self.total_chunks,
            "avg_chunk_size": self.avg_chunk_size,
            "std_dev_size": self.std_dev_size,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "undersize_count": self.undersize_count,
            "oversize_count": self.oversize_count,
        }


@dataclass
class ChunkingResult:
    """
    Result of chunking a document.

    Contains chunks and metadata about the chunking process.
    """

    chunks: list[Chunk]
    strategy_used: str
    processing_time: float = 0.0
    total_chars: int = 0
    total_lines: int = 0

    @property
    def chunk_count(self) -> int:
        """Number of chunks produced."""
        return len(self.chunks)

    @property
    def total_output_size(self) -> int:
        """Total size of all chunks."""
        return sum(c.size for c in self.chunks)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "chunks": [c.to_dict() for c in self.chunks],
            "strategy_used": self.strategy_used,
            "processing_time": self.processing_time,
            "total_chars": self.total_chars,
            "total_lines": self.total_lines,
            "chunk_count": self.chunk_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChunkingResult":
        """Create from dictionary."""
        chunks = [Chunk.from_dict(c) for c in data.get("chunks", [])]
        return cls(
            chunks=chunks,
            strategy_used=data.get("strategy_used", "unknown"),
            processing_time=data.get("processing_time", 0.0),
            total_chars=data.get("total_chars", 0),
            total_lines=data.get("total_lines", 0),
        )
