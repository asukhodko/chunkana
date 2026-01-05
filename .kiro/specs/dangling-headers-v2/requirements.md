# Requirements Document: Dangling Headers v2 & Metadata Consistency

## Introduction

Данная спецификация адресует проблемы, выявленные в тестировании v2 (TEST_REPORT_v2.md):
1. Dangling headers фикс работает частично — только в секции Scope, но не в Impact, Leadership, Improvement
2. `section_tags` не пересчитываются после переноса заголовков
3. `header_moved_from` всегда null
4. Несогласованность `start_line/end_line` в hierarchical режиме

## Glossary

- **Dangling_Header**: Заголовок (####), который остаётся в конце чанка, а его контент (список/абзац) — в следующем чанке
- **section_tags**: Метаданные, содержащие теги секций внутри чанка
- **header_moved_from**: Поле метаданных, указывающее откуда был перенесён заголовок
- **Hierarchical_Mode**: Режим чанкинга с построением дерева parent-child отношений

## Requirements

### Requirement 1: Универсальный Dangling Header Fix

**User Story:** Как пользователь, выполняющий семантический поиск, я хочу чтобы заголовки всегда находились вместе со своим контентом, независимо от секции документа.

#### Acceptance Criteria

1. WHEN заголовок `#### Итоги работы` находится в конце чанка, THEN он SHALL быть перенесён в следующий чанк вместе со списком
2. WHEN заголовок `#### Кто участвовал в реализации` находится в конце чанка, THEN он SHALL быть перенесён в следующий чанк вместе с текстом
3. WHEN dangling header fix применяется, THEN он SHALL работать во ВСЕХ секциях документа (Scope, Impact, Leadership, Improvement, Technical Complexity)
4. WHEN чанк помечен `allow_oversize: true`, THEN заголовок секции SHALL быть включён в этот чанк
5. WHEN dangling header обнаружен, THEN поле `dangling_header_fixed` SHALL быть установлено в `true`

### Requirement 2: Пересчёт section_tags после переноса заголовков

**User Story:** Как разработчик, использующий section_tags для фильтрации, я хочу чтобы теги соответствовали фактическому содержимому чанка.

#### Acceptance Criteria

1. WHEN заголовок перенесён из чанка A в чанк B, THEN section_tags чанка A SHALL быть пересчитаны без этого заголовка
2. WHEN заголовок перенесён в чанк B, THEN section_tags чанка B SHALL включать этот заголовок
3. WHEN section_tags содержит "Итоги работы", THEN контент чанка SHALL содержать заголовок `#### Итоги работы`
4. WHEN пост-обработка (dangling fix, merge) завершена, THEN section_tags SHALL быть пересчитаны на финальных чанках
5. THE порядок операций SHALL быть: chunk → dangling fix → merge → recalculate section_tags

### Requirement 3: Информативное поле header_moved_from

**User Story:** Как разработчик, отлаживающий чанкинг, я хочу знать откуда был перенесён заголовок для трассировки.

#### Acceptance Criteria

1. WHEN заголовок перенесён из чанка A в чанк B, THEN header_moved_from в чанке B SHALL содержать chunk_index чанка A
2. WHEN заголовок НЕ был перенесён, THEN header_moved_from SHALL быть null или отсутствовать
3. WHEN несколько заголовков перенесены в один чанк, THEN header_moved_from SHALL быть списком источников
4. IF поле не может быть заполнено корректно, THEN оно SHALL быть удалено из схемы метаданных

### Requirement 4: Согласованный контракт start_line/end_line в hierarchical режиме

**User Story:** Как разработчик, использующий hierarchical режим, я хочу понимать семантику start_line/end_line для всех типов узлов.

#### Acceptance Criteria

1. WHEN узел является leaf, THEN start_line/end_line SHALL покрывать только контент этого чанка
2. WHEN узел является internal (не leaf, не root), THEN start_line/end_line SHALL покрывать только контент этого чанка (не детей)
3. WHEN узел является root, THEN start_line/end_line SHALL покрывать весь документ (1 до последней строки)
4. THE контракт SHALL быть явно задокументирован в README и docstrings
5. WHEN контракт нарушен, THEN валидация SHALL выдавать предупреждение

### Requirement 5: Регрессионные тесты для выявленных проблем

**User Story:** Как мейнтейнер библиотеки, я хочу иметь тесты, которые предотвратят повторение этих проблем.

#### Acceptance Criteria

1. WHEN тест запускается, THEN он SHALL проверять dangling headers во ВСЕХ секциях тестового документа
2. WHEN тест запускается, THEN он SHALL проверять соответствие section_tags фактическому контенту
3. WHEN тест запускается, THEN он SHALL проверять корректность header_moved_from
4. WHEN тест запускается, THEN он SHALL проверять согласованность start_line/end_line контракта
5. THE тесты SHALL использовать реальный документ из TEST_REPORT_v2 как fixture
