# NZ Tech Jobs Market Intelligence Platform

> **COMP693 Industrial Project - Lincoln University**  
> A comprehensive job market analytics platform for the New Zealand tech industry

## Project Overview

**NZ Tech Jobs Market Intelligence** is a full-stack web application that aggregates, analyzes, and visualizes technology job postings from across New Zealand. The platform provides data-driven insights to help developers, recruiters, and employers make informed decisions about the tech job market.

### Key Features

-   **Intelligent Job Scraping**: Automated collection from Seek.co.nz with advanced parsing
-   **AI-Powered NLP Processing**: spaCy-based text analysis for skill extraction and job classification
-   **Real-time Analytics Dashboard**: Interactive visualizations of market trends and statistics
-   **Skills Intelligence**: Track trending technologies and in-demand skills
-   **Company Insights**: Company hiring patterns and job posting analysis
-   **Salary Analytics**: Salary ranges and compensation insights
-   **Modern UI/UX**: Responsive React interface with dark mode support

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + TS)                    │
│  Dashboard | Skills Analytics | Companies | Job Search       │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│                  Backend API (FastAPI)                       │
│  Jobs | Skills | Analytics | Companies | Categories          │
└─────────┬──────────────────────────┬────────────────────────┘
          │                          │
    ┌─────▼─────┐            ┌───────▼────────┐
    │  Scrapers  │            │  NLP Engine    │
    │  (Seek.nz) │            │  (spaCy)       │
    └─────┬──────┘            └───────┬────────┘
          │                           │
          └────────────┬──────────────┘
                       ▼
          ┌────────────────────────┐
          │  PostgreSQL Database   │
          │  Raw Jobs → Processed  │
          └────────────────────────┘
```

## Technology Stack

### Backend

-   **Framework**: FastAPI 0.104.1 (Python 3.11+)
-   **Database**: PostgreSQL 17 (Docker containerized)
-   **ORM**: SQLAlchemy 2.0.23 with Alembic migrations
-   **NLP**: spaCy 3.8.7 with en_core_web_sm model
-   **Web Scraping**: BeautifulSoup4 4.12.2 + Requests
-   **Data Processing**: Python-dateutil, pytz

### Frontend

-   **Framework**: React 19 + TypeScript 5.8
-   **Build Tool**: Vite 7.1
-   **Routing**: React Router DOM 7.8
-   **State Management**: Zustand 5.0, TanStack React Query 5.87
-   **UI Components**: Headless UI, Heroicons, Lucide React
-   **Styling**: Tailwind CSS (via utilities)
-   **Charts**: Recharts 3.2, Framer Motion 12.23
-   **Testing**: Vitest 1.6, Testing Library

### Infrastructure & DevOps

-   **Containerization**: Docker + Docker Compose
-   **Database Versioning**: Alembic migrations
-   **Development**: Hot reload (Vite + Uvicorn)
-   **API Documentation**: OpenAPI/Swagger (auto-generated)
-   **Deployment**: Azure Web App Service, Azure Static Web Apps, Supabase
-   **Automation**: GitHub Actions for daily data updates

### Automation

-   **Daily Updates**: Automated job scraping and processing at 2 AM NZDT
-   **Workflow**: GitHub Actions orchestrating API calls
-   **Monitoring**: Comprehensive logging and status tracking
-   **Cost**: $0 additional infrastructure (uses GitHub Actions free tier)

> See [AUTOMATION_SUMMARY.md](AUTOMATION_SUMMARY.md) for complete automation documentation

## Quick Start Guide

### Prerequisites

```
- Python 3.11+
- Node.js 18+
- Docker Desktop
- Git
```

### 1. Clone the Repository

```bash
git clone https://github.com/COMP693-Projects-25S2/COMP693_25S2_project__Tan_1162169.git
cd COMP693_25S2_project__Tan_1162169
```

### 2. Backend Setup

#### Option A: Docker (Recommended)

```bash
# Start PostgreSQL database
docker-compose up -d database

# Build and start backend
docker-compose up -d backend

# Initialize database schema
docker-compose exec backend python -c "
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
print('✅ Database initialized')
"
```

#### Option B: Local Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start database only
docker-compose up -d database

# Initialize database
python -c "
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
"

# Start API server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Application

-   **Frontend**: http://localhost:5173
-   **Backend API**: http://localhost:8000
-   **API Docs**: http://localhost:8000/docs
-   **Database**: localhost:5432 (postgres/password)

## Project Structure

```
COMP693_25S2_project__Tan_1162169/
│
├── backend/                      # Python FastAPI Backend
│   ├── app/                      # Main application code
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── tables.py        # Database table definitions
│   │   │   └── enums.py         # Enum types (employment, experience, etc.)
│   │   ├── routers/             # API endpoint handlers
│   │   │   ├── jobs.py          # Job listings endpoints
│   │   │   ├── skills.py        # Skills analytics endpoints
│   │   │   ├── analytics.py     # Dashboard & analytics
│   │   │   ├── companies.py     # Company endpoints
│   │   │   └── categories.py    # Job categories
│   │   ├── processors/          # Data processing pipeline
│   │   │   ├── nlp_engine.py    # spaCy NLP processing
│   │   │   ├── data_pipeline.py # Job processing pipeline
│   │   │   └── url_checker.py   # URL validation
│   │   ├── scrapers/            # Web scraping modules
│   │   │   ├── base_scraper.py  # Base scraper class
│   │   │   └── seek_scraper.py  # Seek.co.nz scraper
│   │   ├── core/                # Core utilities
│   │   │   ├── config.py        # Configuration management
│   │   │   └── logging.py       # Logging setup
│   │   ├── database.py          # Database connection & session
│   │   ├── schemas.py           # Pydantic models
│   │   ├── crud.py              # Database operations
│   │   └── main.py              # FastAPI application
│   │
│   ├── database/                # Database management
│   │   ├── schema/              # Schema initialization
│   │   ├── operations/          # Data pipelines
│   │   ├── maintenance/         # Validation scripts
│   │   └── docs/                # Database documentation
│   │
│   ├── scripts/                 # Utility scripts
│   │   ├── collection/          # Data collection scripts
│   │   └── migrations/          # Database migrations
│   │
│   ├── alembic/                 # Database migrations
│   │   └── versions/            # Migration files
│   │
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Backend container
│   └── alembic.ini             # Alembic configuration
│
├── frontend/                    # React TypeScript Frontend
│   ├── src/
│   │   ├── pages/              # Page components
│   │   │   ├── Dashboard.tsx   # Main dashboard
│   │   │   ├── Skills.tsx      # Skills analytics
│   │   │   ├── SkillDetail.tsx # Skill details
│   │   │   ├── Companies.tsx   # Companies list
│   │   │   └── About.tsx       # About page
│   │   ├── components/         # Reusable components
│   │   │   ├── layout/         # Layout components
│   │   │   ├── common/         # Common UI components
│   │   │   ├── charts/         # Chart components
│   │   │   └── dashboard/      # Dashboard widgets
│   │   ├── services/           # API service layer
│   │   │   ├── api.ts          # Base API client
│   │   │   ├── dashboardService.ts
│   │   │   └── skillsService.ts
│   │   ├── types/              # TypeScript types
│   │   ├── hooks/              # Custom React hooks
│   │   ├── utils/              # Utility functions
│   │   ├── App.tsx             # Main app component
│   │   └── main.tsx            # Entry point
│   │
│   ├── tests/                  # Frontend tests
│   ├── package.json            # Node dependencies
│   ├── vite.config.ts          # Vite configuration
│   └── tsconfig.json           # TypeScript config
│
├── ERD/                         # Database diagrams
│   ├── Current_Database_ERD.drawio
│   ├── database_erd.mmd
│   └── README.md
│
├── docker-compose.yml           # Docker orchestration
└── README.md                    # This file
```

## Database Schema

### Core Tables

#### 1. raw_jobs (Raw Data Layer)

-   Stores unprocessed scraped job listings
-   Fields: title, company, url, full_description, location, posting_date, search_term
-   Tracks processing status with `processed` flag

#### 2. jobs (Processed Data Layer)

-   NLP-processed and structured job data
-   **Key Features**:
    -   `extracted_skills`: JSONB field for flexible skill storage
    -   Enum fields: `employment_type`, `experience_level`, `work_arrangement`
    -   Salary information with confidence scores
    -   Tech job classification with confidence
-   Links to: companies, locations, categories

#### 3. companies

-   Normalized company information
-   Uses `normalized_name` for case-insensitive matching

#### 4. locations

-   Structured location data (city, region, country)
-   Includes job statistics

#### 5. categories

-   Job category classifications
-   UI metadata (color codes, sort order)

### Database Features

-   Two-stage processing pipeline (raw → processed)
-   JSONB for flexible skill storage
-   Enum-based classifications (3NF compliant)
-   Alembic migrations for version control
-   Comprehensive indexes for performance
-   Audit trails with timestamps

## Data Pipeline

### 1. Collection Phase

```python
# scripts/collection/collect_raw_data.py
SeekScraper → raw_jobs table
```

-   Scrapes job listings from Seek.co.nz
-   Stores raw HTML and metadata
-   Handles pagination and rate limiting
-   Duplicate detection via URL

### 2. Processing Phase

```python
# app/processors/data_pipeline.py
raw_jobs → NLP Engine → jobs table
```

-   **NLP Analysis** (spaCy):
    -   Skill extraction (70+ tech skills across 8 categories)
    -   Employment type classification
    -   Experience level detection
    -   Salary parsing with regex
-   **Data Normalization**:
    -   Company name standardization
    -   Location parsing
    -   Category assignment
-   **Quality Assurance**:
    -   Confidence scoring
    -   Tech job validation
    -   URL accessibility checks (optional)

### 3. Analytics Generation

```python
# app/routers/analytics.py
jobs table → Aggregations → API responses
```

-   Real-time statistics calculation
-   Trend analysis
-   Skill popularity rankings
-   Company hiring patterns

## API Endpoints

### Jobs

```
GET    /api/v1/jobs              # List jobs (paginated, filterable)
GET    /api/v1/jobs/{id}         # Job details
POST   /api/v1/jobs              # Create job (admin)
PUT    /api/v1/jobs/{id}         # Update job
```

### Skills

```
GET    /api/v1/skills                      # List all skills
GET    /api/v1/skills/popular              # Popular skills
GET    /api/v1/skills/{name}               # Skill details
GET    /api/v1/skills/{name}/jobs          # Jobs requiring skill
GET    /api/v1/skills/compare              # Compare skills
```

### Analytics

```
GET    /api/v1/analytics/dashboard         # Dashboard stats
GET    /api/v1/analytics/trending-skills   # Trending skills
GET    /api/v1/analytics/popular-companies # Top hiring companies
GET    /api/v1/analytics/skill-trends      # Skill trend data
```

### Companies

```
GET    /api/v1/companies           # List companies
GET    /api/v1/companies/{id}      # Company details
GET    /api/v1/companies/{id}/jobs # Company jobs
```

### Categories

```
GET    /api/v1/categories          # List categories
```

## Frontend Features

### Pages

1. **Dashboard** (`/`)

    - Market overview statistics
    - Trending skills widget
    - Recent jobs feed
    - Popular companies

2. **Skills Analytics** (`/skills`)

    - Skill popularity rankings
    - Category filtering
    - Job count per skill
    - Growth trends

3. **Skill Detail** (`/skills/:skillName`)

    - Skill-specific statistics
    - Related jobs
    - Salary insights
    - Related skills

4. **Companies** (`/companies`)

    - Company listings
    - Hiring activity
    - Job counts

5. **Company Detail** (`/companies/:id`)
    - Company profile
    - Active job postings
    - Hiring patterns

### UI Features

-   Dark/Light mode toggle
-   Fully responsive design
-   Real-time search and filtering
-   Interactive charts (Recharts)
-   Smooth animations (Framer Motion)
-   Accessibility features

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test              # Run tests
npm run test:ui       # Interactive UI
npm run test:coverage # Coverage report
```

## Data Collection

### Manual Scraping

```bash
cd backend

# Collect raw jobs
python scripts/collection/collect_raw_data.py

# Process collected jobs
python -c "
from app.database import SessionLocal
from app.processors.data_pipeline import DataProcessingPipeline

db = SessionLocal()
pipeline = DataProcessingPipeline()
stats = pipeline.process_unprocessed_jobs()
print(f'Processed {stats.processed_jobs} jobs')
"
```

### Automated Operations

```bash
# Run complete daily update
python backend/database/operations/daily_update.py

# Or run steps individually
python backend/database/operations/incremental_scrape.py  # Collect new jobs
python backend/database/operations/run_nlp_pipeline.py    # Process jobs
```

## Key Implementation Details

### NLP Engine

The `nlp_engine.py` module provides:

-   **70+ Tech Skills** across 8 categories:
    -   Programming Languages (Python, JavaScript, Java, etc.)
    -   Web Frameworks (React, Angular, Django, etc.)
    -   Databases (PostgreSQL, MongoDB, Redis, etc.)
    -   Cloud Platforms (AWS, Azure, GCP)
    -   DevOps Tools (Docker, Kubernetes, Jenkins)
    -   AI/ML (TensorFlow, PyTorch, scikit-learn)
    -   Mobile (iOS, Android, React Native)
    -   Testing Tools (Selenium, Jest, Pytest)
-   **Advanced Parsing**:
    -   Salary extraction with confidence scores
    -   Employment type classification
    -   Experience level detection
    -   Work arrangement identification
    -   Location normalization

### Web Scraper

The `seek_scraper.py` implements:

-   **Multi-page scraping** with pagination
-   **Both normal and premium job cards** extraction
-   **Rate limiting** and respectful scraping
-   **Duplicate detection** via URL
-   **Comprehensive search terms** (40+ terms)
-   **Detailed metadata** extraction

### Database Management

-   **Alembic migrations** for schema versioning
-   **Two-stage pipeline**: raw_jobs → jobs
-   **JSONB skill storage** for flexibility
-   **Normalized relationships** (3NF)
-   **Strategic indexes** for performance

## Common Issues & Solutions

### Backend Issues

**Issue**: spaCy model not found

```bash
python -m spacy download en_core_web_sm
```

**Issue**: Database connection refused

```bash
# Ensure database is running
docker-compose ps
docker-compose up -d database
```

**Issue**: Alembic migration conflicts

```bash
cd backend
alembic stamp head  # Reset migration state
```

### Frontend Issues

**Issue**: Module not found

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue**: Port already in use

```bash
# Change port in vite.config.ts or kill process
lsof -ti:5173 | xargs kill -9  # Unix
netstat -ano | findstr :5173   # Windows
```

## Performance Metrics

### Backend Performance

-   **API Response Time**: < 100ms (average)
-   **Job Processing**: ~2-3 seconds per job (NLP included)
-   **Scraping Speed**: ~1 second per job listing
-   **Database Queries**: Optimized with indexes

### Frontend Performance

-   **Initial Load**: < 2 seconds
-   **Page Transitions**: < 500ms
-   **Chart Rendering**: < 300ms
-   **Lighthouse Score**: 90+ (Performance)

## Security Considerations

-   No authentication required (public data)
-   CORS configured for frontend access
-   SQL injection prevention (SQLAlchemy ORM)
-   Rate limiting on scraper
-   Environment variables for sensitive config
-   Future: Add rate limiting to API endpoints
-   Future: Implement API key authentication

## Future Enhancements

### Phase 2 Features

-   [ ] User accounts and saved searches
-   [ ] Email job alerts
-   [ ] Salary trend predictions (ML)
-   [ ] More job sources (Indeed, LinkedIn)
-   [ ] Mobile app (React Native)
-   [ ] Employer dashboard
-   [ ] Resume matching

### Technical Improvements

-   [ ] Redis caching layer
-   [ ] Celery task queue for background jobs
-   [ ] Elasticsearch for advanced search
-   [ ] GraphQL API
-   [ ] Real-time WebSocket updates
-   [ ] CI/CD pipeline (GitHub Actions)
-   [ ] Kubernetes deployment

## Documentation

Additional documentation available in:

-   `backend/README.md` - Backend development guide
-   `backend/database/README.md` - Database management
-   `backend/database/docs/` - Detailed database docs
-   `ERD/README.md` - Database schema diagrams
-   `REORGANIZATION_SUMMARY.md` - Project structure changes

## Contributing

### Development Workflow

1. Create a feature branch
2. Make changes with clear commits
3. Write/update tests
4. Update documentation
5. Create pull request

### Code Style

-   **Python**: PEP 8, type hints
-   **TypeScript**: ESLint rules
-   **Git**: Conventional commits

## License

This project is part of COMP693 Industrial Project at Lincoln University.  
© 2025 - For educational purposes.

## Developer

**Student**: Tan  
**Student ID**: 1162169  
**Course**: COMP693 Industrial Project (25S2)  
**Institution**: Lincoln University, New Zealand

## Support

For questions or issues:

1. Check documentation in `/docs` folders
2. Review common issues section above
3. Check API documentation at `/docs` endpoint
4. Review migration summaries in root directory

## Acknowledgments

-   **spaCy** - Natural language processing
-   **FastAPI** - Modern Python web framework
-   **React** - Frontend framework
-   **PostgreSQL** - Reliable database
-   **Seek.co.nz** - Job data source
-   **Lincoln University** - Educational support

---

**Last Updated**: January 2025  
**Version**: 1.0.0 (MVP)  
**Status**: Active Development
