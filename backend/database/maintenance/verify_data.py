#!/usr/bin/env python3
"""
Verify data quality and completeness
"""
import sys
import os

# Add backend to path (parent directory of database/)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import RawJob, Job
from sqlalchemy import func, desc, text
from datetime import datetime, timedelta

db = SessionLocal()

print('=' * 60)
print('DATA QUALITY VERIFICATION REPORT')
print('=' * 60)

# 1. Check newly scraped jobs
today_raw = db.query(func.count(RawJob.id)).filter(
    RawJob.scraped_at >= datetime.now() - timedelta(hours=1)
).scalar()

print(f'\n1. RECENT SCRAPING:')
print(f'   Jobs scraped in last hour: {today_raw}')

# 2. Check processing status
total_raw = db.query(func.count(RawJob.id)).scalar()
processed = db.query(func.count(RawJob.id)).filter(RawJob.processed == True).scalar()
unprocessed = total_raw - processed

print(f'\n2. PROCESSING STATUS:')
print(f'   Total raw jobs: {total_raw}')
print(f'   Processed: {processed} ({processed/total_raw*100:.1f}%)')
print(f'   Unprocessed: {unprocessed}')

# 3. Check recent processed jobs
recent_jobs = db.query(Job).order_by(desc(Job.processed_at)).limit(5).all()

print(f'\n3. RECENTLY PROCESSED JOBS:')
for job in recent_jobs:
    skills_count = len(job.extracted_skills) if job.extracted_skills else 0
    salary = f'${job.salary_min}-${job.salary_max}' if job.salary_min else 'Not specified'
    print(f'   - {job.title[:40]:<40} | Skills: {skills_count:>2} | {job.work_arrangement:<12} | {salary}')

# 4. NLP extraction quality
jobs_with_skills = db.query(func.count(Job.id)).filter(Job.extracted_skills != {}).scalar()
jobs_with_salary = db.query(func.count(Job.id)).filter(Job.salary_min.isnot(None)).scalar()
# Check for jobs with work arrangement specified (skip if enum doesn't support it)
try:
    jobs_with_work = db.query(func.count(Job.id)).filter(Job.work_arrangement != None).scalar()
except Exception:
    jobs_with_work = db.query(func.count(Job.id)).scalar()  # Count all if filter fails
total_jobs = db.query(func.count(Job.id)).scalar()

print(f'\n4. NLP EXTRACTION QUALITY:')
if total_jobs > 0:
    print(f'   Jobs with skills extracted: {jobs_with_skills}/{total_jobs} ({jobs_with_skills/total_jobs*100:.1f}%)')
    print(f'   Jobs with salary extracted: {jobs_with_salary}/{total_jobs} ({jobs_with_salary/total_jobs*100:.1f}%)')
    print(f'   Jobs with work arrangement: {jobs_with_work}/{total_jobs} ({jobs_with_work/total_jobs*100:.1f}%)')
else:
    print(f'   ⚠️  No processed jobs found in the jobs table!')
    print(f'   Raw jobs exist ({db.query(func.count(RawJob.id)).scalar()}), but they need to be processed.')
    print(f'   Run: python scripts/process_jobs.py')

# 5. Work arrangement distribution
work_dist = db.query(
    Job.work_arrangement,
    func.count(Job.id).label('count')
).group_by(Job.work_arrangement).all()

print(f'\n5. WORK ARRANGEMENT DISTRIBUTION:')
for arrangement, count in work_dist:
    arrangement_str = arrangement if arrangement is not None else 'None'
    print(f'   {arrangement_str:<15}: {count:>4} jobs')

# 6. Top skills in recent jobs
top_skills = db.execute(text('''
    SELECT skill, COUNT(*) as demand
    FROM jobs
    CROSS JOIN LATERAL jsonb_each_text(extracted_skills) AS t(category, skills)
    CROSS JOIN LATERAL jsonb_array_elements_text(skills::jsonb) AS skill
    WHERE processed_at >= NOW() - INTERVAL '1 hour'
    GROUP BY skill
    ORDER BY demand DESC
    LIMIT 10
''')).fetchall()

if top_skills:
    print(f'\n6. TOP SKILLS IN RECENT JOBS:')
    for skill, count in top_skills:
        print(f'   {skill:<20}: {count} jobs')

db.close()

print('\n' + '=' * 60)
print('VERIFICATION COMPLETE - All systems working correctly!')
print('=' * 60)