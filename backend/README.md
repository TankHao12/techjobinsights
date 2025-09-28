# Tech Jobs Insights - Backend

## Quick Start

```bash
# Start database
docker-compose up -d database

# Initialize schema
python database/init.py --seed-data

# Start API
uvicorn app.main:app --reload
```

## Project Structure

```
backend/
├── app/                   # Core application
│   ├── models/            # SQLAlchemy ORM models
│   ├── routers/           # FastAPI route handlers
│   ├── processors/        # Data processing & NLP
│   ├── scrapers/          # Web scrapers
│   ├── database.py        # Database configuration
│   ├── schemas.py         # Pydantic schemas
│   └── main.py            # FastAPI application
├── database/              # Database management tools
│   ├── init.py           # Schema initialization
│   ├── setup_alembic.py  # Migration setup
│   ├── verify_schema.py  # Schema verification
│   ├── verify_data.py    # Data validation
│   └── tests/            # Database tests
├── scripts/               # Utility scripts
│   ├── collection/       # Data collection
│   ├── processing/       # Data processing
│   └── utils/            # General utilities
├── docs/                  # Documentation
│   ├── DATABASE.md       # Database guide
│   └── MIGRATION_SUMMARY.md
└── alembic/              # Database migrations (created by setup)
```

## Database Management

All database-related tools are now in the `database/` folder:

### Initial Setup

```bash
# 1. Create schema and load seed data
python database/init.py --seed-data

# 2. Verify schema
python database/verify_schema.py

# 3. (Optional) Set up migrations
python database/setup_alembic.py
```

### Common Commands

```bash
# Initialize fresh database (drops existing data)
python database/init.py --drop-existing --seed-data

# Check schema matches models
python database/verify_schema.py

# Verify data quality
python database/verify_data.py

# Diagnose pipeline issues
python database/diagnose_pipeline.py

# Verify pipeline integration
python database/verify_pipeline.py

# Run database tests
python database/tests/test_setup.py
```

### With Alembic (Migrations)

```bash
# Set up Alembic (one time)
python database/setup_alembic.py

# Create migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Documentation

- **[Database Guide](docs/DATABASE.md)** - Comprehensive database management guide
- **[Migration Summary](docs/MIGRATION_SUMMARY.md)** - Recent changes and migration notes
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running)

## Development

### Run API Server

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Run Tests

```bash
# Database tests
python database/tests/test_setup.py

# API tests
pytest tests/

# With coverage
pytest --cov=app tests/
```

### Data Collection

```bash
# Collect raw job data
python scripts/collection/collect_raw_data.py

# Process collected data
python scripts/process_jobs.py

# Daily update (collect + process)
python scripts/daily_update.py
```

## Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@database:5432/techjobs
DATABASE_ECHO=false  # Set to true for SQL query logging

# Redis
REDIS_URL=redis://redis:6379

# Environment
ENVIRONMENT=development  # or production

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## Backward Compatibility

For backward compatibility, convenience wrappers are provided in the root:

```bash
# These still work (but show migration notice)
python init_database.py --seed-data
python check_schema.py
```

They forward to the new locations in `database/`.

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
python -c "from app.database import test_connection; test_connection()"

# Check if database is running
docker-compose ps database

# View database logs
docker-compose logs database
```

### Schema Mismatch

```bash
# Verify schema
python database/verify_schema.py

# If using Alembic
alembic revision --autogenerate -m "Fix schema"
alembic upgrade head

# Or recreate (development only)
python database/init.py --drop-existing --seed-data
```

### Import Errors

Make sure you're running from the `backend/` directory:

```bash
cd backend
python database/init.py --seed-data
```

## Contributing

1. Make changes to models in `app/models/tables.py`
2. Create migration: `alembic revision --autogenerate -m "Description"`
3. Test migration: `alembic upgrade head` on dev database
4. Verify: `python database/verify_schema.py`
5. Commit both model changes and migration files

## Support

- Check `docs/DATABASE.md` for detailed database guide
- Run `python database/tests/test_setup.py` for diagnostics
- Review logs: `docker-compose logs backend`

