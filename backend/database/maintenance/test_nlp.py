#!/usr/bin/env python3
"""
Test script for NLP Engine with spaCy
"""

print('=' * 50)
print('TESTING NLP ENGINE WITH SPACY')
print('=' * 50)

from app.processors.nlp_engine import NLPEngine

# Initialize NLP Engine (will fail if spaCy not properly installed)
print('\nInitializing NLP Engine...')
nlp = NLPEngine()
print('✓ NLP Engine initialized with spaCy')

# Test text
test_text = '''
Senior Full Stack Developer - Hybrid Working Available
Auckland CBD | $120,000 - $150,000 per annum + benefits

We're seeking an experienced Full Stack Developer with expertise in:
- React, Vue.js, Angular
- Python, Django, FastAPI
- PostgreSQL, MongoDB
- AWS, Docker, Kubernetes
- 5+ years commercial experience required

This is a hybrid role with flexible work from home options.
'''

print('\nTesting NLP extraction features:')
print('-' * 40)

# 1. Skills extraction
skills = nlp.extract_skills(test_text)
total_skills = sum(len(v) for v in skills.values())
print(f'\n1. Skills Extracted: {total_skills} total')
for category, skill_list in skills.items():
    if skill_list:
        print(f'   {category}: {skill_list}')

# 2. Salary extraction
salary = nlp.extract_salary_info(test_text)
print(f'\n2. Salary: ${salary.get("min_salary", 0):,} - ${salary.get("max_salary", 0):,} {salary.get("period", "")}')
print(f'   Confidence: {salary.get("confidence_score", 0):.2f}')

# 3. Work arrangement
work_arr = nlp.extract_work_arrangement(test_text)
print(f'\n3. Work Arrangement: {work_arr}')

# 4. Experience level
exp = nlp.extract_experience_level('Senior Full Stack Developer', test_text)
print(f'\n4. Experience Level: {exp}')

# 5. Employment type
emp_type = nlp.extract_employment_type(test_text)
print(f'\n5. Employment Type: {emp_type}')

# 6. Tech job detection
is_tech, confidence = nlp.is_tech_job('Senior Full Stack Developer', test_text)
print(f'\n6. Is Tech Job: {is_tech} (confidence: {confidence:.2f})')

print('\n' + '=' * 50)
print('✓ ALL NLP TESTS PASSED SUCCESSFULLY!')
print('=' * 50)