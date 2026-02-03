# 🏥 CNN-Based ICD-10 Auto-Coding System

Automated ICD-10 diagnosis code prediction from medical documents using Convolutional Neural Networks.

## 🎯 Project Overview

This system processes medical documents (PT/OT evaluations, Home Health certifications) and automatically predicts relevant ICD-10 diagnosis codes with confidence scores.

**Input**: Medical PDF or clinical text  
**Output**: Top predicted ICD-10 codes with confidence percentages

## 📊 Data

- **831 PDFs** (346 PT/OT + 485 Home Health)
- ~60% require OCR, 40% text-selectable
- All documents contain labeled ICD-10 codes

## 🚀 Quick Start (Google Colab)

### Step 1: Upload Notebook to Colab
Upload `notebooks/1_Setup_and_Data_Extraction.ipynb` to Google Colab.

### Step 2: Configure Paths
Update the paths in Section 1.3 to match your Google Drive:
```python
HOME_HEALTH_PATH = "/content/drive/MyDrive/485/485 DOCS"
PT_OT_PATH = "/content/drive/MyDrive/485/Other Than 485"
```

### Step 3: Run All Cells
The notebook will:
1. Mount Google Drive
2. Install dependencies
3. Extract text from PDFs (with OCR fallback)
4. Extract ICD-10 codes
5. Generate statistics and visualizations

## 📁 Project Structure

```
ICD10_CNN_Project/
├── notebooks/
│   ├── 1_Setup_and_Data_Extraction.ipynb    # Phase 1
│   ├── 2_Text_Preprocessing.ipynb           # Phase 2 (coming)
│   ├── 3_CNN_Training.ipynb                 # Phase 3 (coming)
│   └── 4_Model_Evaluation.ipynb             # Phase 3 (coming)
├── src/
│   ├── __init__.py
│   ├── icd10_validator.py    # ICD-10 code extraction/validation
│   └── pdf_extractor.py      # Hybrid PDF text extraction
├── config/
│   └── config.py             # Configuration settings
├── requirements.txt
└── README.md
```

## 📋 Phases

| Phase | Notebook | Deliverable | Status |
|-------|----------|-------------|--------|
| 1 | Data Extraction | 831 docs processed, ICD-10 codes extracted | ✅ Ready |
| 2 | Preprocessing | Text cleaned, vocabulary built | ⏳ Coming |
| 3 | CNN Training | Model trained, 75%+ F1-score | ⏳ Coming |
| 4 | Evaluation | Performance reports, visualizations | ⏳ Coming |
| 5 | Web Interface | Streamlit app for predictions | ⏳ Coming |

## 🔧 Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

## 📈 Expected Performance

- **F1-Score**: 75-85% (basic CNN), 82-90% (optimized)
- **Top codes**: 85-95% accuracy
- **Rare codes**: 55-65% accuracy

## 👤 Author

Healthcare AI Implementation Team - College Project 2026

## 📝 License

For educational purposes only.
