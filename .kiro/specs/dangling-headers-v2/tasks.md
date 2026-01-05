# Tasks Document: Dangling Headers v2 & Metadata Consistency

## Overview

Задачи для исправления проблем, выявленных в TEST_REPORT_v2.md.

## Task Organization

- **Phase 1**: P0 - Universal Dangling Header Fix (Critical)
- **Phase 2**: P0 - section_tags Recalculation (Critical)
- **Phase 3**: P1 - header_moved_from Implementation (High)
- **Phase 4**: P2 - Line Range Contract Documentation (Medium)
- **Phase 5**: P1 - Regression Tests (High)

---

## Phase 1: Universal Dangling Header Fix (P0)

### Task 1.1: Рефакторинг DanglingHeaderDetector

**Priority**: P0  
**Status**: ✅ DONE  
**Estimated Effort**: 2-3 часа

**Description**: Убрать привязку к конкретным header_path, сделать детекцию универсальной.

**Acceptance Criteria**:
- [x] Детекция работает для ЛЮБОГО header_path
- [x] Детекция работает для заголовков уровней 3-6 (###, ####, etc.)
- [x] Не зависит от названия секции (Scope, Impact, Leadership, etc.)
- [x] Учитывает allow_oversize флаг

**Files to Modify**:
- `src/chunkana/header_processor.py`

**Implementation Notes**:
```python
# Текущая проблема: логика может быть привязана к конкретным условиям
# Нужно: универсальная проверка "заканчивается ли чанк заголовком"

def _is_dangling_header(self, chunk: Chunk, next_chunk: Chunk) -> bool:
    content = chunk.content.rstrip()
    lines = content.split('\n')
    
    # Найти последнюю непустую строку
    last_line = None
    for line in reversed(lines):
        if line.strip():
            last_line = line.strip()
            break
    
    if not last_line:
        return False
    
    # Проверить, является ли это заголовком
    match = re.match(r'^(#{1,6})\s+(.+)$', last_line)
    if not match:
        return False
    
    # Проверить, что следующий чанк содержит контент (не начинается с заголовка)
    next_first = next_chunk.content.lstrip().split('\n')[0].strip()
    next_is_header = re.match(r'^#{1,6}\s+', next_first)
    
    return not next_is_header  # Dangling если следующий НЕ заголовок
```

---

### Task 1.2: Исправить HeaderMover для всех секций

**Priority**: P0  
**Status**: ✅ DONE  
**Estimated Effort**: 2 часа

**Description**: Убедиться, что перенос заголовков работает во всех секциях.

**Acceptance Criteria**:
- [x] Перенос работает в секции Scope ✅ (уже работает)
- [x] Перенос работает в секции Impact
- [x] Перенос работает в секции Leadership
- [x] Перенос работает в секции Improvement
- [x] Перенос работает в секции Technical Complexity

**Files to Modify**:
- `src/chunkana/header_processor.py`

**Test Case**:
```python
def test_dangling_fix_all_sections():
    doc = load_sde_criteria_document()
    chunks = chunker.chunk(doc)
    
    sections_with_dangling = []
    for i, chunk in enumerate(chunks[:-1]):
        if chunk.content.rstrip().endswith('#### Итоги работы'):
            sections_with_dangling.append(chunk.metadata.get('header_path'))
    
    assert len(sections_with_dangling) == 0, f"Dangling in: {sections_with_dangling}"
```

---

### Task 1.3: Интеграция с allow_oversize

**Priority**: P0  
**Status**: ✅ DONE  
**Estimated Effort**: 1 час

**Description**: Когда чанк помечен allow_oversize, заголовок секции должен быть включён.

**Acceptance Criteria**:
- [x] Если список помечен allow_oversize, заголовок переносится В этот чанк
- [x] oversize_reason учитывается при принятии решения
- [x] Не создаются чанки без заголовка при наличии oversize контента

**Files to Modify**:
- `src/chunkana/header_processor.py`

---

## Phase 2: section_tags Recalculation (P0)

### Task 2.1: Создать MetadataRecalculator

**Priority**: P0  
**Status**: ✅ DONE  
**Estimated Effort**: 2 часа

**Description**: Новый компонент для пересчёта derived-метаданных.

**Acceptance Criteria**:
- [x] Класс MetadataRecalculator создан
- [x] Метод recalculate_section_tags() реализован
- [x] Извлечение заголовков из контента работает корректно
- [x] Поддержка заголовков уровней 3-4

**Files to Create**:
- `src/chunkana/metadata_recalculator.py`

**Implementation**:
```python
class MetadataRecalculator:
    def recalculate_all(self, chunks: list[Chunk]) -> list[Chunk]:
        """Пересчитывает все derived-поля."""
        return self._recalculate_section_tags(chunks)
    
    def _recalculate_section_tags(self, chunks: list[Chunk]) -> list[Chunk]:
        for chunk in chunks:
            headers = self._extract_headers(chunk.content)
            chunk.metadata['section_tags'] = headers
        return chunks
    
    def _extract_headers(self, content: str) -> list[str]:
        headers = []
        for line in content.split('\n'):
            match = re.match(r'^#{3,4}\s+(.+)$', line.strip())
            if match:
                headers.append(match.group(1).strip())
        return headers
```

---

### Task 2.2: Интегрировать в пайплайн чанкинга

**Priority**: P0  
**Status**: ✅ DONE  
**Estimated Effort**: 1 час

**Description**: Вызывать MetadataRecalculator после всех пост-обработок.

**Acceptance Criteria**:
- [x] MetadataRecalculator вызывается после HeaderProcessor
- [x] MetadataRecalculator вызывается после ChunkMerger
- [x] Порядок: chunk → dangling fix → merge → recalculate
- [x] Работает в обоих режимах (hierarchical и flat)

**Files to Modify**:
- `src/chunkana/chunker.py`

**Integration Point**:
```python
def chunk(self, text: str) -> list[Chunk]:
    # ... existing chunking logic ...
    
    # Post-processing
    chunks = self.header_processor.prevent_dangling_headers(chunks)
    chunks = self.chunk_merger.merge_small_chunks(chunks)
    
    # NEW: Recalculate metadata after all post-processing
    chunks = self.metadata_recalculator.recalculate_all(chunks)
    
    return chunks
```

---

### Task 2.3: Тесты на соответствие section_tags контенту

**Priority**: P0  
**Status**: ✅ DONE  
**Estimated Effort**: 1.5 часа

**Description**: Тесты, проверяющие что section_tags соответствуют фактическому контенту.

**Acceptance Criteria**:
- [x] Тест: каждый тег в section_tags присутствует в контенте
- [x] Тест: после dangling fix теги пересчитаны
- [x] Тест: chunk_index=23 НЕ содержит "Итоги работы" если заголовок перенесён
- [x] Тест: chunk_index=24 содержит "Итоги работы" после переноса

**Files to Create**:
- `tests/regression/test_v2_report_issues.py` (TestSectionTagsConsistency)

---

## Phase 3: header_moved_from Implementation (P1)

### Task 3.1: Добавить трекинг в HeaderMover

**Priority**: P1  
**Status**: ✅ DONE  
**Estimated Effort**: 1.5 часа

**Description**: При переносе заголовка записывать источник.

**Acceptance Criteria**:
- [x] header_moved_from заполняется chunk_index источника
- [x] При отсутствии переноса поле null или отсутствует
- [x] При множественном переносе — список индексов

**Files to Modify**:
- `src/chunkana/header_processor.py`

**Implementation**:
```python
def _move_header_to_next_chunk(self, chunks, source_idx, header_info):
    # ... existing logic ...
    
    # Track the move
    target_chunk = chunks[source_idx + 1]
    moved_from = target_chunk.metadata.get('header_moved_from')
    
    if moved_from is None:
        target_chunk.metadata['header_moved_from'] = source_idx
    elif isinstance(moved_from, int):
        target_chunk.metadata['header_moved_from'] = [moved_from, source_idx]
    else:
        target_chunk.metadata['header_moved_from'].append(source_idx)
```

---

### Task 3.2: Тесты на header_moved_from

**Priority**: P1  
**Status**: ✅ DONE  
**Estimated Effort**: 1 час

**Description**: Тесты на корректность заполнения поля.

**Acceptance Criteria**:
- [x] Тест: поле заполнено при переносе
- [x] Тест: поле null при отсутствии переноса
- [x] Тест: поле — список при множественном переносе

**Files to Create**:
- `tests/regression/test_v2_report_issues.py` (TestHeaderMovedFromTracking)

---

## Phase 4: Line Range Contract Documentation (P2)

### Task 4.1: Документировать контракт в README

**Priority**: P2  
**Status**: ✅ DONE  
**Estimated Effort**: 1 час

**Description**: Явно задокументировать семантику start_line/end_line.

**Acceptance Criteria**:
- [x] Контракт описан в README.md
- [x] Примеры для leaf, internal, root узлов
- [x] Объяснение почему диапазоны не "складываются"

**Files to Modify**:
- `README.md`

**Documentation Content**:
```markdown
### Line Range Contract (Hierarchical Mode)

- **Leaf nodes**: `start_line/end_line` covers only the chunk's own content
- **Internal nodes**: `start_line/end_line` covers only the node's own content (not children)
- **Root node**: `start_line/end_line` covers the entire document (1 to last line)

Note: The sum of children's line ranges does NOT equal the parent's range.
The parent contains only its "header" content, while children contain detailed content.
```

---

### Task 4.2: Добавить валидацию в debug режиме

**Priority**: P2  
**Status**: ✅ DONE  
**Estimated Effort**: 1 час

**Description**: Предупреждение при нарушении контракта.

**Acceptance Criteria**:
- [x] Валидация включена в debug режиме
- [x] Warning при несоответствии контракту
- [x] Не блокирует выполнение

**Files to Modify**:
- `src/chunkana/metadata_recalculator.py`

---

## Phase 5: Regression Tests (P1)

### Task 5.1: Создать fixture из реального документа

**Priority**: P1  
**Status**: ✅ DONE  
**Estimated Effort**: 0.5 часа

**Description**: Использовать документ из TEST_REPORT_v2 как тестовый fixture.

**Acceptance Criteria**:
- [x] Fixture содержит полный документ SDE критериев
- [x] Fixture доступен для всех тестов
- [x] Документ содержит все проблемные секции

**Files to Create**:
- `tests/fixtures/sde_criteria.md`
- `tests/regression/test_v2_report_issues.py` (fixtures)

---

### Task 5.2: Тесты на все выявленные проблемы

**Priority**: P1  
**Status**: ✅ DONE  
**Estimated Effort**: 2 часа

**Description**: Регрессионные тесты для каждой проблемы из отчёта.

**Acceptance Criteria**:
- [x] Тест: dangling headers во всех секциях
- [x] Тест: section_tags соответствие контенту
- [x] Тест: header_moved_from корректность
- [x] Тест: start_line/end_line контракт

**Files to Create**:
- `tests/regression/test_v2_report_issues.py`

**Test Structure**:
```python
class TestV2ReportIssues:
    """Регрессионные тесты для проблем из TEST_REPORT_v2."""
    
    def test_dangling_headers_impact_section(self, sde_criteria_fixture):
        """Issue: chunk 26/27 в Impact."""
        ...
    
    def test_dangling_headers_leadership_section(self, sde_criteria_fixture):
        """Issue: chunk 30/31 в Leadership."""
        ...
    
    def test_dangling_headers_improvement_section(self, sde_criteria_fixture):
        """Issue: chunk 33/34 и 34/35 в Improvement."""
        ...
    
    def test_section_tags_after_dangling_fix(self, sde_criteria_fixture):
        """Issue: section_tags съехали после фикса."""
        ...
    
    def test_header_moved_from_not_null(self, sde_criteria_fixture):
        """Issue: header_moved_from всегда null."""
        ...
```

---

## Summary

### Priority Distribution
- **P0 (Critical)**: 6 tasks — Universal dangling fix + section_tags recalculation ✅ ALL DONE
- **P1 (High)**: 4 tasks — header_moved_from + regression tests ✅ ALL DONE
- **P2 (Medium)**: 2 tasks — Documentation (1 done, 1 optional)

### Estimated Total Effort
- Phase 1: ~5-6 часов ✅
- Phase 2: ~4.5 часа ✅
- Phase 3: ~2.5 часа ✅
- Phase 4: ~2 часа (1 час done)
- Phase 5: ~2.5 часа ✅
- **Total**: ~16-17 часов

### Completion Status
- **12 of 12 tasks completed** ✅ ALL DONE

### Dependencies
```
Task 1.1 → Task 1.2 → Task 1.3 ✅
                ↓
Task 2.1 → Task 2.2 → Task 2.3 ✅
                ↓
Task 3.1 → Task 3.2 ✅
                ↓
Task 5.1 → Task 5.2 ✅

Task 4.1 ✅, 4.2 ✅ — независимые
```

### Definition of Done
1. ✅ Все тесты проходят (267 passed)
2. ✅ Dangling headers исправлены во ВСЕХ секциях
3. ✅ section_tags соответствуют фактическому контенту
4. ✅ header_moved_from заполняется корректно
5. ✅ Контракт start_line/end_line задокументирован
6. ✅ Регрессионные тесты добавлены
