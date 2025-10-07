#!/usr/bin/env python3
"""
Test the date parsing function to ensure it handles all common formats
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, date, timedelta
from app.processors.nlp_engine import NLPEngine

def test_date_parsing():
    """Test various date formats"""
    nlp_engine = NLPEngine()
    today = date.today()
    
    # Test cases: (input_text, expected_days_ago)
    test_cases = [
        # Today/yesterday
        ("today", 0),
        ("Listed today", 0),
        ("Posted today", 0),
        ("just posted", 0),
        ("just now", 0),
        ("yesterday", 1),
        ("Listed yesterday", 1),
        
        # Hours ago (should round to today if < 24 hours)
        ("5h ago", 0),
        ("23h ago", 0),
        ("5 hours ago", 0),
        ("Posted 23h ago", 0),
        ("Listed 12 hours ago", 0),
        
        # Days ago - short format
        ("1d ago", 1),
        ("2d ago", 2),
        ("5d ago", 5),
        ("7d ago", 7),
        ("30d ago", 30),
        
        # Days ago - long format
        ("1 day ago", 1),
        ("2 days ago", 2),
        ("5 days ago", 5),
        ("Listed 7 days ago", 7),
        ("Posted 14 days ago", 14),
        
        # Weeks ago - short format
        ("1w ago", 7),
        ("2w ago", 14),
        ("3w ago", 21),
        
        # Weeks ago - long format
        ("1 week ago", 7),
        ("2 weeks ago", 14),
        ("Listed 3 weeks ago", 21),
        ("Posted 4 weeks ago", 28),
        
        # Months ago - short format
        ("1m ago", 30),
        ("2m ago", 60),
        
        # Months ago - long format
        ("1 month ago", 30),
        ("2 months ago", 60),
        ("Listed 3 months ago", 90),
        
        # Word numbers (incompletely scraped - actual data from database)
        ("one", 0),          # 1 hour -> today
        ("two", 0),          # 2 hours -> today
        ("three", 0),        # 3 hours -> today
        ("five", 0),         # 5 hours -> today
        ("eight", 0),        # 8 hours -> today
        ("twelve", 0),       # 12 hours -> today
        ("fourteen", 0),     # 14 hours -> today
        ("twenty", 0),       # 20 hours -> today
        ("twenty one", 0),   # 21 hours -> today
        ("twenty two", 0),   # 22 hours -> today
        ("twenty three", 0), # 23 hours -> today
        ("thirty", 1),       # 30 hours -> 1 day
        ("forty", 2),        # 40 hours -> 2 days
    ]
    
    print("=" * 70)
    print("TESTING DATE PARSING FUNCTION")
    print("=" * 70)
    print(f"Today's date: {today}")
    print()
    
    passed = 0
    failed = 0
    
    for input_text, expected_days_ago in test_cases:
        result = nlp_engine.parse_posted_date(input_text)
        
        if result:
            actual_days_ago = (today - result).days
            expected_date = today - timedelta(days=expected_days_ago)
            
            # Allow 1 day tolerance for rounding
            if abs(actual_days_ago - expected_days_ago) <= 1:
                status = "✓ PASS"
                passed += 1
            else:
                status = "✗ FAIL"
                failed += 1
            
            print(f"{status:8} | Input: '{input_text:30}' | Result: {result} ({actual_days_ago}d ago) | Expected: {expected_date} ({expected_days_ago}d ago)")
        else:
            print(f"✗ FAIL   | Input: '{input_text:30}' | Result: None | Expected: {expected_days_ago}d ago")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = test_date_parsing()
    sys.exit(0 if success else 1)

