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
        
        # Simple dictionary for expanding common medical acronyms
        abbrev_map = {
            'pt': 'patient', 'dx': 'diagnosis', 'htn': 'hypertension',
            'ckd': 'chronic kidney disease',
            'copd': 'chronic obstructive pulmonary disease',
            'chf': 'congestive heart failure', 'cva': 'cerebrovascular accident'
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
        # \b denotes a 'word boundary' in regular expressions
        pattern = r'\b' + re.escape(word) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _apply_keyword_rules(self, text: str, probs: np.ndarray) -> np.ndarray:
        """
        A rule-based AI enhancement layer.
        
        While the neural network makes general statistical predictions, sometimes explicit
        keywords found in the text guarantee an ICD-10 code applies. This function boosts 
        the predicted probability scores for particular codes when their associated explicit 
        keywords or phrases are unambiguously found.
        """
        text_lower = text.lower()
        
        # Dictionary outlining rules: 
        # Key: Expected ICD-10 code snippet 
        # Value: List of tuples -> (Trigger keyword/phrase, is_phrase_flag, boost_amount)
        # Note: If is_phrase is True, it does a simple substring match. If False, it uses a whole-word match.
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
            
            # Other Specific Nutrient conditions
            'E55.9': [('vitamin d deficiency', True, 0.9)],
        }
        
        # Set to track which specific ICD-10 classes received a boost for logging/debugging purposes
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
            
            # Cycle through all keyword patterns mapped to this code
            for rule in rules:
                keyword = rule[0]      # The text triggered term
                is_phrase = rule[1]    # Whether to match exactly as a whole word
                boost = rule[2]        # Amount to increase model confidence by
                
                # Check for the keyword based on its matching rule type
                if is_phrase:
                    # Simple substring contains check
                    if keyword in text_lower:
                        # Apply boost, capping the possibility at 1.0 (100% confidence)
                        probs[code_idx] = min(1.0, probs[code_idx] + boost)
                        boosted_codes.add(code)
                else:
                    # Stricter standalone whole-word check
                    if self._find_whole_word(text_lower, keyword):
                        probs[code_idx] = min(1.0, probs[code_idx] + boost)
                        boosted_codes.add(code)
        
        return probs
    
    def predict(self, text: str, top_k: int = 10, threshold: float = 0.1) -> List[Dict]:
        """
        Takes raw medical text and processes it completely to return structured ICD-10 predictions.
        
        Args:
            text: Raw input medical record or notes.
            top_k: The maximum number of predicted codes to return.
            threshold: Minimum probability/confidence required to include a prediction in the result.
        
        Returns:
            A list of dictionary objects describing each predicted ICD-10 code (code, description, confidence, etc.).
        """
        if not self.model:
            raise RuntimeError("Model not loaded!")
        
        # 1. Clean and normalize the raw text into word tokens
        tokens = self.preprocess_text(text)
        
        # 2. Convert string tokens to model-consumable integer embeddings mapped to memory/GPU device
        encoded = self.encode_text(tokens).to(self.device)
        
        # 3. Perform a forward pass through the Neural Network
        # torch.no_grad() speeds up computation and saves memory since we are not training/updating weights
        with torch.no_grad():
            predictions = self.model(encoded)
        
        # 4. Extract raw probability scores mapped by index (flattening batch layer)
        probs = predictions.cpu().numpy()[0]
        
        # 5. Integrate deterministic rule-based predictions to cover neural network weak spots
        probs = self._apply_keyword_rules(text, probs)
        
        # 6. Safety boundary: Ensure all probabilities remain strictly between 0 and 1
        probs = np.clip(probs, 0.0, 1.0)
        
        # 7. Identify the indices covering the top-scoring predictions by ordering them in descending fashion
        top_indices = np.argsort(probs)[::-1]
        
        results = []
        for idx in top_indices:
            # Stop accumulating results once we hit the requested limit
            if len(results) >= top_k:
                break
            
            # Check the probability score; if it drops below the cutoff, we can stop evaluating (since array is sorted)
            confidence = float(probs[idx])
            if confidence < threshold:
                continue
            
            # Retrieve the standard ICD-10 code string mapping directly to this prediction
            code = self.idx_to_code[idx]
            
            # Bundle all the necessary metadata detailing this prediction for the frontend application
            results.append({
                'code': code,
                'description': get_code_description(code),
                'confidence': confidence,
                'color': get_code_color(code),
                'chapter': get_chapter_name(code)
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
