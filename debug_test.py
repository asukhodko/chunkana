#!/usr/bin/env python3

from chunkana import ChunkConfig, chunk_markdown

# Проблемный документ из теста
doc = """# Section 1

1. aaaaaaaaaaaaaaaaaaaa
2. aaaaaaaaaaaaaaaaaaaa
3. aaaaaaaaaaaaaaaaaaaa
4. aaaaaaaaaaaaaaaaaaaa
5. aaaaaaaaaaaaaaaaaaaa
6. aaaaaaaaaaaaaaaaaaaa
   aaaaaaaaaa

## Section 2

1. aaaaaaaaaaaaaaaaaaaa
2. aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
   aaaaaaaaaa
3. aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
   aaaaaaaaaaaaaaaaaaa
4. aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
   aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
5. aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
6. aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
7. aaaaaaaaaaaaaaaaaaaa
8. aaaaaaaaaaaaaaaaaaaa

# Section 3

1. aaaaaaaaaaaaaaaaaaaa
2. aaaaaaaaaaaaaaaaaaaa
3. aaaaaaaaaaaaaaaaaaaa"""

config = ChunkConfig(max_chunk_size=400, overlap_size=50)
chunks = chunk_markdown(doc, config)

print(f"Total chunks: {len(chunks)}")
print()

# Group split chunks
split_groups = {}
for chunk in chunks:
    if "split_index" in chunk.metadata:
        header_path = chunk.metadata.get("header_path", "")
        if header_path not in split_groups:
            split_groups[header_path] = []
        split_groups[header_path].append(chunk)

print(f"Split groups: {len(split_groups)}")

# Verify total size is reasonable
for header_path, group in split_groups.items():
    if len(group) > 1:
        total_content_size = sum(len(c.content) for c in group)
        original_size = group[0].metadata.get("original_section_size", 0)

        print(f"\nHeader path: {header_path}")
        print(f"Group size: {len(group)} chunks")
        print(f"Total content size: {total_content_size}")
        print(f"Original size: {original_size}")

        if original_size > 0:
            ratio = total_content_size / original_size
            print(f"Ratio: {ratio:.4f}")

            # Показать содержимое чанков
            for i, chunk in enumerate(group):
                print(f"\nChunk {i} (split_index={chunk.metadata.get('split_index')}):")
                print(f"  Size: {len(chunk.content)}")
                print(f"  Content preview: {repr(chunk.content[:100])}")
