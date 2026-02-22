
import sys
import logging
from pathlib import Path
import numpy as np

# Setup path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the class to test (we need to mock some parts)
from src.model_inference import ICD10Predictor

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

def test_negation_logic():
    print("="*60)
    print("TESTING NEGATION LOGIC")
    print("="*60)

    # Instantiate predictor (mocking the heavy loading parts)
    # We can't easily mock __init__ without extensive patching, so we'll just use the methods directly
    # if possible, or subclass.

    class MockPredictor(ICD10Predictor):
        def __init__(self):
            # Skip loading model
            self.idx_to_code = {0: 'I10', 1: 'Z91.81'}
            self.code_to_idx = {'I10': 0, 'Z91.81': 1}
            self.device = 'cpu'
            self.model = True # Mock

        def _load_model(self):
            pass

    predictor = MockPredictor()

    # Test cases for _check_negation
    negation_tests = [
        ("Patient has no hypertension", "hypertension", True),
        ("Patient denies hypertension", "hypertension", True),
        ("Negative for hypertension", "hypertension", True),
        ("History of hypertension", "hypertension", False),
        ("Patient has hypertension", "hypertension", False),
        ("No evidence of fall", "fall", True),
        ("Patient fell yesterday", "fell", False),
        ("Patient denies any fall", "fall", True),
        ("Patient presents without chest pain", "chest pain", True),
    ]

    print("\n1. Testing _check_negation direct logic:")
    for text, keyword, expected in negation_tests:
        # Find index of keyword
        import re
        match = re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE)
        if not match:
            print(f"  Skipping '{text}': keyword '{keyword}' not found")
            continue

        start_index = match.start()
        result = predictor._check_negation(text, start_index)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {status} | Text: '{text}' | Keyword: '{keyword}' | Negated: {result} (Expected: {expected})")

    # Test _apply_keyword_rules integration
    print("\n2. Testing _apply_keyword_rules integration:")

    # Case 1: Positive mention of I10 (Hypertension)
    probs = np.array([0.1, 0.1]) # [I10, Z91.81]
    text_pos = "Patient has hypertension."
    new_probs = predictor._apply_keyword_rules(text_pos, probs.copy())
    print(f"  Positive Text: '{text_pos}'")
    print(f"  Original I10 prob: 0.1 -> New: {new_probs[0]:.2f}")
    if new_probs[0] > 0.5:
        print("  ✅ Boost applied correctly.")
    else:
        print("  ❌ Boost FAILED.")

    # Case 2: Negative mention of I10
    probs = np.array([0.1, 0.1])
    text_neg = "Patient denies hypertension."
    new_probs_neg = predictor._apply_keyword_rules(text_neg, probs.copy())
    print(f"  Negative Text: '{text_neg}'")
    print(f"  Original I10 prob: 0.1 -> New: {new_probs_neg[0]:.2f}")
    if new_probs_neg[0] == 0.1:
        print("  ✅ Boost correctly skipped.")
    else:
        print("  ❌ Boost applied incorrectly (should have been skipped).")

if __name__ == "__main__":
    test_negation_logic()
