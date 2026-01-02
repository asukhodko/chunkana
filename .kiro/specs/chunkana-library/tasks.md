# Implementation Plan: Chunkana Library

## Overview

Создание Python-библиотеки Chunkana путём портирования core-логики из dify-markdown-chunker v2 методом "port 1:1". Структура модулей и логика сохраняются максимально близко к оригиналу.

**Ключевой принцип**: Сначала зафиксировать baseline, затем скопировать код как есть, затем прогнать baseline тесты, и только после их прохождения допускать любые изменения.

## Tasks

- [x] 0. Freeze baseline от dify-markdown-chunker v2
  - [x] 0.1 Зафиксировать commit hash плагина
    - Записать в BASELINE.md точный commit hash
    - _Requirements: 11.7_
  - [x] 0.2 Создать скрипт генерации baseline
    - Создать scripts/generate_baseline.py
    - Скрипт запускает v2 chunker на fixtures и сохраняет golden outputs
    - **Скрипт должен быть устойчив к типу возврата v2**: если list — берём list, если объект с `.chunks` — берём `.chunks`, если dict — вытаскиваем по ключу
    - Сохранять canonical chunks (без embedded overlap в content)
    - В Chunkana `include_metadata` не является параметром чанкинга; форматирование регулируется renderer'ом
    - _Requirements: 11.3, 11.7_
  - [x] 0.3 Создать baseline fixtures
    - Скопировать тестовые markdown файлы из плагина
    - Добавить edge cases: nested fences, large tables, complex lists, code-context
    - _Requirements: 11.3, 11.7_
  - [x] 0.4 Сгенерировать golden outputs
    - Запустить scripts/generate_baseline.py
    - Сохранить JSON с chunks и metadata в tests/baseline/golden/
    - **Документировать параметры**: max_chunk_size, overlap_size, strategy_override (если есть)
    - _Requirements: 11.7_
  - [x] 0.4b Сгенерировать view-level golden outputs
    - Сохранить `golden_dify_style/` — результат v2 с include_metadata=True (строки/JSONL)
    - Сохранить `golden_no_metadata/` — результат v2 с include_metadata=False (строки/JSONL)
    - Зафиксировать в BASELINE.md какой renderer соответствует v2 include_metadata=False (prev-only или bidirectional)
    - _Requirements: 11.7, 19.3_
  - [x] 0.5 Создать BASELINE.md
    - Документировать commit hash, дату генерации, список fixtures
    - **Документировать параметры baseline**: какие значения ChunkConfig использовались
    - **Пояснить**: baseline генерируется из v2 core-результатов в canonical виде (без embedded overlap)
    - Инструкции по регенерации golden outputs
    - _Requirements: 11.7_

- [x] 1. Инициализация репозитория и структуры проекта
  - [x] 1.1 Создать pyproject.toml с build-system и project metadata
    - name="chunkana", version="0.1.0", python_requires=">=3.12"
    - Включить extras: [dev], [docs]
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
  - [x] 1.2 Создать src-layout структуру директорий
    - src/chunkana/ с __init__.py
    - tests/ с conftest.py
    - docs/ с placeholder файлами
    - _Requirements: 10.1_
  - [x] 1.3 Создать базовые файлы документации
    - README.md с quickstart
    - CHANGELOG.md
    - CONTRIBUTING.md
    - _Requirements: 10.5, 10.6, 12.1, 12.5_

- [x] 2. Checkpoint - Проверить базовую структуру
  - Убедиться что `pip install -e .` работает
  - Убедиться что `python -c "import chunkana"` работает


- [x] 3. Портирование core-модулей из плагина (port 1:1)
  - [x] 3.1 Скопировать markdown_chunker_v2/ целиком в src/chunkana/
    - Сохранить структуру файлов: types.py, config.py, parser.py, chunker.py
    - Сохранить strategies/ как есть
    - Сохранить streaming/ как есть (существует в v2)
    - Сохранить adaptive_sizing.py, table_grouping.py, hierarchy.py
    - _Requirements: 1.4, 2.1-2.8, 3.1-3.7, 4.1-4.6, 8.1-8.5, 18.1-18.9_
  - [x] 3.2 Минимальные правки для работы без Dify SDK
    - Убрать импорты dify_plugin, dify_plugin.entities
    - Сохранить ChunkConfig как есть, добавить ChunkerConfig = ChunkConfig как алиас
    - Исправить относительные импорты
    - _Requirements: 6.4_
  - [x] 3.3 Портировать существующие тесты из плагина
    - Скопировать релевантные тесты из tests/
    - Адаптировать импорты
    - _Requirements: 11.1, 11.2_

- [x] 4. Checkpoint - Проверить что код компилируется
  - Запустить `python -c "from chunkana.chunker import MarkdownChunker"`
  - Исправить import errors

- [x] 5. Создание публичного API (тонкий слой поверх v2)
  - [x] 5.1 Создать src/chunkana/api.py с convenience функциями
    - chunk_markdown(text, config) → list[Chunk] (всегда List, не union)
    - analyze_markdown(text, config) → ContentAnalysis
    - chunk_with_analysis(text, config) → ChunkingResult
    - chunk_with_metrics(text, config) → tuple[list[Chunk], ChunkingMetrics]
    - iter_chunks(text, config) → Iterator[Chunk]
    - _Requirements: 1.1, 1.3, 1a.1-1a.4, 9.4_
  - [x] 5.2 Создать src/chunkana/renderers/
    - render_json(chunks) → list[dict]
    - render_inline_metadata(chunks) → list[str]
    - render_dify_style(chunks) → list[str]
    - render_with_embedded_overlap(chunks) → list[str] — bidirectional "rich context"
    - render_with_prev_overlap(chunks) → list[str] — prev-only "sliding window"
    - **Какой renderer соответствует v2 include_metadata=False — фиксируется в BASELINE.md**
    - **Renderers НЕ модифицируют Chunk объекты, только форматируют вывод**
    - _Requirements: 6.1-6.8_
  - [x] 5.3 Создать src/chunkana/validation.py
    - validate_chunks(text, chunks) → ValidationReport
    - ChunkingMetrics.from_chunks() (если не в types.py)
    - _Requirements: 9.1-9.3_
  - [x] 5.4 Обновить src/chunkana/__init__.py с публичными экспортами
    - Экспортировать все публичные классы и функции
    - _Requirements: 1.1, 1.2_

- [x] 6. Checkpoint - Проверить публичный API
  - Запустить простой тест: `chunk_markdown("# Hello\n\nWorld")`
  - Убедиться что возвращается list[Chunk]


- [x] 7. Baseline compatibility тесты (КРИТИЧНО)
  - [x] 7.1 Создать tests/baseline/ структуру
    - tests/baseline/fixtures/ — markdown файлы
    - tests/baseline/golden/ — ожидаемые JSON outputs (canonical chunks)
    - _Requirements: 11.3, 11.7_
  - [x] 7.2 Написать baseline compatibility тест
    - Сравнить output chunkana с golden outputs
    - **Baseline покрывает core output**: границы чанков, canonical content, ключевые metadata
    - **Baseline НЕ сравнивает**: `<metadata>...</metadata>` рендер, embedded overlap strings (это тесты renderers)
    - Структурное сравнение: start_line, end_line, strategy, header_path, content_type
    - Сравнение content: нормализация `\r\n -> \n`, но **НЕ использовать .strip()** — это скрывает баги
    - Сравнение metadata: все ключевые поля должны совпадать
    - _Requirements: 11.3, 11.7_
  - [x] 7.3 Запустить baseline тесты и исправить расхождения
    - Все fixtures должны проходить
    - Любое расхождение — баг в портировании
    - _Requirements: 11.7_
  - [x] 7.4 Renderer compatibility tests
    - Сравнить `render_dify_style(chunks)` с `golden_dify_style`
    - Сравнить выбранный renderer для include_metadata=False с `golden_no_metadata`
    - Выбор renderer'а (prev-only или bidirectional) — по BASELINE.md
    - _Requirements: 6.3, 6.4, 6.5, 19.3_

- [x] 8. Checkpoint - Baseline совместимость подтверждена
  - Все baseline тесты проходят
  - Output идентичен v2

- [x] 9. Сериализация и round-trip
  - [x] 9.1 Проверить Chunk.to_dict() и from_dict() (уже в types.py)
    - Убедиться что работает как в v2
    - _Requirements: 1.5, 1.7, 14.1_
  - [x] 9.2 Проверить Chunk.to_json() и from_json() (уже в types.py)
    - Убедиться что работает как в v2
    - _Requirements: 1.6, 1.8, 14.2_
  - [x] 9.3 Добавить ChunkerConfig.to_dict() и from_dict() если отсутствуют
    - Включить все поля включая code-context binding
    - _Requirements: 2.8, 14.3, 14.4_
  - [x] 9.4 Написать property тест для Chunk round-trip
    - **Property 1: Chunk Round-Trip (Dict)**
    - **Validates: Requirements 1.5, 1.7, 14.1**
  - [x] 9.5 Написать property тест для JSON round-trip
    - **Property 2: Chunk Round-Trip (JSON)**
    - **Validates: Requirements 1.6, 1.8, 14.2**
  - [x] 9.6 Написать property тест для Config round-trip
    - **Property 3: ChunkerConfig Round-Trip**
    - **Validates: Requirements 2.8, 14.3**

- [x] 10. Checkpoint - Проверить сериализацию
  - Запустить property тесты
  - Убедиться что round-trip работает


- [-] 11. Property-based тесты для инвариантов
  - [x] 11.1 Написать property тест для atomic block integrity
    - **Property 4: Atomic Block Integrity**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**
  - [ ] 11.2 Написать property тест для strategy selection
    - **Property 5: Strategy Selection Correctness**
    - **Validates: Requirements 3.1-3.5**
  - [x] 11.3 Написать property тест для required metadata
    - **Property 6: Required Metadata Presence**
    - **Validates: Requirements 5.1-5.5**
  - [ ] 11.4 Написать property тест для overlap metadata mode
    - **Property 7: Overlap Metadata Mode**
    - **Validates: Requirements 5.8, 5.9, 5.10**
  - [ ] 11.5 Написать property тест для overlap cap ratio
    - **Property 8: Overlap Cap Ratio**
    - **Validates: Requirements 5.11**
  - [x] 11.6 Написать property тест для line coverage
    - **Property 9: Line Coverage**
    - **Validates: Requirements 9.1**
  - [x] 11.7 Написать property тест для monotonic ordering
    - **Property 10: Monotonic Ordering**
    - **Validates: Requirements 9.2**
  - [ ] 11.8 Написать property тест для small chunk handling
    - **Property 11: Small Chunk Handling**
    - **Validates: Requirements 17.3, 17.4**
  - [ ] 11.9 Написать property тест для hierarchy navigation
    - **Property 12: Hierarchy Navigation Consistency**
    - **Validates: Requirements 7.2, 7.3**

- [ ] 12. Checkpoint - Проверить все property тесты
  - Запустить pytest tests/property/
  - Все тесты должны проходить

- [ ] 13. Unit тесты для edge cases
  - [ ] 13.1 Написать unit тесты для Chunk validation
    - Тесты на invalid start_line, end_line, empty content
    - _Requirements: 1.4_
  - [ ] 13.2 Написать unit тесты для ChunkerConfig validation
    - Тесты на invalid values, factory methods
    - _Requirements: 2.7_
  - [ ] 13.3 Написать unit тесты для renderers
    - Тесты на JSON format, inline metadata format
    - _Requirements: 6.1-6.3_
  - [ ] 13.4 Написать unit тесты для hierarchy navigation
    - Тесты на get_parent, get_children, get_ancestors
    - _Requirements: 7.2-7.4_


- [ ] 14. Документация
  - [ ] 14.1 Написать docs/quickstart.md
    - 3-10 строк кода для базового использования
    - _Requirements: 12.1_
  - [ ] 14.2 Написать docs/config.md
    - Все параметры конфигурации с описанием
    - Включить code-context binding параметры
    - _Requirements: 12.2_
  - [ ] 14.3 Написать docs/strategies.md
    - Описание каждой стратегии и критериев выбора
    - _Requirements: 12.2_
  - [ ] 14.4 Написать docs/renderers.md
    - Описание форматов вывода
    - _Requirements: 12.2_
  - [ ] 14.5 Написать docs/integrations/dify.md
    - Как использовать с Dify
    - _Requirements: 12.3_
  - [ ] 14.6 Написать docs/integrations/n8n.md
    - Как использовать с n8n
    - _Requirements: 12.3_
  - [ ] 14.7 Написать docs/integrations/windmill.md
    - Как использовать с windmill
    - _Requirements: 12.3_
  - [ ] 14.8 Написать MIGRATION_GUIDE.md
    - **Breaking changes**: `chunk()` всегда возвращает `List[Chunk]`, не union
    - **Parameter mapping**:
      - `include_metadata=True` → `render_dify_style()`
      - `include_metadata=False` → renderer по BASELINE.md (prev-only или bidirectional)
    - **Decision tree для выбора renderer'а**:
      - Dify plugin (include_metadata=True) → `render_dify_style`
      - Dify plugin (include_metadata=False) → renderer по baseline
      - "Больше контекста, чем в v2" → `render_with_embedded_overlap`
      - "Классический sliding window" → `render_with_prev_overlap`
    - **Code snippets**: "до" (dify-markdown-chunker) и "после" (chunkana + renderer)
    - **Compatibility guarantees**: границы чанков, metadata schema
    - **Not guaranteed 1:1**: output formatting, Dify-specific parameters
    - _Requirements: 19.1-19.6_

- [ ] 15. CI/CD настройка
  - [ ] 15.1 Создать .github/workflows/ci.yml
    - pytest, mypy, ruff на Python 3.12
    - python -m build, twine check dist/*
    - _Requirements: 13.1-13.3, 13.7_
  - [ ] 15.2 Создать .github/workflows/publish.yml
    - Trusted Publishing на tag push
    - permissions: contents: read, id-token: write
    - _Requirements: 13.4-13.6_
  - [ ] 15.3 Создать .gitignore, pyproject.toml [tool.ruff], [tool.mypy]
    - Использовать ruff (как в плагине или совместимый)
    - _Requirements: 13.1_

- [ ] 16. Финальная проверка
  - [ ] 16.1 Запустить полный тестовый suite
    - pytest --cov=chunkana
    - Проверить coverage >= 80%
    - _Requirements: 11.5_
  - [ ] 16.2 Проверить сборку пакета
    - python -m build
    - twine check dist/*
    - _Requirements: 13.2, 13.3_
  - [ ] 16.3 Проверить установку из wheel
    - pip install dist/*.whl
    - python -c "import chunkana; print(chunkana.__version__)"

- [ ] 17. Checkpoint - Готовность к публикации
  - Все тесты проходят (baseline, property, unit)
  - Документация написана
  - CI workflows настроены
  - Пакет собирается и проходит twine check

- [ ] 18. Дополнительные задачи (инфраструктура)
  - [x] 18.1 Добавить LICENSE файл (MIT)
    - Скопировать MIT license с правильным copyright
    - Убедиться что license metadata в pyproject.toml соответствует
    - _Requirements: 10.7 (LICENSE file and license metadata in pyproject.toml)_
  - [ ] 18.2 Настроить `__version__` в `__init__.py`
    - Использовать importlib.metadata или hardcoded version
    - Синхронизировать с pyproject.toml
    - _Requirements: 10.2_
  - [ ] 18.3 (Опционально) Создать mkdocs.yml для документации
    - Если планируется публикация docs на GitHub Pages
    - _Requirements: 12.2_
  - [ ] 18.4 Сделать baseline скрипт портируемым
    - Скрипт должен работать из любой директории
    - Использовать относительные пути от скрипта
    - _Requirements: 11.7_

## Notes

- **Task 0 критичен**: без baseline невозможно гарантировать совместимость
- **Port 1:1 для логики**: структура модулей и алгоритмы сохраняются, но API намеренно упрощается
- **Python 3.12**: совпадает с dify-markdown-chunker v2
- **Code-context binding**: все флаги из v2 должны быть сохранены
- Property тесты используют hypothesis с минимум 100 итерациями
- Baseline тесты — главный критерий успеха портирования

### Design Decisions (зафиксированы)

- **A1 (API)**: `chunk()` и `chunk_markdown()` всегда возвращают `List[Chunk]`. Расширенные результаты — через отдельные методы (`chunk_with_analysis`, `chunk_with_metrics`). Это breaking change vs v2.
- **A2 (Overlap)**: `chunk.content` всегда canonical (без embedded overlap). Overlap хранится в metadata. Вшивание overlap в content — это renderer-level операция (`render_with_embedded_overlap`).
- **A3 (Responsibility)**: Библиотека отвечает за chunking + renderers. Плагин отвечает за маппинг Dify параметров и выбор renderer'а.
- **A4 (Baseline)**: Baseline сравнивает core output (canonical chunks + metadata), не Dify-форматирование. Не использовать `.strip()` для "прощения" расхождений.

## Red Flags (что НЕ делать при переносе)

- ❌ Менять логику генерации chunk_id (8-char SHA256 hash)
- ❌ Менять формат header_path (должен быть string "/Level1/Level2")
- ❌ Менять порядок/границы чанков из-за "улучшенного" парсера
- ❌ "Оптимизировать" overlap (особенно cap 0.35)
- ❌ "Упрощать" конфиг (выкидывать code-context binding флаги)
- ❌ Переименовывать модули/пакеты до прохождения baseline
- ❌ Менять ChunkConfig на ChunkerConfig (только добавить алиас)

