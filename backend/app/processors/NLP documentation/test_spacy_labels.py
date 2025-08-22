#!/usr/bin/env python3
"""Quick test to show what entity labels spaCy actually returns"""
import spacy

nlp = spacy.load("en_core_web_sm")

text = "Senior Python Developer at Microsoft. Must have React, AWS, and Docker experience."

doc = nlp(text)

print("Entities found by spaCy:")
print("-" * 50)
for ent in doc.ents:
    print(f"'{ent.text}' → Label: {ent.label_}")

print("\n" + "=" * 50)
print("Available labels in en_core_web_sm model:")
print("=" * 50)
print(nlp.get_pipe("ner").labels)

