#!/usr/bin/env python3
"""
Quick script to check location data in raw_jobs
"""
import sys
import os

# Add backend to path (parent directory of database/)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.tables import RawJob
from sqlalchemy import func

db = SessionLocal()

try:
    # Check total jobs
    total = db.query(func.count(RawJob.id)).scalar()
    
    # Check how many have location
    with_location = db.query(func.count(RawJob.id)).filter(
        RawJob.location != None, 
        RawJob.location != ''
    ).scalar()
    
    without_location = total - with_location
    
    print("=" * 60)
    print("LOCATION DATA CHECK")
    print("=" * 60)
    print(f"Total raw jobs: {total}")
    print(f"Jobs WITH location: {with_location} ({with_location/total*100:.1f}%)")
    print(f"Jobs WITHOUT location: {without_location} ({without_location/total*100:.1f}%)")
    print("=" * 60)
    
    if without_location > 0:
        print("\n⚠️  WARNING: Many jobs are missing location data!")
        print("This is because they were scraped before the location column was added.")
        print("\nOptions:")
        print("1. Continue processing - NLP will extract from description (may be less accurate)")
        print("2. Rescrape the data to get proper location metadata")
    else:
        print("\n✓ All jobs have location data!")
        
    # Show sample of jobs without location
    if without_location > 0:
        print("\nSample jobs without location (first 5):")
        samples = db.query(RawJob.id, RawJob.title, RawJob.company).filter(
            (RawJob.location == None) | (RawJob.location == '')
        ).limit(5).all()
        
        for job in samples:
            print(f"  ID {job.id}: {job.title[:50]} @ {job.company[:30]}")
            
finally:
    db.close()

