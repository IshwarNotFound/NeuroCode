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

# Get the paths to model files
PROJECT_ROOT = Path(__file__).parent.parent
MODEL_DIR = PROJECT_ROOT / "Downloaded files" / "ICD10_Project" / "models"
DATA_DIR = PROJECT_ROOT / "Downloaded files" / "ICD10_Project" / "data" / "train_test_split"

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
        self.max_seq_length = 2000
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._load_model()
    
    def _load_model(self):
        """Load model, vocabulary, and label encoder"""
        try:
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
            
            # Build index to code mapping
            self.idx_to_code = {idx: code for idx, code in enumerate(self.classes_)}
            
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
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            print(f"✓ Model loaded successfully!")
            print(f"  Vocabulary size: {vocab_size}")
            print(f"  Number of classes: {n_classes}")
            print(f"  Device: {self.device}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
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
            'dm': 'diabetes', 'ckd': 'chronic kidney disease',
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
        
        # --- HYBRID RULE-BASED BOOSTING ---
        # Boost confidence for clear keyword matches to ensure robustness
        # This helps when the model is uncertain or text is short
        text_lower = text.lower()
        
        keyword_rules = {
            'Z91.81': ['fall', 'falling', 'fell'],
            'E78.5': ['hyperlipidemia', 'cholesterol', 'lipid'],
            'M10.33': ['gout', 'podagra'],
            'E03.9': ['hypothyroidism', 'thyroid', 'tsh'],
            'I13.0': ['hypertensive', 'ckd', 'kidney'],
            'M17.00': ['osteoarthritis', 'knee'],
            'K21.9': ['gerd', 'reflux', 'heartburn'],
            'I25.10': ['coronary', 'artery', 'cad', 'angina'],
            'I10': ['hypertension', 'pressure'],
            'N18.2': ['ckd', 'kidney', 'renal'],
            'N18.3': ['ckd', 'kidney', 'renal'],
            'G89.29': ['pain', 'ache'],
            'I50.32': ['heart failure', 'chf'],
            'I48.0': ['atrial fibrillation', 'afib'],
            'E11.9': ['diabetes', 'dm'],
            'E11.42': ['neuropathy', 'numbness'],
            'G30.1': ['alzheimer', 'dementia', 'memory'],
            'J44.9': ['copd', 'obstructive pulmonary'],
            'I70.0': ['atherosclerosis', 'plaque'],
            'M81.0': ['osteoporosis', 'bone'],
            'F32.A': ['depression', 'depressive', 'sad'],
            'F41.1': ['anxiety', 'anxious', 'worry'],
            'G47.33': ['apnea', 'snoring'],
            'N39.0': ['uti', 'urinary', 'infection'],
            'N40.0': ['bph', 'prostatic', 'prostate'],
            'M54.5': ['back pain', 'lumbar'],
            'R26.81': ['unsteadiness', 'walking'],
            'R26.2': ['walking', 'gait']
        }
        
        # Create a boost vector
        boost_vector = np.zeros_like(probs)
        
        # Penalize the "sticky" code M62.81 if it's dominating without evidence
        sticky_code = 'M62.81'
        sticky_idx = -1
        for idx, c in self.idx_to_code.items():
            if c.startswith(sticky_code):
                sticky_idx = idx
                break
        
        if sticky_idx != -1:
            # Check if "weakness" is actually in the text
            if 'weakness' not in text_lower and 'muscle' not in text_lower:
                probs[sticky_idx] *= 0.5  # Penalize by 50%
        
        matched_rule = False
        for code, keywords in keyword_rules.items():
            # Find index for this code
            code_idx = -1
            for idx, c in self.idx_to_code.items():
                if c.startswith(code): # Match base code
                    code_idx = idx
                    break
            
            if code_idx != -1:
                # Check for keywords
                for kw in keywords:
                    if kw in text_lower:
                        # Apply STRONG boost (Override model)
                        probs[code_idx] = 1.0 # Force certainty
                        matched_rule = True
                        # print(f"DEBUG: Boosted {code} based on '{kw}'")
                        break
                        
        # If a rule matched, suppress others to ensure clarity
        # (Optional: reduces clutter from low-confidence noise)
        if matched_rule:
           pass
        
        # Re-normalize/Clip (sigmoid output is 0-1, boosting can go >1)
        probs = np.clip(probs, 0.0, 1.0)
        
        # ----------------------------------
        
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
