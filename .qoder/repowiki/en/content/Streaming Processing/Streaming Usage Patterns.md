# Streaming Usage Patterns

<cite>
**Referenced Files in This Document**   
- [StreamingConfig](file://src/chunkana/streaming/config.py)
- [StreamingChunker](file://src/chunkana/streaming/streaming_chunker.py)
- [BufferManager](file://src/chunkana/streaming/buffer_manager.py)
- [SplitDetector](file://src/chunkana/streaming/split_detector.py)
- [FenceTracker](file://src/chunkana/streaming/fence_tracker.py)
- [chunk_file_streaming](file://src/chunkana/api.py#L228-L271)
- [MarkdownChunker.chunk_file_streaming](file://src/chunkana/chunker.py#L249-L274)
- [MarkdownChunker.chunk_stream](file://src/chunkana/chunker.py#L275-L299)
- [render_json](file://src/chunkana/renderers/formatters.py#L15-L27)
- [render_dify_style](file://src/chunkana/renderers/formatters.py#L56-L84)
- [render_with_embedded_overlap](file://src/chunkana/renderers/formatters.py#L87-L116)
- [render_with_prev_overlap](file://src/chunkana/renderers/formatters.py#L119-L145)
- [test_streaming.py](file://tests/unit/test_streaming.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Core Streaming Components](#core-streaming-components)
3. [Processing Large Files from Disk](#processing-large-files-from-disk)
4. [Handling Network Streams](#handling-network-streams)
5. [Generator-Based Source Processing](#generator-based-source-processing)
6. [Integration with RAG Pipelines](#integration-with-rag-pipelines)
7. [Error Handling Strategies](#error-handling-strategies)
8. [Renderer Integration and Output Formats](#renderer-integration-and-output-formats)
9. [Performance Optimization](#performance-optimization)
10. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
11. [Test Case Validation](#test-case-validation)

## Introduction

Chunkana's streaming API provides memory-efficient processing for large markdown files, enabling chunking of documents exceeding 10MB without loading the entire file into memory. The streaming architecture processes files in buffer windows with configurable overlap, maintaining critical invariants such as line coverage, atomic block preservation, and monotonic ordering. This document details practical usage patterns for the streaming API, covering various input sources, error handling strategies, renderer integration, performance optimization, and common pitfalls.

**Section sources**
- [StreamingChunker](file://src/chunkana/streaming/streaming_chunker.py#L1-L99)
- [chunk_file_streaming](file://src/chunkana/api.py#L228-L271)

## Core Streaming Components

The streaming architecture consists of several key components that work together to enable memory-efficient processing:

```mermaid
classDiagram
class StreamingConfig {
+buffer_size : int = 100_000
+overlap_lines : int = 20
+max_memory_mb : int = 100
+safe_split_threshold : float = 0.8
}
class StreamingChunker {
-chunk_config : ChunkConfig
-streaming_config : StreamingConfig
-base_chunker : MarkdownChunker
-buffer_manager : BufferManager
-split_detector : SplitDetector
+chunk_file(file_path : str) Iterator[Chunk]
+chunk_stream(stream : TextIOBase) Iterator[Chunk]
-_process_window(buffer : list[str], overlap : list[str], window_index : int, start_chunk_index : int) Iterator[Chunk]
}
class BufferManager {
-config : StreamingConfig
+read_windows(stream : TextIOBase) Iterator[tuple[list[str], list[str], int]]
-_extract_overlap(buffer : list[str]) list[str]
}
class SplitDetector {
-threshold : float
+find_split_point(buffer : list[str], fence_tracker : FenceTracker) int
-_try_split_at_header(buffer : list[str], start_idx : int) int | None
-_try_split_at_paragraph(buffer : list[str], start_idx : int) int | None
-_try_split_at_newline(buffer : list[str], start_idx : int, fence_tracker : FenceTracker) int | None
-_fallback_split(start_idx : int) int
}
class FenceTracker {
-_fence_stack : list[tuple[str, int]]
-_fence_pattern : Pattern
+track_line(line : str) None
+is_inside_fence() bool
+get_fence_info() tuple[str, int] | None
+reset() None
-_is_opening(line : str) tuple[str, int] | None
-_is_closing(line : str, char : str, length : int) bool
}
StreamingChunker --> BufferManager : "uses"
StreamingChunker --> SplitDetector : "uses"
StreamingChunker --> FenceTracker : "uses"
StreamingChunker --> StreamingConfig : "config"
BufferManager --> StreamingConfig : "config"
SplitDetector --> FenceTracker : "uses"
```

**Diagram sources **
- [StreamingConfig](file://src/chunkana/streaming/config.py#L8-L23)
- [StreamingChunker](file://src/chunkana/streaming/streaming_chunker.py#L18-L99)
- [BufferManager](file://src/chunkana/streaming/buffer_manager.py#L13-L61)
- [SplitDetector](file://src/chunkana/streaming/split_detector.py#L10-L93)
- [FenceTracker](file://src/chunkana/streaming/fence_tracker.py#L10-L65)

**Section sources**
- [StreamingConfig](file://src/chunkana/streaming/config.py#L8-L23)
- [StreamingChunker](file://src/chunkana/streaming/streaming_chunker.py#L18-L99)
- [BufferManager](file://src/chunkana/streaming/buffer_manager.py#L13-L61)
- [SplitDetector](file://src/chunkana/streaming/split_detector.py#L10-L93)
- [FenceTracker](file://src/chunkana/streaming/fence_tracker.py#L10-L65)

## Processing Large Files from Disk

The primary interface for processing large files from disk is the `chunk_file_streaming` function, which can be accessed through both the API module and the MarkdownChunker class. This function reads files in chunks, processes them in buffer windows, and yields chunks incrementally.

```mermaid
sequenceDiagram
participant User as "Application"
participant API as "chunk_file_streaming()"
participant Chunker as "StreamingChunker"
participant Buffer as "BufferManager"
participant File as "Disk File"
User->>API : chunk_file_streaming("large_doc.md")
API->>Chunker : Initialize with config
loop Read Buffer Windows
Chunker->>Buffer : read_windows(file_stream)
Buffer->>File : Read lines until buffer_size reached
File-->>Buffer : Return lines
Buffer-->>Chunker : Yield (buffer, overlap, bytes_processed)
Chunker->>Chunker : _process_window()
Chunker->>MarkdownChunker : chunk(text)
MarkdownChunker-->>Chunker : Return chunks
loop Yield Chunks
Chunker-->>API : Yield chunk
API-->>User : Yield chunk
end
end
User->>User : Process each chunk
```

**Diagram sources **
- [chunk_file_streaming](file://src/chunkana/api.py#L228-L271)
- [StreamingChunker.chunk_file](file://src/chunkana/streaming/streaming_chunker.py#L43-L54)
- [BufferManager.read_windows](file://src/chunkana/streaming/buffer_manager.py#L29-L55)

**Section sources**
- [chunk_file_streaming](file://src/chunkana/api.py#L228-L271)
- [StreamingChunker.chunk_file](file://src/chunkana/streaming/streaming_chunker.py#L43-L54)
- [BufferManager.read_windows](file://src/chunkana/streaming/buffer_manager.py#L29-L55)

## Handling Network Streams

For network streams or any text stream source, use the `chunk_stream` method of the MarkdownChunker class or the streaming capabilities of the StreamingChunker directly. This approach is ideal for processing content from HTTP responses, database streams, or other network sources.

```mermaid
flowchart TD
Start([HTTP Request]) --> GetStream["Get response stream"]
GetStream --> Initialize["Initialize StreamingChunker"]
Initialize --> ProcessStream["Process stream with chunk_stream()"]
ProcessStream --> ReadWindow["Read buffer window"]
ReadWindow --> CheckSize{"Buffer size >= threshold?"}
CheckSize --> |No| ReadMore["Read more lines"]
ReadMore --> ReadWindow
CheckSize --> |Yes| ProcessWindow["Process window with base chunker"]
ProcessWindow --> ExtractOverlap["Extract overlap lines"]
ExtractOverlap --> YieldChunks["Yield chunks with metadata"]
YieldChunks --> MoreData{"More data available?"}
MoreData --> |Yes| ReadWindow
MoreData --> |No| CheckRemaining{"Remaining buffer?"}
CheckRemaining --> |Yes| ProcessRemaining["Process remaining buffer"]
ProcessRemaining --> EndStream["End stream processing"]
CheckRemaining --> |No| EndStream
EndStream --> End([Processing Complete])
```

**Diagram sources **
- [MarkdownChunker.chunk_stream](file://src/chunkana/chunker.py#L275-L299)
- [StreamingChunker.chunk_stream](file://src/chunkana/streaming/streaming_chunker.py#L56-L78)
- [BufferManager.read_windows](file://src/chunkana/streaming/buffer_manager.py#L29-L55)

**Section sources**
- [MarkdownChunker.chunk_stream](file://src/chunkana/chunker.py#L275-L299)
- [StreamingChunker.chunk_stream](file://src/chunkana/streaming/streaming_chunker.py#L56-L78)

## Generator-Based Source Processing

Generator-based sources can be processed by wrapping them in a text stream interface. This pattern is useful for processing data from databases, message queues, or other sources that provide data through generators.

```mermaid
classDiagram
class GeneratorStream {
-generator : Iterator[str]
-buffer : str
-position : int
+read(size : int) str
+readline() str
+__iter__() Iterator[str]
+__next__() str
}
class StreamingChunker {
+chunk_stream(stream : TextIOBase) Iterator[Chunk]
}
class DataProcessor {
+process_from_generator(generator : Iterator[str]) Iterator[Chunk]
}
DataProcessor --> GeneratorStream : "creates"
GeneratorStream --> StreamingChunker : "passes to chunk_stream"
StreamingChunker --> DataProcessor : "yields chunks"
```

**Diagram sources **
- [StreamingChunker.chunk_stream](file://src/chunkana/streaming/streaming_chunker.py#L56-L78)
- [BufferManager.read_windows](file://src/chunkana/streaming/buffer_manager.py#L29-L55)

**Section sources**
- [StreamingChunker.chunk_stream](file://src/chunkana/streaming/streaming_chunker.py#L56-L78)

## Integration with RAG Pipelines

The streaming API integrates seamlessly with RAG (Retrieval-Augmented Generation) pipelines by providing chunks with metadata that enhances context preservation. The overlap metadata fields (`previous_content` and `next_content`) are particularly valuable for maintaining context across chunk boundaries.

```mermaid
flowchart LR
A[Large Document] --> B[StreamingChunker]
B --> C[Chunk 1]
B --> D[Chunk 2]
B --> E[Chunk N]
C --> F[Embedding Model]
D --> F
E --> F
F --> G[Vector Database]
H[User Query] --> I[Retriever]
I --> G
G --> J[Relevant Chunks]
J --> K[Context Enrichment]
K --> L[Generation Model]
M[Streaming Metadata] --> K
C --> M
D --> M
E --> M
style M fill:#f9f,stroke:#333
```

**Diagram sources **
- [MarkdownChunker._apply_overlap](file://src/chunkana/chunker.py#L301-L369)
- [Chunk](file://src/chunkana/types.py#L241-L375)

**Section sources**
- [MarkdownChunker._apply_overlap](file://src/chunkana/chunker.py#L301-L369)

## Error Handling Strategies

The streaming API includes comprehensive error handling for various scenarios, including incomplete streams and corrupted input. The system maintains invariants even when processing malformed input.

```mermaid
flowchart TD
A[Input Stream] --> B{Valid UTF-8?}
B --> |No| C[UnicodeDecodeError]
B --> |Yes| D{Empty/Whitespace?}
D --> |Yes| E[Return empty list]
D --> |No| F[Process Buffer Windows]
F --> G{Buffer Complete?}
G --> |No| H[Handle Incomplete Stream]
H --> I[Yield partial chunks]
G --> |Yes| J[Process Complete Window]
J --> K{Safe Split Point?}
K --> |Yes| L[Split at semantic boundary]
K --> |No| M[Fallback to threshold split]
L --> N[Preserve atomic blocks]
M --> N
N --> O[Yield chunks with metadata]
O --> P{More Data?}
P --> |Yes| F
P --> |No| Q[End Processing]
style C fill:#fdd,stroke:#333
style H fill:#fdd,stroke:#333
```

**Diagram sources **
- [StreamingChunker.chunk_stream](file://src/chunkana/streaming/streaming_chunker.py#L56-L78)
- [BufferManager.read_windows](file://src/chunkana/streaming/buffer_manager.py#L29-L55)
- [SplitDetector.find_split_point](file://src/chunkana/streaming/split_detector.py#L26-L61)

**Section sources**
- [StreamingChunker.chunk_stream](file://src/chunkana/streaming/streaming_chunker.py#L56-L78)
- [BufferManager.read_windows](file://src/chunkana/streaming/buffer_manager.py#L29-L55)
- [SplitDetector.find_split_point](file://src/chunkana/streaming/split_detector.py#L26-L61)

## Renderer Integration and Output Formats

The streaming API integrates with various renderers to produce different output formats suitable for different downstream applications. The renderers are pure functions that format chunks without modifying them.

```mermaid
classDiagram
class Chunk {
+content : str
+start_line : int
+end_line : int
+metadata : dict[str, Any]
}
class Renderer {
<<interface>>
+render(chunks : list[Chunk]) list[str or dict]
}
class RenderJson {
+render(chunks : list[Chunk]) list[dict]
}
class RenderDifyStyle {
+render(chunks : list[Chunk]) list[str]
}
class RenderWithEmbeddedOverlap {
+render(chunks : list[Chunk]) list[str]
}
class RenderWithPrevOverlap {
+render(chunks : list[Chunk]) list[str]
}
class RenderInlineMetadata {
+render(chunks : list[Chunk]) list[str]
}
Chunk --> Renderer : "input to"
Renderer <|-- RenderJson
Renderer <|-- RenderDifyStyle
Renderer <|-- RenderWithEmbeddedOverlap
Renderer <|-- RenderWithPrevOverlap
Renderer <|-- RenderInlineMetadata
```

**Diagram sources **
- [render_json](file://src/chunkana/renderers/formatters.py#L15-L27)
- [render_dify_style](file://src/chunkana/renderers/formatters.py#L56-L84)
- [render_with_embedded_overlap](file://src/chunkana/renderers/formatters.py#L87-L116)
- [render_with_prev_overlap](file://src/chunkana/renderers/formatters.py#L119-L145)
- [render_inline_metadata](file://src/chunkana/renderers/formatters.py#L30-L53)

**Section sources**
- [render_json](file://src/chunkana/renderers/formatters.py#L15-L27)
- [render_dify_style](file://src/chunkana/renderers/formatters.py#L56-L84)
- [render_with_embedded_overlap](file://src/chunkana/renderers/formatters.py#L87-L116)
- [render_with_prev_overlap](file://src/chunkana/renderers/formatters.py#L119-L145)

## Performance Optimization

Optimal performance can be achieved by tuning buffer size, overlap lines, and other streaming configuration parameters based on the specific use case and hardware constraints.

```mermaid
flowchart TD
A[Performance Goals] --> B{Memory Constrained?}
B --> |Yes| C[Smaller buffer_size<br/>(e.g., 50KB)]
B --> |No| D[Larger buffer_size<br/>(e.g., 500KB)]
A --> E{Preserve Context?}
E --> |Yes| F[Increase overlap_lines<br/>(e.g., 30-50)]
E --> |No| G[Default overlap_lines<br/>(20)]
A --> H{Large Files?}
H --> |Yes| I[Adjust safe_split_threshold<br/>(e.g., 0.7-0.9)]
H --> |No| J[Default safe_split_threshold<br/>(0.8)]
C --> K[Monitor max_memory_mb]
D --> K
F --> L[Test with sample data]
G --> L
I --> L
J --> L
L --> M[Measure throughput]
M --> N{Optimal?}
N --> |No| O[Adjust parameters]
O --> L
N --> |Yes| P[Deploy optimized config]
style K fill:#ff9,stroke:#333
style L fill:#ff9,stroke:#333
style M fill:#ff9,stroke:#333
```

**Diagram sources **
- [StreamingConfig](file://src/chunkana/streaming/config.py#L8-L23)
- [BufferManager](file://src/chunkana/streaming/buffer_manager.py#L13-L61)
- [SplitDetector](file://src/chunkana/streaming/split_detector.py#L10-L93)

**Section sources**
- [StreamingConfig](file://src/chunkana/streaming/config.py#L8-L23)

## Common Pitfalls and Solutions

Several common pitfalls can occur when using the streaming API, but they can be avoided with proper usage patterns and awareness of the system's behavior.

```mermaid
flowchart TD
A[Common Pitfalls] --> B[Improper Stream Closure]
A --> C[Memory Leaks]
A --> D[Inconsistent Chunk Boundaries]
A --> E[Lost Metadata]
B --> F[Use context managers<br/>with open() or StringIO]
C --> G[Process chunks immediately<br/>avoid storing all in memory]
D --> H[Understand buffer-based<br/>splitting differences]
E --> I[Preserve metadata when<br/>transforming chunks]
F --> J[Solution: Always use 'with' statements]
G --> K[Solution: Process chunks in pipeline]
H --> L[Solution: Accept streaming<br/>boundary variations]
I --> M[Solution: Copy metadata when<br/>creating new chunks]
style B fill:#fdd,stroke:#333
style C fill:#fdd,stroke:#333
style D fill:#fdd,stroke:#333
style E fill:#fdd,stroke:#333
style J fill:#dfd,stroke:#333
style K fill:#dfd,stroke:#333
style L fill:#dfd,stroke:#333
style M fill:#dfd,stroke:#333
```

**Diagram sources **
- [StreamingChunker.chunk_file](file://src/chunkana/streaming/streaming_chunker.py#L53-L54)
- [StreamingChunker.chunk_stream](file://src/chunkana/streaming/streaming_chunker.py#L68-L77)
- [Chunk](file://src/chunkana/types.py#L241-L375)

**Section sources**
- [StreamingChunker.chunk_file](file://src/chunkana/streaming/streaming_chunker.py#L53-L54)
- [StreamingChunker.chunk_stream](file://src/chunkana/streaming/streaming_chunker.py#L68-L77)

## Test Case Validation

The streaming functionality is thoroughly tested in test_streaming.py, with test cases that validate expected behavior for various scenarios including edge cases and error conditions.

```mermaid
erDiagram
TEST_SUITE ||--o{ TEST_CASE : contains
TEST_CASE ||--o{ ASSERTION : contains
TEST_SUITE {
string name
string description
}
TEST_CASE {
string name
string description
string component
}
ASSERTION {
string type
string condition
string expected
}
TEST_SUITE ||--o{ CONFIGURATION : uses
CONFIGURATION {
string parameter
string value
string description
}
TEST_CASE ||--o{ INPUT : uses
INPUT {
string type
string content
string description
}
TEST_CASE ||--o{ OUTPUT : produces
OUTPUT {
string type
string content
string description
}
TEST_SUITE }|--|| StreamingModule : "tests"
StreamingModule {
string name
string path
}
```

**Diagram sources **
- [test_streaming.py](file://tests/unit/test_streaming.py)
- [StreamingConfig](file://src/chunkana/streaming/config.py#L8-L23)
- [StreamingChunker](file://src/chunkana/streaming/streaming_chunker.py#L18-L99)

**Section sources**
- [test_streaming.py](file://tests/unit/test_streaming.py)