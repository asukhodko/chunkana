# Migration Content Analysis

## Document Analysis Results

### MIGRATION_GUIDE.md
**Status**: Содержит смешанную информацию
**Полезное содержимое для извлечения**:

1. **API Reference** - Полная таблица параметров и их соответствий:
   - Dify Tool Input Parameters → Chunkana mapping
   - ChunkConfig Fields → ChunkerConfig mapping
   - Renderer Selection Decision Tree

2. **Code Examples** - Практические примеры использования:
   - Basic chunking patterns
   - Hierarchical chunking examples
   - Advanced features (streaming, adaptive sizing, table grouping)

3. **Compatibility Guarantees** - Важная информация о совместимости:
   - Что гарантированно совпадает
   - Поведенческие различия
   - Troubleshooting guide

4. **Performance Benchmarks** - Полезные метрики производительности

**Миграционное содержимое для удаления**:
- Заголовки "Migration Guide"
- Секции "Breaking Changes" и "Step-by-Step Migration"
- Ссылки на старый плагин
- Checklist для миграции

### BASELINE.md
**Status**: Содержит смешанную информацию
**Полезное содержимое для извлечения**:

1. **Test Fixtures Documentation** - Описание тестовых данных:
   - Список всех fixtures и их назначение
   - Схемы данных для golden outputs

2. **Baseline Parameters** - Эталонные параметры конфигурации:
   - Значения по умолчанию для ChunkConfig
   - Параметры для воспроизведения результатов

3. **Renderer Mapping** - Техническая информация о рендерерах:
   - Соответствие параметров v2 и Chunkana
   - Поведение различных режимов

**Миграционное содержимое для удаления**:
- Ссылки на конкретный commit плагина
- Секции о генерации baseline из плагина
- Инструкции по регенерации baseline

### docs/integrations/dify.md
**Status**: Полезная документация API
**Действие**: Сохранить с минимальными изменениями

**Полезное содержимое**:
- Parameter mapping tables
- Code examples для Dify workflows
- Metadata format documentation
- Common pitfalls и troubleshooting

**Минимальные изменения**:
- Убрать упоминания "migration" в заголовках
- Обновить ссылки на MIGRATION_GUIDE.md

### docs/architecture/dify-integration.md
**Status**: Архитектурная документация
**Действие**: Сохранить как есть

**Содержимое**: Полностью полезная архитектурная документация без миграционных артефактов.

## Extraction Plan

### 1. Создать docs/api/parameter-mapping.md
Извлечь из MIGRATION_GUIDE.md:
- Complete Parameter Mapping tables
- Renderer Selection Decision Tree
- ChunkConfig field mappings

### 2. Создать docs/api/compatibility.md
Извлечь из MIGRATION_GUIDE.md:
- Compatibility Guarantees
- Behavioral Differences
- Performance Considerations

### 3. Создать docs/examples/advanced-usage.md
Извлечь из MIGRATION_GUIDE.md:
- Advanced Features examples
- Streaming, adaptive sizing, table grouping
- LaTeX preservation

### 4. Создать docs/testing/fixtures.md
Извлечь из BASELINE.md:
- Test fixtures documentation
- Golden output schemas
- Baseline parameters

### 5. Обновить docs/integrations/dify.md
- Убрать миграционные ссылки
- Сохранить всю API документацию

### 6. Обновить README.md
Добавить ссылки на новые документы:
- Parameter mapping
- Compatibility information
- Advanced usage examples