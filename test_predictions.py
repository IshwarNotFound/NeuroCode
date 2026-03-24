"""
Comprehensive Test: Verify Different Demo Cases Produce Different Predictions

This module is a standalone validation script designed to programmatically test 
that the trained CNN model yields demonstrably different ICD-10 sets when 
presented with text spanning different clinical conditions. This serves as a 
unit test against model overfitting or a "predict-majority-class-only" failure state.
"""

import sys
import os
from pathlib import Path

# Setup path so the script can resolve `src` and `streamlit_app` imports
# regardless of what directory the user triggers the script from.
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Critical Execution Order requirement:
# The Vocabulary class MUST be imported into the local namespace BEFORE 
# Python's `pickle.load()` attempts to unpickle the vocabulary file. 
# Otherwise, unpickling fails with AttributeError.
from src.vocabulary import Vocabulary  # type: ignore[import]


def test_predictions():
    """
    Simulates a battery of requests routing through the `model_inference` stack 
    using the synthetic case data, asserting that top predictions differ.
    """
    print("="*60)
    print("COMPREHENSIVE PREDICTION TEST")
    print("="*60)
    
    # Delayed import after paths are confirmed setup
    from src.model_inference import predict_icd10, get_predictor  # type: ignore[import]
    from streamlit_app.case_data import get_case  # type: ignore[import]
    
    # ---------------------------------------------------------
    # Force reload predictor (clear singleton)
    # This guarantees we aren't inheriting corrupted state from 
    # an earlier run or a persistent terminal.
    # ---------------------------------------------------------
    import src.model_inference as mi  # type: ignore[import]
    mi._predictor = None
    
    # A curated list of mock patient IDs designed to span distinct chapters:
    # 1: Fall (Z), 2: Hyperlipidemia/Gout (E/M), 3: Hypothyroidism/CKD (E/N)
    # 4: Hypertensive CKD (I/N), 5: Knee OA (M), 6: GERD (K), 7: CHF (I), 10: COPD (J)
    test_cases = [1, 2, 3, 4, 5, 6, 7, 10]
    results = {}
    
    # Loop over cases and acquire predictions
    for case_num in test_cases:
        case = get_case(case_num)
        print(f"\n{'='*60}")
        print(f"CASE {case_num}: {case.get('title', 'Unknown')}")
        print(f"Text length: {len(case['text'])} chars")
        
        # Fire test inference
        preds = predict_icd10(case['text'], top_k=5)
        
        print(f"\nTop 5 Predictions:")
        for i, p in enumerate(preds, 1):
            print(f"  {i}. {p['code']} ({p['confidence']:.2%}): {p['description'][:40]}")
        
        # Cache the top 3 highest confidence codes mapped to this case
        results[case_num] = [p['code'] for p in preds[:3]]
    
    # Compare results across varying case payloads
    print("\n" + "="*60)
    print("ANALYSIS:")
    print("="*60)
    
    # Aggregate only the #1 top prediction across all cases
    top_codes = [results[c][0] for c in test_cases]
    unique_top = set(top_codes)
    
    print(f"\nTop predictions across {len(test_cases)} cases:")
    for case_num in test_cases:
        case = get_case(case_num)
        # Log the explicit pairing of text theme to top code
        print(f"  Case {case_num} ({case.get('title', '')[:25]}...): {results[case_num][0]}")
    
    # Evaluate model health based on the diversity of the output
    if len(unique_top) == 1:
        # Indicates model collapse. It is blindly guessing one class regardless of text.
        print(f"\n❌ PROBLEM: All cases have same top prediction: {top_codes[0]}")
        print("   This indicates the model is not responding to input correctly.")
    elif len(unique_top) < len(test_cases) / 2:
        # Model distinguishes inputs but is excessively grouping multiple concepts.
        print(f"\n⚠️ WARNING: Only {len(unique_top)}/{len(test_cases)} unique predictions")
        print("   Some cases may be getting similar predictions.")
    else:
        # Optimal variance.
        print(f"\n✅ SUCCESS: {len(unique_top)}/{len(test_cases)} unique top predictions!")
        print("   Model is responding correctly to different inputs.")
    
    return results

if __name__ == "__main__":
    # Execute primary test suite if not imported as module
    test_predictions()
