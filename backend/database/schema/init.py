#!/usr/bin/env python3
"""
Database initialization script using SQLAlchemy

This script:
1. Creates all database tables from SQLAlchemy models
2. Creates necessary indexes
3. Loads seed data for reference tables
4. Validates the database schema

Usage:
    python database/init.py [--drop-existing] [--seed-data]
    # OR from backend root:
    python -m database.init [--drop-existing] [--seed-data]

Options:
    --drop-existing: Drop all existing tables before creating new ones
    --seed-data: Load seed data after creating tables
"""

import sys
import os
import argparse
from typing import List, Dict, Any

# Add backend to path (parent directory of database/)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text, inspect
from app.database import engine, SessionLocal, Base, logger
from app.models import (
    RawJob, Job, Company, Skill, JobSkill, Location, 
    Category, SkillTrend,
    EmploymentType, ExperienceLevel, WorkArrangement, SkillCategory
)


def drop_all_tables() -> bool:
    """
    Drop all existing tables.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("🗑️  Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ All tables dropped successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        return False


def create_all_tables() -> bool:
    """
    Create all tables from SQLAlchemy models.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("🏗️  Creating database tables from SQLAlchemy models...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False


def verify_tables() -> bool:
    """
    Verify that all expected tables exist in the database.
    
    Returns:
        bool: True if all tables exist, False otherwise
    """
    try:
        logger.info("🔍 Verifying database tables...")
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Expected tables from models
        expected_tables = [
            'raw_jobs',
            'jobs',
            'companies',
            'locations',
            'categories',
            'skills',
            'job_skills',
            'skill_trends'
        ]
        
        missing_tables = [table for table in expected_tables if table not in existing_tables]
        
        if missing_tables:
            logger.error(f"❌ Missing tables: {', '.join(missing_tables)}")
            return False
        
        logger.info(f"✅ All {len(expected_tables)} expected tables exist")
        
        # Show table details
        for table in expected_tables:
            columns = inspector.get_columns(table)
            logger.info(f"   📊 {table}: {len(columns)} columns")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Table verification failed: {e}")
        return False


def create_indexes() -> bool:
    """
    Create additional performance indexes.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("📇 Creating performance indexes...")
        
        with engine.begin() as conn:
            # Additional indexes not defined in models
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_jobs_title_search ON jobs USING gin(to_tsvector('english', title));",
                "CREATE INDEX IF NOT EXISTS idx_jobs_description_search ON jobs USING gin(to_tsvector('english', description));",
                "CREATE INDEX IF NOT EXISTS idx_companies_name_search ON companies USING gin(to_tsvector('english', name));",
            ]
            
            for idx_sql in indexes:
                try:
                    conn.execute(text(idx_sql))
                    logger.info(f"   ✓ Created: {idx_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Index creation skipped: {e}")
        
        logger.info("✅ Indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")
        return False


def load_seed_data() -> bool:
    """
    Load seed data for reference tables.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("🌱 Loading seed data...")
        
        db = SessionLocal()
        
        try:
            # Check if data already exists
            existing_categories = db.query(Category).count()
            if existing_categories > 0:
                logger.info(f"   ℹ️  Database already has {existing_categories} categories, skipping seed data")
                return True
            
            # Load categories (matches processing pipeline categories)
            # Note: sort_order determines display order in frontend
            categories_data = [
                {"name": "Software Development", "description": "Software engineering and development roles", "color_code": "#3B82F6", "sort_order": 1},
                {"name": "Data & Analytics", "description": "Data science, analytics, machine learning, and AI", "color_code": "#06B6D4", "sort_order": 2},
                {"name": "DevOps & Infrastructure", "description": "DevOps, SRE, cloud infrastructure, and automation", "color_code": "#EF4444", "sort_order": 3},
                {"name": "UI/UX Design", "description": "User interface and user experience design", "color_code": "#EC4899", "sort_order": 4},
                {"name": "Mobile Development", "description": "iOS, Android, and cross-platform mobile development", "color_code": "#F59E0B", "sort_order": 5},
                {"name": "QA & Testing", "description": "Software testing, quality assurance, and automation", "color_code": "#84CC16", "sort_order": 6},
                {"name": "Security", "description": "Cybersecurity, information security, and compliance", "color_code": "#DC2626", "sort_order": 7},
                {"name": "Product Management", "description": "Product strategy, management, and coordination", "color_code": "#F97316", "sort_order": 8},
                {"name": "Project Management", "description": "Technical project and program management", "color_code": "#7C3AED", "sort_order": 9},
                {"name": "Database Administration", "description": "Database design, optimization, and administration", "color_code": "#059669", "sort_order": 10},
                {"name": "Support & IT", "description": "Technical support and IT operations", "color_code": "#6366F1", "sort_order": 11},
                {"name": "Other Tech Roles", "description": "Miscellaneous technology roles", "color_code": "#6B7280", "sort_order": 99},
            ]
            
            for cat_data in categories_data:
                category = Category(**cat_data)
                db.add(category)
            
            db.commit()
            logger.info(f"   ✅ Loaded {len(categories_data)} categories")
            
            # Load common skills
            skills_data = [
                # Programming Languages
                {"name": "Python", "category": "programming", "skill_type": "technical"},
                {"name": "JavaScript", "category": "programming", "skill_type": "technical"},
                {"name": "TypeScript", "category": "programming", "skill_type": "technical"},
                {"name": "Java", "category": "programming", "skill_type": "technical"},
                {"name": "C#", "category": "programming", "skill_type": "technical"},
                {"name": "Go", "category": "programming", "skill_type": "technical"},
                {"name": "Rust", "category": "programming", "skill_type": "technical"},
                {"name": "PHP", "category": "programming", "skill_type": "technical"},
                {"name": "Ruby", "category": "programming", "skill_type": "technical"},
                {"name": "SQL", "category": "database", "skill_type": "technical"},
                
                # Frontend
                {"name": "React", "category": "frontend", "skill_type": "technical"},
                {"name": "Vue.js", "category": "frontend", "skill_type": "technical"},
                {"name": "Angular", "category": "frontend", "skill_type": "technical"},
                {"name": "HTML", "category": "frontend", "skill_type": "technical"},
                {"name": "CSS", "category": "frontend", "skill_type": "technical"},
                
                # Backend
                {"name": "Node.js", "category": "backend", "skill_type": "technical"},
                {"name": "Django", "category": "backend", "skill_type": "technical"},
                {"name": "Flask", "category": "backend", "skill_type": "technical"},
                {"name": "FastAPI", "category": "backend", "skill_type": "technical"},
                {"name": "Spring Boot", "category": "backend", "skill_type": "technical"},
                {"name": ".NET", "category": "backend", "skill_type": "technical"},
                
                # Databases
                {"name": "PostgreSQL", "category": "database", "skill_type": "technical"},
                {"name": "MySQL", "category": "database", "skill_type": "technical"},
                {"name": "MongoDB", "category": "database", "skill_type": "technical"},
                {"name": "Redis", "category": "database", "skill_type": "technical"},
                
                # Cloud
                {"name": "AWS", "category": "cloud", "skill_type": "technical"},
                {"name": "Azure", "category": "cloud", "skill_type": "technical"},
                {"name": "GCP", "category": "cloud", "skill_type": "technical"},
                
                # DevOps
                {"name": "Docker", "category": "devops", "skill_type": "technical"},
                {"name": "Kubernetes", "category": "devops", "skill_type": "technical"},
                {"name": "CI/CD", "category": "devops", "skill_type": "technical"},
                {"name": "Terraform", "category": "devops", "skill_type": "technical"},
                {"name": "Jenkins", "category": "devops", "skill_type": "technical"},
                
                # Tools
                {"name": "Git", "category": "tools", "skill_type": "technical"},
                {"name": "Linux", "category": "tools", "skill_type": "technical"},
                {"name": "Agile", "category": "tools", "skill_type": "methodology"},
            ]
            
            for skill_data in skills_data:
                skill = Skill(**skill_data)
                db.add(skill)
            
            db.commit()
            logger.info(f"   ✅ Loaded {len(skills_data)} skills")
            
            # Load common locations
            locations_data = [
                {"city": "Auckland", "region": "Auckland"},
                {"city": "Wellington", "region": "Wellington"},
                {"city": "Christchurch", "region": "Canterbury"},
                {"city": "Hamilton", "region": "Waikato"},
                {"city": "Tauranga", "region": "Bay of Plenty"},
                {"city": "Dunedin", "region": "Otago"},
                {"city": "Palmerston North", "region": "Manawatū-Whanganui"},
                {"city": "Napier", "region": "Hawke's Bay"},
                {"city": "Nelson", "region": "Nelson"},
                {"city": "Queenstown", "region": "Otago"},
                {"city": "Remote", "region": "Remote"},
            ]
            
            for loc_data in locations_data:
                location = Location(**loc_data)
                db.add(location)
            
            db.commit()
            logger.info(f"   ✅ Loaded {len(locations_data)} locations")
            
            logger.info("✅ Seed data loaded successfully")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Failed to load seed data: {e}")
        return False


def main():
    """Main initialization process"""
    parser = argparse.ArgumentParser(description='Initialize database schema using SQLAlchemy')
    parser.add_argument('--drop-existing', action='store_true', 
                       help='Drop all existing tables before creating new ones')
    parser.add_argument('--seed-data', action='store_true',
                       help='Load seed data after creating tables')
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("DATABASE INITIALIZATION - SQLAlchemy Based")
    logger.info("="*80)
    
    success = True
    
    # Step 1: Drop existing tables if requested
    if args.drop_existing:
        logger.info("\n⚠️  WARNING: Dropping existing tables...")
        if not drop_all_tables():
            success = False
            logger.error("❌ Initialization failed at drop tables step")
            sys.exit(1)
    
    # Step 2: Create all tables
    logger.info("\n📊 Creating database tables...")
    if not create_all_tables():
        success = False
        logger.error("❌ Initialization failed at create tables step")
        sys.exit(1)
    
    # Step 3: Verify tables
    logger.info("\n🔍 Verifying database schema...")
    if not verify_tables():
        success = False
        logger.error("❌ Initialization failed at verification step")
        sys.exit(1)
    
    # Step 4: Create indexes
    logger.info("\n📇 Creating performance indexes...")
    if not create_indexes():
        logger.warning("⚠️  Some indexes may not have been created")
    
    # Step 5: Load seed data if requested
    if args.seed_data:
        logger.info("\n🌱 Loading seed data...")
        if not load_seed_data():
            logger.warning("⚠️  Seed data loading had issues")
    
    # Final summary
    logger.info("\n" + "="*80)
    if success:
        logger.info("✅ DATABASE INITIALIZATION COMPLETE!")
        logger.info("="*80)
        logger.info("\n📋 Next steps:")
        logger.info("   1. Run data collection: python scripts/collection/collect_raw_data.py")
        logger.info("   2. Process collected data: python scripts/process_jobs.py")
        logger.info("   3. Start the API: uvicorn app.main:app --reload")
    else:
        logger.error("❌ DATABASE INITIALIZATION FAILED")
        logger.error("="*80)
        sys.exit(1)


if __name__ == "__main__":
    main()

