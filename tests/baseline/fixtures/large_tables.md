# Large Tables Document

This document contains various table structures for testing table handling.

## Simple Table

| Name  | Age | City     |
|-------|-----|----------|
| Alice | 30  | New York |
| Bob   | 25  | London   |
| Carol | 35  | Paris    |

## Wide Table

| ID | Name | Email | Phone | Address | City | Country | Postal | Status | Created |
|----|------|-------|-------|---------|------|---------|--------|--------|---------|
| 1 | Alice | alice@example.com | 555-0101 | 123 Main St | NYC | USA | 10001 | Active | 2024-01-01 |
| 2 | Bob | bob@example.com | 555-0102 | 456 Oak Ave | LA | USA | 90001 | Active | 2024-01-02 |
| 3 | Carol | carol@example.com | 555-0103 | 789 Pine Rd | CHI | USA | 60601 | Inactive | 2024-01-03 |

## Tall Table

| Item | Value |
|------|-------|
| Row 1 | Data 1 |
| Row 2 | Data 2 |
| Row 3 | Data 3 |
| Row 4 | Data 4 |
| Row 5 | Data 5 |
| Row 6 | Data 6 |
| Row 7 | Data 7 |
| Row 8 | Data 8 |
| Row 9 | Data 9 |
| Row 10 | Data 10 |
| Row 11 | Data 11 |
| Row 12 | Data 12 |

## Table with Alignment

| Left | Center | Right |
|:-----|:------:|------:|
| L1   | C1     | R1    |
| L2   | C2     | R2    |
| L3   | C3     | R3    |

## Multiple Related Tables

### Users Table

| UserID | Username | Role |
|--------|----------|------|
| 1 | admin | Administrator |
| 2 | user1 | User |
| 3 | user2 | User |

### Permissions Table

| RoleID | Permission |
|--------|------------|
| 1 | read |
| 1 | write |
| 1 | delete |
| 2 | read |

## Conclusion

Tables should be kept atomic during chunking.
