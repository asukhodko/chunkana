# Migration Artifacts Catalog

## Overview

Каталог всех найденных артефактов миграции в библиотеке chunkana, созданных для поддержки миграции плагина dify-markdown-chunker.

## Migration Documents

### Primary Migration Documents
- `MIGRATION_GUIDE.md` - Руководство по миграции
- `BASELINE.md` - Baseline документ с эталонными данными

### Plugin-Specific Documentation
- `docs/integrations/dify.md` - Документация интеграции с Dify
- `docs/architecture/dify-integration.md` - Архитектурная документация интеграции

## Plugin-Specific Code

### Renderer Functions
- `chunkana/src/chunkana/renderers/formatters.py`:
  - `render_dify_style()` - функция рендеринга в формате Dify (строка 56)

### Test Files with Dify Functions
- `chunkana/tests/unit/test_renderers.py`:
  - `TestRenderDifyStyle` класс (строка 97)
  - `test_render_dify_style_export()` (строка 47)

- `chunkana/tests/unit/test_exports.py`:
  - `test_render_dify_style_export()` (строка 47)
  - `TestNoDifySDKImports` класс (строка 144)
  - `test_no_dify_imports_in_init()` (строка 147)
  - `test_no_dify_in_api_module()` (строка 160)
  - `test_no_dify_in_renderers()` (строка 172)

- `chunkana/tests/property/test_renderers.py`:
  - `TestRenderDifyStyleFormat` класс (строка 232)

- `chunkana/tests/baseline/test_renderer_compatibility.py`:
  - `test_render_dify_style_compatibility()` (строка 46)
  - `test_golden_dify_style_outputs_exist()` (строка 141)

### Baseline Generation Scripts
- `chunkana/scripts/generate_baseline.py`:
  - `render_dify_style()` функция (строка 90)

## Test Artifacts

### Integration Tests
- `chunkana/tests/test_dify_bug_fix_integration.py` - тесты исправления багов Dify
- `chunkana/tests/integration/test_dify_hierarchical_integration.py` - тесты иерархической интеграции
- `chunkana/tests/integration/test_dify_plugin_integration.py` - тесты интеграции плагина

### Compatibility Tests
- `chunkana/tests/baseline/test_renderer_compatibility.py` - тесты совместимости рендереров

## Configuration Files

### Dify-Specific Config
- `.difyignore` - файл игнорирования для Dify

## Classification Summary

### Documents (4 files)
- MIGRATION_GUIDE.md - **DELETE** (только миграция)
- BASELINE.md - **ANALYZE** (смешанное содержимое)
- docs/integrations/dify.md - **PRESERVE** (полезная документация API)
- docs/architecture/dify-integration.md - **PRESERVE** (архитектурная документация)

### Code (1 core function)
- render_dify_style() - **REPORT** (plugin-specific, сложность: medium)

### Tests (7 files)
- Dify integration tests - **DELETE** (только совместимость)
- Dify compatibility tests - **DELETE** (только совместимость)
- Dify unit tests - **DELETE** (только совместимость)

### Config (1 file)
- .difyignore - **DELETE** (только для плагина)

## Dependencies Analysis

### Safe to Remove
- Все тесты Dify (не влияют на основную функциональность)
- .difyignore (конфигурация плагина)
- MIGRATION_GUIDE.md (только информация о миграции)

### Requires Analysis
- render_dify_style() - используется в экспортах библиотеки
- docs/integrations/dify.md - может содержать полезную API документацию
- BASELINE.md - может содержать полезные эталонные данные

## Next Steps

1. Анализ документов миграции на предмет полезного содержимого
2. Извлечение полезной информации в основную документацию
3. Создание детального отчёта о plugin-specific коде
4. Планирование безопасного удаления артефактов