"""
Hybrid PDF Text Extraction Module
Extracts text from PDFs using native extraction with OCR fallback

Optimized for Google Colab Free Tier:
- Checkpoint saving every N documents
- Memory management for large batches
- Retry logic for OCR failures
- Quality validation for extracted text
"""

import os
import time
import gc
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json

import pandas as pd
from tqdm import tqdm

# PDF extraction libraries
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from pdf2image import convert_from_path
    import pytesseract
except ImportError:
    convert_from_path = None
    pytesseract = None

# Import ICD-10 validator
try:
    from src.icd10_validator import ICD10Validator
except ImportError:
    from icd10_validator import ICD10Validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Data class for PDF extraction results"""
    filename: str
    filepath: str
    document_type: str
    full_text: str
    text_length: int
    icd10_codes: List[str]
    num_codes: int
    extraction_method: str  # 'native' or 'ocr'
    success: bool
    error_message: str = ""


class HybridPDFExtractor:
    """
    Extracts text from PDFs using hybrid approach:
    1. First attempts native text extraction (fast)
    2. Falls back to OCR if native extraction fails or returns garbage
    
    Includes:
    - Retry logic for OCR failures
    - Text quality validation
    - Checkpoint saving for long batches
    - Memory management
    """
    
    def __init__(
        self,
        ocr_dpi: int = 200,
        ocr_language: str = 'eng',
        max_retries: int = 3,
        min_text_length: int = 50,
        max_garbage_ratio: float = 0.3,
        checkpoint_interval: int = 50
    ):
        """
        Initialize the PDF extractor.
        
        Args:
            ocr_dpi: DPI for PDF to image conversion
            ocr_language: Tesseract language code
            max_retries: Maximum retry attempts for OCR
            min_text_length: Minimum characters for valid text
            max_garbage_ratio: Maximum ratio of garbage characters allowed
            checkpoint_interval: Save progress every N documents
        """
        self.ocr_dpi = ocr_dpi
        self.ocr_language = ocr_language
        self.max_retries = max_retries
        self.min_text_length = min_text_length
        self.max_garbage_ratio = max_garbage_ratio
        self.checkpoint_interval = checkpoint_interval
        
        self.icd_validator = ICD10Validator()
        
        # Check library availability
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required libraries are available"""
        if pdfplumber is None:
            logger.warning("pdfplumber not installed. Native extraction unavailable.")
        if convert_from_path is None or pytesseract is None:
            logger.warning("pdf2image or pytesseract not installed. OCR unavailable.")
    
    def is_text_quality_acceptable(self, text: str) -> bool:
        """
        Check if extracted text quality is acceptable.
        
        Args:
            text: Extracted text
            
        Returns:
            True if text quality is acceptable
        """
        if not text or len(text) < self.min_text_length:
            return False
        
        # Count garbage characters (non-alphanumeric, non-common punctuation)
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:!?\'-\n\t/()')
        garbage_count = sum(1 for c in text if c not in valid_chars)
        garbage_ratio = garbage_count / len(text)
        
        if garbage_ratio > self.max_garbage_ratio:
            return False
        
        # Check for reasonable word structure
        words = text.split()
        if len(words) < 10:
            return False
        
        # Check average word length (garbage typically has very short/long "words")
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len < 2 or avg_word_len > 20:
            return False
        
        return True
    
    def extract_text_native(self, pdf_path: str) -> Tuple[str, bool]:
        """
        Extract text using pdfplumber (native text extraction).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted text, success boolean)
        """
        if pdfplumber is None:
            return "", False
        
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            full_text = '\n'.join(text_parts).strip()
            return full_text, bool(full_text)
            
        except Exception as e:
            logger.debug(f"Native extraction failed for {pdf_path}: {e}")
            return "", False
    
    def extract_text_ocr(self, pdf_path: str) -> Tuple[str, bool]:
        """
        Extract text using OCR (Tesseract).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted text, success boolean)
        """
        if convert_from_path is None or pytesseract is None:
            return "", False
        
        for attempt in range(self.max_retries):
            try:
                # Convert PDF pages to images
                images = convert_from_path(
                    pdf_path,
                    dpi=self.ocr_dpi,
                    fmt='jpeg'
                )
                
                # OCR each page
                text_parts = []
                for image in images:
                    page_text = pytesseract.image_to_string(
                        image,
                        lang=self.ocr_language
                    )
                    if page_text:
                        text_parts.append(page_text)
                    
                    # Free memory
                    del image
                
                del images
                gc.collect()
                
                full_text = '\n'.join(text_parts).strip()
                return full_text, bool(full_text)
                
            except Exception as e:
                logger.warning(f"OCR attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)  # Wait before retry
        
        return "", False
    
    def smart_extract(self, pdf_path: str) -> ExtractionResult:
        """
        Smart extraction: try native first, OCR fallback.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ExtractionResult with extracted data
        """
        filename = os.path.basename(pdf_path)
        
        # Try native extraction first (faster)
        text, native_success = self.extract_text_native(pdf_path)
        extraction_method = 'native'
        
        # Check if native extraction produced quality text
        if not native_success or not self.is_text_quality_acceptable(text):
            # Fall back to OCR
            ocr_text, ocr_success = self.extract_text_ocr(pdf_path)
            
            if ocr_success and (not text or len(ocr_text) > len(text)):
                text = ocr_text
                extraction_method = 'ocr'
        
        # Determine success
        success = bool(text) and len(text) >= self.min_text_length
        
        # Extract ICD-10 codes
        icd_codes = self.icd_validator.extract_codes(text) if text else []
        
        # Determine document type
        doc_type = self._determine_document_type(text, filename)
        
        return ExtractionResult(
            filename=filename,
            filepath=str(pdf_path),
            document_type=doc_type,
            full_text=text,
            text_length=len(text),
            icd10_codes=icd_codes,
            num_codes=len(icd_codes),
            extraction_method=extraction_method,
            success=success,
            error_message="" if success else "Extraction failed or text too short"
        )
    
    def _determine_document_type(self, text: str, filename: str) -> str:
        """Determine document type from content and filename"""
        if not text:
            return 'Unknown'
        
        text_upper = text[:2000].upper()
        filename_upper = filename.upper()
        
        if 'G0179' in text_upper or 'G0180' in text_upper:
            return 'Home Health Certification'
        elif '485' in filename_upper or 'HOME HEALTH' in text_upper:
            return 'Home Health'
        elif 'PHYSICAL THERAPY' in text_upper or 'PT EVAL' in text_upper:
            return 'Physical Therapy'
        elif 'OCCUPATIONAL THERAPY' in text_upper or 'OT EVAL' in text_upper:
            return 'Occupational Therapy'
        elif 'SPEECH' in text_upper:
            return 'Speech Therapy'
        else:
            return 'Other'
    
    def process_directory(
        self,
        directory: str,
        output_csv: str,
        checkpoint_file: Optional[str] = None,
        resume: bool = True
    ) -> pd.DataFrame:
        """
        Process all PDFs in a directory.
        
        Args:
            directory: Path to directory containing PDFs
            output_csv: Path to save results CSV
            checkpoint_file: Path for checkpoint saves (optional)
            resume: If True, resume from checkpoint if exists
            
        Returns:
            DataFrame with extraction results
        """
        # Find all PDF files
        pdf_files = list(Path(directory).rglob('*.pdf'))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        if not pdf_files:
            logger.warning("No PDF files found!")
            return pd.DataFrame()
        
        # Load checkpoint if resuming
        processed_files = set()
        results = []
        
        if resume and checkpoint_file and os.path.exists(checkpoint_file):
            checkpoint_df = pd.read_csv(checkpoint_file)
            processed_files = set(checkpoint_df['filename'].tolist())
            results = checkpoint_df.to_dict('records')
            logger.info(f"Resuming from checkpoint: {len(processed_files)} already processed")
        
        # Filter remaining files
        remaining_files = [f for f in pdf_files if os.path.basename(f) not in processed_files]
        logger.info(f"Processing {len(remaining_files)} remaining files...")
        
        # Process with progress bar
        batch_count = 0
        for pdf_path in tqdm(remaining_files, desc="Extracting PDFs"):
            try:
                result = self.smart_extract(str(pdf_path))
                result_dict = asdict(result)
                result_dict['icd10_codes'] = json.dumps(result.icd10_codes)  # Serialize list
                results.append(result_dict)
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {e}")
                results.append({
                    'filename': os.path.basename(pdf_path),
                    'filepath': str(pdf_path),
                    'document_type': 'Unknown',
                    'full_text': '',
                    'text_length': 0,
                    'icd10_codes': '[]',
                    'num_codes': 0,
                    'extraction_method': 'failed',
                    'success': False,
                    'error_message': str(e)
                })
            
            batch_count += 1
            
            # Save checkpoint
            if batch_count % self.checkpoint_interval == 0:
                df = pd.DataFrame(results)
                if checkpoint_file:
                    df.to_csv(checkpoint_file, index=False)
                logger.info(f"Checkpoint saved: {len(results)} documents processed")
                
                # Memory cleanup
                gc.collect()
        
        # Final save
        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False)
        logger.info(f"Final results saved to {output_csv}")
        
        # Log statistics
        self._log_statistics(df)
        
        return df
    
    def _log_statistics(self, df: pd.DataFrame):
        """Log extraction statistics"""
        total = len(df)
        success = df['success'].sum() if 'success' in df.columns else 0
        native = (df['extraction_method'] == 'native').sum() if 'extraction_method' in df.columns else 0
        ocr = (df['extraction_method'] == 'ocr').sum() if 'extraction_method' in df.columns else 0
        
        # Count total ICD codes
        total_codes = 0
        all_codes = []
        if 'icd10_codes' in df.columns:
            for codes_str in df['icd10_codes']:
                try:
                    codes = json.loads(codes_str) if isinstance(codes_str, str) else codes_str
                    total_codes += len(codes)
                    all_codes.extend(codes)
                except:
                    pass
        
        unique_codes = len(set(all_codes))
        
        logger.info("=" * 50)
        logger.info("EXTRACTION STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total documents: {total}")
        logger.info(f"Successful: {success} ({success/total*100:.1f}%)")
        logger.info(f"Native extraction: {native} ({native/total*100:.1f}%)")
        logger.info(f"OCR extraction: {ocr} ({ocr/total*100:.1f}%)")
        logger.info(f"Total ICD-10 codes: {total_codes}")
        logger.info(f"Unique ICD-10 codes: {unique_codes}")
        logger.info(f"Avg codes per doc: {total_codes/total:.1f}")


# ============================================
# Convenience functions for Colab
# ============================================

def process_pdfs_batch(
    directory: str,
    output_csv: str,
    checkpoint_interval: int = 50
) -> pd.DataFrame:
    """
    Convenience function to process a batch of PDFs.
    
    Args:
        directory: Path to PDF directory
        output_csv: Output CSV path
        checkpoint_interval: Save every N documents
        
    Returns:
        DataFrame with results
    """
    extractor = HybridPDFExtractor(checkpoint_interval=checkpoint_interval)
    
    checkpoint = output_csv.replace('.csv', '_checkpoint.csv')
    return extractor.process_directory(
        directory=directory,
        output_csv=output_csv,
        checkpoint_file=checkpoint,
        resume=True
    )


# ============================================
# Testing
# ============================================
if __name__ == "__main__":
    print("PDF Extractor Module")
    print("=" * 50)
    print("This module provides hybrid PDF text extraction.")
    print("Import and use HybridPDFExtractor class or")
    print("process_pdfs_batch() convenience function.")
    print("\nExample usage in Colab:")
    print("  from src.pdf_extractor import process_pdfs_batch")
    print("  df = process_pdfs_batch('/content/drive/MyDrive/pdfs/', 'output.csv')")
