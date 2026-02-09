
# Backend

## Database migrations (Alembic)

1. Create a new revision:

```bash
alembic revision -m "add is_closed to nhs_jobs"
```

2. Apply migrations:

```bash
alembic upgrade head
```

