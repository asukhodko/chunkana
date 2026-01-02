"""
Hierarchical chunking support for markdown_chunker v2.

Provides parent-child relationships and navigation methods for chunks.
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .types import Chunk


@dataclass
class HierarchicalChunkingResult:
    """
    Result of hierarchical chunking with navigation methods.

    Provides O(1) navigation between chunks via parent-child-sibling relationships.
    All chunks stored flat; hierarchy exists in metadata only.

    Attributes:
        chunks: All chunks including root document chunk
        root_id: ID of document-level chunk
        strategy_used: Name of chunking strategy applied
        _index: Internal index for O(1) chunk lookup by ID
    """

    chunks: List[Chunk]
    root_id: str
    strategy_used: str
    _index: Dict[str, Chunk] = field(default_factory=dict, repr=False, init=False)

    def __post_init__(self) -> None:
        """Build index for O(1) lookups."""
        self._index = {
            c.metadata.get("chunk_id"): c
            for c in self.chunks
            if c.metadata.get("chunk_id")
        }

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """
        Get chunk by ID with O(1) lookup.

        Args:
            chunk_id: Unique chunk identifier

        Returns:
            Chunk if found, None otherwise
        """
        return self._index.get(chunk_id)

    def get_children(self, chunk_id: str) -> List[Chunk]:
        """
        Get all child chunks of given chunk.

        Args:
            chunk_id: Parent chunk ID

        Returns:
            List of child chunks (empty if no children or chunk not found)
        """
        chunk = self.get_chunk(chunk_id)
        if not chunk:
            return []

        children_ids = chunk.metadata.get("children_ids", [])
        return [self.get_chunk(cid) for cid in children_ids if self.get_chunk(cid)]

    def get_parent(self, chunk_id: str) -> Optional[Chunk]:
        """
        Get parent chunk of given chunk.

        Args:
            chunk_id: Child chunk ID

        Returns:
            Parent chunk if found, None if root or chunk not found
        """
        chunk = self.get_chunk(chunk_id)
        if not chunk:
            return None

        parent_id = chunk.metadata.get("parent_id")
        return self.get_chunk(parent_id) if parent_id else None

    def get_ancestors(self, chunk_id: str) -> List[Chunk]:
        """
        Get all ancestor chunks from parent to root.

        Args:
            chunk_id: Starting chunk ID

        Returns:
            List of ancestors ordered from immediate parent to root
        """
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

    def get_siblings(self, chunk_id: str) -> List[Chunk]:
        """
        Get all sibling chunks (including self).

        Siblings are chunks with same parent, ordered by start_line.

        Args:
            chunk_id: Chunk ID

        Returns:
            List of siblings including self
        """
        chunk = self.get_chunk(chunk_id)
        if not chunk:
            return []

        parent_id = chunk.metadata.get("parent_id")
        if not parent_id:
            return [chunk]  # Root has no siblings

        return self.get_children(parent_id)

    def get_flat_chunks(self) -> List[Chunk]:
        """
        Get only leaf chunks for backward-compatible retrieval.

        Leaf chunks have no children OR have significant content.
        This enables systems that don't support hierarchy to work
        with hierarchical results while preserving all content.

        Logs warnings if any content would be lost during filtering.

        Returns:
            List of leaf chunks only
        """
        leaf_chunks = []
        lost_content_count = 0

        for chunk in self.chunks:
            is_leaf = chunk.metadata.get("is_leaf", True)

            if is_leaf:
                leaf_chunks.append(chunk)
            else:
                # Check if we're filtering out content (should not happen)
                # This is a safety check to detect bugs in leaf detection
                chunk_id = chunk.metadata.get("chunk_id", "unknown")
                header_path = chunk.metadata.get("header_path", "unknown")

                # Simple content check: non-empty after stripping
                content = chunk.content.strip()
                if content and len(content) > 50:  # Minimal threshold
                    lost_content_count += 1
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Content preservation issue: Chunk {chunk_id} "
                        f"at '{header_path}' has content but is_leaf=False. "
                        f"This should not happen with current implementation."
                    )

        if lost_content_count > 0:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Content loss detected: {lost_content_count} chunks with content "
                f"were filtered out. This indicates a bug in leaf detection."
            )

        return leaf_chunks

    def get_by_level(self, level: int) -> List[Chunk]:
        """
        Get all chunks at specific hierarchy level.

        Levels: 0=document, 1=section, 2=subsection, 3=paragraph

        Args:
            level: Hierarchy level (0-3)

        Returns:
            List of chunks at specified level
        """
        return [c for c in self.chunks if c.metadata.get("hierarchy_level") == level]

    def to_tree_dict(self) -> Dict:
        """
        Convert hierarchy to tree dictionary for serialization.

        Uses IDs instead of object references to avoid circular refs.
        Safe for JSON serialization.

        Returns:
            Nested dictionary representing tree structure
        """

        def build_node(chunk_id: str) -> Dict:
            chunk = self.get_chunk(chunk_id)
            if not chunk:
                return {}

            content_preview = chunk.content[:100]
            if len(chunk.content) > 100:
                content_preview += "..."

            return {
                "id": chunk_id,
                "content_preview": content_preview,
                "header_path": chunk.metadata.get("header_path", ""),
                "level": chunk.metadata.get("hierarchy_level", 0),
                "children": [
                    build_node(cid) for cid in chunk.metadata.get("children_ids", [])
                ],
            }

        return build_node(self.root_id)


class HierarchyBuilder:
    """
    Builds hierarchical relationships between chunks.

    Takes flat chunk list and creates parent-child-sibling links
    using existing header_path metadata. Maintains C901 complexity < 10
    through method decomposition.
    """

    def __init__(
        self, include_document_summary: bool = True, validate_chains: bool = True
    ):
        """
        Initialize hierarchy builder.

        Args:
            include_document_summary: Whether to create root document chunk
            validate_chains: Whether to validate sibling chains (default True)
        """
        self.include_document_summary = include_document_summary
        self.validate_chains = validate_chains

    def build(
        self, chunks: List[Chunk], original_text: str
    ) -> HierarchicalChunkingResult:
        """
        Build hierarchy from flat chunks. Complexity: < 8 (orchestration only).

        Args:
            chunks: Flat list of chunks from MarkdownChunker
            original_text: Original document text for summary generation

        Returns:
            HierarchicalChunkingResult with navigation methods
        """
        if not chunks:
            return HierarchicalChunkingResult([], "", "none")

        # Step 1: Assign unique IDs
        self._assign_ids(chunks)

        # Step 2: Create root chunk if enabled
        all_chunks = list(chunks)
        root_chunk = None
        if self.include_document_summary:
            root_chunk = self._create_root_chunk(original_text, chunks)
            all_chunks.insert(0, root_chunk)

        # Step 3: Build parent-child relationships
        self._build_parent_child_links(all_chunks, root_chunk)

        # Step 4: Build sibling relationships
        self._build_sibling_links(all_chunks)

        # Step 5: Assign hierarchy levels (MUST come after parent-child links)
        # Fix #2: Calculate based on tree depth, not header_level
        self._assign_hierarchy_levels(all_chunks, root_chunk)

        # Step 6: Mark leaf chunks
        self._mark_leaves(all_chunks)

        # Step 7: Validate relationships (optional)
        if self.validate_chains:
            self._validate_parent_child_counts(all_chunks)
            self._validate_sibling_chains(all_chunks)

        root_id = (
            root_chunk.metadata["chunk_id"]
            if root_chunk
            else chunks[0].metadata["chunk_id"]
        )
        strategy = chunks[0].metadata.get("strategy", "unknown") if chunks else "none"

        return HierarchicalChunkingResult(all_chunks, root_id, strategy)

    def _generate_id(self, content: str, index: int) -> str:
        """
        Generate short unique ID. Complexity: < 5.

        Uses 8-char SHA256 hash for space efficiency vs UUID.

        Args:
            content: Chunk content
            index: Chunk position

        Returns:
            8-character hex ID
        """
        data = f"{content[:50]}:{index}".encode()
        return hashlib.sha256(data).hexdigest()[:8]

    def _assign_ids(self, chunks: List[Chunk]) -> None:
        """
        Assign chunk_id to all chunks. Complexity: < 5.

        Args:
            chunks: List of chunks to assign IDs
        """
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = self._generate_id(chunk.content, i)

    def _create_root_chunk(self, text: str, chunks: List[Chunk]) -> Chunk:
        """
        Create document-level root chunk. Complexity: < 8.

        Fix #1: Root as document container with header_path="/"
        Fix #5: Extract meaningful summary, not preamble duplication
        Fix #7: Add strategy field to root chunk

        Args:
            text: Original document text
            chunks: Existing chunks for extracting title

        Returns:
            Root chunk with document summary
        """
        # Extract document title
        title = self._extract_document_title(chunks)

        # Extract document summary (not preamble duplication)
        summary = self._extract_document_summary(chunks)

        root_chunk = Chunk(
            content=f"# {title}\n\n{summary}",
            start_line=1,
            end_line=chunks[-1].end_line if chunks else 1,
            metadata={
                "chunk_id": self._generate_id(title, -1),
                "content_type": "document",
                "header_path": "/",  # Fix #1: Root has unique path
                "header_level": 0,
                "parent_id": None,
                "children_ids": [],
                "hierarchy_level": 0,
                "is_root": True,
                "strategy": "hierarchical",  # Fix #7: Add strategy field
            },
        )
        return root_chunk

    def _build_parent_child_links(
        self, chunks: List[Chunk], root_chunk: Optional[Chunk]
    ) -> None:
        """
        Build parent-child links via header_path. Complexity: < 10.

        Args:
            chunks: All chunks including root
            root_chunk: Root chunk if created
        """
        # Index by header_path for O(1) parent lookup
        path_to_chunk: Dict[str, Chunk] = {}
        for chunk in chunks:
            hp = chunk.metadata.get("header_path", "")
            if hp:
                path_to_chunk[hp] = chunk

        for chunk in chunks:
            if chunk.metadata.get("is_root"):
                continue

            hp = chunk.metadata.get("header_path", "")

            # Preamble is child of root
            if not hp or hp == "/__preamble__":
                if root_chunk:
                    chunk.metadata["parent_id"] = root_chunk.metadata["chunk_id"]
                    root_chunk.metadata["children_ids"].append(
                        chunk.metadata["chunk_id"]
                    )
                continue

            # Find parent by walking up path segments
            parts = hp.strip("/").split("/")
            parent_found = False

            for i in range(len(parts) - 1, 0, -1):
                parent_path = "/" + "/".join(parts[:i])
                if parent_path in path_to_chunk:
                    parent = path_to_chunk[parent_path]
                    chunk.metadata["parent_id"] = parent.metadata["chunk_id"]
                    parent.metadata.setdefault("children_ids", []).append(
                        chunk.metadata["chunk_id"]
                    )
                    parent_found = True
                    break

            # Orphans link to root
            if not parent_found and root_chunk:
                chunk.metadata["parent_id"] = root_chunk.metadata["chunk_id"]
                root_chunk.metadata["children_ids"].append(chunk.metadata["chunk_id"])

    def _build_sibling_links(self, chunks: List[Chunk]) -> None:
        """
        Build prev/next sibling links. Complexity: < 7.

        Args:
            chunks: All chunks with parent_id assigned
        """
        # Group by parent_id
        siblings_by_parent: Dict[str, List[Chunk]] = {}
        for chunk in chunks:
            parent_id = chunk.metadata.get("parent_id")
            if parent_id:
                siblings_by_parent.setdefault(parent_id, []).append(chunk)

        # Link siblings within each group
        for parent_id, sibs in siblings_by_parent.items():
            sibs.sort(key=lambda c: c.start_line)
            for i, chunk in enumerate(sibs):
                if i > 0:
                    chunk.metadata["prev_sibling_id"] = sibs[i - 1].metadata["chunk_id"]
                if i < len(sibs) - 1:
                    chunk.metadata["next_sibling_id"] = sibs[i + 1].metadata["chunk_id"]

    def _assign_hierarchy_levels(
        self, chunks: List[Chunk], root_chunk: Optional[Chunk] = None
    ) -> None:
        """
        Assign hierarchy_level based on tree depth from root. Complexity: < 7.

        Fix #2: Calculate actual tree depth instead of mapping header_level.
        Uses BFS traversal to assign levels:
        - Root: level 0
        - Root's children (preamble, H1 sections): level 1
        - H2 subsections: level 2
        - H3+ subsections: level 3

        Args:
            chunks: All chunks
            root_chunk: Root chunk if created
        """
        # Build chunk lookup map
        chunk_map = {c.metadata["chunk_id"]: c for c in chunks}

        # Find starting point (root or first chunk)
        if root_chunk and root_chunk.metadata.get("chunk_id") in chunk_map:
            start_id = root_chunk.metadata["chunk_id"]
        elif chunks:
            start_id = chunks[0].metadata["chunk_id"]
        else:
            return

        # BFS traversal from root
        queue = [(start_id, 0)]  # (chunk_id, level)
        visited = set()

        while queue:
            current_id, current_level = queue.pop(0)

            if current_id in visited:
                continue
            visited.add(current_id)

            current_chunk = chunk_map.get(current_id)
            if not current_chunk:
                continue

            # Assign level
            current_chunk.metadata["hierarchy_level"] = current_level

            # Add children to queue
            for child_id in current_chunk.metadata.get("children_ids", []):
                if child_id not in visited:
                    queue.append((child_id, current_level + 1))

    def _mark_leaves(self, chunks: List[Chunk]) -> None:
        """
        Mark leaf chunks using hybrid criteria. Complexity: < 5.

        A chunk is a leaf if:
        - It has no children, OR
        - It has children but also contains significant content of its own

        This handles split sections where parent has content before the split,
        ensuring no content is lost in leaf-only filtering.

        Args:
            chunks: All chunks
        """
        for chunk in chunks:
            children = chunk.metadata.get("children_ids", [])
            has_children = len(children) > 0

            if not has_children:
                # No children = definitely a leaf
                chunk.metadata["is_leaf"] = True
            else:
                # Has children - check if parent also has own content
                has_content = self._has_significant_content(chunk)
                chunk.metadata["is_leaf"] = has_content

    def _has_significant_content(self, chunk: Chunk) -> bool:
        """
        Check if chunk has significant content beyond headers. Complexity: < 5.

        "Significant" means:
        - More than just section headers
        - More than 100 characters of actual text
        - Not just whitespace

        This is used to identify content-bearing parent chunks that should
        be included in leaf-only results despite having children.

        Args:
            chunk: Chunk to analyze

        Returns:
            True if chunk has significant non-header content, False otherwise
        """
        content = chunk.content.strip()

        if not content:
            return False

        # Remove all ATX-style headers (# to ######)
        content_without_headers = re.sub(
            r"^#{1,6}\s+.*$", "", content, flags=re.MULTILINE  # Match any level header
        )

        # Remove excess whitespace and measure remaining text
        text_only = re.sub(r"\s+", " ", content_without_headers).strip()

        # Threshold: 100 chars of non-header content
        return len(text_only) > 100

    def _extract_document_title(self, chunks: List[Chunk]) -> str:
        """
        Extract document title for root chunk. Complexity: < 5.

        Priority:
        1. First H1 header text
        2. "Document" as fallback

        Args:
            chunks: All chunks

        Returns:
            Document title string
        """
        for chunk in chunks:
            if chunk.metadata.get("header_level") == 1:
                # Get header text from content (first line after #)
                lines = chunk.content.strip().split("\n")
                for line in lines:
                    if line.strip().startswith("#"):
                        return line.strip().lstrip("#").strip()
        return "Document"

    def _is_url_line(self, line: str) -> bool:
        """
        Check if line contains primarily URL content. Complexity: < 5.

        Detects:
        1. Lines starting with http:// or https://
        2. Label-colon-URL pattern (e.g., "Description: https://...")
        3. Lines where URL takes up majority of content (>60% ratio)

        Args:
            line: Text line to check

        Returns:
            True if line is URL-based, False otherwise
        """
        line = line.strip()
        if not line:
            return False

        # Direct URL start
        if line.startswith(("http://", "https://")):
            return True

        # Label: URL pattern
        if re.match(r"^[^:]+:\s*https?://", line):
            return True

        # URL dominance check (>60% of line is URL)
        url_match = re.search(r"https?://\S+", line)
        if url_match:
            url_portion = url_match.group(0)
            if len(url_portion) / len(line) > 0.6:
                return True

        return False

    def _extract_document_summary(self, chunks: List[Chunk]) -> str:
        """
        Extract document summary for root chunk. Complexity: < 8.

        Fix #5: Extract meaningful summary, avoid preamble URL duplication.

        Priority:
        1. First paragraph from preamble (if exists and not just URLs)
        2. First paragraph from first H1 section (skip URLs and headers)
        3. Empty string

        Args:
            chunks: All chunks

        Returns:
            Summary text
        """
        # Check preamble
        preamble = next(
            (c for c in chunks if c.metadata.get("content_type") == "preamble"), None
        )
        if preamble:
            content = preamble.content
            # Skip if it's just URLs
            lines = content.strip().split("\n")
            non_url_lines = [line for line in lines if not self._is_url_line(line)]
            if non_url_lines:
                # Take first paragraph (up to 200 chars)
                first_para = non_url_lines[0][:200]
                return first_para

        # Fallback to first H1 section's first paragraph
        first_h1 = next(
            (c for c in chunks if c.metadata.get("header_level") == 1), None
        )
        if first_h1:
            content = first_h1.content
            if content:
                # Get first paragraph after header line, skip URLs
                paragraphs = content.split("\n\n")
                for para in paragraphs:
                    # Skip header line and URL lines
                    if para.strip().startswith("#"):
                        continue
                    if self._is_url_line(para):
                        continue
                    # Found non-URL paragraph
                    return para[:200]

        # Empty content as last resort
        return ""

    def _validate_parent_child_counts(self, chunks: List[Chunk]) -> None:
        """
        Validate parent-child relationship counts. Complexity: < 6.

        Fix #3: Ensure children_ids count matches actual children.

        Args:
            chunks: All chunks

        Raises:
            ValueError: If validation fails
        """
        for chunk in chunks:
            chunk_id = chunk.metadata["chunk_id"]
            declared_count = len(chunk.metadata.get("children_ids", []))

            # Count actual children
            actual_children = [
                c for c in chunks if c.metadata.get("parent_id") == chunk_id
            ]

            if declared_count != len(actual_children):
                raise ValueError(
                    f"Chunk {chunk_id} declares {declared_count} children "
                    f"but has {len(actual_children)} actual children"
                )

    def _validate_sibling_chains(self, chunks: List[Chunk]) -> None:
        """
        Validate sibling chain integrity. Complexity: < 9.

        Fix #8: Ensure sibling chains are complete and continuous.

        Args:
            chunks: All chunks

        Raises:
            ValueError: If validation fails
        """
        chunk_map = {c.metadata["chunk_id"]: c for c in chunks}
        errors = []

        # Group siblings by parent
        parent_groups = self._group_siblings_by_parent(chunks)

        # Validate each sibling group
        for parent_id, siblings in parent_groups.items():
            if len(siblings) <= 1:
                continue

            group_errors = self._validate_sibling_group(parent_id, siblings, chunk_map)
            errors.extend(group_errors)

        if errors:
            error_msg = "Sibling chain validation failed:\n" + "\n".join(errors)
            raise ValueError(error_msg)

    def _group_siblings_by_parent(self, chunks: List[Chunk]) -> Dict[str, List[Chunk]]:
        """
        Group chunks by their parent_id. Complexity: < 4.

        Args:
            chunks: All chunks

        Returns:
            Dictionary mapping parent_id to list of children
        """
        parent_groups: Dict[str, List[Chunk]] = {}
        for chunk in chunks:
            parent_id = chunk.metadata.get("parent_id")
            if parent_id:
                parent_groups.setdefault(parent_id, []).append(chunk)
        return parent_groups

    def _validate_sibling_group(
        self, parent_id: str, siblings: List[Chunk], chunk_map: Dict[str, Chunk]
    ) -> List[str]:
        """
        Validate single sibling group. Complexity: < 8.

        Args:
            parent_id: Parent chunk ID
            siblings: List of sibling chunks
            chunk_map: Mapping of chunk_id to Chunk

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Find first sibling
        first_siblings = [
            s for s in siblings if s.metadata.get("prev_sibling_id") is None
        ]
        if len(first_siblings) != 1:
            errors.append(
                f"Parent {parent_id}: Expected 1 first sibling, "
                f"found {len(first_siblings)}"
            )
            return errors

        # Traverse and validate chain
        chain_errors, chain_length = self._traverse_sibling_chain(
            first_siblings[0], chunk_map
        )
        errors.extend(chain_errors)

        # Verify chain length
        if chain_length != len(siblings):
            errors.append(
                f"Parent {parent_id}: Chain length {chain_length} != "
                f"sibling count {len(siblings)}"
            )

        return errors

    def _traverse_sibling_chain(
        self, start_chunk: Chunk, chunk_map: Dict[str, Chunk]
    ) -> tuple:
        """
        Traverse sibling chain and validate links. Complexity: < 7.

        Args:
            start_chunk: First sibling in chain
            chunk_map: Mapping of chunk_id to Chunk

        Returns:
            Tuple of (error_messages, chain_length)
        """
        errors = []
        current = start_chunk
        chain_length = 1
        visited = {current.metadata["chunk_id"]}

        while current.metadata.get("next_sibling_id"):
            next_id = current.metadata["next_sibling_id"]
            next_chunk = chunk_map.get(next_id)

            if not next_chunk:
                errors.append(
                    f"Chunk {current.metadata['chunk_id']}: "
                    f"next_sibling {next_id} not found"
                )
                break

            # Verify backward link
            prev_id = current.metadata["chunk_id"]
            if next_chunk.metadata.get("prev_sibling_id") != prev_id:
                errors.append(
                    f"Chain broken: {prev_id}.next = {next_id}, "
                    f"but {next_id}.prev = "
                    f"{next_chunk.metadata.get('prev_sibling_id')}"
                )

            # Check for cycles
            if next_id in visited:
                errors.append(f"Cycle in sibling chain at {next_id}")
                break

            visited.add(next_id)
            current = next_chunk
            chain_length += 1

        return errors, chain_length
