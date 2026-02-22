"""
ICD-10 Model Inference Module
Loads the trained PyTorch CNN model and performs predictions
"""

import os
import pickle
import json
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from typing import List, Dict, Tuple
import re
from src.vocabulary import Vocabulary
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the paths to model files
# Use resolve() for absolute path and better robustness
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define possible data locations (prioritize existing structure)
MODEL_DIR = PROJECT_ROOT / "Downloaded files" / "ICD10_Project" / "models"
DATA_DIR = PROJECT_ROOT / "Downloaded files" / "ICD10_Project" / "data" / "train_test_split"

# If hardcoded paths don't exist, try falling back to standard project structure
if not MODEL_DIR.exists():
    MODEL_DIR = PROJECT_ROOT / "models"
if not DATA_DIR.exists():
    DATA_DIR = PROJECT_ROOT / "data" / "train_test_split"

# Load ICD-10 descriptions
try:
    from streamlit_app.icd10_descriptions import get_code_description, get_code_color, get_chapter_name
except ImportError:
    # Fallback if import fails
    def get_code_description(code): return f"ICD-10: {code}"
    def get_code_color(code): return "#808080"
    def get_chapter_name(code): return "Unknown"


class TextCNN(nn.Module):
    """CNN Model for ICD-10 classification - matches trained model architecture"""
    def __init__(self, vocab_size, embedding_dim, n_classes, max_seq_length=2000):
        super(TextCNN, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        
        # 4 conv layers with kernel sizes 2, 3, 4, 5 (matching saved model)
        self.convs = nn.ModuleList([
            nn.Conv1d(embedding_dim, 128, kernel_size=2),
            nn.Conv1d(embedding_dim, 128, kernel_size=3),
            nn.Conv1d(embedding_dim, 128, kernel_size=4),
            nn.Conv1d(embedding_dim, 128, kernel_size=5),
        ])
        
        # 4 convs * 128 filters = 512 features
        self.fc1 = nn.Linear(512, 256)
        self.fc2 = nn.Linear(256, n_classes)
        self.bn = nn.BatchNorm1d(256)
        self.dropout = nn.Dropout(0.5)
        
    def forward(self, x):
        # x: (batch, seq_len)
        x = self.embedding(x)  # (batch, seq_len, embed_dim)
        x = x.permute(0, 2, 1)  # (batch, embed_dim, seq_len)
        
        # Apply each conv + relu + max_pool
        conv_outputs = []
        for conv in self.convs:
            c = torch.relu(conv(x))
            c = torch.max_pool1d(c, c.size(2)).squeeze(2)
            conv_outputs.append(c)
        
        # Concatenate all conv outputs: (batch, 512)
        x = torch.cat(conv_outputs, dim=1)
        
        x = self.dropout(x)
        x = torch.relu(self.fc1(x))
        x = self.bn(x)
        x = self.dropout(x)
        x = torch.sigmoid(self.fc2(x))
        
        return x


class ICD10Predictor:
    """Handles model loading and prediction"""
    
    def __init__(self):
        self.model = None
        self.vocabulary = None
        self.label_encoder = None
        self.word_to_idx = None
        self.idx_to_code = None
        self.code_to_idx = None  # Reverse mapping
        self.max_seq_length = 2000
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._load_model()
    
    def _load_model(self):
        """Load model, vocabulary, and label encoder"""
        try:
            # Check if directories exist
            if not DATA_DIR.exists():
                raise FileNotFoundError(f"Data directory not found at {DATA_DIR}")
            if not MODEL_DIR.exists():
                raise FileNotFoundError(f"Model directory not found at {MODEL_DIR}")

            # Load vocabulary
            vocab_path = DATA_DIR / "vocabulary.pkl"
            with open(vocab_path, 'rb') as f:
                self.vocabulary = pickle.load(f)
            
            # Use the existing word_to_idx from the loaded Vocabulary object
            if hasattr(self.vocabulary, 'word2idx'):
                self.word_to_idx = self.vocabulary.word2idx
            else:
                # Fallback if it's a raw list (older version compatibility)
                self.word_to_idx = {word: idx for idx, word in enumerate(self.vocabulary, start=1)}
                self.word_to_idx['<PAD>'] = 0
                self.word_to_idx['<UNK>'] = len(self.vocabulary) + 1
            
            # Load label encoder
            label_path = DATA_DIR / "label_encoder.pkl"
            with open(label_path, 'rb') as f:
                loaded_le = pickle.load(f)
            
            # Handle if it's a dictionary (from notebook) or raw object
            if isinstance(loaded_le, dict):
                self.classes_ = loaded_le.get('classes')
                # If we need the actual MLB object for other things:
                self.label_encoder = loaded_le.get('mlb') 
            else:
                self.label_encoder = loaded_le
                self.classes_ = self.label_encoder.classes_
            
            # Build index to code mapping (and reverse)
            self.idx_to_code = {idx: code for idx, code in enumerate(self.classes_)}
            self.code_to_idx = {code: idx for idx, code in enumerate(self.classes_)}
            
            # Load preprocessing summary
            preproc_path = DATA_DIR / "preprocessing_summary.json"
            with open(preproc_path, 'r') as f:
                preproc_info = json.load(f)
            
            vocab_size = len(self.word_to_idx)  # Exact size to match saved model
            n_classes = preproc_info['n_classes']
            
            # Initialize model
            self.model = TextCNN(
                vocab_size=vocab_size,
                embedding_dim=128,
                n_classes=n_classes,
                max_seq_length=self.max_seq_length
            )
            
            # Load model weights (weights_only=False needed for PyTorch 2.6+)
            model_path = MODEL_DIR / "icd10_cnn_latest.pt"
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found at {model_path}")

            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Model loaded successfully!")
            logger.info(f"Vocabulary size: {vocab_size}")
            logger.info(f"Number of classes: {n_classes}")
            logger.info(f"Device: {self.device}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text similar to training"""
        # Lowercase and basic cleaning
        text = text.lower()
        
        # Remove special characters but keep medical terms
        text = re.sub(r'[^a-z0-9\s\.\-/]', ' ', text)
        
        # Tokenize
        tokens = text.split()
        
        # Basic medical abbreviation expansion (simplified)
        abbrev_map = {
            'pt': 'patient', 'dx': 'diagnosis', 'htn': 'hypertension',
            'ckd': 'chronic kidney disease',
            'copd': 'chronic obstructive pulmonary disease',
            'chf': 'congestive heart failure', 'cva': 'cerebrovascular accident'
        }
        
        tokens = [abbrev_map.get(token, token) for token in tokens]
        
        return tokens
    
    def encode_text(self, tokens: List[str]) -> torch.Tensor:
        """Convert tokens to indices"""
        indices = [self.word_to_idx.get(token, self.word_to_idx['<UNK>']) for token in tokens]
        
        # Pad or truncate to max_seq_length
        if len(indices) < self.max_seq_length:
            indices += [0] * (self.max_seq_length - len(indices))
        else:
            indices = indices[:self.max_seq_length]
        
        return torch.tensor(indices, dtype=torch.long).unsqueeze(0)  # Add batch dimension
    
    def _find_whole_word(self, text: str, word: str) -> bool:
        """
        Check if a whole word exists in text (not as part of another word).
        Uses word boundary matching to prevent 'dm' matching 'admission'.
        """
        # Use regex word boundaries for accurate matching
        pattern = r'\b' + re.escape(word) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _check_negation(self, text: str, match_index: int) -> bool:
        """
        Check for negation terms preceding the match.
        Looks back approx 40 characters (approx 5-6 words).
        """
        lookback_chars = 40
        start = max(0, match_index - lookback_chars)
        preceding_text = text[start:match_index]

        # Common medical negation terms
        negation_terms = [
            r'\bno\b', r'\bnot\b', r'\bdenies\b', r'\bdenied\b',
            r'\bnegative for\b', r'\bwithout\b', r'\bfree of\b'
        ]

        for term in negation_terms:
            if re.search(term, preceding_text, re.IGNORECASE):
                return True
        return False

    def _apply_keyword_rules(self, text: str, probs: np.ndarray) -> np.ndarray:
        """
        Apply rule-based keyword boosting to improve prediction accuracy.
        Uses whole-word matching and negation detection.
        """
        text_lower = text.lower()
        
        # Keyword rules: {ICD_code: [(keyword, is_phrase, boost_amount), ...]}
        # is_phrase=True means search as substring, False means whole word only
        keyword_rules = {
            # Falls and mobility
            'Z91.81': [('fall', False, 0.8), ('falling', False, 0.8), ('fell', False, 0.8), ('history of fall', True, 0.9)],
            'R26.81': [('unsteadiness', False, 0.7), ('unsteady gait', True, 0.8)],
            'R26.2': [('difficulty walking', True, 0.8), ('difficulty in walking', True, 0.8), ('gait disturbance', True, 0.7)],
            'M62.81': [('muscle weakness', True, 0.8), ('muscular weakness', True, 0.8), ('generalized weakness', True, 0.7)],
            
            # Metabolic/Endocrine
            'E78.5': [('hyperlipidemia', False, 0.9), ('cholesterol', False, 0.6), ('elevated lipid', True, 0.7)],
            'E03.9': [('hypothyroidism', False, 0.9), ('thyroid', False, 0.5), ('tsh elevated', True, 0.8)],
            'E11.9': [('type 2 diabetes', True, 0.9), ('diabetes mellitus', True, 0.8), ('diabetic', False, 0.6)],
            'E11.42': [('diabetic neuropathy', True, 0.9), ('peripheral neuropathy', True, 0.7)],
            
            # Gout
            'M10.33': [('gout', False, 0.9), ('podagra', False, 0.9), ('uric acid', True, 0.6)],
            
            # Kidney
            'I13.0': [('hypertensive chronic kidney', True, 0.9), ('hypertensive ckd', True, 0.9)],
            'N18.2': [('ckd stage 2', True, 0.9), ('chronic kidney disease stage 2', True, 0.9)],
            'N18.3': [('ckd stage 3', True, 0.9), ('chronic kidney disease stage 3', True, 0.9)],
            'N18.4': [('ckd stage 4', True, 0.9), ('chronic kidney disease stage 4', True, 0.9)],
            
            # Musculoskeletal
            'M17.00': [('osteoarthritis', False, 0.7), ('knee osteoarthritis', True, 0.9), ('bilateral knee', True, 0.7)],
            'M81.0': [('osteoporosis', False, 0.8), ('bone loss', True, 0.6)],
            'M54.5': [('low back pain', True, 0.9), ('lumbar pain', True, 0.8), ('back pain', True, 0.6)],
            
            # Gastrointestinal
            'K21.9': [('gerd', False, 0.9), ('gastroesophageal reflux', True, 0.9), ('heartburn', False, 0.7), ('reflux', False, 0.5)],
            
            # Cardiovascular
            'I25.10': [('coronary artery disease', True, 0.9), ('cad', False, 0.8), ('coronary atherosclerosis', True, 0.9)],
            'I10': [('hypertension', False, 0.7), ('high blood pressure', True, 0.8), ('elevated blood pressure', True, 0.7)],
            'I50.32': [('heart failure', True, 0.8), ('congestive heart failure', True, 0.9), ('chf', False, 0.8)],
            'I48.0': [('atrial fibrillation', True, 0.9), ('afib', False, 0.9), ('a-fib', False, 0.9)],
            'I70.0': [('atherosclerosis', False, 0.8), ('aortic atherosclerosis', True, 0.9)],
            
            # Respiratory
            'J44.9': [('copd', False, 0.9), ('chronic obstructive pulmonary', True, 0.9)],
            'G47.33': [('sleep apnea', True, 0.9), ('obstructive sleep apnea', True, 0.95), ('snoring', False, 0.5)],
            
            # Neurological
            'G30.1': [('alzheimer', False, 0.9), ('alzheimers', False, 0.9)],
            'G89.29': [('chronic pain', True, 0.7), ('pain syndrome', True, 0.6)],
            
            # Mental Health
            'F32.A': [('depression', False, 0.6), ('major depressive', True, 0.8), ('depressive disorder', True, 0.8)],
            'F41.1': [('anxiety', False, 0.6), ('generalized anxiety', True, 0.8), ('anxiety disorder', True, 0.8)],
            
            # Urinary
            'N39.0': [('urinary tract infection', True, 0.9), ('uti', False, 0.8)],
            'N40.0': [('benign prostatic hyperplasia', True, 0.9), ('bph', False, 0.8), ('prostate', False, 0.5)],
            
            # Other
            'E55.9': [('vitamin d deficiency', True, 0.9)],
        }
        
        # Track which codes were boosted
        boosted_codes = set()
        
        for code, rules in keyword_rules.items():
            # Find the indices for this code (or codes starting with it)
            matching_indices = []
            for idx, c in self.idx_to_code.items():
                if c.startswith(code):
                    matching_indices.append(idx)
            
            if not matching_indices:
                continue
            
            # Check each keyword rule
            for rule in rules:
                keyword = rule[0]
                is_phrase = rule[1]
                boost = rule[2]
                
                # Find matching locations
                matches = []
                if is_phrase:
                    # Find all occurrences
                    for m in re.finditer(re.escape(keyword), text_lower):
                        matches.append(m.start())
                else:
                    # Whole word search
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    for m in re.finditer(pattern, text_lower):
                        matches.append(m.start())

                # Check for negation
                matched = False
                for match_idx in matches:
                    if not self._check_negation(text_lower, match_idx):
                        matched = True
                        break # Found at least one non-negated occurrence

                if matched:
                    # Apply boost to ALL matching codes
                    for code_idx in matching_indices:
                        probs[code_idx] = min(1.0, probs[code_idx] + boost)
                        boosted_codes.add(code)
        
        return probs
    
    def predict(self, text: str, top_k: int = 10, threshold: float = 0.1) -> List[Dict]:
        """
        Predict ICD-10 codes from text
        
        Args:
            text: Medical text to analyze
            top_k: Number of top predictions to return
            threshold: Minimum confidence threshold
        
        Returns:
            List of predictions with code, description, confidence, color
        """
        if not self.model:
            raise RuntimeError("Model not loaded!")
        
        # Preprocess
        tokens = self.preprocess_text(text)
        encoded = self.encode_text(tokens).to(self.device)
        
        # Predict
        with torch.no_grad():
            predictions = self.model(encoded)
        
        # Get probabilities
        probs = predictions.cpu().numpy()[0]
        
        # Apply keyword-based boosting for robustness
        probs = self._apply_keyword_rules(text, probs)
        
        # Re-normalize/Clip (sigmoid output is 0-1, boosting can go >1)
        probs = np.clip(probs, 0.0, 1.0)
        
        # Get top predictions above threshold
        top_indices = np.argsort(probs)[::-1]
        
        results = []
        for idx in top_indices:
            if len(results) >= top_k:
                break
            
            confidence = float(probs[idx])
            if confidence < threshold:
                continue
            
            code = self.idx_to_code[idx]
            
            results.append({
                'code': code,
                'description': get_code_description(code),
                'confidence': confidence,
                'color': get_code_color(code),
                'chapter': get_chapter_name(code)
            })
        
        return results


# Global predictor instance
_predictor = None

def get_predictor() -> ICD10Predictor:
    """Get or create predictor instance (singleton)"""
    global _predictor
    if _predictor is None:
        _predictor = ICD10Predictor()
    return _predictor


def predict_icd10(text: str, top_k: int = 10) -> List[Dict]:
    """
    Main prediction function
    
    Args:
        text: Medical text
        top_k: Number of predictions to return
    
    Returns:
        List of predictions
    """
    predictor = get_predictor()
    return predictor.predict(text, top_k=top_k)
