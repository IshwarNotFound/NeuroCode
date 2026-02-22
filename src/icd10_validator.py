"""
ICD-10 Code Validation and Extraction Module
This module provides classes and functions to search through raw text, 
extract strings that structurally resemble ICD-10-CM codes, and validate 
them against standardized rules to prevent false positives.
"""

import re
from typing import List, Dict, Optional, Tuple
from collections import Counter

# Attempt to import global configurations; if run dynamically where paths differ (like Colab), fallback is handled.
try:
    from config.config import ICD10_PATTERN, ICD10_CHAPTERS, INVALID_ICD10_CATEGORIES
except ImportError:
    # Default fallback values mirroring the main config file to ensure modular independence
    # Valid pattern: Single letter A-Z (excluding some), 2 digits, optional dot, up to 4 alphanumerics.
    ICD10_PATTERN = r'\b([A-TV-Z][0-9]{2})\.?([0-9A-Z]{1,4})?\b'
    # Core categorization dictionary dividing the alphabet into physiological systems or visit causes
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
    # Category U is traditionally reserved and treated here as invalid by default
    INVALID_ICD10_CATEGORIES = {'U'}


class ICD10Validator:
    """
    A robust class utility that parses free text and accurately captures and validates ICD-10-CM diagnosis codes.
    
    Standard Format Reference:
    - 1st character: Alpha Letter (A-Z except U) denoting chapter
    - 2nd & 3rd characters: Digits (00-99) specifying category
    - Optional: Decimal point + up to 4 alphanumeric subclass extension characters
    
    Valid Examples: I10, E11.9, M62.81, R26.81, Z91.81
    """
    
    def __init__(self):
        """
        Initializes the validator with compiled regex patterns and chapter dictionaries for rapid text scanning.
        """
        # Compile the regex pattern once for performance, making it case-insensitive
        self.pattern = re.compile(ICD10_PATTERN, re.IGNORECASE)
        self.chapters = ICD10_CHAPTERS
        self.invalid_categories = INVALID_ICD10_CATEGORIES
        
        # A curated set of codes that technically match the regex but are almost always 
        # artifacts, placeholders, or headers rather than actual patient diagnoses.
        self.false_positives = {
            'A00', 'B00', 'C00', 'D00',  # Broad category headers rather than specifics
            'T00', 'V00', 'W00', 'X00', 'Y00',  # Placeholder or generic external cause codes
        }
    
    def validate_code(self, code: str) -> bool:
        """
        Checks whether a provided string stringently adheres to ICD-10 formatting and exclusions.
        
        Args:
            code: The extracted ICD-10 code string candidate (e.g., 'I10', 'E11.9')
            
        Returns:
            True if it passes all formatting checks, False if it is invalid or a known false positive.
        """
        # Discard trivially short or empty strings
        if not code or len(code) < 3:
            return False
            
        # Normalize to uppercase and strip whitespace to ensure consistent checking
        code = code.upper().strip()
        
        # Verify the first character is an allowed alphabetical letter
        if code[0] in self.invalid_categories:
            return False
        if not code[0].isalpha():
            return False
            
        # Verify characters 2 and 3 are actually numbers
        base = code[:3].replace('.', '')
        if len(base) < 3:
            return False
        if not base[1:3].isdigit():
            return False
            
        # Verify the code isn't listed in our known false positive exclusion set
        if code[:3] in self.false_positives:
            return False
            
        return True
    
    def normalize_code(self, base: str, extension: str = '') -> str:
        """
        Standardizes the format of an ICD-10 code, ensuring it is uppercase and has the correct decimal placement.
        
        Args:
            base: The root 3 alphanumeric characters (e.g., 'I10')
            extension: The remaining alphanumeric characters following the dot (e.g., '9')
            
        Returns:
            A clean, formatted code string (e.g., 'I10.9')
        """
        code = base.upper()
        # Append the extension via a decimal dot if one exists
        if extension:
            code = f"{code}.{extension.upper()}"
        return code
    
    def extract_codes(self, text: str) -> List[str]:
        """
        Scans an entire document string and returns a list of all valid, unique ICD-10 codes mentioned.
        
        Args:
            text: A block of medical text (e.g., a patient discharge summary)
            
        Returns:
            List of parsed, normalized, and validated ICD-10 code strings found within the text.
        """
        if not text:
            return []
            
        # Execute the compiled regex to locate all strings matching the ICD-10 pattern
        matches = self.pattern.findall(text.upper())
        
        codes = []
        seen = set()  # Set utilized to bypass duplicate codes while maintaining chronological discovery order
        
        # Iterate over all raw hits
        for base, extension in matches:
            # Reconstruct the code format
            code = self.normalize_code(base, extension)
            
            # If the code hasn't been added yet and passes deep validation, keep it
            if code not in seen and self.validate_code(code):
                codes.append(code)
                seen.add(code)
        
        return codes
    
    def get_code_info(self, code: str) -> Optional[Dict]:
        """
        Breaks down a validated ICD-10 code into its semantic structural properties.
        
        Args:
            code: A validated ICD-10 code string.
            
        Returns:
            A dictionary containing structural details (chapter, extension, billability) or None if invalid.
        """
        if not self.validate_code(code):
            return None
            
        code = code.upper().strip()
        # The topmost hierarchy level indicated by the first letter
        chapter_letter = code[0]
        
        # Parse output into base category and precise fractional extension
        if '.' in code:
            category, extension = code.split('.', 1)
        else:
            category = code[:3]
            extension = ''
        
        # Return a compiled dictionary describing the code's attributes
        return {
            'full_code': code,
            'category': category,
            'extension': extension,
            'chapter_letter': chapter_letter,
            'chapter_name': self.chapters.get(chapter_letter, 'Unknown'),
            # A simplistic heuristic determining billability: codes with extensions are typically terminal nodes 
            'is_billable': len(code) >= 4  
        }
    
    def get_code_category(self, code: str) -> str:
        """
        Fetches the primary 3-character disease category root.
        
        Args:
            code: The input ICD-10 string.
            
        Returns:
            Just the first 3 characters signifying the broad disease cluster.
        """
        if not code or len(code) < 3:
            return ''
        return code[:3].upper()
    
    def get_chapter(self, code: str) -> str:
        """
        Identifies the high-level human-readable anatomical or pathological chapter for a code.
        
        Args:
            code: The input ICD-10 string.
            
        Returns:
            The descriptive name of the chapter (e.g., 'Circulatory system').
        """
        if not code:
            return 'Unknown'
        return self.chapters.get(code[0].upper(), 'Unknown')
    
    def analyze_codes(self, codes: List[str]) -> Dict:
        """
        Computes summary statistics across an array of ICD-10 codes. Useful for patient/document level overviews.
        
        Args:
            codes: A list containing ICD-10 strings to be processed.
            
        Returns:
            A dictionary of compiled statistics mapping chapters and most common code categories.
        """
        # First filter out any garbage codes that somehow slipped in
        valid_codes = [c for c in codes if self.validate_code(c)]
        
        # Use Counter to calculate frequencies for chapters and categories
        chapter_counts = Counter(self.get_chapter(c) for c in valid_codes)
        category_counts = Counter(self.get_code_category(c) for c in valid_codes)
        
        # Return analytical payload
        return {
            'total_codes': len(codes),
            'valid_codes': len(valid_codes),
            'invalid_codes': len(codes) - len(valid_codes),
            'unique_codes': len(set(valid_codes)),
            'chapter_distribution': dict(chapter_counts),         # How diseases spread across chapters
            'top_categories': category_counts.most_common(10)     # Most frequent root illness categories
        }


def extract_icd10_codes(text: str) -> List[str]:
    """
    A simple wrapper function enabling code extraction without manually instantiating the Validator class.
    
    Args:
        text: Medical document text block.
        
    Returns:
        List of unique extracted ICD-10 codes.
    """
    validator = ICD10Validator()
    return validator.extract_codes(text)


# ============================================
# Local Module Testing logic
# Provided to test extraction behavior without booting the entire application
# ============================================
if __name__ == "__main__":
    # Mock patient profile imitating raw EMR/OCR text dumps
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
    
    # Initialize processor
    validator = ICD10Validator()
    # Extract codes from string
    codes = validator.extract_codes(test_text)
    
    # Print extraction logs to console
    print("=" * 50)
    print("ICD-10 EXTRACTION TEST")
    print("=" * 50)
    print(f"\nExtracted {len(codes)} codes:")
    for i, code in enumerate(codes, 1):
        info = validator.get_code_info(code)
        print(f"  {i}. {code} - {info['chapter_name']}")
    
    # Print quantitative distributions
    print("\n" + "=" * 50)
    print("ANALYSIS")
    print("=" * 50)
    analysis = validator.analyze_codes(codes)
    print(f"Total codes: {analysis['total_codes']}")
    print(f"Unique codes: {analysis['unique_codes']}")
    print(f"\nBy chapter:")
    for chapter, count in analysis['chapter_distribution'].items():
        print(f"  {chapter}: {count}")
