#!/usr/bin/env python3
"""
Demonstration of how spaCy processes job descriptions
This shows what's happening behind the scenes in nlp_engine.py
"""

import spacy

# Load the same model used in your app
nlp = spacy.load("en_core_web_sm")

# Sample job description
text = """
Senior Python Developer needed for exciting fintech startup.
Must have 5+ years experience with React, Django, and PostgreSQL.
We offer $120,000 - $150,000 per annum plus benefits.
AWS and Docker skills are a plus.
"""

print("=" * 70)
print("SPACY NLP PROCESSING DEMONSTRATION")
print("=" * 70)
print(f"\nOriginal Text:\n{text}\n")

# Process with spaCy
doc = nlp(text)

# 1. TOKENIZATION
print("\n" + "=" * 70)
print("1. TOKENS (Individual words/punctuation)")
print("=" * 70)
print(f"{'Token':<20} {'POS':<10} {'Lemma':<20} {'Is Alpha?'}")
print("-" * 70)
for token in doc[:20]:  # First 20 tokens
    print(f"{token.text:<20} {token.pos_:<10} {token.lemma_:<20} {token.is_alpha}")

# 2. NAMED ENTITY RECOGNITION (NER)
print("\n" + "=" * 70)
print("2. NAMED ENTITIES (Things spaCy recognizes)")
print("=" * 70)
print(f"{'Entity':<30} {'Label':<15} {'Explanation'}")
print("-" * 70)
for ent in doc.ents:
    # Explain what each label means
    label_explanation = {
        'ORG': 'Organization',
        'PRODUCT': 'Product/Technology',
        'CARDINAL': 'Number',
        'MONEY': 'Monetary value',
        'DATE': 'Date/Time',
        'GPE': 'Geo-political entity',
        'PERSON': 'Person name'
    }
    explanation = label_explanation.get(ent.label_, ent.label_)
    print(f"{ent.text:<30} {ent.label_:<15} {explanation}")

# 3. NOUN CHUNKS
print("\n" + "=" * 70)
print("3. NOUN CHUNKS (Noun phrases)")
print("=" * 70)
print(f"{'Noun Chunk':<40} {'Root':<15} {'Root POS'}")
print("-" * 70)
for chunk in doc.noun_chunks:
    print(f"{chunk.text:<40} {chunk.root.text:<15} {chunk.root.pos_}")

# 4. DEMONSTRATE SKILL EXTRACTION LOGIC
print("\n" + "=" * 70)
print("4. SKILL EXTRACTION SIMULATION")
print("=" * 70)

# Define tech skills (subset from nlp_engine.py)
tech_skills = {
    'programming_languages': {'python', 'javascript', 'java', 'c#', 'ruby'},
    'web_frameworks': {'react', 'django', 'flask', 'angular', 'vue'},
    'databases': {'postgresql', 'mysql', 'mongodb', 'redis'},
    'cloud_platforms': {'aws', 'azure', 'gcp', 'google cloud'},
    'devops_tools': {'docker', 'kubernetes', 'jenkins', 'terraform'}
}

all_skills = set()
for category_skills in tech_skills.values():
    all_skills.update(category_skills)

found_skills = {category: [] for category in tech_skills.keys()}

# Method 1: Check named entities
print("\nMethod 1: Named Entity Recognition")
print("-" * 70)
for ent in doc.ents:
    skill_lower = ent.text.lower()
    if skill_lower in all_skills:
        for category, skills in tech_skills.items():
            if skill_lower in skills:
                found_skills[category].append(skill_lower)
                print(f"  Found '{ent.text}' (Entity: {ent.label_}) → {category}")

# Method 2: Check noun chunks
print("\nMethod 2: Noun Chunk Analysis")
print("-" * 70)
for chunk in doc.noun_chunks:
    chunk_text = chunk.text.lower()
    # Check if chunk contains tech indicators
    if any(tech_word in chunk_text for tech_word in 
           ['software', 'developer', 'engineer', 'experience', 'skills']):
        # Check for skills within the chunk
        for category, skills in tech_skills.items():
            for skill in skills:
                if skill in chunk_text and skill not in found_skills[category]:
                    found_skills[category].append(skill)
                    print(f"  Found '{skill}' in chunk '{chunk.text}' → {category}")

# Method 3: Pattern matching on full text
print("\nMethod 3: Direct Pattern Matching")
print("-" * 70)
text_lower = text.lower()
for category, skills in tech_skills.items():
    for skill in skills:
        if skill in text_lower and skill not in found_skills[category]:
            found_skills[category].append(skill)
            print(f"  Found '{skill}' in text → {category}")

# Show final extracted skills
print("\n" + "=" * 70)
print("FINAL EXTRACTED SKILLS (Deduplicated)")
print("=" * 70)
for category, skills in found_skills.items():
    if skills:
        unique_skills = list(set(skills))
        print(f"{category}: {unique_skills}")

total_skills = sum(len(list(set(skill_list))) for skill_list in found_skills.values())
print(f"\nTotal unique skills found: {total_skills}")

# 5. DEMONSTRATE is_tech_job CALCULATION
print("\n" + "=" * 70)
print("5. TECH JOB CLASSIFICATION SIMULATION")
print("=" * 70)

title = "Senior Python Developer"
description = text

# Calculate confidence score
confidence = 0.0

# Skills weight (60%)
if total_skills >= 5:
    skills_score = 0.6
elif total_skills >= 3:
    skills_score = 0.4
elif total_skills >= 1:
    skills_score = 0.2
else:
    skills_score = 0.0

confidence += skills_score
print(f"Skills score ({total_skills} skills found): +{skills_score:.2f}")

# Title indicators
tech_title_indicators = {
    'developer', 'engineer', 'programmer', 'analyst', 'architect',
    'software', 'web', 'mobile', 'data', 'cloud', 'devops', 'ai', 'ml'
}
title_score = sum(1 for indicator in tech_title_indicators if indicator in title.lower())

if title_score >= 2:
    title_weight = 0.3
elif title_score >= 1:
    title_weight = 0.2
else:
    title_weight = 0.0

confidence += title_weight
print(f"Title score ({title_score} indicators): +{title_weight:.2f}")

# Content weight
tech_content_words = ['code', 'coding', 'programming', 'algorithm', 'api', 'database']
content_score = sum(1 for word in tech_content_words if word in text.lower())
content_weight = min(content_score * 0.02, 0.1)
confidence += content_weight
print(f"Content score ({content_score} tech words): +{content_weight:.2f}")

print(f"\nFinal confidence: {confidence:.2f}")
print(f"Is tech job: {confidence >= 0.5} (threshold: 0.5)")

# 6. DEMONSTRATE SALARY EXTRACTION
print("\n" + "=" * 70)
print("6. SALARY EXTRACTION WITH SPACY")
print("=" * 70)

import re

# Find salary pattern
salary_pattern = r'\$([0-9]{2,3}),?([0-9]{3})\s*-\s*\$([0-9]{2,3}),?([0-9]{3})'
match = re.search(salary_pattern, text)

if match:
    print(f"Salary range found: {match.group(0)}")
    min_sal = int(match.groups()[0]) * 1000 + int(match.groups()[1])
    max_sal = int(match.groups()[2]) * 1000 + int(match.groups()[3])
    print(f"Parsed as: ${min_sal:,} - ${max_sal:,}")
    
    # Use spaCy to determine period
    print("\nUsing spaCy to find salary period:")
    for token in doc:
        token_lower = token.text.lower()
        if token_lower in ['hour', 'hourly', '/hr', 'hr']:
            print(f"  Found token '{token.text}' → Period: hourly")
            break
        elif token_lower in ['annum', 'annual', 'yearly', 'pa']:
            print(f"  Found token '{token.text}' → Period: yearly")
            break

print("\n" + "=" * 70)
print("END OF DEMONSTRATION")
print("=" * 70)

