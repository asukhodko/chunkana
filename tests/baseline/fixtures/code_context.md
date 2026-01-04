# Code Context Binding Document

This document tests code-context binding scenarios where explanatory text should be bound to code blocks.

## Function Documentation

The following function calculates factorial recursively:

```python
def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

The time complexity is O(n) and space complexity is O(n) due to recursion.

## Input/Output Examples

Here's how to use the sorting function:

```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```

Example output:

```
>>> quicksort([3, 6, 8, 10, 1, 2, 1])
[1, 1, 2, 3, 6, 8, 10]
```

## Before/After Pairs

Before optimization:

```python
def slow_sum(numbers):
    total = 0
    for n in numbers:
        total = total + n
    return total
```

After optimization:

```python
def fast_sum(numbers):
    return sum(numbers)
```

## Related Code Blocks

Configuration setup:

```yaml
database:
  host: localhost
  port: 5432
  name: myapp
```

Connection code:

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="myapp"
)
```

## Conclusion

Code context binding helps keep related content together.
