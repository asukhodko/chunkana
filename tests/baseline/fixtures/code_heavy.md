# Code-Heavy Document

This document contains lots of code blocks for testing code-focused chunking.

## Python Example

Here's a Python function:

```python
def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Example usage
for i in range(10):
    print(f"F({i}) = {calculate_fibonacci(i)}")
```

## JavaScript Example

And here's some JavaScript:

```javascript
class DataProcessor {
    constructor(data) {
        this.data = data;
        this.processed = false;
    }
    
    process() {
        if (this.processed) {
            throw new Error('Already processed');
        }
        
        this.data = this.data.map(item => ({
            ...item,
            timestamp: Date.now(),
            processed: true
        }));
        
        this.processed = true;
        return this.data;
    }
}

const processor = new DataProcessor([{id: 1}, {id: 2}]);
console.log(processor.process());
```

## SQL Example

Database queries:

```sql
SELECT 
    u.id,
    u.username,
    COUNT(p.id) as post_count,
    MAX(p.created_at) as last_post
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
WHERE u.active = true
GROUP BY u.id, u.username
HAVING COUNT(p.id) > 5
ORDER BY last_post DESC
LIMIT 10;
```

## Conclusion

Code blocks should be kept together when possible.
