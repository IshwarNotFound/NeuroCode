"""
ICD-10 Code Validation and Extraction Module
Extracts and validates ICD-10-CM codes from medical text
"""

import re
from typing import List, Dict, Optional, Tuple
from collections import Counter

# Import config (adjust path for Colab)
try:
    from config.config import ICD10_PATTERN, ICD10_CHAPTERS, INVALID_ICD10_CATEGORIES
except ImportError:
    # Default values if config not available
    ICD10_PATTERN = r'\b([A-TV-Z][0-9]{2})\.?([0-9A-Z]{1,4})?\b'
    ICD10_CHAPTERS = {
        'A': 'Infectious diseases', 'B': 'Infectious diseases',
        'C': 'Neoplasms', 'D': 'Neoplasms/Blood diseases',
        'E': 'Endocrine/Metabolic', 'F': 'Mental disorders',
        'G': 'Nervous system', 'H': 'Eye/Ear',
        'I': 'Circulatory system', 'J': 'Respiratory system',
        'K': 'Digestive system', 'L': 'Skin diseases',
        'M': 'Musculoskeletal', 'N': 'Genitourinary',
        'O': 'Pregnancy', 'P': 'Perinatal conditions',
        'Q': 'Congenital malformations', 'R': 'Symptoms/Signs',
        'S': 'Injury', 'T': 'Injury/Poisoning',
        'V': 'External causes', 'W': 'External causes',
        'X': 'External causes', 'Y': 'External causes',
        'Z': 'Factors influencing health'
    }
    INVALID_ICD10_CATEGORIES = {'U'}


class ICD10Validator:
    """
    Validates and extracts ICD-10-CM diagnosis codes from text.
    
    ICD-10-CM Format:
    - First character: Letter (A-Z except U)
    - Characters 2-3: Digits (00-99)
    - Optional: Decimal point + 1-4 alphanumeric characters
    
    Examples: I10, E11.9, M62.81, R26.81, Z91.81
    """
    
    def __init__(self):
        """Initialize the ICD-10 validator with regex pattern"""
        self.pattern = re.compile(ICD10_PATTERN, re.IGNORECASE)
        self.chapters = ICD10_CHAPTERS
        self.invalid_categories = INVALID_ICD10_CATEGORIES
        
        # Common false positives to exclude
        self.false_positives = {
            'A00', 'B00', 'C00', 'D00',  # Too generic
            'T00', 'V00', 'W00', 'X00', 'Y00',  # Placeholder codes
        }
    
    def validate_code(self, code: str) -> bool:
        """
        Validate a single ICD-10-CM code.
        
        Args:
            code: ICD-10 code string (e.g., 'I10', 'E11.9')
            
        Returns:
            True if valid, False otherwise
        """
        if not code or len(code) < 3:
            return False
            
        code = code.upper().strip()
        
        # Check first character is valid letter
        if code[0] in self.invalid_categories:
            return False
        if not code[0].isalpha():
            return False
            
        # Check positions 2-3 are digits
        base = code[:3].replace('.', '')
        if len(base) < 3:
            return False
        if not base[1:3].isdigit():
            return False
            
        # Check not in false positives
        if code[:3] in self.false_positives:
            return False
            
        return True
    
    def normalize_code(self, base: str, extension: str = '') -> str:
        """
        Normalize ICD-10 code to standard format (with decimal).
        
        Args:
            base: First 3 characters (e.g., 'I10')
            extension: Characters after decimal (e.g., '9')
            
        Returns:
            Normalized code (e.g., 'I10' or 'E11.9')
        """
        code = base.upper()
        if extension:
            code = f"{code}.{extension.upper()}"
        return code
    
    def extract_codes(self, text: str) -> List[str]:
        """
        Extract all valid ICD-10 codes from text.
        
        Args:
            text: Medical document text
            
        Returns:
            List of unique ICD-10 codes found (preserves order)
        """
        if not text:
            return []
            
        # Find all matches
        matches = self.pattern.findall(text.upper())
        
        # Normalize and validate
        codes = []
        seen = set()
        
        for base, extension in matches:
            code = self.normalize_code(base, extension)
            
            if code not in seen and self.validate_code(code):
                codes.append(code)
                seen.add(code)
        
        return codes
    
    def get_code_info(self, code: str) -> Optional[Dict]:
        """
        Get detailed information about an ICD-10 code.
        
        Args:
            code: ICD-10 code string
            
        Returns:
            Dictionary with code details or None if invalid
        """
        if not self.validate_code(code):
            return None
            
        code = code.upper().strip()
        chapter_letter = code[0]
        
        # Parse code structure
        if '.' in code:
            category, extension = code.split('.', 1)
        else:
            category = code[:3]
            extension = ''
        
        return {
            'full_code': code,
            'category': category,
            'extension': extension,
            'chapter_letter': chapter_letter,
            'chapter_name': self.chapters.get(chapter_letter, 'Unknown'),
            'is_billable': len(code) >= 4  # Generally, codes with extension are billable
        }
    
    def get_code_category(self, code: str) -> str:
        """
        Get the 3-character category for a code.
        
        Args:
            code: ICD-10 code string
            
        Returns:
            Category (first 3 characters) or empty string
        """
        if not code or len(code) < 3:
            return ''
        return code[:3].upper()
    
    def get_chapter(self, code: str) -> str:
        """
        Get the chapter/disease category for a code.
        
        Args:
            code: ICD-10 code string
            
        Returns:
            Chapter name or 'Unknown'
        """
        if not code:
            return 'Unknown'
        return self.chapters.get(code[0].upper(), 'Unknown')
    
    def analyze_codes(self, codes: List[str]) -> Dict:
        """
        Analyze a list of ICD-10 codes.
        
        Args:
            codes: List of ICD-10 codes
            
        Returns:
            Dictionary with analysis results
        """
        valid_codes = [c for c in codes if self.validate_code(c)]
        
        # Count by chapter
        chapter_counts = Counter(self.get_chapter(c) for c in valid_codes)
        
        # Count by category
        category_counts = Counter(self.get_code_category(c) for c in valid_codes)
        
        return {
            'total_codes': len(codes),
            'valid_codes': len(valid_codes),
            'invalid_codes': len(codes) - len(valid_codes),
            'unique_codes': len(set(valid_codes)),
            'chapter_distribution': dict(chapter_counts),
            'top_categories': category_counts.most_common(10)
        }


def extract_icd10_codes(text: str) -> List[str]:
    """
    Convenience function to extract ICD-10 codes from text.
    
    Args:
        text: Medical document text
        
    Returns:
        List of unique ICD-10 codes
    """
    validator = ICD10Validator()
    return validator.extract_codes(text)


# ============================================
# Testing
# ============================================
if __name__ == "__main__":
    # Test cases
    test_text = """
    Patient: Allan Enrich, Male, DOB: 6/11/1952
    Primary Diagnosis: G31.1 - Senile degeneration of brain
    Other Diagnoses:
    - I69.354 - Hemiplegia following cerebral infarction
    - I69.391 - Dysphagia following cerebral infarction
    - R13.12 - Dysphagia, oropharyngeal phase
    - J43.9 - Emphysema, unspecified
    - I13.10 - Hypertensive heart and chronic kidney disease
    - N18.1 - Chronic kidney disease, stage 1
    - I25.10 - Atherosclerotic heart disease
    - I48.91 - Unspecified atrial fibrillation
    - E11.9 - Type 2 diabetes mellitus
    - I10 - Essential hypertension
    """
    
    validator = ICD10Validator()
    codes = validator.extract_codes(test_text)
    
    print("=" * 50)
    print("ICD-10 EXTRACTION TEST")
    print("=" * 50)
    print(f"\nExtracted {len(codes)} codes:")
    for i, code in enumerate(codes, 1):
        info = validator.get_code_info(code)
        print(f"  {i}. {code} - {info['chapter_name']}")
    
    print("\n" + "=" * 50)
    print("ANALYSIS")
    print("=" * 50)
    analysis = validator.analyze_codes(codes)
    print(f"Total codes: {analysis['total_codes']}")
    print(f"Unique codes: {analysis['unique_codes']}")
    print(f"\nBy chapter:")
    for chapter, count in analysis['chapter_distribution'].items():
        print(f"  {chapter}: {count}")
