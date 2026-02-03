"""
Configuration settings for CNN-Based ICD-10 Auto-Coding System
Optimized for Google Colab Free Tier
"""

import os

# ============================================
# Google Drive Paths (for Colab)
# ============================================
DRIVE_BASE = "/content/drive/MyDrive"
DRIVE_HOME_HEALTH = f"{DRIVE_BASE}/485/485 DOCS/"
DRIVE_PT_OT = f"{DRIVE_BASE}/485/Other Than 485/"

# Project output folder on Drive
PROJECT_FOLDER = f"{DRIVE_BASE}/ICD10_Project"
DATA_FOLDER = f"{PROJECT_FOLDER}/data"
PROCESSED_FOLDER = f"{DATA_FOLDER}/processed"
SPLIT_FOLDER = f"{DATA_FOLDER}/train_test_split"
MODELS_FOLDER = f"{PROJECT_FOLDER}/models"
RESULTS_FOLDER = f"{PROJECT_FOLDER}/results"

# ============================================
# Data Processing Settings
# ============================================
MAX_SEQUENCE_LENGTH = 2000      # Maximum tokens per document
MIN_TOKEN_FREQUENCY = 3         # Minimum word frequency for vocabulary
TOP_N_CODES = 100               # Number of ICD-10 codes to predict
CHECKPOINT_INTERVAL = 50        # Save progress every N PDFs

# ============================================
# Train/Val/Test Split Ratios
# ============================================
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15
RANDOM_SEED = 42

# ============================================
# Model Hyperparameters (Basic CNN)
# ============================================
EMBEDDING_DIM = 128
CNN_FILTER_SIZES = [3, 4, 5]    # N-gram sizes to detect
CNN_NUM_FILTERS = 256           # Filters per size
DROPOUT_RATE = 0.5
DENSE_UNITS = [512, 256]

# ============================================
# Training Parameters (Colab Free Tier Optimized)
# ============================================
BATCH_SIZE = 16                 # Safe for Colab ~12GB RAM
MAX_EPOCHS = 30
EARLY_STOPPING_PATIENCE = 5
LEARNING_RATE = 0.001

# ============================================
# OCR Settings
# ============================================
OCR_DPI = 200                   # DPI for PDF to image conversion
OCR_LANGUAGE = 'eng'            # Tesseract language
OCR_MAX_RETRIES = 3             # Retry count for failed OCR
MIN_TEXT_LENGTH = 50            # Minimum chars for valid extraction
MAX_GARBAGE_RATIO = 0.3         # Max ratio of non-alphanumeric chars

# ============================================
# ICD-10 Code Settings
# ============================================
# Valid ICD-10-CM pattern: Letter + 2 digits + optional (. + 1-4 chars)
ICD10_PATTERN = r'\b([A-TV-Z][0-9]{2})\.?([0-9A-Z]{1,4})?\b'

# ICD-10-CM Chapter mappings
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

# Invalid category letters (U is reserved for special use)
INVALID_ICD10_CATEGORIES = {'U'}

# ============================================
# Logging Settings
# ============================================
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================
# Helper Functions
# ============================================
def create_colab_directories():
    """Create all project directories on Google Drive"""
    directories = [
        DATA_FOLDER,
        PROCESSED_FOLDER,
        SPLIT_FOLDER,
        MODELS_FOLDER,
        f"{MODELS_FOLDER}/checkpoints",
        f"{MODELS_FOLDER}/embeddings",
        RESULTS_FOLDER,
        f"{RESULTS_FOLDER}/visualizations"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print(f"✓ Created {len(directories)} project directories")
    return directories


def get_output_paths():
    """Get all output file paths"""
    return {
        'extracted_csv': f"{PROCESSED_FOLDER}/all_documents_extracted.csv",
        'preprocessed_csv': f"{PROCESSED_FOLDER}/documents_preprocessed.csv",
        'vocabulary_json': f"{PROCESSED_FOLDER}/vocabulary.json",
        'code_stats_csv': f"{PROCESSED_FOLDER}/code_statistics.csv",
        'X_train': f"{SPLIT_FOLDER}/X_train.npy",
        'y_train': f"{SPLIT_FOLDER}/y_train.npy",
        'X_val': f"{SPLIT_FOLDER}/X_val.npy",
        'y_val': f"{SPLIT_FOLDER}/y_val.npy",
        'X_test': f"{SPLIT_FOLDER}/X_test.npy",
        'y_test': f"{SPLIT_FOLDER}/y_test.npy",
        'label_mappings': f"{SPLIT_FOLDER}/label_mappings.json",
        'class_weights': f"{SPLIT_FOLDER}/class_weights.npy",
        'model': f"{MODELS_FOLDER}/cnn_model.h5",
        'embeddings': f"{MODELS_FOLDER}/embeddings/word2vec_128d.npy"
    }


if __name__ == "__main__":
    print("CNN ICD-10 Configuration")
    print("=" * 40)
    print(f"Drive Home Health: {DRIVE_HOME_HEALTH}")
    print(f"Drive PT/OT: {DRIVE_PT_OT}")
    print(f"Max Sequence Length: {MAX_SEQUENCE_LENGTH}")
    print(f"Top N Codes: {TOP_N_CODES}")
    print(f"Batch Size: {BATCH_SIZE}")
