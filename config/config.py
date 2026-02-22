"""
Configuration settings for CNN-Based ICD-10 Auto-Coding System
Optimized for Google Colab Free Tier
This module centralizes all configurable parameters, paths, and hyperparameters
used throughout the ICD-10 automated coding project.
"""

import os

# ============================================
# Google Drive Paths (configurable via environment variables)
# These paths dictate where data is read from and where outputs are stored.
# They default to Google Drive locations but can be overridden by environment variables.
# ============================================
DRIVE_BASE = os.environ.get("DRIVE_BASE", "/content/drive/MyDrive")
# Path to Home Health 485 documents
DRIVE_HOME_HEALTH = os.environ.get("DRIVE_HOME_HEALTH", f"{DRIVE_BASE}/485/485 DOCS/")
# Path to PT/OT and other non-485 documents
DRIVE_PT_OT = os.environ.get("DRIVE_PT_OT", f"{DRIVE_BASE}/485/Other Than 485/")

# Project output folder on Drive to store generated project artifacts
PROJECT_FOLDER = os.environ.get("ICD10_PROJECT_FOLDER", f"{DRIVE_BASE}/ICD10_Project")
# Subfolder for raw and processed data
DATA_FOLDER = f"{PROJECT_FOLDER}/data"
# Subfolder for intermediate processed data files
PROCESSED_FOLDER = f"{DATA_FOLDER}/processed"
# Subfolder for data split into training, validation, and testing sets
SPLIT_FOLDER = f"{DATA_FOLDER}/train_test_split"
# Subfolder to save trained model weights and architectures
MODELS_FOLDER = f"{PROJECT_FOLDER}/models"
# Subfolder for outputting final metrics, predictions, and visualizations
RESULTS_FOLDER = f"{PROJECT_FOLDER}/results"

# ============================================
# Data Processing Settings
# Configures how raw text is tokenized, filtered, and vectorized
# ============================================
MAX_SEQUENCE_LENGTH = 2000      # Maximum tokens (words) to keep per document. Longer documents are truncated.
MIN_TOKEN_FREQUENCY = 3         # Minimum number of times a word must appear in the corpus to be added to the vocabulary
TOP_N_CODES = 100               # Number of final most frequent ICD-10 codes the model is trained to predict
CHECKPOINT_INTERVAL = 50        # Frequency of saving intermediate progress during long data extraction/processing runs

# ============================================
# Train/Val/Test Split Ratios
# Defines the proportions for dividing the dataset for machine learning
# ============================================
TRAIN_RATIO = 0.70              # 70% of data used to train the model
VAL_RATIO = 0.15                # 15% used for validation during training to tune hyperparameters
TEST_RATIO = 0.15               # 15% withheld for final unbiased evaluation
RANDOM_SEED = 42                # Fixed seed to ensure reproducibility of the random splits

# ============================================
# Model Hyperparameters (Basic CNN)
# Architecture and learning parameters defining the Convolutional Neural Network
# ============================================
EMBEDDING_DIM = 128             # Dimensionality of the dense word vectors representing the vocabulary
CNN_FILTER_SIZES = [3, 4, 5]    # Sizes of the convolutional windows (detecting 3-word, 4-word, and 5-word phrases)
CNN_NUM_FILTERS = 256           # Number of distinct feature maps learned for each filter size
DROPOUT_RATE = 0.5              # Percentage of neurons randomly disabled during training to prevent overfitting
DENSE_UNITS = [512, 256]        # Number of neurons in the fully connected layers before the final classification head

# ============================================
# Training Parameters (Colab Free Tier Optimized)
# Defines how the model optimizes its weights
# ============================================
BATCH_SIZE = 16                 # Number of samples processed before updating weights (small to fit in ~12GB RAM)
MAX_EPOCHS = 30                 # Maximum number of complete passes over the training dataset
EARLY_STOPPING_PATIENCE = 5     # Number of epochs to wait for validation improvement before stopping training early
LEARNING_RATE = 0.001           # Step size multiplier affecting how much weights are adjusted per batch

# ============================================
# OCR Settings
# Configurations for extracting text from scanned PDF images using Tesseract
# ============================================
OCR_DPI = 200                   # Resolution used when converting PDF pages to images (higher means better OCR but slower)
OCR_LANGUAGE = 'eng'            # Language package to use in Tesseract for text recognition
OCR_MAX_RETRIES = 3             # Number of times to re-attempt OCR on a failed page
MIN_TEXT_LENGTH = 50            # Minimum number of characters a document must yield to be considered successfully extracted
MAX_GARBAGE_RATIO = 0.3         # Tolerance threshold for non-alphanumeric characters (rejects heavily artifacted pages)

# ============================================
# ICD-10 Code Settings
# Rules for identifying and categorizing ICD-10 medical codes
# ============================================
# Regular expression pattern to reliably locate valid ICD-10-CM codes in free text.
# Matches: Letter A-TV-Z + 2 digits + optional decimal point + up to 4 alphanumeric extensions
ICD10_PATTERN = r'\b([A-TV-Z][0-9]{2})\.?([0-9A-Z]{1,4})?\b'

# Dictionary mapping the first letter of an ICD-10 code to its broader medical chapter category
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

# The letter 'U' is reserved by the WHO for special conditions (like COVID-19/U07.1) and often excluded 
# in general legacy coding logic unless specifically updated.
INVALID_ICD10_CATEGORIES = {'U'}

# ============================================
# Logging Settings
# Formats for console and file output logging
# ============================================
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s' # Standard output format including timestamp and severity
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'                    # Precise date and time formatting string

# ============================================
# Helper Functions
# Utility methods dealing with environment setup
# ============================================
def create_colab_directories():
    """
    Creates all necessary directories for the project on Google Drive or the local file system.
    Ensures that scripts won't crash due to missing paths when attempting to save output data or models.
    
    Returns:
        List of strings representing the created directory pathways.
    """
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
    # Iteratively create directories; exist_ok=True prevents errors if paths already exist
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print(f"✓ Created {len(directories)} project directories")
    return directories


def get_output_paths():
    """
    Returns a dictionary aggregating all standard file paths used across to project.
    Centralized path management avoids hardcoded strings scattered across various modules.
    
    Returns:
        Dict mapping readable string keys to exact file paths.
    """
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
    # If the file is executed directly, print a summary of the active configuration
    print("CNN ICD-10 Configuration")
    print("=" * 40)
    print(f"Drive Home Health: {DRIVE_HOME_HEALTH}")
    print(f"Drive PT/OT: {DRIVE_PT_OT}")
    print(f"Max Sequence Length: {MAX_SEQUENCE_LENGTH}")
    print(f"Top N Codes: {TOP_N_CODES}")
    print(f"Batch Size: {BATCH_SIZE}")
