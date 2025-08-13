"""
TechInsights  - Database Initialization Script
Initialize database with schema and seed data
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path so we can import from src
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Also add the src directory specifically
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

from sqlalchemy import text
from src.core.database import (
    create_all_tables, 
    drop_all_tables, 
    sync_engine, 
    check_database_connection
)
from src.core.config import settings
from src.models import *  # Import all models
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_initial_data_sources():
    """Create initial data source records."""
    from src.core.database import SessionLocal
    from src.models.data_source import DataSource
    
    logger.info("Creating initial data sources...")
    
    with SessionLocal() as db:
        # Check if data sources already exist
        existing_sources = db.query(DataSource).count()
        if existing_sources > 0:
            logger.info(f"Found {existing_sources} existing data sources, skipping creation")
            return
        
        sources = [
            DataSource(
                source_name="seek",
                base_url="https://www.seek.co.nz",
                api_endpoint="https://www.seek.co.nz/api/jobsearch/v5/search",
                rate_limit_per_hour=100,
                scraping_config={
                    "classification": "6281",
                    "pageSize": 22,
                    "default_location": "All New Zealand"
                },
                is_active=True
            ),
            DataSource(
                source_name="indeed",
                base_url="https://nz.indeed.com",
                api_endpoint="https://nz.indeed.com/jobs",
                rate_limit_per_hour=50,
                scraping_config={
                    "country": "NZ",
                    "sort": "date"
                },
                is_active=True
            ),
            DataSource(
                source_name="trademe",
                base_url="https://www.trademe.co.nz",
                api_endpoint="https://api.trademe.co.nz/v1/Jobs",
                rate_limit_per_hour=75,
                scraping_config={
                    "category": "5023"
                },
                is_active=True
            ),
            DataSource(
                source_name="linkedin",
                base_url="https://www.linkedin.com",
                api_endpoint="https://api.linkedin.com/v2/jobs",
                rate_limit_per_hour=25,
                scraping_config={
                    "location": "New Zealand",
                    "industry": "technology"
                },
                is_active=False  # Disabled until implementation
            )
        ]
        
        for source in sources:
            db.add(source)
        
        db.commit()
        logger.info(f"Created {len(sources)} data sources")


def create_initial_tech_stacks():
    """Create initial technology stack records."""
    from src.core.database import SessionLocal
    from src.models.tech_stack import TechStack
    
    logger.info("Creating initial technology stacks...")
    
    with SessionLocal() as db:
        # Check if tech stacks already exist
        existing_techs = db.query(TechStack).count()
        if existing_techs > 0:
            logger.info(f"Found {existing_techs} existing tech stacks, skipping creation")
            return
        
        tech_stacks = [
            # Programming Languages
            TechStack(
                technology_name="JavaScript",
                normalized_name="javascript",
                category="Frontend",
                aliases=["js", "ecmascript"],
                is_programming_language=True,
                description="Dynamic programming language for web development",
                popularity_score=95.0
            ),
            TechStack(
                technology_name="TypeScript",
                normalized_name="typescript",
                category="Frontend",
                aliases=["ts"],
                is_programming_language=True,
                description="Typed superset of JavaScript",
                popularity_score=85.0
            ),
            TechStack(
                technology_name="Python",
                normalized_name="python",
                category="Backend",
                aliases=["py"],
                is_programming_language=True,
                description="High-level programming language",
                popularity_score=90.0
            ),
            TechStack(
                technology_name="Java",
                normalized_name="java",
                category="Backend",
                aliases=["jvm"],
                is_programming_language=True,
                description="Object-oriented programming language",
                popularity_score=80.0
            ),
            TechStack(
                technology_name="C#",
                normalized_name="csharp",
                category="Backend",
                aliases=["c-sharp", "c sharp", "csharp"],
                is_programming_language=True,
                description="Microsoft .NET programming language",
                popularity_score=75.0
            ),
            TechStack(
                technology_name="Go",
                normalized_name="go",
                category="Backend",
                aliases=["golang"],
                is_programming_language=True,
                description="Google systems programming language",
                popularity_score=70.0
            ),
            
            # Frontend Frameworks
            TechStack(
                technology_name="React",
                normalized_name="react",
                category="Frontend",
                aliases=["reactjs", "react.js"],
                is_framework=True,
                description="JavaScript library for building user interfaces",
                popularity_score=90.0
            ),
            TechStack(
                technology_name="Vue.js",
                normalized_name="vue",
                category="Frontend",
                aliases=["vuejs", "vue.js"],
                is_framework=True,
                description="Progressive JavaScript framework",
                popularity_score=75.0
            ),
            TechStack(
                technology_name="Angular",
                normalized_name="angular",
                category="Frontend",
                aliases=["angularjs", "angular.js"],
                is_framework=True,
                description="TypeScript-based web application framework",
                popularity_score=70.0
            ),
            TechStack(
                technology_name="Next.js",
                normalized_name="nextjs",
                category="Frontend",
                aliases=["next.js"],
                is_framework=True,
                description="React-based web framework",
                popularity_score=65.0
            ),
            
            # Backend Frameworks
            TechStack(
                technology_name="Node.js",
                normalized_name="nodejs",
                category="Backend",
                aliases=["node", "node.js"],
                is_framework=True,
                description="JavaScript runtime for server-side development",
                popularity_score=85.0
            ),
            TechStack(
                technology_name="Django",
                normalized_name="django",
                category="Backend",
                aliases=["django-python"],
                is_framework=True,
                description="Python web framework",
                popularity_score=75.0
            ),
            TechStack(
                technology_name="Flask",
                normalized_name="flask",
                category="Backend",
                aliases=["flask-python"],
                is_framework=True,
                description="Micro web framework for Python",
                popularity_score=65.0
            ),
            TechStack(
                technology_name="FastAPI",
                normalized_name="fastapi",
                category="Backend",
                aliases=["fast-api"],
                is_framework=True,
                description="Modern Python web framework",
                popularity_score=60.0
            ),
            TechStack(
                technology_name="Spring Boot",
                normalized_name="spring-boot",
                category="Backend",
                aliases=["spring", "springboot"],
                is_framework=True,
                description="Java application framework",
                popularity_score=70.0
            ),
            
            # Databases
            TechStack(
                technology_name="PostgreSQL",
                normalized_name="postgresql",
                category="Database",
                aliases=["postgres", "psql"],
                is_database=True,
                description="Advanced open source relational database",
                popularity_score=80.0
            ),
            TechStack(
                technology_name="MySQL",
                normalized_name="mysql",
                category="Database",
                aliases=["mysql-db"],
                is_database=True,
                description="Popular open source relational database",
                popularity_score=75.0
            ),
            TechStack(
                technology_name="MongoDB",
                normalized_name="mongodb",
                category="Database",
                aliases=["mongo"],
                is_database=True,
                description="Document-oriented NoSQL database",
                popularity_score=70.0
            ),
            TechStack(
                technology_name="Redis",
                normalized_name="redis",
                category="Database",
                aliases=["redis-cache"],
                is_database=True,
                description="In-memory data structure store",
                popularity_score=65.0
            ),
            
            # Cloud Services
            TechStack(
                technology_name="AWS",
                normalized_name="aws",
                category="Cloud",
                aliases=["amazon-web-services", "amazon web services"],
                is_cloud_service=True,
                description="Amazon Web Services cloud platform",
                popularity_score=85.0
            ),
            TechStack(
                technology_name="Azure",
                normalized_name="azure",
                category="Cloud",
                aliases=["microsoft-azure", "microsoft azure"],
                is_cloud_service=True,
                description="Microsoft cloud computing platform",
                popularity_score=75.0
            ),
            TechStack(
                technology_name="Google Cloud",
                normalized_name="gcp",
                category="Cloud",
                aliases=["google-cloud-platform", "gcp"],
                is_cloud_service=True,
                description="Google Cloud Platform",
                popularity_score=70.0
            ),
            
            # DevOps Tools
            TechStack(
                technology_name="Docker",
                normalized_name="docker",
                category="DevOps",
                aliases=["containerization"],
                is_tool=True,
                description="Containerization platform",
                popularity_score=80.0
            ),
            TechStack(
                technology_name="Kubernetes",
                normalized_name="kubernetes",
                category="DevOps",
                aliases=["k8s", "kube"],
                is_tool=True,
                description="Container orchestration platform",
                popularity_score=75.0
            ),
            TechStack(
                technology_name="Git",
                normalized_name="git",
                category="DevOps",
                aliases=["version-control"],
                is_tool=True,
                description="Distributed version control system",
                popularity_score=95.0
            ),
            TechStack(
                technology_name="Jenkins",
                normalized_name="jenkins",
                category="DevOps",
                aliases=["ci-cd"],
                is_tool=True,
                description="Automation server for CI/CD",
                popularity_score=60.0
            )
        ]
        
        for tech in tech_stacks:
            db.add(tech)
        
        db.commit()
        logger.info(f"Created {len(tech_stacks)} technology stacks")


def create_initial_job_categories():
    """Create initial job category records."""
    from src.core.database import SessionLocal
    from src.models.job_category import JobCategory
    from src.models.data_source import DataSource
    
    logger.info("Creating initial job categories...")
    
    with SessionLocal() as db:
        # Check if categories already exist
        existing_categories = db.query(JobCategory).count()
        if existing_categories > 0:
            logger.info(f"Found {existing_categories} existing job categories, skipping creation")
            return
        
        # Get the Seek data source
        seek_source = db.query(DataSource).filter(DataSource.source_name == "seek").first()
        if not seek_source:
            logger.error("Seek data source not found, cannot create categories")
            return
        
        categories = [
            JobCategory(
                category_name="Software Development",
                source_id=seek_source.source_id,
                external_category_id="6281",
                description="Software engineering and development roles",
                is_tech_related=True
            ),
            JobCategory(
                category_name="Data Science & Analytics",
                source_id=seek_source.source_id,
                external_category_id="6281-data",
                description="Data analysis, machine learning, and AI roles",
                is_tech_related=True
            ),
            JobCategory(
                category_name="DevOps & Infrastructure",
                source_id=seek_source.source_id,
                external_category_id="6281-devops",
                description="System administration and DevOps roles",
                is_tech_related=True
            ),
            JobCategory(
                category_name="Frontend Development",
                source_id=seek_source.source_id,
                external_category_id="6281-frontend",
                description="Frontend and client-side development roles",
                is_tech_related=True
            ),
            JobCategory(
                category_name="Backend Development",
                source_id=seek_source.source_id,
                external_category_id="6281-backend",
                description="Backend and server-side development roles",
                is_tech_related=True
            ),
            JobCategory(
                category_name="Mobile Development",
                source_id=seek_source.source_id,
                external_category_id="6281-mobile",
                description="iOS and Android development roles",
                is_tech_related=True
            ),
            JobCategory(
                category_name="Quality Assurance",
                source_id=seek_source.source_id,
                external_category_id="6281-qa",
                description="Software testing and QA roles",
                is_tech_related=True
            ),
            JobCategory(
                category_name="Cybersecurity",
                source_id=seek_source.source_id,
                external_category_id="6281-security",
                description="Information security and cybersecurity roles",
                is_tech_related=True
            )
        ]
        
        for category in categories:
            db.add(category)
        
        db.commit()
        logger.info(f"Created {len(categories)} job categories")


def run_database_initialization(drop_existing: bool = False):
    """
    Run the complete database initialization process.
    
    Args:
        drop_existing: Whether to drop existing tables first
    """
    try:
        logger.info("Starting database initialization...")
        
        # Check database connection
        if not check_database_connection():
            logger.error("Cannot connect to database. Please check configuration.")
            return False
        
        # Drop existing tables if requested
        if drop_existing:
            logger.warning("Dropping existing tables...")
            drop_all_tables()
        
        # Create all tables
        logger.info("Creating database tables...")
        create_all_tables()
        
        # Create initial data
        create_initial_data_sources()
        create_initial_tech_stacks()
        create_initial_job_categories()
        
        logger.info("Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize TechInsights database")
    parser.add_argument(
        "--drop", 
        action="store_true", 
        help="Drop existing tables before creating new ones"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force initialization without confirmation"
    )
    
    args = parser.parse_args()
    
    # Safety check for production
    if args.drop and settings.ENVIRONMENT == "production" and not args.force:
        logger.error("Cannot drop tables in production without --force flag")
        sys.exit(1)
    
    # Confirmation for dropping tables
    if args.drop and not args.force:
        confirmation = input("This will DROP ALL EXISTING TABLES. Are you sure? (yes/no): ")
        if confirmation.lower() != "yes":
            logger.info("Operation cancelled")
            sys.exit(0)
    
    # Run initialization
    success = run_database_initialization(drop_existing=args.drop)
    
    if success:
        print("✅ Database initialization completed successfully!")
        print(f"🔗 Database URL: {settings.DATABASE_URL}")
        print("🚀 You can now start the application")
    else:
        print("❌ Database initialization failed!")
        sys.exit(1)
