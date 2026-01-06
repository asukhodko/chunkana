# Design Document: V2 Critical Fixes

## Overview

Данный дизайн решает критические проблемы чанкования, выявленные в тестировании после миграции. Основные изменения:
1. **Исправленный порядок стадий**: dangling fix → section split
2. Умное разбиение длинных секций с повторением header_stack
3. Удаление `section_integrity` как причины oversize для текста/списков
4. Валидация инвариантов с recall-метрикой coverage

## Architecture

### Исправленный порядок стадий (КРИТИЧНО)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MarkdownChunker.chunk()                       │
├─────────────────────────────────────────────────────────────────┤
│  1. Parse & Analyze                                              │
│  2. Select Strategy                                              │
│  3. Apply Strategy → Initial Chunks                              │
│  4. Merge Small Chunks                                           │
│  5. ┌─────────────────────────────────────────────────────────┐ │
│     │  HeaderProcessor.prevent_dangling_headers()             │ │
│     │  ← СНАЧАЛА "пришиваем" заголовок к телу                 │ │
│     └─────────────────────────────────────────────────────────┘ │
│  6. ┌─────────────────────────────────────────────────────────┐ │
│     │  SectionSplitter.split_oversize_sections()              │ │
│     │  ← ПОТОМ режем секцию (уже с заголовком внутри)         │ │
│     └─────────────────────────────────────────────────────────┘ │
│  7. Apply Overlap (metadata-only, не в content)                  │
│  8. MetadataRecalculator.recalculate_all()                       │
│  9. InvariantValidator.validate()                                │
│  10. Return Final Chunks                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Почему этот порядок критичен:**
- В отчёте: `#### Итоги работы` в конце chunk N, контент списка в chunk N+1 без заголовка
- Если сначала split: chunk N+1 разрежется, но там НЕТ заголовка для повторения
- Если сначала dangling fix: заголовок переносится в N+1, потом N+1 режется С заголовком



## Components and Interfaces

### SectionSplitter (исправленный алгоритм)

```python
class SectionSplitter:
    """
    Разбивает секции, превышающие max_chunk_size.
    
    ВАЖНО: Вызывается ПОСЛЕ HeaderProcessor.prevent_dangling_headers(),
    поэтому чанки уже содержат свои заголовки.
    
    Стратегия разбиения:
    1. По границам пунктов списка (нумерованного или маркированного)
    2. По границам абзацев (\\n\\n)
    3. По границам предложений (как fallback)
    
    При разбиении header_stack повторяется в каждом продолжающем чанке.
    """
    
    def __init__(self, config: ChunkConfig):
        self.config = config
        self.min_content_after_header = 100
    
    def split_oversize_sections(self, chunks: list[Chunk]) -> list[Chunk]:
        """Разбивает oversized секции."""
        result = []
        for chunk in chunks:
            if self._needs_splitting(chunk):
                result.extend(self._split_chunk(chunk))
            else:
                result.append(chunk)
        return result
    
    def _needs_splitting(self, chunk: Chunk) -> bool:
        """Проверяет, нужно ли разбивать чанк."""
        if len(chunk.content) <= self.config.max_chunk_size:
            return False
        # Атомарные блоки не разбиваем
        return not self._is_atomic_block(chunk)
    
    def _is_atomic_block(self, chunk: Chunk) -> bool:
        """Код и таблицы — атомарные."""
        content_type = chunk.metadata.get("content_type", "")
        return content_type in ("code", "table")
    
    def _split_chunk(self, chunk: Chunk) -> list[Chunk]:
        """Разбивает чанк с повторением header_stack."""
        header_stack, body = self._extract_header_stack_and_body(chunk.content)
        segments = self._find_segments(body)
        return self._pack_segments_into_chunks(chunk, header_stack, segments)
    
    def _extract_header_stack_and_body(self, content: str) -> tuple[str, str]:
        """
        Извлекает header_stack (все заголовки в начале) и тело.
        
        Header_stack — это последовательность подряд идущих header-строк
        в начале контента (пропуская пустые строки).
        
        Пример:
          "## Impact\\n\\n#### Итоги работы\\n\\n1. Первый пункт..."
          → header_stack = "## Impact\\n\\n#### Итоги работы"
          → body = "1. Первый пункт..."
        """
        lines = content.split('\n')
        header_lines = []
        body_start_idx = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                # Пустая строка — продолжаем искать заголовки
                if header_lines:
                    header_lines.append('')  # Сохраняем пустую строку между заголовками
                continue
            if stripped.startswith('#'):
                header_lines.append(line)
                body_start_idx = i + 1
            else:
                # Первая non-header строка — конец header_stack
                break
        
        # Убираем trailing пустые строки из header_stack
        while header_lines and not header_lines[-1].strip():
            header_lines.pop()
        
        header_stack = '\n'.join(header_lines) if header_lines else ''
        body = '\n'.join(lines[body_start_idx:]).strip()
        
        return header_stack, body

    def _find_segments(self, body: str) -> list[str]:
        """
        Находит сегменты для разбиения.
        
        Приоритет:
        1. Пункты списка (нумерованного или маркированного)
        2. Абзацы (разделённые \\n\\n)
        3. Предложения (fallback)
        """
        # Пробуем разбить по пунктам списка
        list_segments = self._split_by_list_items(body)
        if len(list_segments) > 1:
            return list_segments
        
        # Пробуем разбить по абзацам
        para_segments = self._split_by_paragraphs(body)
        if len(para_segments) > 1:
            return para_segments
        
        # Fallback: по предложениям
        return self._split_by_sentences(body)
    
    def _split_by_list_items(self, body: str) -> list[str]:
        """Разбивает по пунктам списка."""
        # Паттерн: начало строки + (число+точка ИЛИ маркер)
        pattern = re.compile(r'^(\d+\.|[-*+])\s+', re.MULTILINE)
        
        matches = list(pattern.finditer(body))
        if len(matches) <= 1:
            return [body]
        
        segments = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            segment = body[start:end].strip()
            if segment:
                segments.append(segment)
        
        return segments if segments else [body]
    
    def _split_by_paragraphs(self, body: str) -> list[str]:
        """Разбивает по абзацам."""
        paragraphs = re.split(r'\n\n+', body)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_by_sentences(self, body: str) -> list[str]:
        """Разбивает по предложениям (fallback)."""
        # Простой паттерн: конец предложения
        sentences = re.split(r'(?<=[.!?])\s+', body)
        return [s.strip() for s in sentences if s.strip()]
    
    def _pack_segments_into_chunks(
        self, 
        original: Chunk, 
        header_stack: str, 
        segments: list[str]
    ) -> list[Chunk]:
        """
        Упаковывает сегменты в чанки с повторением header_stack.
        
        Алгоритм "pack until full":
        1. Накапливаем сегменты пока помещаются
        2. Когда не помещается — создаём чанк и начинаем новый
        3. Каждый чанк (кроме первого) начинается с header_stack
        """
        header_size = len(header_stack) + 2 if header_stack else 0  # +2 для \n\n
        max_body_size = self.config.max_chunk_size - header_size
        
        chunks = []
        current_segments = []
        current_size = 0
        chunk_index = 0
        
        for segment in segments:
            segment_size = len(segment) + 2  # +2 для разделителя
            
            # Проверяем, поместится ли сегмент
            if current_size + segment_size <= max_body_size:
                current_segments.append(segment)
                current_size += segment_size
            else:
                # Создаём чанк из накопленного
                if current_segments:
                    chunks.append(self._create_chunk(
                        original, header_stack, current_segments, chunk_index
                    ))
                    chunk_index += 1
                
                # Начинаем новый чанк
                # Проверяем, помещается ли сегмент сам по себе
                if segment_size <= max_body_size:
                    current_segments = [segment]
                    current_size = segment_size
                else:
                    # Сегмент слишком большой — создаём oversize чанк
                    chunks.append(self._create_chunk(
                        original, header_stack, [segment], chunk_index,
                        allow_oversize=True, oversize_reason="list_item_integrity"
                    ))
                    chunk_index += 1
                    current_segments = []
                    current_size = 0
        
        # Последний чанк
        if current_segments:
            chunks.append(self._create_chunk(
                original, header_stack, current_segments, chunk_index
            ))
        
        return chunks if chunks else [original]

    def _create_chunk(
        self, 
        original: Chunk, 
        header_stack: str, 
        segments: list[str], 
        index: int,
        allow_oversize: bool = False,
        oversize_reason: str = ""
    ) -> Chunk:
        """Создаёт чанк с header_stack."""
        body = '\n\n'.join(segments)
        
        if header_stack and index > 0:
            # Продолжающий чанк — повторяем header_stack
            content = f"{header_stack}\n\n{body}"
            continued = True
        elif header_stack:
            # Первый чанк — header_stack уже есть
            content = f"{header_stack}\n\n{body}"
            continued = False
        else:
            content = body
            continued = index > 0
        
        metadata = original.metadata.copy()
        metadata["continued_from_header"] = continued
        metadata["split_index"] = index
        metadata["original_section_size"] = len(original.content)
        
        if allow_oversize:
            metadata["allow_oversize"] = True
            metadata["oversize_reason"] = oversize_reason
        
        return Chunk(
            content=content,
            start_line=original.start_line,
            end_line=original.end_line,
            metadata=metadata
        )
```

### Enhanced HeaderProcessor

```python
class HeaderProcessor:
    """
    Процессор для предотвращения dangling headers.
    
    Изменения v2.1:
    - Детекция для уровней 2-6 (не только 3-6)
    - Порог 30 символов вместо 50
    - Использование chunk_id вместо chunk_index для tracking
    """
    
    def __init__(self, config: ChunkConfig):
        self.config = config
        self.detector = EnhancedDanglingHeaderDetector()
        self.mover = HeaderMover(config)
    
    def prevent_dangling_headers(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Предотвращает dangling headers.
        
        ВАЖНО: Вызывается ДО SectionSplitter, чтобы заголовки
        были "пришиты" к телу перед разбиением.
        """
        result = chunks.copy()
        max_iterations = 20
        
        for iteration in range(max_iterations):
            dangling = self.detector.detect_all(result)
            if not dangling:
                break
            
            info = dangling[0]
            result = self.mover.fix(result, info)
        
        return result


class EnhancedDanglingHeaderDetector:
    """
    Детектор dangling headers.
    
    Изменения:
    - Уровни 2-6 (не только 3-6)
    - Порог 30 символов
    """
    
    def __init__(self):
        self.header_pattern = re.compile(r'^(#{2,6})\s+(.+)$')  # Уровни 2-6
        self.min_content_threshold = 30  # Уменьшено с 50
    
    def detect_all(self, chunks: list[Chunk]) -> list[DanglingHeaderInfo]:
        """Обнаруживает все dangling headers."""
        results = []
        for i in range(len(chunks) - 1):
            info = self._check_chunk(chunks[i], chunks[i + 1], i)
            if info:
                results.append(info)
        return results
    
    def _check_chunk(self, current: Chunk, next_chunk: Chunk, index: int) -> DanglingHeaderInfo | None:
        """Проверяет один чанк."""
        content = current.content.rstrip()
        lines = content.split('\n')
        
        # Находим последнюю непустую строку
        last_line = None
        last_line_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                last_line = lines[i].strip()
                last_line_idx = i
                break
        
        if not last_line:
            return None
        
        match = self.header_pattern.match(last_line)
        if not match:
            return None
        
        header_level = len(match.group(1))
        header_text = match.group(2).strip()
        
        # Проверяем контент после заголовка
        content_after = '\n'.join(lines[last_line_idx + 1:]).strip()
        if len(content_after) > self.min_content_threshold:
            return None
        
        # Проверяем следующий чанк
        next_content = next_chunk.content.lstrip()
        if not next_content or len(next_content.strip()) < 20:
            return None
        
        next_first_line = next_content.split('\n')[0].strip()
        next_match = self.header_pattern.match(next_first_line)
        if next_match and len(next_match.group(1)) <= header_level:
            return None
        
        return DanglingHeaderInfo(
            chunk_index=index,
            chunk_id=current.metadata.get("chunk_id"),  # Стабильный ID
            header_text=header_text,
            header_level=header_level,
            header_line_in_chunk=last_line_idx
        )
```


### HeaderMover (с chunk_id tracking)

```python
class HeaderMover:
    """Перемещает заголовки между чанками."""
    
    def __init__(self, config: ChunkConfig):
        self.config = config
    
    def fix(self, chunks: list[Chunk], info: DanglingHeaderInfo) -> list[Chunk]:
        """Исправляет dangling header."""
        idx = info.chunk_index
        current = chunks[idx]
        next_chunk = chunks[idx + 1]
        
        # Извлекаем заголовок
        lines = current.content.strip().split('\n')
        header_line = lines[-1]
        new_current_content = '\n'.join(lines[:-1]).strip()
        
        # Добавляем заголовок в начало следующего чанка
        new_next_content = header_line + '\n\n' + next_chunk.content
        
        # Проверяем размер
        if len(new_next_content) <= self.config.max_chunk_size:
            # Перемещаем заголовок
            new_current = Chunk(
                content=new_current_content,
                start_line=current.start_line,
                end_line=current.end_line - 1,
                metadata=current.metadata.copy()
            )
            
            new_next = Chunk(
                content=new_next_content,
                start_line=next_chunk.start_line - 1,
                end_line=next_chunk.end_line,
                metadata=next_chunk.metadata.copy()
            )
            
            # Tracking с chunk_id (стабильный)
            new_next.metadata["dangling_header_fixed"] = True
            new_next.metadata["header_moved_from_id"] = info.chunk_id
            
            result = chunks.copy()
            result[idx] = new_current
            result[idx + 1] = new_next
            return result
        
        # Если не помещается — merge
        merged_content = current.content + '\n\n' + next_chunk.content
        if len(merged_content) <= self.config.max_chunk_size:
            merged = Chunk(
                content=merged_content,
                start_line=current.start_line,
                end_line=next_chunk.end_line,
                metadata=current.metadata.copy()
            )
            merged.metadata["dangling_header_fixed"] = True
            merged.metadata["merge_reason"] = "dangling_header_prevention"
            merged.metadata["header_moved_from_id"] = info.chunk_id
            
            result = chunks.copy()
            result[idx:idx + 2] = [merged]
            return result
        
        # Не можем исправить без превышения лимита
        import logging
        logging.warning(f"Cannot fix dangling header at chunk {idx}")
        return chunks
```

### InvariantValidator (с recall-метрикой)

```python
@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]
    coverage: float  # Recall оригинальных строк


class InvariantValidator:
    """
    Валидатор инвариантов качества чанкования.
    
    Проверяет:
    1. Отсутствие dangling headers (уровни 1-6 для инварианта)
    2. Соблюдение max_chunk_size (кроме атомарных блоков)
    3. Полнота покрытия (recall оригинальных строк ≥95%)
    """
    
    def __init__(self, config: ChunkConfig, strict: bool = False):
        self.config = config
        self.strict = strict
    
    def validate(self, chunks: list[Chunk], original_text: str) -> ValidationResult:
        """Выполняет все проверки."""
        errors = []
        warnings = []
        
        # Инвариант 1: Нет dangling headers (ВСЕ уровни 1-6)
        dangling = self._check_no_dangling_headers(chunks)
        if dangling:
            msg = f"Found {len(dangling)} dangling headers at chunks: {dangling}"
            if self.strict:
                errors.append(msg)
            else:
                warnings.append(msg)
        
        # Инвариант 2: Нет oversize без валидной причины
        oversize = self._check_no_invalid_oversize(chunks)
        if oversize:
            msg = f"Found {len(oversize)} invalid oversize chunks: {oversize}"
            if self.strict:
                errors.append(msg)
            else:
                warnings.append(msg)
        
        # Инвариант 3: Coverage как recall строк
        coverage = self._calculate_line_recall(chunks, original_text)
        if coverage < 0.95:
            msg = f"Content coverage {coverage:.1%} < 95%"
            warnings.append(msg)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            coverage=coverage
        )
    
    def _check_no_dangling_headers(self, chunks: list[Chunk]) -> list[int]:
        """Проверяет отсутствие dangling headers (уровни 1-6)."""
        header_pattern = re.compile(r'^#{1,6}\s+')  # ВСЕ уровни для инварианта
        dangling_indices = []
        
        for i in range(len(chunks) - 1):
            content = chunks[i].content.rstrip()
            lines = content.split('\n')
            
            # Находим последнюю непустую строку
            for line in reversed(lines):
                if line.strip():
                    if header_pattern.match(line.strip()):
                        dangling_indices.append(i)
                    break
        
        return dangling_indices
    
    def _check_no_invalid_oversize(self, chunks: list[Chunk]) -> list[int]:
        """Проверяет отсутствие oversize без валидной причины."""
        invalid = []
        valid_reasons = {"code_block_integrity", "table_integrity", "list_item_integrity"}
        
        for i, chunk in enumerate(chunks):
            if len(chunk.content) > self.config.max_chunk_size:
                reason = chunk.metadata.get("oversize_reason", "")
                if reason not in valid_reasons:
                    invalid.append(i)
        
        return invalid

    def _calculate_line_recall(self, chunks: list[Chunk], original: str) -> float:
        """
        Вычисляет recall оригинальных строк.
        
        Метрика: доля строк оригинала (длиной ≥20 символов),
        которые присутствуют хотя бы в одном чанке.
        
        Это честная метрика, которая НЕ улучшается от:
        - Повторения заголовков
        - Overlap
        - Дублирования контента
        """
        # Нормализуем whitespace
        def normalize(s: str) -> str:
            return ' '.join(s.split())
        
        # Собираем значимые строки оригинала
        original_lines = []
        for line in original.split('\n'):
            normalized = normalize(line)
            if len(normalized) >= 20:
                original_lines.append(normalized)
        
        if not original_lines:
            return 1.0
        
        # Собираем весь текст чанков
        chunks_text = normalize(' '.join(c.content for c in chunks))
        
        # Считаем recall
        found = 0
        for line in original_lines:
            if line in chunks_text:
                found += 1
        
        return found / len(original_lines)
```

## Data Models

### Enhanced Chunk Metadata

```python
chunk.metadata = {
    # Существующие поля
    "section_tags": list[str],
    "header_path": str,
    "start_line": int,  # Может пересекаться с другими чанками при header repetition
    "end_line": int,
    "chunk_id": str,    # Стабильный идентификатор (8-char SHA256)
    
    # Dangling header fix
    "dangling_header_fixed": bool,
    "header_moved_from_id": str | None,  # chunk_id источника (стабильный)
    "merge_reason": str | None,          # "dangling_header_prevention"
    
    # Section splitting
    "continued_from_header": bool,  # True если это продолжение разбитой секции
    "split_index": int,             # Индекс части (0, 1, 2...)
    "original_section_size": int,   # Размер до разбиения
    
    # Oversize
    "allow_oversize": bool,
    "oversize_reason": str,  # "code_block_integrity" | "table_integrity" | "list_item_integrity"
    # УДАЛЕНО: "section_integrity" для текста/списков
    
    # Hierarchical
    "indexable": bool,  # Устанавливается библиотекой, downstream должны уважать
}
```

### Line Range Contract

```
Контракт для start_line/end_line после операций split/move:

1. start_line/end_line отражают минимальную/максимальную исходную строку,
   присутствующую в content чанка

2. При header repetition line ranges МОГУТ пересекаться между чанками
   (один и тот же заголовок присутствует в нескольких чанках)

3. Это допустимое поведение, не является ошибкой

4. Для уникальной идентификации позиции используйте chunk_id, не line ranges
```

## Testing Strategy

### Recall-based Coverage Test

```python
def test_content_coverage_recall(sde_criteria_document):
    """Проверяет покрытие как recall строк."""
    chunker = MarkdownChunker(ChunkConfig(max_chunk_size=1000))
    chunks = chunker.chunk(sde_criteria_document)
    
    validator = InvariantValidator(ChunkConfig(max_chunk_size=1000))
    result = validator.validate(chunks, sde_criteria_document)
    
    assert result.coverage >= 0.95, f"Coverage {result.coverage:.1%} < 95%"
```

### Dangling Headers Test (все секции)

```python
@pytest.mark.parametrize("section", [
    "Scope", "Impact", "Leadership", "Improvement", "Technical Complexity"
])
def test_no_dangling_in_section(sde_criteria_document, section):
    """Проверяет отсутствие dangling во всех секциях."""
    chunker = MarkdownChunker(ChunkConfig(max_chunk_size=1000))
    chunks = chunker.chunk(sde_criteria_document)
    
    validator = InvariantValidator(ChunkConfig(max_chunk_size=1000), strict=True)
    result = validator.validate(chunks, sde_criteria_document)
    
    assert result.valid, f"Dangling headers found: {result.errors}"
```

### Header Stack Repetition Test

```python
def test_continued_chunks_have_header_stack(sde_criteria_document):
    """Проверяет, что продолжающие чанки содержат header_stack."""
    chunker = MarkdownChunker(ChunkConfig(max_chunk_size=1000))
    chunks = chunker.chunk(sde_criteria_document)
    
    for chunk in chunks:
        if chunk.metadata.get("continued_from_header"):
            # Должен начинаться с заголовка
            first_line = chunk.content.strip().split('\n')[0]
            assert first_line.startswith('#'), \
                f"Continued chunk should start with header: {first_line[:50]}"
```

## Implementation Plan

### Phase 1: Исправить порядок стадий (1 день)
1. Переместить вызов `SectionSplitter` ПОСЛЕ `HeaderProcessor`
2. Обновить docstrings с объяснением порядка
3. Тесты на порядок

### Phase 2: SectionSplitter с header_stack (2 дня)
1. Реализовать `_extract_header_stack_and_body()`
2. Реализовать `_pack_segments_into_chunks()` (исправленный алгоритм)
3. Тесты на разбиение с повторением header_stack

### Phase 3: Улучшить HeaderProcessor (1 день)
1. Расширить детекцию на уровни 2-6
2. Уменьшить порог до 30 символов
3. Использовать chunk_id вместо chunk_index
4. Тесты

### Phase 4: InvariantValidator с recall (1 день)
1. Реализовать `_calculate_line_recall()`
2. Проверка dangling для уровней 1-6
3. Удалить `section_integrity` из валидных причин oversize
4. Тесты

### Phase 5: Интеграция и регрессионные тесты (1 день)
1. Интеграционные тесты на реальном документе
2. Параметризованные тесты по секциям
3. Обновить документацию
