# Adaptive Sizing Document

This document tests adaptive chunk sizing with varying content density.

## Dense Code Section

This section has high code density:

```python
class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.data = []
        self.processed = False
    
    def load(self, source):
        with open(source) as f:
            self.data = json.load(f)
        return self
    
    def transform(self, func):
        self.data = [func(item) for item in self.data]
        return self
    
    def filter(self, predicate):
        self.data = [item for item in self.data if predicate(item)]
        return self
    
    def save(self, target):
        with open(target, 'w') as f:
            json.dump(self.data, f)
        self.processed = True
        return self
```

```python
def process_batch(items, batch_size=100):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        processed = [transform(item) for item in batch]
        results.extend(processed)
    return results
```

## Sparse Text Section

This section contains mostly prose with minimal structure.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

## Mixed Density Section

Some introductory text here.

```javascript
const handler = async (req, res) => {
    const { id } = req.params;
    const data = await fetchData(id);
    res.json(data);
};
```

More explanatory text between code blocks.

```javascript
app.get('/api/:id', handler);
```

Final remarks about the implementation.

## List-Heavy Section

Key features:
- Feature A with detailed description
- Feature B with another description
- Feature C with yet another description
- Feature D
- Feature E
- Feature F

Implementation steps:
1. Initialize the system
2. Configure parameters
3. Load data sources
4. Process records
5. Validate results
6. Export output

## Conclusion

Adaptive sizing should adjust chunk sizes based on content density.
