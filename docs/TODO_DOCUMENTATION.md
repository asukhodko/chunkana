# Documentation TODO

## Тезисы для обновления документации

### 1. README.md - Обновить секции: ✅ COMPLETED

- [x] **Hierarchical Chunking** - добавить информацию о:
  - `validate_invariants` параметр (default: True)
  - `strict_mode` параметр (default: False)
  - Автоматическое исправление инвариантов в non-strict mode
  
- [x] **Configuration Options** - добавить новые параметры:
  ```python
  ChunkConfig(
      validate_invariants=True,  # Validate tree invariants
      strict_mode=False,         # Raise exceptions vs auto-fix
  )
  ```

- [x] **Exception Handling** - документировать новые исключения:
  - `ChunkanaError` - базовый класс
  - `HierarchicalInvariantError` - нарушения инвариантов дерева
  - `ValidationError` - ошибки валидации
  - `ConfigurationError` - ошибки конфигурации
  - `TreeConstructionError` - ошибки построения дерева

- [x] **Quality Features** - новая секция:
  - Dangling Header Prevention
  - Micro-Chunk Minimization
  - Tree Invariant Validation

### 2. API Reference - Новые компоненты: ⏳ DEFERRED

- [ ] **HeaderProcessor** (`header_processor.py`):
  - `DanglingHeaderDetector` - обнаружение "висячих" заголовков
  - `HeaderMover` - перемещение заголовков между чанками
  - `HeaderProcessor` - основной класс обработки

- [ ] **Exceptions** (`exceptions.py`):
  - Иерархия исключений с примерами использования
  - Формат сообщений об ошибках
  - Поле `suggested_fix` для actionable guidance

**Note**: Internal API, documented in code docstrings. Full API reference deferred to future release.

### 3. docs/debug_mode.md - ✅ COMPLETED

### 4. Новые metadata поля: ⏳ DEFERRED

- [ ] `dangling_header_fixed: bool` - был ли исправлен висячий заголовок
- [ ] `small_chunk: bool` - флаг маленького чанка
- [ ] `invariant_violations: list` - обнаруженные нарушения (в debug)

**Note**: These are internal metadata fields. Documented in code, not in user-facing docs.

### 5. Migration Guide: ✅ COMPLETED

- [x] Изменения в `get_flat_chunks()`:
  - Теперь включает non-leaf chunks с significant content (>100 chars)
  - Это предотвращает потерю контента
  
- [x] Новое поведение валидации:
  - По умолчанию включена (`validate_invariants=True`)
  - Auto-fix в non-strict mode
  - Exceptions в strict mode

### 6. Troubleshooting: ✅ COMPLETED

- [x] "HierarchicalInvariantError: is_leaf_consistency" - что делать
- [x] "HierarchicalInvariantError: parent_child_bidirectionality" - что делать
- [x] "HierarchicalInvariantError: orphaned_chunk" - что делать
- [x] Performance considerations

### 7. Examples: ✅ COMPLETED (in README and Migration Guide)

- [x] Пример использования strict_mode для отладки
- [x] Пример обработки HierarchicalInvariantError
- [ ] Пример работы с HeaderProcessor напрямую (internal API, deferred)

---

## Summary

### Completed ✅
1. README.md - updated with new features, configuration, exceptions, quality features
2. MIGRATION_GUIDE.md - updated with hierarchical chunking changes and troubleshooting
3. docs/debug_mode.md - created earlier

### Deferred ⏳
- Full API reference for internal components (HeaderProcessor, etc.)
- Detailed metadata field documentation

**Reason**: Internal APIs are documented in code docstrings. User-facing documentation focuses on public API.
