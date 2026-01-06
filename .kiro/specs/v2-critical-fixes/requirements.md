# Requirements Document: V2 Critical Fixes (Post-Testing Report)

## Introduction

Данная спецификация адресует критические проблемы, выявленные в тестировании качества чанкования после миграции на библиотеку chunkana. Отчёт выявил три критических дефекта (CHNK-CRIT-02, CHNK-CRIT-03) и один высокоприоритетный (CHNK-HIGH-04), требующие исправления в библиотеке.

**Связанные дефекты:**
- CHNK-CRIT-02: Разрыв заголовков от контента (dangling headers)
- CHNK-CRIT-03: Нарушение Max Chunk Size (allow_oversize)
- CHNK-HIGH-04: Уникальный контент в non-leaf узлах (частично)

## Glossary

- **Dangling_Header**: Заголовок (уровня 2-6), который остаётся в конце чанка, а его контент — в следующем чанке
- **Oversize_Chunk**: Чанк, размер которого превышает max_chunk_size
- **Section_Integrity**: УСТАРЕВШАЯ причина oversize — подлежит удалению для текстовых секций
- **List_Boundary**: Граница между пунктами списка, пригодная для разбиения
- **Header_Repetition**: Повторение заголовка (или стека заголовков) в начале продолжающего чанка
- **Header_Stack**: Последовательность заголовков в начале чанка до первого контентного блока (например: `## Impact` + `#### Итоги работы`)
- **Chunk_Size_Unit**: Единица измерения размера чанка — **символы UTF-8** (`len(str)` в Python), измеряется на `chunk.content` до рендеринга и без metadata-блоков
- **Overlap_Model**: Модель "сдвиг окна" — overlap хранится в metadata (`previous_content`, `next_content`), НЕ дублируется в `chunk.content`, размер чанка проверяется БЕЗ учёта overlap
- **Content_Coverage**: Метрика полноты покрытия — **recall оригинальных строк** (доля строк оригинала длиной ≥20 символов, которые присутствуют хотя бы в одном чанке)

## Requirements

### Requirement 1: Полное устранение Dangling Headers

**User Story:** Как пользователь RAG-системы, я хочу чтобы каждый чанк был самодостаточным и содержал заголовок вместе с его контентом.

**Связанный дефект:** CHNK-CRIT-02

#### Acceptance Criteria

1. WHEN чанк заканчивается заголовком уровня 2-6 (##, ###, ####, #####, ######), AND следующий чанк содержит контент этого заголовка, THEN заголовок SHALL быть перенесён в следующий чанк
2. WHEN заголовок `#### Итоги работы` находится в конце чанка, THEN он SHALL быть перенесён вместе с первыми пунктами списка
3. WHEN заголовок `#### Кто участвовал в реализации` находится в конце чанка, THEN он SHALL быть перенесён вместе с текстом участника
4. WHEN dangling header обнаружен в секциях Impact, Leadership, Improvement, Technical Complexity, THEN он SHALL быть исправлен так же как в секции Scope
5. WHEN dangling header исправлен, THEN поле `dangling_header_fixed` SHALL быть `true`, AND `header_moved_from_id` SHALL содержать стабильный chunk_id источника (не chunk_index)
6. WHEN перенос заголовка выполнен, THEN он SHALL выполняться ДО разбиения oversize-секций (см. Requirement 2)

### Requirement 2: Жёсткое соблюдение Max Chunk Size

**User Story:** Как администратор vector DB, я хочу чтобы все чанки соблюдали заданный лимит размера для предсказуемой работы эмбеддингов.

**Связанный дефект:** CHNK-CRIT-03

#### Acceptance Criteria

1. WHEN max_chunk_size=1000, THEN ни один чанк SHALL NOT иметь `len(chunk.content) > 1000` при стандартной конфигурации (кроме атомарных блоков)
2. WHEN секция содержит длинный список, THEN она SHALL быть разбита по границам пунктов списка
3. WHEN секция разбита на несколько чанков, THEN каждый продолжающий чанк SHALL начинаться с **header_stack** секции (все заголовки от начала чанка до первого контентного блока)
4. WHEN чанк разбит, THEN метаданные SHALL содержать `continued_from_header: true` и `split_index: N` для продолжающих чанков
5. WHEN атомарный блок (код, таблица) превышает max_chunk_size, THEN allow_oversize SHALL быть `true` с причиной `code_block_integrity` или `table_integrity`
6. WHEN секция текста/списка превышает max_chunk_size, THEN allow_oversize SHALL NOT применяться — секция SHALL быть разбита
7. THE причина `section_integrity` для oversize SHALL быть УДАЛЕНА или ограничена только случаями, когда разбиение технически невозможно (единственный пункт списка > max_chunk_size)
8. THE проверка размера SHALL применяться к `chunk.content` БЕЗ учёта overlap (overlap хранится в metadata, не в content)

### Requirement 3: Умное разбиение длинных секций

**User Story:** Как пользователь, я хочу чтобы длинные секции разбивались интеллектуально, сохраняя контекст.

#### Acceptance Criteria

1. WHEN секция содержит нумерованный список, THEN разбиение SHALL происходить между пунктами списка (не внутри пункта)
2. WHEN секция содержит маркированный список, THEN разбиение SHALL происходить между пунктами списка
3. WHEN секция содержит абзацы без списков, THEN разбиение SHALL происходить между абзацами (на `\n\n`)
4. WHEN разбиение происходит, THEN **header_stack** секции SHALL быть повторён в начале каждого продолжающего чанка
5. WHEN пункт списка сам по себе превышает max_chunk_size, THEN он SHALL быть разбит по предложениям с пометкой `allow_oversize: true, oversize_reason: "list_item_integrity"` только если разбиение невозможно
6. THE минимальный контент после header_stack в чанке SHALL быть не менее 100 символов (избежание "почти пустых" чанков)
7. THE header_stack для повторения SHALL извлекаться как последовательность подряд идущих header-строк в начале чанка (до первого non-header контента)

### Requirement 4: Инвариант — чанк не заканчивается заголовком

**User Story:** Как разработчик, я хочу иметь формальный инвариант для валидации качества чанкования.

#### Acceptance Criteria

1. FOR ALL chunks in result, IF chunk is not last, THEN chunk.content SHALL NOT end with a header line of ANY level (1-6) after stripping whitespace
2. WHEN инвариант нарушен, THEN валидация SHALL выдавать ошибку в strict режиме или warning в non-strict
3. THE инвариант SHALL быть проверяем через метод `validate_no_dangling_headers(chunks)`
4. WHEN debug=True, THEN результат валидации SHALL быть включён в метаданные

### Requirement 5: Корректная работа hierarchical режима с leaf-only

**User Story:** Как пользователь hierarchical режима, я хочу чтобы leaf-only фильтрация не теряла контент.

**Связанный дефект:** CHNK-HIGH-04 (частично)

#### Acceptance Criteria

1. WHEN узел имеет `is_leaf=false` AND содержит уникальный контент (не дублированный в детях), THEN этот контент SHALL быть доступен через `get_flat_chunks()`
2. WHEN `get_flat_chunks()` вызван, THEN он SHALL возвращать все leaf-узлы PLUS non-leaf узлы с significant content (>100 символов non-header текста)
3. WHEN библиотека устанавливает `indexable` поле, THEN downstream consumers (плагины) SHALL уважать это значение
4. THE метод `validate_content_coverage(chunks, original_text)` SHALL проверять полноту покрытия как **recall оригинальных строк** (≥95%)

### Requirement 6: Регрессионные тесты на реальном документе

**User Story:** Как мейнтейнер библиотеки, я хочу иметь тесты, предотвращающие регрессию выявленных проблем.

#### Acceptance Criteria

1. THE тестовый документ из отчёта (SDE criteria + пример задачи) SHALL быть добавлен как fixture
2. WHEN тест запускается, THEN он SHALL проверять отсутствие dangling headers во ВСЕХ секциях (уровни 2-6)
3. WHEN тест запускается, THEN он SHALL проверять соблюдение max_chunk_size для всех чанков (кроме атомарных)
4. WHEN тест запускается, THEN он SHALL проверять корректность header_moved_from_id (стабильный chunk_id)
5. WHEN тест запускается, THEN он SHALL проверять полноту покрытия контента как recall ≥95%
6. THE тесты SHALL быть параметризованы для конфигураций: max_chunk_size=1000, overlap=200, strategy=auto

### Requirement 7: Контракт на line ranges после перемещений/дублирования

**User Story:** Как разработчик, я хочу понимать семантику start_line/end_line после операций split/move.

#### Acceptance Criteria

1. WHEN заголовок перемещён или повторён, THEN `start_line/end_line` SHALL отражать минимальную/максимальную исходную строку, присутствующую в content чанка
2. WHEN чанки имеют повторённые заголовки, THEN их line ranges МОГУТ пересекаться — это допустимо
3. THE контракт SHALL быть задокументирован: "line ranges могут пересекаться при header repetition"

