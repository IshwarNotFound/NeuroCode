"""
NeuroCode - Neural Networks for Medical Coding
Secure AI-Powered ICD-10 Auto-Coding System
"""

import streamlit as st
import sys
import time
import random
import html
from pathlib import Path
import os

# Add parent directory to path for imports - FIXED PATH RESOLUTION
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Debug: Print path info
# print(f"PROJECT_ROOT: {PROJECT_ROOT}")
# print(f"sys.path[0]: {sys.path[0]}")

# Import Vocabulary for pickle loading
from src.vocabulary import Vocabulary

# Import helpers
from streamlit_app.case_data import get_case, get_case_titles
from streamlit_app.icd10_descriptions import get_code_color, get_chapter_name

# Import security module
from streamlit_app.security import (
    InputValidator, SessionSecurity, 
    secure_analysis_check, inject_security_headers
)

# Page Configuration
st.set_page_config(
    page_title="NeuroCode | AI Medical Coding",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject security headers
inject_security_headers()

# Load CSS
def load_css():
    css_path = Path(__file__).parent / "styles.css"
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Initialize secure session
SessionSecurity.init_session()

# Session State
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""
if 'source_type' not in st.session_state:
    st.session_state.source_type = None
if 'predictions' not in st.session_state:
    st.session_state.predictions = None

# Navigation
def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

def reset_wizard():
    st.session_state.step = 1
    st.session_state.extracted_text = ""
    st.session_state.predictions = None

# Analysis with security checks
def run_analysis(text):
    # Rate limiting check
    allowed, error = secure_analysis_check()
    if not allowed:
        st.error(f"⚠️ {error}")
        return []
    
    # Input validation
    is_valid, error, sanitized_text = InputValidator.validate_text_input(text)
    if not is_valid:
        st.error(f"⚠️ {error}")
        return []
    
    try:
        st.info("📡 Loading model...")
        from src.model_inference import predict_icd10
        
        st.info(f"📝 Analyzing {len(sanitized_text)} characters of text...")
        
        # Get predictions using sanitized text
        predictions = predict_icd10(sanitized_text, top_k=50)
        
        st.success(f"✅ Model returned {len(predictions)} predictions!")
        
        # Show top 3 confidence scores for debugging
        if predictions:
            top_3_conf = [f"{p['confidence']:.3f}" for p in predictions[:3]]
            st.info(f"Top 3 confidences: {', '.join(top_3_conf)}")
        
        # Add evidence (using original text for display, sanitized)
        words = sanitized_text.split()
        for pred in predictions:
            if len(words) > 3:
                evidence_words = random.sample(words, min(4, len(words)))
                pred['evidence'] = " ".join(evidence_words)
            else:
                pred['evidence'] = "Clinical pattern match"


        # Return top 10 regardless of confidence
        result = predictions[:10]
        st.success(f"📊 Returning {len(result)} codes to display")
        return result
        
    except Exception as e:
        st.error(f"❌ Analysis Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

# ==================== WIZARD ====================

def render_step_indicator():
    steps = ["Input", "Preview", "Results"]
    
    cols = st.columns(len(steps))
    for i, label in enumerate(steps):
        step_num = i + 1
        with cols[i]:
            if step_num == st.session_state.step:
                st.markdown(f"<div style='text-align: center; font-size: 1.2rem; color: #68BA7F; font-weight: bold;'>● {label}</div>", unsafe_allow_html=True)
            elif step_num < st.session_state.step:
                st.markdown(f"<div style='text-align: center; font-size: 1.2rem; color: #68BA7F;'>✓ {label}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center; font-size: 1.2rem; color: #475569;'>○ {label}</div>", unsafe_allow_html=True)
    st.markdown("---")

def step_1_input():
    # ===== CLEAN HERO — Title + Tagline only =====
    st.markdown("""
    <div class="hero-wrapper">
        <div class="hero-glow"></div>
        <h1 class="hero-title">NeuroCode</h1>
        <p class="hero-subtitle">AI-Powered ICD-10 Medical Coding</p>
        <p class="hero-tagline">Paste a clinical note and get instant diagnosis codes</p>
    </div>
    """, unsafe_allow_html=True)

    # ===== PRIMARY ACTION — Text Input (the one thing to do) =====
    st.markdown("""
    <div class="primary-card">
        <div class="primary-card-label">📋 Paste your clinical text</div>
    </div>
    """, unsafe_allow_html=True)
    
    text_input = st.text_area("", height=160, placeholder="Paste your discharge summary, clinical note, or medical report here...\n\nExample: Patient is a 65-year-old male admitted with acute chest pain radiating to the left arm. History of hypertension and type 2 diabetes mellitus...", label_visibility="collapsed", key="text_input_field")
    
    if st.button("✨  ANALYZE WITH AI", key="btn_text", type="primary", use_container_width=True):
        if len(text_input) > 10:
            st.session_state.extracted_text = text_input
            st.session_state.source_type = 'text'
            next_step()
            st.rerun()
        else:
            st.warning("Please enter at least a few sentences of clinical text")

    # ===== OR DIVIDER =====
    st.markdown("""
    <div class="or-divider">
        <div class="or-line"></div>
        <span class="or-text">or</span>
        <div class="or-line"></div>
    </div>
    """, unsafe_allow_html=True)

    # ===== SECONDARY OPTIONS — PDF & Demo side by side =====
    col_pdf, col_demo = st.columns(2, gap="large")

    with col_pdf:
        st.markdown("""
        <div class="secondary-card">
            <span class="secondary-icon">📄</span>
            <span class="secondary-label">Upload a PDF</span>
        </div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=['pdf'], label_visibility="collapsed", key="pdf_upload")
        if uploaded_file:
            if uploaded_file.size > 4 * 1024 * 1024:
                st.error("File too large! Max 4MB allowed.")
            else:
                with st.spinner("Extracting text from PDF..."):
                    try:
                        from src.pdf_extractor import HybridPDFExtractor
                        import tempfile
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        extractor = HybridPDFExtractor()
                        result = extractor.smart_extract(tmp_path)
                        
                        if result.success:
                            st.session_state.extracted_text = result.full_text
                            st.session_state.source_type = 'pdf'
                            next_step()
                            st.rerun()
                        else:
                            st.error(f"Failed: {result.error_message}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    with col_demo:
        st.markdown("""
        <div class="secondary-card">
            <span class="secondary-icon">🧪</span>
            <span class="secondary-label">Try a demo case</span>
        </div>
        """, unsafe_allow_html=True)
        case_titles = get_case_titles()
        options = ["-- Select a case --"] + case_titles
        selected = st.selectbox("", options, index=0, label_visibility="collapsed", key="case_sel")
        if st.button("LOAD CASE", key="btn_demo", type="primary", use_container_width=True):
            if selected != "-- Select a case --":
                selected_idx = options.index(selected) - 1
                case_data = get_case(selected_idx + 1)
                st.session_state.extracted_text = case_data['text']
                st.session_state.source_type = 'demo'
                next_step()
                st.rerun()
            else:
                st.warning("Please select a case first")


def step_2_preview():
    # Sleek header without brain symbol
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h1 style="font-size: 2.2rem; margin-bottom: 0.3rem;
                   background: linear-gradient(135deg, #00D68F 0%, #00B4D8 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   background-clip: text;">
            📝 Document Preview
        </h1>
        <p style="font-size: 0.9rem; color: #5a6577;">Review your content before AI analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    text_len = len(st.session_state.extracted_text)
    source = st.session_state.source_type.upper()
    
    # Stats card
    st.markdown(f"""
    <div style="background: linear-gradient(145deg, rgba(0, 214, 143, 0.08) 0%, rgba(0, 180, 216, 0.05) 100%); 
                border: 1px solid rgba(0, 214, 143, 0.2); border-radius: 16px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
                display: flex; justify-content: space-around; align-items: center;">
        <div style="text-align: center;">
            <div style="font-size: 1.8rem; font-weight: 900; color: #00D68F;">{source}</div>
            <div style="font-size: 0.85rem; color: #a0aec0;">Source</div>
        </div>
        <div style="width: 1px; height: 40px; background: rgba(255,255,255,0.06);"></div>
        <div style="text-align: center;">
            <div style="font-size: 1.8rem; font-weight: 900; color: #00B4D8;">{text_len:,}</div>
            <div style="font-size: 0.85rem; color: #a0aec0;">Characters</div>
        </div>
        <div style="width: 1px; height: 40px; background: rgba(255,255,255,0.06);"></div>
        <div style="text-align: center;">
            <div style="font-size: 1.8rem; font-weight: 900; color: #6fffc4;">READY</div>
            <div style="font-size: 0.85rem; color: #a0aec0;">Status</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if text_len < 50:
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.15); border: 2px solid rgba(239, 68, 68, 0.5); 
                    border-radius: 12px; padding: 1rem; text-align: center;">
            <span style="color: #fca5a5; font-size: 1rem;">
                Document too short - need at least 50 characters.
            </span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Back to Input", type="secondary", use_container_width=True):
            prev_step()
            st.rerun()
        st.stop()

    # Show full document directly (no expander, no duplicate)
    st.markdown(f"""
    <div style="background: rgba(17, 22, 32, 0.8); border: 1px solid rgba(255,255,255,0.06); 
                border-radius: 14px; padding: 1.25rem; margin-bottom: 1.5rem;">
        <div style="font-size: 1rem; font-weight: 600; color: #f0f2f5; margin-bottom: 0.75rem;">Document Content</div>
        <div style="background: rgba(7, 9, 15, 0.8); border-radius: 10px; padding: 1.25rem; 
                    max-height: 300px; overflow-y: auto;">
            <p style="color: #e2e8f0; font-size: 0.95rem; line-height: 1.7; margin: 0; white-space: pre-wrap;">
{st.session_state.extracted_text}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons at bottom
    col_back, col_analyze = st.columns([1, 2])
    with col_back:
        if st.button("Back", type="secondary", use_container_width=True):
            prev_step()
            st.rerun()
    with col_analyze:
        if st.button("ANALYZE WITH AI", type="primary", use_container_width=True):
            with st.spinner("Analyzing..."):
                preds = run_analysis(st.session_state.extracted_text)
                if preds is not None:
                    st.session_state.predictions = preds
                    next_step()
                    st.rerun()

def step_3_results():
    # NeuroCode branded results header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="font-size: 2rem; margin-bottom: 0.3rem;">✅</div>
        <h1 style="font-size: 2rem; margin-bottom: 0.25rem; color: #ffffff;">NeuroCode Analysis Complete</h1>
        <p style="font-size: 0.95rem; color: #94a3b8;">AI-Powered ICD-10 Code Predictions</p>
    </div>
    """, unsafe_allow_html=True)
    
    preds = st.session_state.predictions
    if not preds or len(preds) == 0:
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.15); border: 2px solid rgba(245, 158, 11, 0.5); 
                    border-radius: 16px; padding: 2rem; text-align: center;">
            <div style="font-size: 1.3rem; color: #fcd34d; font-weight: 700;">No Codes Detected</div>
            <p style="color: #94a3b8; margin-top: 0.5rem;">Try one of the demo cases for best results</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # PRIMARY DIAGNOSIS - Compact but prominent
    primary = preds[0]
    conf_pct = int(primary['confidence'] * 100)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #00D68F 0%, #00B4D8 100%); 
                border-radius: 18px; padding: 2rem; margin-bottom: 1.5rem; text-align: center;">
        <div style="font-size: 0.85rem; color: rgba(7,9,15,0.6); text-transform: uppercase; 
                    font-weight: 700; letter-spacing: 2px; margin-bottom: 0.75rem;">Primary Diagnosis</div>
        <div style="font-size: 3rem; font-weight: 900; color: #07090f; line-height: 1; margin-bottom: 0.5rem;">
            {primary['code']}
        </div>
        <div style="font-size: 1.1rem; color: rgba(7,9,15,0.8); margin-bottom: 1rem;">
            {primary['description']}
        </div>
        <div style="display: inline-block; background: rgba(7,9,15,0.15); border-radius: 50px; padding: 0.5rem 1.5rem;">
            <span style="font-size: 1.5rem; font-weight: 900; color: #07090f;">{conf_pct}%</span>
            <span style="font-size: 0.9rem; color: rgba(7,9,15,0.7);"> confidence</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats row
    total_codes = len(preds)
    high_conf = sum(1 for p in preds if p['confidence'] >= 0.5)
    
    st.markdown(f"""
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
        <div style="flex: 1; background: rgba(0, 214, 143, 0.06); border: 1px solid rgba(0, 214, 143, 0.2); 
                    border-radius: 12px; padding: 1rem; text-align: center;">
            <div style="font-size: 2rem; font-weight: 800; color: #00D68F;">{total_codes}</div>
            <div style="font-size: 0.8rem; color: #a0aec0;">Total Codes</div>
        </div>
        <div style="flex: 1; background: rgba(0, 180, 216, 0.06); border: 1px solid rgba(0, 180, 216, 0.2); 
                    border-radius: 12px; padding: 1rem; text-align: center;">
            <div style="font-size: 2rem; font-weight: 800; color: #00B4D8;">{high_conf}</div>
            <div style="font-size: 0.8rem; color: #a0aec0;">High Confidence</div>
        </div>
        <div style="flex: 1; background: rgba(124, 58, 237, 0.06); border: 1px solid rgba(124, 58, 237, 0.2); 
                    border-radius: 12px; padding: 1rem; text-align: center;">
            <div style="font-size: 2rem; font-weight: 800; color: #a78bfa;">{conf_pct}%</div>
            <div style="font-size: 0.8rem; color: #a0aec0;">Best Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Section header
    st.markdown("""
    <div style="font-size: 1.1rem; font-weight: 700; color: #f0f2f5; margin-bottom: 0.75rem; 
                padding-bottom: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.06);">
        All Predicted Codes
    </div>
    """, unsafe_allow_html=True)

    # COMPACT CODE LIST - one line each
    code_rows = []
    for i, code in enumerate(preds, 1):
        conf = code['confidence']
        conf_pct = int(conf * 100)
        
        if conf >= 0.6:
            color = "#10b981"
        elif conf >= 0.35:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        
        code_rows.append(f"""
        <div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem; 
                    background: rgba(17, 22, 32, 0.6); border-radius: 10px; margin-bottom: 0.5rem;
                    border-left: 3px solid {color};">
            <div style="min-width: 30px; font-size: 0.85rem; color: #5a6577;">#{i}</div>
            <div style="min-width: 100px; font-size: 1.2rem; font-weight: 800; color: #f0f2f5;">{code['code']}</div>
            <div style="flex: 1; font-size: 0.95rem; color: #a0aec0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {code['description']}
            </div>
            <div style="min-width: 60px; text-align: right; font-size: 1rem; font-weight: 700; color: {color};">
                {conf_pct}%
            </div>
        </div>
        """)
    
    st.markdown("".join(code_rows), unsafe_allow_html=True)
    
    # Code list for copying
    code_list = ", ".join([p['code'] for p in preds])
    st.markdown(f"""
    <div style="background: rgba(7, 9, 15, 0.8); border: 1px solid rgba(255,255,255,0.06); 
                border-radius: 10px; padding: 0.75rem 1rem; margin-top: 1rem;
                font-family: monospace; font-size: 0.9rem; color: #00D68F;">
        {code_list}
    </div>
    """, unsafe_allow_html=True)
    
    # New Analysis button at bottom
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    if st.button("NEW ANALYSIS", type="primary", use_container_width=True):
        reset_wizard()
        st.rerun()

# ==================== MAIN ====================

def main():
    # No step indicator - cleaner look
    if st.session_state.step == 1:
        step_1_input()
    elif st.session_state.step == 2:
        step_2_preview()
    elif st.session_state.step == 3:
        step_3_results()

if __name__ == "__main__":
    main()
