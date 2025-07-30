# TechInsights  - Multi-Source Job Market Intelligence Platform

## Project Overview

TechInsights  is a comprehensive job market intelligence platform that aggregates and analyzes technology job postings from multiple sources across New Zealand, providing data-driven insights for developers, recruiters, and employers.

### Key Features
- **Multi-Source Data Collection**: Seek NZ, Indeed, LinkedIn, TradeMe
- **AI-Powered Tech Detection**: ML-enhanced technology stack identification
- **Advanced Analytics**: Trend forecasting, salary analysis, skill gap insights
- **Real-time Intelligence**: Live job alerts and market updates
- **Developer-Focused**: Built by developers for the NZ tech community

## Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Frontend  │───▶│  API Gateway │───▶│   Services  │
│   (React)   │    │  (FastAPI)   │    │   Layer     │
└─────────────┘    └──────────────┘    └─────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│     CDN     │    │    Cache     │    │  Database   │
│(CloudFront) │    │   (Redis)    │    │(PostgreSQL)│
└─────────────┘    └──────────────┘    └─────────────┘
                          │                  │
                          ▼                  ▼
                ┌──────────────┐    ┌─────────────┐
                │Multi-Source  │    │  Analytics  │
                │  Scrapers    │    │   Engine    │
                └──────────────┘    └─────────────┘
```

## Technology Stack

### Backend
- **Framework**: Python FastAPI
- **Database**: PostgreSQL 15+
- **Cache**: Redis
- **Task Queue**: Celery
- **ML/Analytics**: pandas, scikit-learn, spaCy

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Chart.js / D3.js
- **State Management**: Redux Toolkit

### Infrastructure
- **Cloud**: AWS (ECS, RDS, ElastiCache)
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Monitoring**: CloudWatch, Prometheus

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd techinsights-v2
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   # Start PostgreSQL and Redis with Docker
   docker-compose up -d database redis
   
   # Run database migrations
   cd database
   alembic upgrade head
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start Development Servers**
   ```bash
   # Backend API (Terminal 1)
   cd backend
   uvicorn src.api.main:app --reload --port 8000
   
   # Frontend (Terminal 2)
   cd frontend
   npm install
   npm start
   ```

6. **Access Application**
   - API Documentation: http://localhost:8000/api/docs
   - Frontend Application: http://localhost:3000
   - Database Admin: http://localhost:5050 (pgAdmin)

## 📊 Database Design

The application uses PostgreSQL with a normalized schema supporting:

- **Multi-source job data** with proper attribution
- **Advanced tech stack relationships** with confidence scoring
- **Analytics-optimized structure** for trend analysis
- **Data quality tracking** and monitoring
- **Audit trails** for all changes

### Key Tables
- `data_sources` - Job platform configurations
- `jobs` - Normalized job postings from all sources
- `companies` - Company profiles and information
- `tech_stacks` - Technology definitions and metadata
- `job_tech_requirements` - Job-technology relationships with ML scoring
- `tech_trend_analytics` - Pre-computed trend data for performance

## Data Pipeline

### Collection Process
1. **Scheduled Scraping**: Daily collection from multiple sources
2. **Data Validation**: Quality checks and cleaning
3. **Tech Detection**: ML-powered technology identification
4. **Normalization**: Standardization across sources
5. **Analytics**: Trend calculation and insights generation

### Data Sources
- **Seek NZ**: REST API + web scraping
- **Indeed NZ**: Web scraping with respect
- **LinkedIn Jobs**: Official API integration
- **TradeMe Jobs**: REST API integration

