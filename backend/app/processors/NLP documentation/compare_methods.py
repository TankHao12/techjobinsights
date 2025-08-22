#!/usr/bin/env python3
"""
Comparison of NLP vs Pattern Matching for skill extraction
"""

import spacy

nlp = spacy.load("en_core_web_sm")

# Sample text
text = "We need a Python developer with React and AI/ML experience. Must know C#."

print("=" * 70)
print("TEXT:", text)
print("=" * 70)

# METHOD 1: NLP - Named Entity Recognition
print("\nMETHOD 1: NLP - Named Entity Recognition")
print("-" * 70)
doc = nlp(text)
print("spaCy processes the text and identifies entities:")
for ent in doc.ents:
    print(f"  '{ent.text}' → Label: {ent.label_}, Length: {len(ent.text)}")
    if len(ent.text) > 2:
        print(f"    [PASS] Passes length filter (> 2 chars)")
    else:
        print(f"    [SKIP] Filtered out (<= 2 chars)")

# METHOD 2: NLP - Noun Chunks
print("\nMETHOD 2: NLP - Noun Chunks")
print("-" * 70)
print("spaCy identifies noun phrases:")
for chunk in doc.noun_chunks:
    print(f"  '{chunk.text}'")

# METHOD 3: Pattern Matching (Direct String Search)
print("\nMETHOD 3: Pattern Matching (Direct String Search)")
print("-" * 70)
print("Simple string search WITHOUT NLP:")

skills_to_find = ['python', 'react', 'ai', 'ml', 'c#', 'java']
text_lower = text.lower()

for skill in skills_to_find:
    if skill in text_lower:
        # Find where it appears
        index = text_lower.find(skill)
        print(f"  [FOUND] '{skill}' at position {index}")
    else:
        print(f"  [NOT FOUND] '{skill}'")

# DEMONSTRATE THE DIFFERENCE
print("\n" + "=" * 70)
print("KEY DIFFERENCE: Context Understanding")
print("=" * 70)

# Example 1: "Go to the store" vs "experience with Go language"
examples = [
    "We need someone with Go programming experience",
    "Please go to the office tomorrow"
]

for example in examples:
    print(f"\nText: '{example}'")
    doc = nlp(example)
    
    # NLP - tries to understand context
    print("  NLP entities:", [ent.text for ent in doc.ents])
    
    # Pattern matching - just searches
    if "go" in example.lower():
        print("  Pattern match: Found 'go' (but can't tell if it's the language!)")
    else:
        print("  Pattern match: 'go' not found")

# Example 2: Short acronyms
print("\n" + "=" * 70)
print("HANDLING SHORT ACRONYMS")
print("=" * 70)

text2 = "We need AI and ML expertise for this role"
doc2 = nlp(text2)

print(f"Text: '{text2}'")
print("\nNLP entities:")
for ent in doc2.ents:
    print(f"  '{ent.text}' → {ent.label_} (length: {len(ent.text)})")
    if len(ent.text) <= 2:
        print(f"    [WARNING] Would be filtered out by len(ent.text) > 2")

print("\nPattern matching:")
for skill in ['ai', 'ml']:
    if skill in text2.lower():
        print(f"  [FOUND] '{skill}' found directly (no length filter needed)")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
NLP (spaCy):
  Pros:
    - Understands context and grammar
    - Can disambiguate (e.g., "Go" the language vs "go" the verb)
    - Identifies entity types (ORG, PRODUCT, etc.)
  
  Cons:
    - Slower (processing overhead)
    - Can make mistakes (like classifying "React" as GPE)
    - Misses short terms if you use len() filter
    - Requires training data - may not know new tech terms

Pattern Matching:
  Pros:
    - Very fast
    - 100% reliable for known terms in your predefined list
    - No length restrictions
    - Catches everything you explicitly define
  
  Cons:
    - No context understanding (finds "go" everywhere)
    - Can have false positives
    - Only finds what you explicitly search for
    - Case-sensitive unless you normalize

Your Code Uses ALL THREE Methods:
  1. NLP entities (smart but incomplete)
  2. NLP noun chunks (hybrid approach)  
  3. Pattern matching (reliable backup)
  
This layered approach ensures you don't miss skills!
""")

