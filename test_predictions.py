"""
Comprehensive Test: Verify Different Demo Cases Produce Different Predictions
"""
import sys
import os
from pathlib import Path

# Setup path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Critical: Import Vocabulary BEFORE pickle loads it
from src.vocabulary import Vocabulary

def test_predictions():
    print("="*60)
    print("COMPREHENSIVE PREDICTION TEST")
    print("="*60)
    
    # Import after path setup
    from src.model_inference import predict_icd10, get_predictor
    from streamlit_app.case_data import get_case
    
    # Force reload predictor (clear singleton)
    import src.model_inference as mi
    mi._predictor = None
    
    # Test with multiple demo cases
    test_cases = [1, 2, 3, 4, 5, 6, 7, 10]  # Fall, Hyperlipidemia, Hypothyroidism, Hypertensive CKD, Knee OA, GERD, CHF, COPD
    results = {}
    
    for case_num in test_cases:
        case = get_case(case_num)
        print(f"\n{'='*60}")
        print(f"CASE {case_num}: {case.get('title', 'Unknown')}")
        print(f"Text length: {len(case['text'])} chars")
        
        # Get predictions
        preds = predict_icd10(case['text'], top_k=5)
        
        print(f"\nTop 5 Predictions:")
        for i, p in enumerate(preds, 1):
            print(f"  {i}. {p['code']} ({p['confidence']:.2%}): {p['description'][:40]}")
        
        results[case_num] = [p['code'] for p in preds[:3]]
    
    # Compare results
    print("\n" + "="*60)
    print("ANALYSIS:")
    print("="*60)
    
    # Check if all cases have unique top predictions
    top_codes = [results[c][0] for c in test_cases]
    unique_top = set(top_codes)
    
    print(f"\nTop predictions across {len(test_cases)} cases:")
    for case_num in test_cases:
        case = get_case(case_num)
        print(f"  Case {case_num} ({case.get('title', '')[:25]}...): {results[case_num][0]}")
    
    if len(unique_top) == 1:
        print(f"\n❌ PROBLEM: All cases have same top prediction: {top_codes[0]}")
        print("   This indicates the model is not responding to input correctly.")
    elif len(unique_top) < len(test_cases) / 2:
        print(f"\n⚠️ WARNING: Only {len(unique_top)}/{len(test_cases)} unique predictions")
        print("   Some cases may be getting similar predictions.")
    else:
        print(f"\n✅ SUCCESS: {len(unique_top)}/{len(test_cases)} unique top predictions!")
        print("   Model is responding correctly to different inputs.")
    
    return results

if __name__ == "__main__":
    test_predictions()
