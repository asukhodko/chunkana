"""
Metadata recalculator for post-processing consistency.

Recalculates derived metadata fields after all post-processing operations
(dangling header fix, chunk merging) to ensure consistency.

v2: New component for section_tags recalculation.
"""

import re

from .types import Chunk


class MetadataRecalculator:
    """
    Recalculates derived metadata fields after post-processing.

    This component ensures that metadata like section_tags accurately
    reflects the actual content of each chunk after operations like
    dangling header fixes and chunk merging.
    """

    def __init__(self, header_levels: tuple[int, ...] = (3, 4)):
        """
        Initialize the recalculator.

        Args:
            header_levels: Header levels to extract for section_tags (default: 3, 4)
        """
        self.header_levels = header_levels

    def recalculate_all(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Recalculate all derived metadata fields.

        Should be called AFTER all post-processing operations:
        - After HeaderProcessor.prevent_dangling_headers()
        - After ChunkMerger.merge_small_chunks()

        Args:
            chunks: List of chunks to process

        Returns:
            Same chunks with recalculated metadata
        """
        chunks = self._recalculate_section_tags(chunks)
        return chunks

    def _recalculate_section_tags(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Recalculate section_tags based on actual chunk content.

        For each chunk:
        1. Extract all headers (level 3-4) from content
        2. Update section_tags to match extracted headers

        Args:
            chunks: List of chunks to process

        Returns:
            Chunks with updated section_tags
        """
        for chunk in chunks:
            headers = self._extract_headers_from_content(chunk.content)
            chunk.metadata["section_tags"] = headers

            # Also store for debugging/validation
            if headers:
                chunk.metadata["headers_in_content"] = headers

        return chunks

    def _extract_headers_from_content(self, content: str) -> list[str]:
        """
        Extract header texts from chunk content.

        Extracts headers of levels specified in header_levels (default: 3, 4).

        Args:
            content: Chunk content text

        Returns:
            List of header texts (without # markers)
        """
        headers = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check for header pattern (### or ####)
            match = re.match(r"^(#{3,4})\s+(.+)$", line)
            if match:
                header_text = match.group(2).strip()
                headers.append(header_text)

        return headers

    def validate_section_tags_consistency(self, chunks: list[Chunk]) -> list[str]:
        """
        Validate that section_tags match actual content.

        Returns list of validation errors (empty if all valid).

        Args:
            chunks: List of chunks to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        for i, chunk in enumerate(chunks):
            section_tags = chunk.metadata.get("section_tags", [])
            actual_headers = self._extract_headers_from_content(chunk.content)

            # Check that all section_tags are in content
            for tag in section_tags:
                if tag not in actual_headers:
                    chunk_index = chunk.metadata.get("chunk_index", i)
                    errors.append(f"Chunk {chunk_index}: section_tag '{tag}' not found in content")

            # Check that all headers in content are in section_tags
            for header in actual_headers:
                if header not in section_tags:
                    chunk_index = chunk.metadata.get("chunk_index", i)
                    errors.append(
                        f"Chunk {chunk_index}: header '{header}' in content but not in section_tags"
                    )

        return errors

    def validate_in_debug_mode(self, chunks: list[Chunk], debug: bool = False) -> list[Chunk]:
        """
        Validate section_tags consistency in debug mode.

        When debug=True, logs warnings for any inconsistencies between
        section_tags and actual content headers.

        Args:
            chunks: List of chunks to validate
            debug: Whether to perform validation and log warnings

        Returns:
            Same chunks (unmodified)
        """
        if not debug:
            return chunks

        import logging

        logger = logging.getLogger(__name__)

        errors = self.validate_section_tags_consistency(chunks)
        for error in errors:
            logger.warning(f"section_tags inconsistency: {error}")

        return chunks
