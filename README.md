<div align="center">

# ⚫ NeuroCode

**Neural Networks for Medical Coding**

*Clinical Text → ICD-10 Codes. Powered by Deep Learning.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Colab Ready](https://img.shields.io/badge/Google%20Colab-Ready-F9AB00?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com)

---

> *"From raw clinical notes to billable ICD-10 codes — in milliseconds."*

</div>

---

## 🧠 What is NeuroCode?

**NeuroCode** is a production-grade AI system that automatically predicts [ICD-10-CM](https://www.cms.gov/medicare/coding-billing/icd-10-codes) medical diagnosis codes from free-form clinical text — discharge summaries, doctor's notes, therapy evaluations, or even scanned PDFs.

It combines a custom-trained **PyTorch TextCNN** deep learning model with a deterministic rule-based enhancement layer, served through a sleek **Streamlit web application** with a dark-themed, terminal-inspired UI.

---

## ✨ Key Features

| Feature | Details |
|---|---|
| 🤖 **Deep Learning Core** | Multi-kernel 1D CNN trained on real clinical notes |
| 🔀 **Hybrid Prediction Engine** | Neural network outputs + rule-based keyword confidence boosting |
| 📄 **Hybrid PDF Extraction** | Native `pdfplumber` text + Tesseract OCR fallback for scanned docs |
| 🔐 **Security-First Design** | SHA-256 TOFU integrity checks, XSS prevention, rate limiting |
| 🏥 **30+ ICD-10 Keyword Rules** | Cardiovascular, metabolic, musculoskeletal, mental health & more |
| ⚡ **Streamlit Wizard UI** | 3-step flow with animated terminal-style inference display |
| 🔁 **Colab-Optimized** | Checkpoint saving & gc memory management for free-tier GPUs |
| 📊 **Multi-label Output** | Predicts multiple co-existing diagnoses with ranked confidence scores |

---

## 🗂️ Project Structure

```
NeuroCode/
│
├── 📁 src/                           # Core backend modules
│   ├── model_inference.py            #  TextCNN + ICD10Predictor singleton
│   ├── icd10_validator.py            #  ICD-10 regex extraction & validation
│   ├── pdf_extractor.py              #  Hybrid native/OCR PDF extractor
│   ├── vocabulary.py                 #  Vocabulary class (required for unpickling)
│   └── __init__.py
│
├── 📁 streamlit_app/                 # Web application
│   ├── app.py                        #  Main 3-step Streamlit wizard
│   ├── security.py                   #  InputValidator, SessionSecurity, rate limiter
│   ├── icd10_descriptions.py         #  Code descriptions, chapter names, colors
│   ├── case_data.py                  #  Pre-loaded synthetic demo clinical cases
│   ├── styles.css                    #  Dark theme UI (14KB custom CSS)
│   └── requirements.txt             #  Minimal app dependencies
│
├── 📁 config/                        # Global configuration & ICD-10 constants
├── 📁 notebooks/                     # Training & experimentation notebooks
│
├── 📁 Downloaded files/              # Model weights & processed data (gitignored)
│   └── ICD10_Project/
│       ├── models/
│       │   └── icd10_cnn_latest.pt   #  Trained PyTorch model weights
│       ├── data/train_test_split/
│       │   ├── vocabulary.pkl        #  Fitted vocabulary object
│       │   ├── label_encoder.pkl     #  Multi-label binarizer
│       │   └── preprocessing_summary.json
│       └── file_hashes.json          #  SHA-256 integrity hashes (auto-generated)
│
├── test_predictions.py               # Inference testing harness
├── requirements.txt                  # Full training pipeline dependencies
├── Fixing Model Bias-2.md            # Bias analysis & mitigation notes
├── ICD-10 Model Training.md          # Model training documentation
└── gameplan.md                       # Project roadmap & architecture decisions
```

---

## 🏗️ Architecture Deep Dive

### The TextCNN Model

NeuroCode's ML backbone is a **Multi-Kernel 1D Convolutional Neural Network** — a battle-tested architecture for text classification adapted here for medical **multi-label** classification (multiple ICD-10 codes can be true simultaneously for one patient).

```
Raw Clinical Text
       │
       ▼
 ┌─────────────────────────────────────────────┐
 │              Text Preprocessing             │
 │  • Lowercase normalization                  │
 │  • Punctuation stripping                    │
 │  • Medical abbreviation expansion:          │
 │    pt→patient · htn→hypertension            │
 │    ckd→chronic kidney disease · copd→...    │
 └─────────────────────────────────────────────┘
       │
       ▼
 Token → Integer Encoding   (max_seq_length = 2000)
       │
       ▼
 Embedding Layer            (vocab_size × 128 dims, padding_idx=0)
       │
       ▼
 ┌───────┬───────┬───────┬───────┐
 │ k = 2 │ k = 3 │ k = 4 │ k = 5 │   ← 4 parallel Conv1D layers
 │  128  │  128  │  128  │  128  │     (n-gram feature detectors)
 │filters│filters│filters│filters│
 └───┬───┴───┬───┴───┬───┴───┬───┘
     │       │       │       │
  MaxPool MaxPool MaxPool MaxPool     ← Global max-over-time pooling
     │       │       │       │
     └───────────────────────┘
                   │
            Concat → [512]
                   │
             Dropout (p=0.5)
                   │
           FC: 512 → 256 + ReLU
           BatchNorm1d(256)
             Dropout (p=0.5)
                   │
           FC: 256 → N_classes
                   │
               Sigmoid()              ← Multi-label output (0–1 per code)
                   │
          ┌────────────────┐
          │ Keyword Booster │          ← Rule-based confidence amplification
          └────────────────┘
                   │
          Top-K Ranked Results        (default: top_k=10, threshold=0.1)
```

### Hybrid Prediction Engine

After the CNN scores all ICD-10 classes, a **deterministic keyword layer** scans the original text and boosts confidence for codes where explicit clinical phrases are unambiguously present. This covers neural network blind spots for common, high-frequency diagnoses:

```python
# Examples from model_inference.py
'I10':    [('hypertension', False, 0.7), ('high blood pressure', True, 0.8)],
'E11.9':  [('type 2 diabetes', True, 0.9), ('diabetic', False, 0.6)],
'J44.9':  [('copd', False, 0.9), ('chronic obstructive pulmonary', True, 0.9)],
'I48.0':  [('atrial fibrillation', True, 0.9), ('afib', False, 0.9)],
'Z91.81': [('fall', False, 0.8), ('history of fall', True, 0.9)],
```

Rules use two matching modes: **whole-word boundary** (`\bword\b`) for single terms to prevent substring false positives, and **phrase substring** matching for multi-word clinical expressions.

---

## 📦 Module Reference

### `src/model_inference.py` — Prediction Engine

| Class / Function | Description |
|---|---|
| `TextCNN(nn.Module)` | PyTorch model: 4×Conv1D → MaxPool → FC → Sigmoid |
| `ICD10Predictor` | Full pipeline controller: load artifacts → preprocess → infer → boost |
| `._verify_file_integrity()` | SHA-256 Trust-On-First-Use (TOFU) check on model, vocab, label files |
| `._apply_keyword_rules()` | Post-inference rule-based confidence boosting |
| `.preprocess_text()` | Lowercase, strip punctuation, expand medical abbreviations |
| `.encode_text()` | Token list → padded/truncated `torch.LongTensor` |
| `.predict()` | End-to-end: raw text → ranked list of ICD-10 prediction dicts |
| `get_predictor()` | Singleton factory — loads model once, caches for all future calls |
| `predict_icd10()` | Public API shorthand for the application layer |

**Security:** Model weights (`.pt`), vocabulary (`.pkl`), and label encoder (`.pkl`) are all verified via SHA-256 hashes stored in `file_hashes.json` using a Trust-On-First-Use approach — tampering with any artifact is detected and raises a `SecurityError` before inference runs.

---

### `src/icd10_validator.py` — Code Extraction & Validation

Extracts and validates raw ICD-10-CM codes from free text using a compiled regex pattern:

```
Pattern: \b([A-TV-Z][0-9]{2})\.?([0-9A-Z]{1,4})?\b
```

| Class / Method | Description |
|---|---|
| `ICD10Validator` | Main class: regex scanner + format validator |
| `.extract_codes(text)` | Returns all unique valid ICD-10 codes in a text block |
| `.validate_code(code)` | Enforces format: alpha letter + 2 digits + optional extension |
| `.normalize_code()` | Standardizes to `LETTER##.EXT` uppercase format |
| `.get_code_info(code)` | Returns chapter, category, extension, billability status |
| `.get_chapter(code)` | Maps first letter to anatomical/pathological chapter name |
| `.analyze_codes(codes)` | Chapter distribution + top-10 category frequency stats |
| `extract_icd10_codes()` | Convenience wrapper (no class instantiation needed) |

**ICD-10 Chapter Map (25 chapters):**

| Letters | Chapter |
|---|---|
| A, B | Infectious & Parasitic Diseases |
| C, D | Neoplasms / Blood Diseases |
| E | Endocrine / Metabolic |
| F | Mental & Behavioral Disorders |
| G | Nervous System |
| H | Eye & Ear |
| I | Circulatory System |
| J | Respiratory System |
| K | Digestive System |
| M | Musculoskeletal |
| N | Genitourinary |
| R | Symptoms & Signs |
| Z | Factors Influencing Health |

---

### `src/pdf_extractor.py` — Hybrid PDF Text Extraction

A two-tier extraction engine designed for clinical PDF documents, with production-grade robustness for Google Colab free tier:

| Class / Method | Description |
|---|---|
| `HybridPDFExtractor` | Two-tier controller: native first, OCR fallback |
| `.extract_text_native()` | Fast `pdfplumber` native text layer extraction |
| `.extract_text_ocr()` | Tesseract OCR for scanned/image-based PDFs (with 3-attempt retry) |
| `.smart_extract()` | Intelligently selects best method; auto-falls back to OCR if quality fails |
| `.is_text_quality_acceptable()` | Rejects garbage text: checks char ratio, word count, avg word length |
| `._determine_document_type()` | Classifies form type: Home Health, PT, OT, Speech Therapy, Other |
| `.process_directory()` | Bulk batch extraction with checkpoint save/resume and progress bar |
| `process_pdfs_batch()` | Colab-friendly one-liner wrapper |

**Text Quality Heuristics:**
- Minimum `50` characters
- Max garbage character ratio `30%`
- Minimum `10` words
- Average word length between `2–20` characters

**Colab Optimizations:**
- `gc.collect()` after every OCR page to free RAM
- Checkpoint CSV saved every `N` documents (default: 50)
- Resume logic skips already-processed files on restart

---

### `streamlit_app/app.py` — Web Application

A 3-step wizard UI built with Streamlit:

| Step | What It Does |
|---|---|
| **① Input** | Accept clinical text (free-form), PDF upload (≤4MB), or a pre-loaded demo case |
| **② Preview** | Display extracted text with character count & source badge; user verifies before analysis |
| **③ Results** | Primary diagnosis shown large; all predictions listed with confidence %; copyable code string |

**Terminal Animation:** During inference, a fake console (`render_terminal()`) animates sequential processing steps ("Tokenizing clinical entities...", "Applying attention layers [2/3]...") with a blinking cursor and green checkmarks — giving users meaningful visual feedback while the model runs.

**Security in the UI:**
- All user text rendered through `html.escape()` to prevent XSS
- Rate limiting enforced before every analysis call
- PDF files validated for MIME type and size before extraction

---

### `streamlit_app/security.py` — Security Middleware

| Component | Role |
|---|---|
| `InputValidator.validate_text_input()` | Scans for XSS/injection patterns; enforces payload size limits |
| `InputValidator.validate_file()` | Validates PDF MIME type and file size (max 4MB) |
| `SessionSecurity.init_session()` | Initializes anti-hijacking session metadata |
| `secure_analysis_check()` | Per-session rate limiter to prevent inference abuse / DoS |
| `inject_security_headers()` | Injects `noindex` robots meta tag and related headers at page load |

---

### `streamlit_app/icd10_descriptions.py` — Code Metadata

Provides three lookup functions used throughout the UI:
- `get_code_description(code)` → Human-readable diagnosis name
- `get_code_color(code)` → Hex color for UI badges (chapter-based)
- `get_chapter_name(code)` → Anatomical system chapter label

---

### `streamlit_app/case_data.py` — Demo Cases

Pre-loaded synthetic clinical case bank with realistic multi-diagnosis discharge summaries. Powers the "Try a Demo" selector on the landing page, letting users test NeuroCode without needing a real medical document.

---

### `streamlit_app/styles.css` — Custom Dark Theme UI

14KB of hand-crafted CSS providing:
- Near-black background (`#080808`)
- `JetBrains Mono` monospace font for terminal aesthetics
- `smoothRise` keyframe animation for staggered content entrance
- `terminalBlink` cursor animation
- Ghost card components for the PDF and demo input blocks
- Fade-in confidence-opacity scaling for lower-ranked predictions

---

## 🚀 Getting Started

### Prerequisites

```bash
# Ubuntu / Debian (for OCR support)
sudo apt install tesseract-ocr poppler-utils

# Python 3.10+
python -m pip install --upgrade pip
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/IshwarNotFound/NeuroCode.git
cd NeuroCode

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Model Artifacts

The trained model artifacts are **not committed to git** (large files). Place them at:

```
Downloaded files/ICD10_Project/
├── models/
│   └── icd10_cnn_latest.pt
└── data/train_test_split/
    ├── vocabulary.pkl
    ├── label_encoder.pkl
    └── preprocessing_summary.json
```

> Refer to `ICD-10 Model Training.md` for the full data prep + training pipeline.

### Run the Web App

```bash
streamlit run streamlit_app/app.py
```

Navigate to [http://localhost:8501](http://localhost:8501).

---

## 🧑‍💻 Usage Examples

### Python API — Single Prediction

```python
from src.model_inference import predict_icd10

clinical_note = """
Patient is a 72-year-old male presenting with type 2 diabetes mellitus,
hypertension, congestive heart failure, and COPD. Reports low back pain
and a history of falls. TSH elevated — hypothyroidism suspected.
"""

predictions = predict_icd10(clinical_note, top_k=10)

for pred in predictions:
    print(f"[{pred['code']}] {pred['description']:<52} {pred['confidence']:.0%}")
```

**Example Output:**
```
[E11.9 ] Type 2 diabetes mellitus, without complications     94%
[I10   ] Essential (primary) hypertension                    87%
[I50.32] Chronic diastolic (congestive) heart failure        83%
[J44.9 ] Chronic obstructive pulmonary disease               91%
[M54.5 ] Low back pain                                       76%
[Z91.81] History of falling                                  80%
[E03.9 ] Hypothyroidism, unspecified                         72%
```

### Batch PDF Processing (Google Colab)

```python
from src.pdf_extractor import process_pdfs_batch

df = process_pdfs_batch(
    directory='/content/drive/MyDrive/clinical_pdfs/',
    output_csv='extracted_notes.csv',
    checkpoint_interval=50      # Save every 50 docs to survive Colab restarts
)

print(df[['filename', 'extraction_method', 'num_codes', 'success']].head(10))
```

### ICD-10 Code Extraction from Text

```python
from src.icd10_validator import ICD10Validator

note = "Diagnoses: I10 - Essential Hypertension, E11.9 - T2DM, J44.9 - COPD, M54.5 - LBP"

validator = ICD10Validator()
codes = validator.extract_codes(note)
# → ['I10', 'E11.9', 'J44.9', 'M54.5']

for code in codes:
    info = validator.get_code_info(code)
    print(f"{code} | {info['chapter_name']} | Billable: {info['is_billable']}")
```

---

## 🏥 Supported ICD-10 Domains

| Clinical Domain | Example Codes Covered |
|---|---|
| **Cardiovascular** | I10 (HTN) · I50.32 (CHF) · I25.10 (CAD) · I48.0 (A-Fib) · I70.0 (Atherosclerosis) |
| **Metabolic / Endocrine** | E11.9 (T2DM) · E11.42 (Diabetic Neuropathy) · E78.5 (Hyperlipidemia) · E03.9 (Hypothyroidism) · E55.9 (Vit D Deficiency) |
| **Musculoskeletal** | M54.5 (LBP) · M17.00 (Knee OA) · M81.0 (Osteoporosis) · M10.33 (Gout) · M62.81 (Muscle Weakness) |
| **Respiratory** | J44.9 (COPD) · G47.33 (Sleep Apnea) |
| **Renal** | N18.2–N18.4 (CKD Stage 2–4) · I13.0 (Hypertensive CKD) |
| **Neurological** | G30.1 (Alzheimer's) · G89.29 (Chronic Pain) |
| **Mental Health** | F32.A (Depression) · F41.1 (Anxiety) |
| **Urinary** | N39.0 (UTI) · N40.0 (BPH / Prostate) |
| **Falls & Mobility** | Z91.81 (Fall History) · R26.81 (Unsteady Gait) · R26.2 (Gait Disturbance) |
| **Gastrointestinal** | K21.9 (GERD / Reflux) |

---

## 🔐 Security Architecture

NeuroCode applies defense-in-depth across every layer:

| Layer | Mechanism |
|---|---|
| **Model Integrity** | SHA-256 TOFU verification on `.pt` and `.pkl` files at every load |
| **Input Sanitization** | XSS / injection pattern regex scan before processing |
| **Render Safety** | `html.escape()` on all user content before HTML rendering |
| **File Validation** | MIME type + size enforcement on PDF uploads (max 4MB) |
| **Rate Limiting** | Per-session request throttling prevents inference abuse |
| **Session Security** | Anti-hijacking metadata initialized on every session start |
| **Dependency Hygiene** | `pypdf` replaces deprecated `PyPDF2` (CVE-2023-36464 mitigated) |

---

## 📋 Full Requirements

```
# ML / Deep Learning
pytorch · tensorflow>=2.16.1 · scikit-learn>=1.4.0 · numpy>=1.26.4

# NLP
nltk>=3.9.0 · gensim>=4.3.2

# PDF Processing
pdfplumber>=0.11.0 · pypdf>=4.3.0 · pdf2image>=1.17.0 · pytesseract>=0.3.10

# Training Utilities
iterative-stratification>=0.1.7 · pandas>=2.2.0 · tqdm>=4.66.0

# Visualization
matplotlib>=3.8.0 · seaborn>=0.13.0

# System (install via apt)
tesseract-ocr · poppler-utils
```

---

## 🗺️ Roadmap

- [x] TextCNN multi-label classifier
- [x] Hybrid PDF extraction (native + OCR)
- [x] Rule-based keyword boosting layer
- [x] Streamlit 3-step wizard UI
- [x] Security hardening (SHA-256, XSS, rate limiting, session security)
- [x] Colab-optimized batch processing with checkpointing
- [ ] Upgrade to BioBERT / ClinicalBERT transformer backbone
- [ ] FHIR R4 JSON export support
- [ ] Batch CSV upload in the web UI
- [ ] Confidence calibration via temperature scaling
- [ ] Docker containerization & Streamlit Cloud deployment
- [ ] Automated model retraining pipeline

---

## 📖 Documentation Files

| File | Contents |
|---|---|
| `ICD-10 Model Training.md` | Full CNN training pipeline — data prep, tokenization, training loop, evaluation |
| `Fixing Model Bias-2.md` | Model bias analysis, per-class performance, and mitigation strategies |
| `gameplan.md` | Project roadmap, architecture decisions, sprint notes |

---

## ⚠️ Disclaimer

NeuroCode is an **AI-assisted coding research tool** for educational and experimental purposes. It is **not** a certified medical device and must not replace licensed medical coders or clinical judgment. Always verify all ICD-10 assignments with qualified healthcare professionals before billing or clinical use.

---

## 👤 Author

**Ishwar**
- GitHub: [@IshwarNotFound](https://github.com/IshwarNotFound)
- Repository: [github.com/IshwarNotFound/NeuroCode](https://github.com/IshwarNotFound/NeuroCode)

---

<div align="center">

*Built with PyTorch · Streamlit · Python · ❤️*

**⚫ NeuroCode** — *Where Neural Networks Meet Clinical Intelligence*

</div>
