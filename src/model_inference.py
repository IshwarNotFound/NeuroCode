"""
ICD-10 Model Inference Module
This module handles loading the trained PyTorch Convolutional Neural Network (CNN) model
and using it to predict ICD-10 medical codes from clinical text.
"""

import os
import pickle
import json
import hashlib
import logging
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from typing import List, Dict, Tuple
import re
from src.vocabulary import Vocabulary

# Initialize a logger for this module to track events and errors
logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception raised when a security check fails (e.g., file integrity verification)."""
    pass


# Determine the root directory of the project (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent

# Define paths to crucial directories and files needed for the model
MODEL_DIR = PROJECT_ROOT / "Downloaded files" / "ICD10_Project" / "models"
DATA_DIR = PROJECT_ROOT / "Downloaded files" / "ICD10_Project" / "data" / "train_test_split"

# Path to the file storing SHA-256 hashes to ensure data integrity
HASH_FILE = PROJECT_ROOT / "Downloaded files" / "ICD10_Project" / "file_hashes.json"


def _compute_sha256(filepath: str) -> str:
    """
    Computes the SHA-256 cryptographic hash of a given file.
    This is used to verify that the file has not been altered or tampered with.
    
    Args:
        filepath (str): The path to the file to be hashed.
        
    Returns:
        str: The hexadecimal representation of the SHA-256 hash.
    """
    sha256 = hashlib.sha256()
    # Read the file in chunks of 8192 bytes to avoid high memory usage for large files
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def _verify_file_integrity(filepath: str, filename_key: str) -> bool:
    """
    Verifies the integrity of a file using SHA-256 hashes.
    
    This function uses a Trust-On-First-Use (TOFU) approach:
    1. If the hash for a file is not yet recorded, it computes and saves it (trusting the first version).
    2. On subsequent runs, it compares the current hash against the saved hash.
    
    Args:
        filepath (str): The full path to the file to verify.
        filename_key (str): The identifier key (usually filename) used in the hash dictionary.
        
    Returns:
        bool: True if the file integrity checks out, False otherwise.
    """
    stored_hashes = {}
    
    # Load previously stored hashes if the hash file exists
    if HASH_FILE.exists():
        with open(HASH_FILE, 'r') as f:
            stored_hashes = json.load(f)
    
    # Compute the hash of the current file on disk
    current_hash = _compute_sha256(filepath)
    
    # If we haven't seen this file before, store its hash (TOFU)
    if filename_key not in stored_hashes:
        stored_hashes[filename_key] = current_hash
        with open(HASH_FILE, 'w') as f:
            json.dump(stored_hashes, f, indent=2)
        logger.info(f"TOFU: Stored initial hash for {filename_key}")
        return True
    
    # If we have seen it, ensure the current hash matches the stored hash
    if stored_hashes[filename_key] != current_hash:
        logger.critical(
            f"INTEGRITY CHECK FAILED for {filename_key}! "
            f"Expected: {stored_hashes[filename_key][:16]}... "
            f"Got: {current_hash[:16]}..."
        )
        return False
    
    return True

# Attempt to load helper functions for ICD-10 code descriptions and UI styling
try:
    from streamlit_app.icd10_descriptions import get_code_description, get_code_color, get_chapter_name
except ImportError:
    # If the import fails (e.g., running outside the Streamlit app context), 
    # define fallback functions that return basic default values
    def get_code_description(code): return f"ICD-10: {code}"
    def get_code_color(code): return "#808080" # Default gray color
    def get_chapter_name(code): return "Unknown"


class TextCNN(nn.Module):
    """
    Convolutional Neural Network (CNN) architecture for text classification.
    This structure must exactly match the architecture used during training 
    so the saved weights can be loaded correctly.
    """
    def __init__(self, vocab_size, embedding_dim, n_classes, max_seq_length=2000):
        super(TextCNN, self).__init__()
        
        # Word embedding layer: converts word indices into dense vector representations
        # padding_idx=0 ensures that padding tokens do not contribute to the gradients
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        
        # Convolutional layers with different kernel (filter) sizes to capture 
        # different lengths of n-grams (2-word, 3-word combinations, etc.)
        self.convs = nn.ModuleList([
            nn.Conv1d(embedding_dim, 128, kernel_size=2), # Extracts features from adjacent pairs of words
            nn.Conv1d(embedding_dim, 128, kernel_size=3), # Extracts features from triplets
            nn.Conv1d(embedding_dim, 128, kernel_size=4), # Extracts features from 4-word sequences
            nn.Conv1d(embedding_dim, 128, kernel_size=5), # Extracts features from 5-word sequences
        ])
        
        # Fully connected (dense) layers to map the extracted features to class predictions
        # 4 conv layers * 128 filters each = 512 total extracted features
        self.fc1 = nn.Linear(512, 256)
        self.fc2 = nn.Linear(256, n_classes)
        
        # Batch normalization helps stabilize and speed up training
        self.bn = nn.BatchNorm1d(256)
        
        # Dropout layer to prevent overfitting by randomly zeroing out 50% of elements
        self.dropout = nn.Dropout(0.5)
        
    def forward(self, x):
        """
        Defines the forward pass of the model: how data flows from input to output.
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length) containing word indices.
        """
        # Pass input through embedding layer -> Output: (batch_size, sequence_length, embedding_dim)
        x = self.embedding(x)
        
        # Rearrange dimensions for PyTorch's Conv1d which expects (batch_size, channels, sequence_length)
        # Output: (batch_size, embedding_dim, sequence_length)
        x = x.permute(0, 2, 1)
        
        # Apply each convolutional layer followed by ReLU activation and 1D Max Pooling
        conv_outputs = []
        for conv in self.convs:
            # Convolution followed by Rectified Linear Unit (ReLU) activation
            c = torch.relu(conv(x))
            
            # Max pooling extracts the single most important feature over the entire sequence 
            # for each of the 128 filters. squeeze(2) removes the now size-1 spatial dimension.
            c = torch.max_pool1d(c, c.size(2)).squeeze(2)
            conv_outputs.append(c)
        
        # Combine the pooled features from all 4 convolutional layers
        # Resulting shape: (batch_size, 512)
        x = torch.cat(conv_outputs, dim=1)
        
        # Pass through a dropout layer for regularization
        x = self.dropout(x)
        
        # First fully connected layer with ReLU activation
        x = torch.relu(self.fc1(x))
        
        # Batch normalization
        x = self.bn(x)
        
        # Second dropout layer
        x = self.dropout(x)
        
        # Final fully connected layer mapping to the number of target classes,
        # followed by a sigmoid activation to output probabilities between 0 and 1
        # (appropriate for multi-label classification where multiple ICD codes can be true)
        x = torch.sigmoid(self.fc2(x))
        
        return x


class ICD10Predictor:
    """
    Main controller class that ties everything together. 
    It handles loading the trained artifacts (model, vocabulary, labels) 
    and exposes a method to process new text and return predictions.
    """
    
    def __init__(self):
        # Initialize placeholders for our loaded artifacts
        self.model = None
        self.vocabulary = None
        self.label_encoder = None
        self.word_to_idx = None
        self.idx_to_code = None
        self.code_to_idx = None  # Mapping from an ICD-10 code string back to its class index
        
        # The maximum number of words/tokens considered in a single document
        self.max_seq_length = 2000
        
        # Decide whether to run on GPU ('cuda') or CPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load the model and related files upon initialization
        self._load_model()
    
    def _load_model(self):
        """Loads the pre-trained vocabulary, label encoder, and PyTorch model weights."""
        try:
            # --- Load Vocabulary ---
            vocab_path = DATA_DIR / "vocabulary.pkl"
            
            # Verify that the vocabulary file hasn't been tampered with
            if not _verify_file_integrity(str(vocab_path), "vocabulary.pkl"):
                raise SecurityError("Vocabulary file integrity check failed! File may have been tampered with.")
                
            with open(vocab_path, 'rb') as f:
                self.vocabulary = pickle.load(f)
            
            # Setup the dictionary mapping words to their integer index
            if hasattr(self.vocabulary, 'word2idx'):
                self.word_to_idx = self.vocabulary.word2idx
            else:
                # Fallback for older formats where vocabulary is just a list of words
                self.word_to_idx = {word: idx for idx, word in enumerate(self.vocabulary, start=1)}
                self.word_to_idx['<PAD>'] = 0  # Index 0 is reserved for padding
                self.word_to_idx['<UNK>'] = len(self.vocabulary) + 1  # Index for unknown words
            
            # --- Load Label Encoder ---
            label_path = DATA_DIR / "label_encoder.pkl"
            
            # Verify the integrity of the label encoder file
            if not _verify_file_integrity(str(label_path), "label_encoder.pkl"):
                raise SecurityError("Label encoder file integrity check failed! File may have been tampered with.")
                
            with open(label_path, 'rb') as f:
                loaded_le = pickle.load(f)
            
            # Extract class labels from the loaded encoder object
            if isinstance(loaded_le, dict):
                self.classes_ = loaded_le.get('classes')
                self.label_encoder = loaded_le.get('mlb') 
            else:
                self.label_encoder = loaded_le
                self.classes_ = self.label_encoder.classes_
            
            # Create bi-directional mappings between class indices and ICD-10 code names
            self.idx_to_code = {idx: code for idx, code in enumerate(self.classes_)}
            self.code_to_idx = {code: idx for idx, code in enumerate(self.classes_)}
            
            # --- Load Preprocessing Dimensions ---
            preproc_path = DATA_DIR / "preprocessing_summary.json"
            with open(preproc_path, 'r') as f:
                preproc_info = json.load(f)
            
            # Network dimensions must align smoothly with the artifacts
            vocab_size = len(self.word_to_idx)
            n_classes = preproc_info['n_classes']
            
            # --- Initialize Neural Network Model ---
            self.model = TextCNN(
                vocab_size=vocab_size,
                embedding_dim=128,
                n_classes=n_classes,
                max_seq_length=self.max_seq_length
            )
            
            # --- Load Model Weights ---
            model_path = MODEL_DIR / "icd10_cnn_latest.pt"
            
            # Verify model weight file integrity
            if not _verify_file_integrity(str(model_path), "icd10_cnn_latest.pt"):
                raise SecurityError("Model file integrity check failed! File may have been tampered with.")
            
            # Load the actual learned weights into the model
            try:
                # First attempt secure loading (weights_only=True blocks loading arbitrary executable objects)
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
            except Exception:
                logger.warning(
                    "torch.load with weights_only=True failed (checkpoint may contain "
                    "non-tensor types). Falling back to weights_only=False after integrity check passed."
                )
                # Fallback if the saved checkpoint format required weights_only=False
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            
            # Move model to CPU/GPU and set to evaluation mode (disables dropout layers during inference)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Model loaded successfully — vocab: {vocab_size}, classes: {n_classes}, device: {self.device}")
            
        except Exception as e:
            logger.exception("Error loading model")
            raise
    
    def preprocess_text(self, text: str) -> List[str]:
        """
        Cleans and normalizes incoming clinical text exactly as it was processed during training.
        """
        # Convert all text to lower case to ensure uniformity
        text = text.lower()
        
        # Remove most punctuation/special characters, keeping only letters, numbers, spaces, periods, dashes, and slashes
        text = re.sub(r'[^a-z0-9\s\.\-/]', ' ', text)
        
        # Split text into a list of constituent words based on whitespace
        tokens = text.split()
        
        # Comprehensive dictionary for expanding common medical acronyms
        # Covers cardiology, endocrine, renal, respiratory, neuro, GI, 
        # musculoskeletal, mental health, medication, and general clinical terms
        abbrev_map = {
            # General Clinical
            'pt': 'patient', 'pts': 'patients', 'dx': 'diagnosis', 'hx': 'history',
            'sx': 'symptoms', 'tx': 'treatment', 'rx': 'prescription', 'fx': 'fracture',
            'pmh': 'past medical history', 'pmhx': 'past medical history',
            'fhx': 'family history', 'shx': 'social history',
            'ros': 'review of systems', 'pe': 'physical examination',
            'wbc': 'white blood cell', 'rbc': 'red blood cell', 'hgb': 'hemoglobin',
            'hct': 'hematocrit', 'plt': 'platelets', 'bmp': 'basic metabolic panel',
            'cbc': 'complete blood count', 'cmp': 'comprehensive metabolic panel',
            'bnp': 'brain natriuretic peptide', 'crp': 'c reactive protein',
            'esr': 'erythrocyte sedimentation rate', 'inr': 'international normalized ratio',
            'ptt': 'partial thromboplastin time',
            
            # Cardiovascular
            'htn': 'hypertension', 'chf': 'congestive heart failure',
            'cad': 'coronary artery disease', 'mi': 'myocardial infarction',
            'afib': 'atrial fibrillation', 'af': 'atrial fibrillation',
            'dvt': 'deep vein thrombosis', 'pe': 'pulmonary embolism',
            'pvd': 'peripheral vascular disease', 'pad': 'peripheral arterial disease',
            'lvef': 'left ventricular ejection fraction', 'ef': 'ejection fraction',
            'cabg': 'coronary artery bypass graft', 'pci': 'percutaneous coronary intervention',
            'icd': 'implantable cardioverter defibrillator',
            'avr': 'aortic valve replacement', 'mvr': 'mitral valve replacement',
            
            # Endocrine / Metabolic
            'dm': 'diabetes mellitus', 'dm2': 'type 2 diabetes mellitus',
            't2dm': 'type 2 diabetes mellitus', 't1dm': 'type 1 diabetes mellitus',
            'hba1c': 'hemoglobin a1c', 'a1c': 'hemoglobin a1c',
            'tsh': 'thyroid stimulating hormone', 'bmi': 'body mass index',
            
            # Respiratory
            'copd': 'chronic obstructive pulmonary disease',
            'sob': 'shortness of breath', 'doe': 'dyspnea on exertion',
            'osa': 'obstructive sleep apnea', 'cpap': 'continuous positive airway pressure',
            'bipap': 'bilevel positive airway pressure', 'o2': 'oxygen',
            'spo2': 'oxygen saturation', 'abg': 'arterial blood gas',
            
            # Renal
            'ckd': 'chronic kidney disease', 'esrd': 'end stage renal disease',
            'gfr': 'glomerular filtration rate', 'egfr': 'estimated glomerular filtration rate',
            'bun': 'blood urea nitrogen', 'aki': 'acute kidney injury',
            'uti': 'urinary tract infection', 'bph': 'benign prostatic hyperplasia',
            
            # Neurological
            'cva': 'cerebrovascular accident', 'tia': 'transient ischemic attack',
            'ms': 'multiple sclerosis', 'alz': 'alzheimer',
            'loc': 'loss of consciousness', 'ams': 'altered mental status',
            
            # Musculoskeletal
            'oa': 'osteoarthritis', 'ra': 'rheumatoid arthritis',
            'lbp': 'low back pain', 'rom': 'range of motion',
            'tka': 'total knee arthroplasty', 'tha': 'total hip arthroplasty',
            'thr': 'total hip replacement', 'tkr': 'total knee replacement',
            'orif': 'open reduction internal fixation',
            
            # Gastrointestinal
            'gerd': 'gastroesophageal reflux disease',
            'gi': 'gastrointestinal', 'npo': 'nothing by mouth',
            'peg': 'percutaneous endoscopic gastrostomy',
            'ibd': 'inflammatory bowel disease',
            
            # Mental Health
            'mdd': 'major depressive disorder', 'gad': 'generalized anxiety disorder',
            'ptsd': 'post traumatic stress disorder', 'etoh': 'alcohol',
            
            # Medication Frequency
            'prn': 'as needed', 'bid': 'twice daily', 'tid': 'three times daily',
            'qid': 'four times daily', 'qd': 'once daily', 'qhs': 'at bedtime',
            'ac': 'before meals', 'pc': 'after meals',
        }
        
        # Expand abbreviations where applicable
        tokens = [abbrev_map.get(token, token) for token in tokens]
        
        return tokens
    
    def encode_text(self, tokens: List[str]) -> torch.Tensor:
        """
        Translates a list of string tokens (words) into a PyTorch tensor populated by integers,
        which is the format required by the neural network's embedding layer.
        """
        # Convert each word to its corresponding integer index. If unknown, use the <UNK> index.
        indices = [self.word_to_idx.get(token, self.word_to_idx['<UNK>']) for token in tokens]
        
        # If the input text is too short, pad it out to max sequence length with zeros (which represent <PAD>)
        if len(indices) < self.max_seq_length:
            indices += [0] * (self.max_seq_length - len(indices))
        else:
            # If the input text is too long, truncate it to the maximum allowed length
            indices = indices[:self.max_seq_length]
        
        # Convert the Python list to a PyTorch long tensor, and add a "batch" dimension of size 1 
        # (since we are processing a single document at a time here)
        return torch.tensor(indices, dtype=torch.long).unsqueeze(0)
    
    def _find_whole_word(self, text: str, word: str) -> bool:
        """
        Checks if a specific word exists as a whole standalone word within a given text block.
        This prevents substring false positives, e.g., 'dm' (diabetes) inside 'admission'.
        """
        pattern = r'\b' + re.escape(word) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    # -------------------------------------------------------------------------
    # Clinical Negation Detection
    # Medical texts frequently contain negated phrases ("no evidence of", "denies",
    # "ruled out"). Without negation awareness, keyword matching would incorrectly
    # boost codes for conditions the patient does NOT have.
    # -------------------------------------------------------------------------
    
    # Pre-compiled negation patterns that precede medical terms
    NEGATION_CUES = re.compile(
        r'\b('
        r'no |not |deny |denies |denied |negative for |'
        r'without |absence of |absent |never |'
        r'no evidence of |no signs of |no symptoms of |'
        r'no history of |no hx of |'
        r'ruled out |rule out |r/o |'
        r'unlikely |does not have |doesn\'t have |'
        r'resolved |no longer has |no current '
        r')', re.IGNORECASE
    )
    
    def _is_negated(self, text_lower: str, keyword: str, is_phrase: bool) -> bool:
        """
        Checks if a keyword match is preceded by a clinical negation cue
        within a 60-character window. This prevents boosting codes for conditions
        explicitly denied in the clinical text.
        
        Uses a sliding-window approach: finds each occurrence of the keyword,
        then scans the preceding context for negation language.
        """
        # Find all occurrences of the keyword
        if is_phrase:
            positions = [m.start() for m in re.finditer(re.escape(keyword), text_lower)]
        else:
            positions = [m.start() for m in re.finditer(r'\b' + re.escape(keyword) + r'\b', text_lower)]
        
        if not positions:
            return False
        
        # Check each occurrence — if ALL are negated, the keyword is negated
        all_negated = True
        for pos in positions:
            # Look at 60 characters before the keyword for negation cues
            window_start = max(0, pos - 60)
            preceding_text = text_lower[window_start:pos]
            if not self.NEGATION_CUES.search(preceding_text):
                all_negated = False
                break
        
        return all_negated
    
    def _apply_keyword_rules(self, text: str, probs: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Hybrid rule-based enhancement layer with negation-awareness and evidence tracking.
        
        Scans the original clinical text for domain-specific keywords mapped to ICD-10 codes.
        When unambiguous clinical phrases are detected (and not negated), the corresponding
        CNN probability scores are boosted. All matched keywords are tracked as "evidence"
        for the explainability layer shown in the UI.
        
        Returns:
            Tuple of (modified probability array, evidence dictionary mapping code → list of matched keywords)
        """
        text_lower = text.lower()
        
        # Evidence tracker: maps ICD-10 code string → list of matched keyword strings
        evidence = {}
        
        # ------------------------------------------------------------------
        # Comprehensive Keyword Rules — covers all 100 model output classes
        # Format: 'ICD_CODE': [(keyword, is_phrase, boost_amount), ...]
        #   - is_phrase=True  → substring match (for multi-word clinical expressions)
        #   - is_phrase=False → whole-word boundary match (prevents false positives)
        #   - boost values are calibrated: 0.3-0.5 for ambiguous terms,
        #     0.6-0.7 for strong clinical indicators, 0.8-0.9 for unambiguous diagnoses
        # ------------------------------------------------------------------
        keyword_rules = {
            # ======================== FALLS & MOBILITY ========================
            'Z91.81': [('fall', False, 0.5), ('falling', False, 0.5), ('fell', False, 0.5),
                        ('history of fall', True, 0.7), ('fall risk', True, 0.6), ('fall prevention', True, 0.5)],
            'R26.81': [('unsteadiness', False, 0.5), ('unsteady gait', True, 0.6), ('unsteady on feet', True, 0.6)],
            'R26.2':  [('difficulty walking', True, 0.6), ('difficulty in walking', True, 0.6),
                        ('gait disturbance', True, 0.5), ('impaired ambulation', True, 0.5)],
            'R26.89': [('abnormal gait', True, 0.5), ('gait abnormality', True, 0.5), ('shuffling gait', True, 0.5)],
            'R29.6':  [('repeated falls', True, 0.6), ('recurrent falls', True, 0.6), ('frequent falls', True, 0.6)],
            'M62.81': [('muscle weakness', True, 0.6), ('muscular weakness', True, 0.6),
                        ('generalized weakness', True, 0.5), ('weakness in extremities', True, 0.5)],
            'R41.841': [('cognitive communication deficit', True, 0.6), ('cognitive deficit', True, 0.4),
                         ('communication deficit', True, 0.4)],
            
            # ======================== CARDIOVASCULAR ========================
            'I10':    [('hypertension', False, 0.5), ('high blood pressure', True, 0.6),
                        ('elevated blood pressure', True, 0.5), ('htn', False, 0.5)],
            'I12.9':  [('hypertensive chronic kidney disease', True, 0.7), ('hypertensive renal disease', True, 0.6)],
            'I13.0':  [('hypertensive heart and chronic kidney', True, 0.7), ('hypertensive heart and ckd', True, 0.7)],
            'I13.10': [('hypertensive heart and ckd without heart failure', True, 0.7),
                        ('hypertensive heart disease and ckd', True, 0.5)],
            'I25.10': [('coronary artery disease', True, 0.7), ('cad', False, 0.6),
                        ('coronary atherosclerosis', True, 0.7), ('ischemic heart disease', True, 0.5)],
            'I25.2':  [('old myocardial infarction', True, 0.7), ('previous mi', True, 0.6),
                        ('prior myocardial infarction', True, 0.7), ('history of mi', True, 0.6)],
            'I27.20': [('pulmonary hypertension', True, 0.7), ('pulmonary htn', True, 0.6)],
            'I48.0':  [('paroxysmal atrial fibrillation', True, 0.7), ('atrial fibrillation', True, 0.6),
                        ('afib', False, 0.6), ('a-fib', False, 0.6)],
            'I48.91': [('atrial fibrillation unspecified', True, 0.6), ('chronic afib', True, 0.5)],
            'I50.32': [('diastolic heart failure', True, 0.7), ('congestive heart failure', True, 0.6),
                        ('chf', False, 0.6), ('heart failure', True, 0.5)],
            'I50.9':  [('heart failure unspecified', True, 0.5), ('cardiac failure', True, 0.5)],
            'I67.9':  [('cerebrovascular disease', True, 0.6), ('cerebrovascular', False, 0.4)],
            'I70.0':  [('atherosclerosis', False, 0.5), ('aortic atherosclerosis', True, 0.7)],
            'I73.9':  [('peripheral vascular disease', True, 0.6), ('pvd', False, 0.5),
                        ('peripheral arterial disease', True, 0.6), ('pad', False, 0.4)],
            'I87.2':  [('venous insufficiency', True, 0.6), ('chronic venous insufficiency', True, 0.7)],
            'I89.0':  [('lymphedema', False, 0.7), ('lymphoedema', False, 0.7)],
            
            # ======================== ENDOCRINE / METABOLIC ========================
            'E03.9':  [('hypothyroidism', False, 0.7), ('thyroid', False, 0.3),
                        ('tsh elevated', True, 0.6), ('underactive thyroid', True, 0.7)],
            'E11.9':  [('type 2 diabetes', True, 0.7), ('diabetes mellitus', True, 0.6),
                        ('diabetic', False, 0.4), ('t2dm', False, 0.6)],
            'E11.22': [('diabetic chronic kidney disease', True, 0.7), ('diabetic ckd', True, 0.7),
                        ('diabetes with kidney disease', True, 0.6), ('diabetic nephropathy', True, 0.6)],
            'E11.42': [('diabetic neuropathy', True, 0.7), ('diabetic polyneuropathy', True, 0.7),
                        ('peripheral neuropathy', True, 0.5)],
            'E11.51': [('diabetic retinopathy', True, 0.7), ('diabetic eye disease', True, 0.6)],
            'E11.65': [('diabetes with hyperglycemia', True, 0.7), ('hyperglycemia', False, 0.4),
                        ('elevated blood sugar', True, 0.5), ('uncontrolled diabetes', True, 0.5)],
            'E11.69': [('diabetes with complication', True, 0.5), ('diabetic complication', True, 0.5)],
            'E26.1':  [('hyperaldosteronism', False, 0.7), ('conn syndrome', True, 0.7), ('aldosterone', False, 0.4)],
            'E55.9':  [('vitamin d deficiency', True, 0.7), ('low vitamin d', True, 0.6), ('vit d deficiency', True, 0.7)],
            'E66.01': [('morbid obesity', True, 0.7), ('severe obesity', True, 0.5), ('bmi 40', True, 0.5),
                        ('bmi over 40', True, 0.5), ('class iii obesity', True, 0.7)],
            'E78.2':  [('mixed hyperlipidemia', True, 0.7), ('combined hyperlipidemia', True, 0.6)],
            'E78.5':  [('hyperlipidemia', False, 0.6), ('high cholesterol', True, 0.5),
                        ('elevated lipid', True, 0.5), ('dyslipidemia', False, 0.5)],
            
            # ======================== MENTAL / BEHAVIORAL ========================
            'F03.90': [('dementia', False, 0.6), ('cognitive decline', True, 0.4),
                        ('memory loss', True, 0.4), ('cognitive impairment', True, 0.5)],
            'F32.A':  [('depression', False, 0.4), ('major depressive', True, 0.6),
                        ('depressive disorder', True, 0.6)],
            'F33.1':  [('recurrent depression', True, 0.6), ('recurrent depressive disorder', True, 0.7),
                        ('recurrent major depressive', True, 0.7)],
            'F41.1':  [('generalized anxiety', True, 0.6), ('anxiety disorder', True, 0.5), ('gad', False, 0.5)],
            'F41.9':  [('anxiety', False, 0.3), ('anxious', False, 0.3)],
            
            # ======================== NERVOUS SYSTEM ========================
            'G20.A1': [('parkinson', False, 0.7), ('parkinsons', False, 0.7), ('parkinsonism', False, 0.5)],
            'G30.1':  [('alzheimer', False, 0.7), ('alzheimers', False, 0.7)],
            'G31.1':  [('senile degeneration', True, 0.7), ('senile dementia', True, 0.5)],
            'G31.84': [('lewy body', True, 0.7), ('lewy bodies', True, 0.7)],
            'G47.00': [('insomnia', False, 0.6), ('difficulty sleeping', True, 0.5), ('sleep disturbance', True, 0.4)],
            'G47.33': [('sleep apnea', True, 0.7), ('obstructive sleep apnea', True, 0.7),
                        ('osa', False, 0.5), ('cpap', False, 0.4)],
            'G62.9':  [('polyneuropathy', False, 0.6), ('peripheral neuropathy', True, 0.5),
                        ('neuropathy', False, 0.3)],
            'G89.29': [('chronic pain', True, 0.5), ('pain syndrome', True, 0.4), ('chronic pain syndrome', True, 0.6)],
            
            # ======================== EYE ========================
            'H40.9':  [('glaucoma', False, 0.7), ('intraocular pressure', True, 0.5)],
            
            # ======================== RESPIRATORY ========================
            'J44.9':  [('copd', False, 0.7), ('chronic obstructive pulmonary', True, 0.7),
                        ('emphysema', False, 0.5), ('chronic bronchitis', True, 0.4)],
            'J96.11': [('chronic respiratory failure', True, 0.7), ('respiratory failure', True, 0.4),
                        ('ventilator dependent', True, 0.5), ('on ventilator', True, 0.4)],
            
            # ======================== DIGESTIVE ========================
            'K21.9':  [('gerd', False, 0.7), ('gastroesophageal reflux', True, 0.7),
                        ('acid reflux', True, 0.5), ('heartburn', False, 0.4)],
            'K59.00': [('constipation', False, 0.6), ('chronic constipation', True, 0.7)],
            
            # ======================== MUSCULOSKELETAL ========================
            'M10.33': [('gout', False, 0.7), ('podagra', False, 0.7), ('gouty arthritis', True, 0.7),
                        ('uric acid', True, 0.4)],
            'M15.0':  [('primary generalized osteoarthritis', True, 0.7), ('generalized oa', True, 0.6)],
            'M15.9':  [('polyosteoarthritis', False, 0.6), ('multiple joint osteoarthritis', True, 0.6)],
            'M17.00': [('bilateral knee osteoarthritis', True, 0.7), ('bilateral knee oa', True, 0.7),
                        ('osteoarthritis both knees', True, 0.6)],
            'M17.10': [('unilateral knee osteoarthritis', True, 0.7), ('knee osteoarthritis', True, 0.5),
                        ('knee oa', True, 0.5)],
            'M17.20': [('post-traumatic osteoarthritis of knee', True, 0.7)],
            'M17.40': [('secondary osteoarthritis of knee', True, 0.7)],
            'M19.90': [('osteoarthritis', False, 0.4), ('degenerative joint disease', True, 0.5),
                        ('djd', False, 0.5)],
            'M48.061': [('spinal stenosis', True, 0.6), ('lumbar stenosis', True, 0.7)],
            'M54.50': [('low back pain', True, 0.7), ('lumbar pain', True, 0.6), ('lumbago', False, 0.6),
                        ('back pain', True, 0.4)],
            'M81.0':  [('osteoporosis', False, 0.6), ('bone density loss', True, 0.5)],
            
            # ======================== RENAL / URINARY ========================
            'N18.2':  [('ckd stage 2', True, 0.7), ('chronic kidney disease stage 2', True, 0.7),
                        ('ckd stage ii', True, 0.7)],
            'N18.31': [('ckd stage 3a', True, 0.7), ('chronic kidney disease stage 3a', True, 0.7)],
            'N18.32': [('ckd stage 3b', True, 0.7), ('chronic kidney disease stage 3b', True, 0.7)],
            'N18.9':  [('chronic kidney disease', True, 0.4), ('ckd', False, 0.3),
                        ('renal insufficiency', True, 0.4)],
            'N32.81': [('overactive bladder', True, 0.7), ('oab', False, 0.5), ('urinary urgency', True, 0.5)],
            'N39.0':  [('urinary tract infection', True, 0.7), ('uti', False, 0.6)],
            'N40.0':  [('benign prostatic hyperplasia', True, 0.7), ('bph', False, 0.6),
                        ('enlarged prostate', True, 0.6)],
            'N40.1':  [('bph with luts', True, 0.7), ('prostatic hyperplasia with lower urinary', True, 0.7)],
            
            # ======================== BLOOD / HEMATOLOGIC ========================
            'D50.9':  [('iron deficiency anemia', True, 0.7), ('iron deficiency', True, 0.5),
                        ('low iron', True, 0.4), ('ferritin low', True, 0.5)],
            'D63.1':  [('anemia of chronic disease', True, 0.7), ('anemia of chronic kidney disease', True, 0.7),
                        ('anemia in ckd', True, 0.6)],
            'D68.69': [('thrombophilia', False, 0.6), ('coagulation disorder', True, 0.5),
                        ('hypercoagulable', False, 0.5)],
            
            # ======================== INFECTIOUS ========================
            'A12.50': [('tuberculosis', False, 0.4)],
            'B12':    [('viral hepatitis', True, 0.5)],
            'B13.00': [('hepatitis c', True, 0.6)],
            'B20.0':  [('hiv', False, 0.6), ('human immunodeficiency', True, 0.7)],
            
            # ======================== NEOPLASMS ========================
            'D07.00': [('carcinoma in situ', True, 0.5)],
            'D18.3':  [('hemangioma', False, 0.6)],
            
            # ======================== Z-CODES (HEALTH FACTORS / STATUS) ========================
            'Z46.6':  [('orthopedic device fitting', True, 0.5), ('orthotic fitting', True, 0.5)],
            'Z55.6':  [('illiteracy', False, 0.7), ('cannot read', True, 0.5), ('unable to read', True, 0.5),
                        ('low literacy', True, 0.5)],
            'Z60.4':  [('social exclusion', True, 0.5), ('social isolation', True, 0.5)],
            'Z74.1':  [('need for assistance with personal care', True, 0.6),
                        ('assistance with adl', True, 0.5), ('dependent on caregiver', True, 0.5)],
            'Z79.01': [('long term use of anticoagulant', True, 0.7), ('on warfarin', True, 0.6),
                        ('on coumadin', True, 0.6), ('on eliquis', True, 0.6), ('on xarelto', True, 0.6),
                        ('anticoagulant therapy', True, 0.5), ('blood thinner', True, 0.4)],
            'Z79.2':  [('long term use of antibiotic', True, 0.6), ('chronic antibiotic', True, 0.5)],
            'Z79.4':  [('long term use of insulin', True, 0.7), ('insulin dependent', True, 0.6),
                        ('on insulin', True, 0.5), ('insulin therapy', True, 0.5)],
            'Z79.51': [('long term use of inhaled steroid', True, 0.6), ('inhaled corticosteroid', True, 0.5)],
            'Z79.82': [('long term use of aspirin', True, 0.6), ('daily aspirin', True, 0.5),
                        ('aspirin therapy', True, 0.5)],
            'Z79.84': [('long term use of oral hypoglycemic', True, 0.6), ('on metformin', True, 0.5),
                        ('oral diabetes medication', True, 0.5)],
            'Z79.891': [('long term use of opiate', True, 0.6), ('chronic opioid', True, 0.5),
                         ('opioid therapy', True, 0.5), ('on morphine', True, 0.5)],
            'Z79.899': [('long term medication use', True, 0.4), ('chronic medication', True, 0.3)],
            'Z86.718': [('history of pulmonary embolism', True, 0.7), ('history of dvt', True, 0.6),
                         ('prior pe', True, 0.5), ('prior dvt', True, 0.5)],
            'Z86.73': [('history of tia', True, 0.6), ('history of stroke', True, 0.6),
                        ('prior stroke', True, 0.6), ('prior cva', True, 0.6)],
            'Z87.440': [('history of urinary tract infection', True, 0.6), ('recurrent uti', True, 0.6)],
            'Z87.891': [('history of nicotine dependence', True, 0.7), ('former smoker', True, 0.6),
                         ('ex-smoker', False, 0.5), ('quit smoking', True, 0.5), ('tobacco history', True, 0.5)],
            'Z99.3':  [('wheelchair dependent', True, 0.7), ('wheelchair bound', True, 0.6),
                        ('uses wheelchair', True, 0.6)],
            'Z99.81': [('ventilator dependent', True, 0.7), ('tracheostomy dependent', True, 0.6)],
            'Z99.89': [('dependence on other enabling machine', True, 0.5), ('cpap dependent', True, 0.5)],
        }
        
        # Set to track which specific ICD-10 classes received a boost
        boosted_codes = set()
        
        for code, rules in keyword_rules.items():
            # Convert the ICD code string to the model's internal class index
            code_idx = None
            for idx, c in self.idx_to_code.items():
                if c.startswith(code):
                    code_idx = idx
                    break
            
            # Skip if this rule refers to a code the CNN does not recognize
            if code_idx is None:
                continue
            
            for rule in rules:
                keyword = rule[0]
                is_phrase = rule[1]
                boost = rule[2]
                
                # Check for the keyword based on its matching rule type
                matched = False
                if is_phrase:
                    matched = keyword in text_lower
                else:
                    matched = self._find_whole_word(text_lower, keyword)
                
                if not matched:
                    continue
                
                # Clinical Negation Detection: check if the matched keyword is negated
                # e.g., "no history of falls", "denies chest pain", "ruled out diabetes"
                if self._is_negated(text_lower, keyword, is_phrase):
                    logger.debug(f"Negated keyword '{keyword}' for {code} — skipping boost")
                    continue
                
                # Apply the boost, capping at 1.0
                probs[code_idx] = min(1.0, probs[code_idx] + boost)
                boosted_codes.add(code)
                
                # Track the matched keyword as evidence for the explainability layer
                if code not in evidence:
                    evidence[code] = []
                evidence[code].append(keyword)
        
        return probs, evidence
    
    def predict(self, text: str, top_k: int = 10, threshold: float = 0.15) -> List[Dict]:
        """
        Takes raw medical text and processes it completely to return structured ICD-10 predictions.
        
        Args:
            text: Raw input medical record or notes.
            top_k: The maximum number of predicted codes to return.
            threshold: Minimum probability/confidence required to include a prediction in the result.
                       Default raised to 0.15 for better precision (reduced false positives).
        
        Returns:
            A list of dictionary objects describing each predicted ICD-10 code 
            (code, description, confidence, evidence, etc.).
        """
        if not self.model:
            raise RuntimeError("Model not loaded!")
        
        # 1. Clean and normalize the raw text into word tokens
        tokens = self.preprocess_text(text)
        
        # 2. Convert string tokens to model-consumable integer embeddings mapped to memory/GPU device
        encoded = self.encode_text(tokens).to(self.device)
        
        # 3. Perform a forward pass through the Neural Network
        with torch.no_grad():
            predictions = self.model(encoded)
        
        # 4. Extract raw probability scores mapped by index (flattening batch layer)
        probs = predictions.cpu().numpy()[0]
        
        # 5. Integrate deterministic rule-based predictions with negation awareness
        probs, evidence = self._apply_keyword_rules(text, probs)
        
        # 6. Safety boundary: Ensure all probabilities remain strictly between 0 and 1
        probs = np.clip(probs, 0.0, 1.0)
        
        # 7. Identify the indices covering the top-scoring predictions by ordering them in descending fashion
        top_indices = np.argsort(probs)[::-1]
        
        results = []
        for idx in top_indices:
            if len(results) >= top_k:
                break
            
            confidence = float(probs[idx])
            if confidence < threshold:
                continue
            
            code = self.idx_to_code[idx]
            
            # Attach real evidence: the actual keywords/phrases that triggered the boost
            # If no keyword match, the prediction came purely from the CNN
            code_evidence = evidence.get(code, [])
            if not code_evidence:
                # Check if any parent code prefix has evidence (e.g., E11.9 rules matching E11.22)
                for ev_code, ev_keywords in evidence.items():
                    if code.startswith(ev_code) or ev_code.startswith(code):
                        code_evidence = ev_keywords
                        break
            
            evidence_str = ", ".join(code_evidence) if code_evidence else "CNN pattern match"
            
            results.append({
                'code': code,
                'description': get_code_description(code),
                'confidence': confidence,
                'color': get_code_color(code),
                'chapter': get_chapter_name(code),
                'evidence': evidence_str
            })
        
        return results


# Global placeholder for the Predictor instance to implement a Singleton pattern
_predictor = None

def get_predictor() -> ICD10Predictor:
    """
    Returns the single global instance of the ICD10Predictor model.
    Instantiates the model upon the very first call, and caches it for all future uses.
    This saves significant compute time/memory by avoiding duplicate loading of weights.
    """
    global _predictor
    if _predictor is None:
        _predictor = ICD10Predictor()
    return _predictor


def predict_icd10(text: str, top_k: int = 10) -> List[Dict]:
    """
    Public entry point to be called rapidly from other parts of the application.
    
    Args:
        text (str): Complete medical note text to be parsed.
        top_k (int): Limit to the number of returned diagnoses.
        
    Returns:
        List of dictionaries with 'code', 'description', 'confidence', etc.
    """
    # Fetch the singleton instance of the predictor logic
    predictor = get_predictor()
    
    # Process the text against the model and return the results
    return predictor.predict(text, top_k=top_k)
