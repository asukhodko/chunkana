# Tasks: V2 Critical Fixes

## Task 1: Исправить порядок стадий в пайплайне

### Subtask 1.1: Переместить SectionSplitter после HeaderProcessor
- [x] В `MarkdownChunker.chunk()` переместить вызов `split_oversize_sections()` ПОСЛЕ `prevent_dangling_headers()`
- [x] Обновить docstring метода `chunk()` с объяснением порядка
- [x] Добавить комментарий: "КРИТИЧНО: dangling fix ДО split, чтобы заголовки были в чанках"

### Subtask 1.2: Тесты на порядок стадий
- [x] Тест: после dangling fix чанки содержат свои заголовки
- [x] Тест: после split продолжающие чанки имеют header_stack
- [x] Тест: на документе из отчёта `#### Итоги работы` не теряется

---

## Task 2: Создать SectionSplitter с header_stack

### Subtask 2.1: Базовая структура
- [x] Создать файл `src/chunkana/section_splitter.py`
- [x] Класс `SectionSplitter` с конструктором
- [x] Метод `split_oversize_sections(chunks) -> list[Chunk]`
- [x] Метод `_needs_splitting(chunk) -> bool`
- [x] Метод `_is_atomic_block(chunk) -> bool`

### Subtask 2.2: Извлечение header_stack
- [x] Реализовать `_extract_header_stack_and_body(content) -> tuple[str, str]`
- [x] Header_stack = последовательность подряд идущих header-строк в начале
- [x] Тесты: `## Impact\n\n#### Итоги работы\n\n1. Пункт` → header_stack = оба заголовка
- [x] Тесты: пустые строки между заголовками сохраняются

### Subtask 2.3: Детекция сегментов
- [x] Реализовать `_split_by_list_items(body) -> list[str]`
- [x] Реализовать `_split_by_paragraphs(body) -> list[str]`
- [x] Реализовать `_split_by_sentences(body) -> list[str]` (fallback)
- [x] Тесты на каждый тип

### Subtask 2.4: Pack segments into chunks
- [x] Реализовать `_pack_segments_into_chunks()` — алгоритм "pack until full"
- [x] Повторение header_stack в каждом продолжающем чанке
- [x] Обработка oversize сегментов (list_item_integrity)
- [x] Тесты на упаковку

### Subtask 2.5: Метаданные split-чанков
- [x] Добавить `continued_from_header: bool`
- [x] Добавить `split_index: int`
- [x] Добавить `original_section_size: int`
- [x] Тесты на метаданные

---

## Task 3: Улучшить HeaderProcessor

### Subtask 3.1: Расширить детекцию на уровни 2-6
- [x] Изменить паттерн с `#{3,6}` на `#{2,6}`
- [x] Тесты на заголовки уровня 2 (##)

### Subtask 3.2: Уменьшить порог детекции
- [x] Изменить `min_content_threshold` с 50 на 30
- [x] Тесты на граничные случаи (29, 30, 31 символ)

### Subtask 3.3: Использовать chunk_id для tracking
- [x] Заменить `header_moved_from` (chunk_index) на `header_moved_from_id` (chunk_id)
- [x] Обновить `HeaderMover.fix()` для использования chunk_id
- [x] Тесты на стабильность tracking после split/merge

### Subtask 3.4: Тесты на все секции документа
- [x] Параметризованный тест по секциям: Scope, Impact, Leadership, Improvement, Technical Complexity
- [x] Тест на `#### Итоги работы` во всех секциях
- [x] Тест на `#### Кто участвовал` во всех секциях

---

## Task 4: Удалить/ограничить section_integrity oversize

### Subtask 4.1: Удалить section_integrity для текста/списков
- [x] В `_validate()` убрать `section_integrity` из автоматически назначаемых причин
- [x] Оставить только: `code_block_integrity`, `table_integrity`, `list_item_integrity`
- [x] Тесты: текстовая секция > max_size НЕ получает allow_oversize

### Subtask 4.2: Обновить документацию
- [x] Обновить docstrings с новым списком валидных причин
- [x] Обновить CHANGELOG

---

## Task 5: Создать InvariantValidator с recall-метрикой

### Subtask 5.1: Базовая структура
- [x] Создать файл `src/chunkana/invariant_validator.py`
- [x] Класс `InvariantValidator`
- [x] Dataclass `ValidationResult` с полем `coverage: float`

### Subtask 5.2: Проверка dangling headers (уровни 1-6)
- [x] Реализовать `_check_no_dangling_headers()` для ВСЕХ уровней 1-6
- [x] Тесты

### Subtask 5.3: Проверка oversize
- [x] Реализовать `_check_no_invalid_oversize()`
- [x] Валидные причины: code_block_integrity, table_integrity, list_item_integrity
- [x] Тесты

### Subtask 5.4: Recall-метрика coverage
- [x] Реализовать `_calculate_line_recall(chunks, original) -> float`
- [x] Строки ≥20 символов, нормализация whitespace
- [x] Тесты: повторение заголовков НЕ улучшает recall
- [x] Тесты: overlap НЕ улучшает recall

### Subtask 5.5: Интеграция валидатора
- [x] Экспортирован в __init__.py для использования
- [ ] Опциональный вызов в `chunk()` при debug=True (отложено)

---

## Task 6: Пересчёт line ranges после split/move

### Subtask 6.1: Документировать контракт
- [x] Line ranges могут пересекаться при header repetition
- [x] Добавить в docstrings

### Subtask 6.2: Корректный пересчёт в SectionSplitter
- [x] Split-чанки наследуют start_line/end_line от оригинала
- [x] Тесты на пересечение ranges

### Subtask 6.3: Корректный пересчёт в HeaderMover
- [x] При переносе заголовка обновить start_line/end_line обоих чанков
- [x] Тесты

---

## Task 7: Регрессионные тесты на реальном документе

### Subtask 7.1: Fixture
- [x] Файл `tests/fixtures/sde_criteria.md` (уже создан)
- [x] Pytest fixture `sde_criteria_document`

### Subtask 7.2: Тесты на dangling headers
- [x] `test_no_dangling_in_scope_section`
- [x] `test_no_dangling_in_impact_section`
- [x] `test_no_dangling_in_leadership_section`
- [x] `test_no_dangling_in_improvement_section`
- [x] `test_no_dangling_in_technical_complexity_section`

### Subtask 7.3: Тесты на max_chunk_size
- [x] `test_no_invalid_oversize`
- [x] `test_all_chunks_within_size_or_valid_reason`

### Subtask 7.4: Тесты на header_stack repetition
- [x] `test_continued_chunks_have_header_stack`
- [x] `test_split_index_is_sequential`

### Subtask 7.5: Тесты на coverage
- [x] `test_content_coverage_recall_at_least_95_percent`
- [x] `test_coverage_not_inflated_by_repetition`

### Subtask 7.6: Тесты на tracking
- [x] `test_header_moved_from_id_is_stable_chunk_id`
- [ ] `test_header_moved_from_id_survives_split` (отложено - требует более сложного сценария)

---

## Task 8: Обновить экспорты и документацию

### Subtask 8.1: Обновить __init__.py
- [x] Экспортировать `SectionSplitter`
- [x] Экспортировать `InvariantValidator`, `InvariantValidationResult`

### Subtask 8.2: Обновить README
- [ ] Документировать порядок стадий (отложено)
- [ ] Документировать header_stack repetition (отложено)
- [ ] Документировать line range contract (отложено)
- [ ] Документировать recall-метрику coverage (отложено)

### Subtask 8.3: Обновить CHANGELOG
- [x] Критические исправления dangling headers
- [x] Удаление section_integrity
- [x] Новые метаданные: continued_from_header, split_index, header_moved_from_id
