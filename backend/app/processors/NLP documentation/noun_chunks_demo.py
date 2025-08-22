#!/usr/bin/env python3
"""
Demonstration of Noun Chunks for skill extraction
"""

import spacy

nlp = spacy.load("en_core_web_sm")

# Sample job description
text = """
We are seeking an experienced Python developer for our cloud infrastructure team.
The ideal candidate will have strong React and Django skills.
You will work on data analytics applications using PostgreSQL and Redis.
Experience with AWS cloud services is essential.
The software engineering team is collaborative and innovative.
"""

print("=" * 70)
print("NOUN CHUNKS DEMONSTRATION")
print("=" * 70)
print(f"\nJob Description:\n{text}")

doc = nlp(text)

# Show ALL noun chunks first
print("\n" + "=" * 70)
print("ALL NOUN CHUNKS FOUND BY SPACY")
print("=" * 70)
print(f"{'Chunk Text':<40} {'Root Noun':<15} {'Root POS'}")
print("-" * 70)

for chunk in doc.noun_chunks:
    print(f"{chunk.text:<40} {chunk.root.text:<15} {chunk.root.pos_}")

# Now apply the filtering logic from your code
print("\n" + "=" * 70)
print("FILTERING: TECH-RELATED NOUN CHUNKS")
print("=" * 70)

# These are the context words from your code
tech_context_words = ['software', 'web', 'data', 'cloud', 'system', 'application']

print(f"Context filters: {tech_context_words}\n")

tech_chunks = []
for chunk in doc.noun_chunks:
    chunk_text = chunk.text.lower()
    # Check if chunk contains any tech context word
    if any(tech_word in chunk_text for tech_word in tech_context_words):
        tech_chunks.append(chunk)
        # Show which context word matched
        matching_words = [w for w in tech_context_words if w in chunk_text]
        print(f"[MATCH] '{chunk.text}'")
        print(f"  Matched context: {matching_words}")

if not tech_chunks:
    print("(No tech-related chunks found)")

# Now search for skills within these chunks
print("\n" + "=" * 70)
print("SKILL EXTRACTION FROM TECH CHUNKS")
print("=" * 70)

# Define some skills (subset from your code)
tech_skills = {
    'programming_languages': ['python', 'java', 'javascript', 'c#'],
    'web_frameworks': ['react', 'django', 'flask', 'angular'],
    'databases': ['postgresql', 'mysql', 'mongodb', 'redis'],
    'cloud_platforms': ['aws', 'azure', 'gcp']
}

found_skills = {category: [] for category in tech_skills.keys()}

for chunk in tech_chunks:
    chunk_text = chunk.text.lower()
    print(f"\nAnalyzing chunk: '{chunk.text}'")
    
    # Search for skills in this chunk
    chunk_found_skills = []
    for category, skills in tech_skills.items():
        for skill in skills:
            if skill in chunk_text and skill not in found_skills[category]:
                found_skills[category].append(skill)
                chunk_found_skills.append(f"{skill} ({category})")
    
    if chunk_found_skills:
        print(f"  Skills found: {', '.join(chunk_found_skills)}")
    else:
        print(f"  No predefined skills found in this chunk")

# Show final results
print("\n" + "=" * 70)
print("FINAL EXTRACTED SKILLS")
print("=" * 70)
for category, skills in found_skills.items():
    if skills:
        print(f"{category}: {skills}")

# Comparison with other methods
print("\n" + "=" * 70)
print("WHY NOUN CHUNKS ARE USEFUL")
print("=" * 70)

examples = [
    ("a Python developer", "Captures 'Python' in context of being a developer role"),
    ("data analytics applications", "Captures 'data' with application context"),
    ("cloud infrastructure team", "Captures 'cloud' in team context"),
    ("AWS cloud services", "Captures both 'AWS' and 'cloud' together"),
]

print("\nExamples of what noun chunks capture:\n")
for chunk_example, explanation in examples:
    print(f"  '{chunk_example}'")
    print(f"    → {explanation}\n")

# Show the advantage over simple pattern matching
print("\n" + "=" * 70)
print("ADVANTAGE OVER SIMPLE PATTERN MATCHING")
print("=" * 70)

comparison_text = """
Example 1: "We need Python developers" vs "Python is mentioned here"
Example 2: "Experience with cloud platforms" vs "The cloud is beautiful"
"""

print(comparison_text)
print("Noun chunks help by providing grammatical context:")
print("  - 'Python developers' → Python is part of a job role (relevant!)")
print("  - 'Python is mentioned' → Python is just mentioned (less relevant)")
print("  - 'cloud platforms' → cloud in tech context (relevant!)")
print("  - 'the cloud is beautiful' → cloud as weather (not relevant!)")

# Demonstrate the filtering
print("\n" + "=" * 70)
print("PRACTICAL EXAMPLE: FILTERING WITH TECH CONTEXT")
print("=" * 70)

tricky_text = "We need someone to develop cloud-based applications using Python and React."
doc2 = nlp(tricky_text)

print(f"\nText: {tricky_text}\n")
print("All noun chunks:")
for chunk in doc2.noun_chunks:
    print(f"  - {chunk.text}")

print("\nTech-filtered chunks (with context words):")
for chunk in doc2.noun_chunks:
    chunk_text = chunk.text.lower()
    if any(tech_word in chunk_text for tech_word in tech_context_words):
        print(f"  [MATCH] {chunk.text}")
    else:
        print(f"  [SKIP] {chunk.text} (no tech context)")

# Show why this is better than NER alone
print("\n" + "=" * 70)
print("COMPARISON: NOUN CHUNKS vs NAMED ENTITY RECOGNITION")
print("=" * 70)

comparison_doc = nlp("The senior React developer will work on cloud applications.")

print("\nText: 'The senior React developer will work on cloud applications.'\n")

print("Named Entities (NER):")
if doc.ents:
    for ent in comparison_doc.ents:
        print(f"  - '{ent.text}' ({ent.label_})")
else:
    print("  (None found by NER)")

print("\nNoun Chunks:")
for chunk in comparison_doc.noun_chunks:
    print(f"  - '{chunk.text}'")

print("\nNoun chunks capture MORE context:")
print("  - 'The senior React developer' → Contains 'React' with full role context")
print("  - 'cloud applications' → Contains 'cloud' with application context")
print("  NER might miss 'React' or misclassify it!")

