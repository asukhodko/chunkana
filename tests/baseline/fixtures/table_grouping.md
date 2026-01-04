# Table Grouping Document

This document tests table grouping scenarios where related tables should be kept together.

## Database Schema

### Users Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| username | VARCHAR(50) | NOT NULL, UNIQUE |
| email | VARCHAR(100) | NOT NULL |
| created_at | TIMESTAMP | DEFAULT NOW() |

### Posts Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| user_id | INTEGER | FOREIGN KEY (users.id) |
| title | VARCHAR(200) | NOT NULL |
| content | TEXT | |
| published | BOOLEAN | DEFAULT FALSE |

### Comments Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY |
| post_id | INTEGER | FOREIGN KEY (posts.id) |
| user_id | INTEGER | FOREIGN KEY (users.id) |
| body | TEXT | NOT NULL |

## API Endpoints

### GET Endpoints

| Endpoint | Description | Auth |
|----------|-------------|------|
| /users | List all users | No |
| /users/:id | Get user by ID | No |
| /posts | List all posts | No |
| /posts/:id | Get post by ID | No |

### POST Endpoints

| Endpoint | Description | Auth |
|----------|-------------|------|
| /users | Create user | No |
| /posts | Create post | Yes |
| /comments | Add comment | Yes |

### DELETE Endpoints

| Endpoint | Description | Auth |
|----------|-------------|------|
| /users/:id | Delete user | Admin |
| /posts/:id | Delete post | Owner |
| /comments/:id | Delete comment | Owner |

## Comparison Tables

### Before Migration

| Metric | Value |
|--------|-------|
| Response Time | 500ms |
| Throughput | 100 req/s |
| Error Rate | 5% |

### After Migration

| Metric | Value |
|--------|-------|
| Response Time | 50ms |
| Throughput | 1000 req/s |
| Error Rate | 0.1% |

## Isolated Table

This table stands alone and should not be grouped:

| Setting | Value |
|---------|-------|
| Debug | false |
| Timeout | 30s |

## Conclusion

Related tables within the same section should be grouped together.
