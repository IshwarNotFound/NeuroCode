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

# Attempt to load native PDF parsing library 
# It's wrapped in a try-except to prevent crashing if the user hasn't installed dependencies
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# Attempt to load OCR capabilities (Optical Character Recognition)
# pdf2image converts PDF pages to pictures, pytesseract reads the text from them
try:
    from pdf2image import convert_from_path
    import pytesseract
except ImportError:
    convert_from_path = None
    pytesseract = None

# Import the ICD-10 validation logic to cross-check extracted terms
# Fallback path is provided if running outside the standard project root
try:
    from src.icd10_validator import ICD10Validator
except ImportError:
    from icd10_validator import ICD10Validator

# Configure standard Python logging for tracking execution progress and anomalies
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """
    Data class defining the structure of the object returned for every processed PDF.
    This acts as a structured record aggregating all extraction metadata and the content itself.
    """
    filename: str
    filepath: str
    document_type: str
    full_text: str
    text_length: int
    icd10_codes: List[str]
    num_codes: int
    extraction_method: str  # Tracks if data came from 'native' digital text or 'ocr' image scanning
    success: bool
    error_message: str = ""


class HybridPDFExtractor:
    """
    Extracts text from PDFs using a two-tier hybrid approach:
    1. First attempts native text extraction using pdfplumber (Fast, high fidelity but requires digital PDFs).
    2. Falls back to Tesseract OCR if native extraction fails or returns scrambled text (Slow but works on scanned papers).
    
    Includes robust operational features:
    - Retry logic for intermittent OCR failures.
    - Text quality validation heuristics.
    - Checkpoint saving for long batch jobs (useful on Colab).
    - Proactive memory management via garbage collection.
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
        Initialize the Hybrid PDF extractor.
        
        Args:
            ocr_dpi: Dots per inch for PDF to image conversion (affects OCR quality vs memory).
            ocr_language: Tesseract language code (e.g., 'eng' for English).
            max_retries: Maximum attempts to execute OCR if an error occurs.
            min_text_length: Minimum character count required to consider a document successfully parsed.
            max_garbage_ratio: Threshold ratio of special characters; if too high, text is treated as corrupt.
            checkpoint_interval: Save intermediate progress to disk every N documents.
        """
        self.ocr_dpi = ocr_dpi
        self.ocr_language = ocr_language
        self.max_retries = max_retries
        self.min_text_length = min_text_length
        self.max_garbage_ratio = max_garbage_ratio
        self.checkpoint_interval = checkpoint_interval
        
        # Instantiate the validator used to pull diagnoses directly from the extracted text
        self.icd_validator = ICD10Validator()
        
        # Verify that all third-party libraries are accessible
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Validates that necessary pip packages are installed, warning the user if any are missing."""
        if pdfplumber is None:
            logger.warning("pdfplumber not installed. Native extraction unavailable.")
        if convert_from_path is None or pytesseract is None:
            logger.warning("pdf2image or pytesseract not installed. OCR unavailable.")
    
    def is_text_quality_acceptable(self, text: str) -> bool:
        """
        Analyzes the extracted text to determine if it is readable or scrambled/corrupt.
        This is crucial because some native PDF extractors output gibberish when handling 
        custom fonts or badly encoded layers.
        
        Args:
            text: The raw string extracted from the document.
            
        Returns:
            True if the text appears coherent based on heuristics, False otherwise.
        """
        # Reject trivially short strings
        if not text or len(text) < self.min_text_length:
            return False
        
        # Define a whitelist of characters typical in medical English
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:!?\'-\n\t/()')
        
        # Count characters outside the whitelist (garbage artifacts)
        garbage_count = sum(1 for c in text if c not in valid_chars)
        garbage_ratio = garbage_count / len(text)
        
        # If the text is overwhelmingly garbage symbols, reject it
        if garbage_ratio > self.max_garbage_ratio:
            return False
        
        # Split text into "words" based on spaces
        words = text.split()
        if len(words) < 10:
            return False
        
        # Check average word length to detect spacing issues
        # (e.g. "C a n c e r" -> avg length 1; "Supercali..." -> very high average)
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len < 2 or avg_word_len > 20:
            return False
        
        return True
    
    def extract_text_native(self, pdf_path: str) -> Tuple[str, bool]:
        """
        Extracts text purely natively by parsing the embedded text layer within the PDF.
        This is the preferred method as it is exponentially faster and more accurate than OCR.
        
        Args:
            pdf_path: Absolute or relative path to the PDF file.
            
        Returns:
            Tuple of (extracted string, boolean denoting operational success).
        """
        if pdfplumber is None:
            return "", False
        
        try:
            text_parts = []
            # Open the PDF file safely using a context manager
            with pdfplumber.open(pdf_path) as pdf:
                # Iterate through every page and pull its text
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            # Combine all page texts, separated by newlines
            full_text = '\n'.join(text_parts).strip()
            return full_text, bool(full_text)
            
        except Exception as e:
            # Native extraction can fail on protected or corrupted documents
            logger.debug(f"Native extraction failed for {pdf_path}: {e}")
            return "", False
    
    def extract_text_ocr(self, pdf_path: str) -> Tuple[str, bool]:
        """
        Extracts text via Optical Character Recognition.
        This visually "reads" the document like a human. It is slow and CPU intensive,
        but necessary for PDFs formulated from scanned physical papers.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Tuple of (extracted string, boolean denoting operational success).
        """
        if convert_from_path is None or pytesseract is None:
            return "", False
        
        # Retry loop to handle transient system errors (e.g. memory spike during image conversion)
        for attempt in range(self.max_retries):
            try:
                # Step 1: Render the PDF pages into a list of JPEG image objects
                images = convert_from_path(
                    pdf_path,
                    dpi=self.ocr_dpi,
                    fmt='jpeg'
                )
                
                text_parts = []
                # Step 2: Feed each JPEG image into the Tesseract OCR engine
                for image in images:
                    page_text = pytesseract.image_to_string(
                        image,
                        lang=self.ocr_language
                    )
                    if page_text:
                        text_parts.append(page_text)
                    
                    # Manually delete the image object immediately to prevent RAM bloat
                    del image
                
                # Cleanup the source images list and force garbage collection
                del images
                gc.collect()
                
                full_text = '\n'.join(text_parts).strip()
                return full_text, bool(full_text)
                
            except Exception as e:
                logger.warning(f"OCR attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)  # Pause execution briefly before the next retry
        
        return "", False
    
    def smart_extract(self, pdf_path: str) -> ExtractionResult:
        """
        The central extraction controller determining which extraction method to finalize.
        Attempts native extraction; if it returns poor results or fails, defaults to OCR.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            An ExtractionResult data object containing text, methodology, and identified codes.
        """
        filename = os.path.basename(pdf_path)
        
        # Phase 1: Attempt the fast native extraction
        text, native_success = self.extract_text_native(pdf_path)
        extraction_method = 'native'
        
        # Evaluate if the native extraction yielded an acceptable outcome
        if not native_success or not self.is_text_quality_acceptable(text):
            # Phase 2: If native fails or looks like garbage, pivot to the slow OCR engine
            ocr_text, ocr_success = self.extract_text_ocr(pdf_path)
            
            # If OCR succeeds and appears to capture more data than native, adopt OCR
            if ocr_success and (not text or len(ocr_text) > len(text)):
                text = ocr_text
                extraction_method = 'ocr'
        
        # Final success is ruled by whether valid text meeting length criteria was captured
        success = bool(text) and len(text) >= self.min_text_length
        
        # Feed the extracted text into the Validator to pull any hardcoded ICD-10 mentions
        icd_codes = self.icd_validator.extract_codes(text) if text else []
        
        # Guess the specific type of medical form based on filename and header text
        doc_type = self._determine_document_type(text, filename)
        
        # Package and return all findings into the standard data class
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
        """
        Applies rudimentary rule-based heuristics to classify the medical document type.
        Focuses on common form numbers or structural titles.
        """
        if not text:
            return 'Unknown'
        
        # Look at the first 2000 characters which generally constitute headers/titles
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
        Orchestrates bulk processing of an entire directory containing PDF files.
        Includes built-in checkpointing so jobs interuppted mid-way do not lose entire progress.
        
        Args:
            directory: Directory string path to search for PDFs.
            output_csv: File path detailing where to save the final compiled CSV of all texts.
            checkpoint_file: File path detailing where to save intermediate progress.
            resume: If True, evaluates the checkpoint_file and skips already processed PDFs.
            
        Returns:
            A Pandas DataFrame containing all extraction results.
        """
        # Recursively search the directory for anything ending in .pdf
        pdf_files = list(Path(directory).rglob('*.pdf'))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        if not pdf_files:
            logger.warning("No PDF files found!")
            return pd.DataFrame()
        
        processed_files = set()
        results = []
        
        # If resuming, load the checkpoint CSV and prepopulate results list and processed set
        if resume and checkpoint_file and os.path.exists(checkpoint_file):
            checkpoint_df = pd.read_csv(checkpoint_file)
            processed_files = set(checkpoint_df['filename'].tolist())
            results = checkpoint_df.to_dict('records')
            logger.info(f"Resuming from checkpoint: {len(processed_files)} already processed")
        
        # Filter down the list of PDFs to only include those not already in the processed set
        remaining_files = [f for f in pdf_files if os.path.basename(f) not in processed_files]
        logger.info(f"Processing {len(remaining_files)} remaining files...")
        
        # Iterate over remaining files displaying a visual progress bar (tqdm)
        batch_count = 0
        for pdf_path in tqdm(remaining_files, desc="Extracting PDFs"):
            try:
                # Trigger extraction logic for single file
                result = self.smart_extract(str(pdf_path))
                
                # Convert Result Object to Dictionary for Pandas conversion
                result_dict = asdict(result)
                # Serialize list into a JSON string since CSV cells don't natively support lists
                result_dict['icd10_codes'] = json.dumps(result.icd10_codes)  
                results.append(result_dict)
                
            except Exception as e:
                # Catch severe operational crashes and log them gracefully
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
            
            # Periodically write current progress to disk
            if batch_count % self.checkpoint_interval == 0:
                df = pd.DataFrame(results)
                if checkpoint_file:
                    df.to_csv(checkpoint_file, index=False)
                logger.info(f"Checkpoint saved: {len(results)} documents processed")
                
                # Force memory flush of dangling Python objects
                gc.collect()
        
        # Produce the conclusive DataFrame and export it as CSV
        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False)
        logger.info(f"Final results saved to {output_csv}")
        
        # Post-operation summary printout
        self._log_statistics(df)
        
        return df
    
    def _log_statistics(self, df: pd.DataFrame):
        """
        Parses the final results DataFrame and prints out aggregate statistics 
        regarding the quality and outcome of the batch extraction job.
        """
        total = len(df)
        success = df['success'].sum() if 'success' in df.columns else 0
        native = (df['extraction_method'] == 'native').sum() if 'extraction_method' in df.columns else 0
        ocr = (df['extraction_method'] == 'ocr').sum() if 'extraction_method' in df.columns else 0
        
        # Aggregate all discovered ICD-10 codes to calculate density/diversity 
        total_codes = 0
        all_codes = []
        if 'icd10_codes' in df.columns:
            for codes_str in df['icd10_codes']:
                try:
                    # Deserialize JSON string back to a Python List
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
    A simplified functional wrapper exposing the Extractor class.
    Streamlines usage in Jupyter Notebooks/Google Colab so only a single function call is needed.
    
    Args:
        directory: Target folder path.
        output_csv: Final output CSV path.
        checkpoint_interval: Save frequency.
        
    Returns:
        DataFrame holding all results.
    """
    extractor = HybridPDFExtractor(checkpoint_interval=checkpoint_interval)
    
    # Automatically generate a checkpoint file naming scheme based on output filename
    checkpoint = output_csv.replace('.csv', '_checkpoint.csv')
    return extractor.process_directory(
        directory=directory,
        output_csv=output_csv,
        checkpoint_file=checkpoint,
        resume=True
    )


# ============================================
# Local Module Testing logic
# ============================================
if __name__ == "__main__":
    # Provides straightforward command line documentation if the script is run directly
    print("PDF Extractor Module")
    print("=" * 50)
    print("This module provides hybrid PDF text extraction.")
    print("Import and use HybridPDFExtractor class or")
    print("process_pdfs_batch() convenience function.")
    print("\nExample usage in Colab:")
    print("  from src.pdf_extractor import process_pdfs_batch")
    print("  df = process_pdfs_batch('/content/drive/MyDrive/pdfs/', 'output.csv')")
