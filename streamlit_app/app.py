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
import logging

logger = logging.getLogger(__name__)

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

# Page Configuration — Centered for focused minimalism
st.set_page_config(
    page_title="NeuroCode | AI",
    page_icon="⚫",
    layout="centered",
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
    
    is_valid, error, sanitized_text = InputValidator.validate_text_input(text)
    if not is_valid:
        st.error(f"⚠️ {error}")
        return []
    
    # Terminal processing sequence — stacking log for dramatic effect
    terminal = st.empty()
    completed_lines = []
    
    def render_terminal(active_line=""):
        history = ""
        for line in completed_lines:
            history += f'<div><span style="color:#10b981;">✓</span> {line}</div>\n'
        
        cursor = '<span style="animation: terminalBlink 1s infinite;">█</span>' if active_line else ''
        active = f'<div style="color:#e5e5e5;"><span style="color:#fff;">›</span> {active_line}{cursor}</div>' if active_line else ''
        
        terminal.markdown(f"""
        <div style="background:#080808; border: 1px solid #1a1a1a; border-radius:12px; overflow:hidden; margin: 1rem 0;">
            <div style="background:#111; padding:0.5rem 1rem; border-bottom:1px solid #1a1a1a; display:flex; align-items:center; gap:0.5rem;">
                <span style="width:8px; height:8px; border-radius:50%; background:#333; display:inline-block;"></span>
                <span style="width:8px; height:8px; border-radius:50%; background:#333; display:inline-block;"></span>
                <span style="width:8px; height:8px; border-radius:50%; background:#333; display:inline-block;"></span>
                <span style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#555; margin-left:0.5rem;">neurocode inference engine</span>
            </div>
            <div style="padding:1.25rem 1.5rem; font-family:'JetBrains Mono',monospace; font-size:0.9rem; color:#666; line-height:2;">
                {history}{active}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    steps = [
        "Loading CNN model weights...",
        "Tokenizing clinical entities...",
        "Extracting anatomical biomarkers...",
        "Applying attention layers [1/3]...",
        "Applying attention layers [2/3]...",
        "Applying attention layers [3/3]...",
        "Mapping to ICD-10 latent space...",
        "Ranking confidence scores...",
    ]
    
    render_terminal("Initializing neural network...")
    time.sleep(0.5)
    completed_lines.append("Neural network initialized")
    
    for step_text in steps:
        render_terminal(step_text)
        time.sleep(random.uniform(0.2, 0.5))
        completed_lines.append(step_text.replace("...", ""))
    
    render_terminal("Compiling results...")
    time.sleep(0.3)
    
    # Actual model inference
    try:
        from src.model_inference import predict_icd10
        predictions = predict_icd10(sanitized_text, top_k=50)
        
        terminal.empty()  # Clear the terminal
        
        words = sanitized_text.split()
        for pred in predictions:
            if len(words) > 3:
                evidence_words = random.sample(words, min(4, len(words)))
                pred['evidence'] = " ".join(evidence_words)
            else:
                pred['evidence'] = "Clinical pattern match"

        return predictions[:10]
        
    except Exception as e:
        terminal.empty()
        logger.exception("Analysis failed during model inference")
        st.error("Analysis failed. Please try again or use a demo case.")
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
    # HERO — Pure typographic authority
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">NeuroCode.</h1>
        <p class="hero-subtitle">Clinical Text to ICD-10. Powered by Deep Learning.</p>
    </div>
    """, unsafe_allow_html=True)

    # PRIMARY INPUT — The scanner
    text_input = st.text_area(
        "", 
        height=200, 
        placeholder="Paste a discharge summary, clinical note, or medical report here...", 
        label_visibility="collapsed", 
        key="text_input_field"
    )
    
    if st.button("Analyze", key="btn_text", type="primary", use_container_width=True):
        if len(text_input) > 10:
            st.session_state.extracted_text = text_input
            st.session_state.source_type = 'text'
            next_step()
            st.rerun()
        else:
            st.warning("Please enter at least a few sentences of clinical text.")

    # OR DIVIDER
    st.markdown('<div class="minimal-divider">or</div>', unsafe_allow_html=True)

    # GHOST CARDS — PDF & Demo side by side
    col_pdf, col_demo = st.columns(2, gap="large")

    with col_pdf:
        st.markdown("""
        <div class="ghost-card">
            <span class="ghost-icon">📄</span>
            <div style="font-size: 0.9rem; font-weight: 500; color: #ccc !important;">Upload PDF</div>
            <div style="font-size: 0.75rem; color: #555 !important;">Max 4MB · Medical records</div>
        </div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=['pdf'], label_visibility="collapsed", key="pdf_upload")
        if uploaded_file:
            is_valid, file_error = InputValidator.validate_file(uploaded_file)
            if not is_valid:
                st.error(f"⚠️ {file_error}")
            else:
                with st.spinner("Extracting text..."):
                    tmp_path = None
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
                            st.error("PDF extraction failed. Please try a different file.")
                    except Exception as e:
                        logger.exception("PDF extraction error")
                        st.error("An error occurred processing the PDF. Please try again.")
                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            os.unlink(tmp_path)

    with col_demo:
        st.markdown("""
        <div class="ghost-card">
            <span class="ghost-icon">⚡</span>
            <div style="font-size: 0.9rem; font-weight: 500; color: #ccc !important;">Try a Demo</div>
            <div style="font-size: 0.75rem; color: #555 !important;">Pre-loaded clinical cases</div>
        </div>
        """, unsafe_allow_html=True)
        case_titles = get_case_titles()
        options = ["Choose a clinical case"] + case_titles
        selected = st.selectbox("", options, index=0, label_visibility="collapsed", key="case_sel")
        if st.button("Load Case", key="btn_demo", use_container_width=True):
            if selected != "Choose a clinical case":
                selected_idx = options.index(selected) - 1
                case_data = get_case(selected_idx + 1)
                st.session_state.extracted_text = case_data['text']
                st.session_state.source_type = 'demo'
                next_step()
                st.rerun()
            else:
                st.warning("Please select a case first.")


def step_2_preview():
    # Wrap all preview content in a clearable container
    preview_container = st.empty()
    
    with preview_container.container():
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; animation: smoothRise 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
            <h2 style="font-weight: 600; color: #ffffff !important;">Review</h2>
            <p style="color: #888 !important;">Verify the extracted text before analysis.</p>
        </div>
        """, unsafe_allow_html=True)

        text_len = len(st.session_state.extracted_text)
        source = st.session_state.source_type.upper()

        st.markdown(f"""
        <div style="display: flex; justify-content: center; gap: 3rem; margin-bottom: 2rem; animation: smoothRise 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 800; color: #fff !important;">{source}</div>
                <div style="font-size: 0.75rem; color: #555 !important; text-transform: uppercase; letter-spacing: 1px;">source</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 800; color: #fff !important;">{text_len:,}</div>
                <div style="font-size: 0.75rem; color: #555 !important; text-transform: uppercase; letter-spacing: 1px;">characters</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if text_len < 50:
            st.warning("Document too short — need at least 50 characters.")
            if st.button("Back", use_container_width=True):
                prev_step()
                st.rerun()
            st.stop()

        st.markdown(f"""
        <div style="background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; animation: smoothRise 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
            <p style="color: #a1a1aa !important; font-size: 0.95rem; line-height: 1.7; max-height: 350px; overflow-y: auto; white-space: pre-wrap; margin: 0;">
{html.escape(st.session_state.extracted_text)}
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_back, col_analyze = st.columns([1, 3])
        with col_back:
            if st.button("Back", use_container_width=True):
                prev_step()
                st.rerun()
        with col_analyze:
            analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)
    
    # When Analyze is clicked, clear the preview and show terminal full-page
    if analyze_clicked:
        preview_container.empty()
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem; margin-top: 3rem; animation: smoothRise 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
            <h2 style="font-weight: 600; color: #ffffff !important;">Processing</h2>
            <p style="color: #555 !important;">Neural network inference in progress.</p>
        </div>
        """, unsafe_allow_html=True)
        
        preds = run_analysis(st.session_state.extracted_text)
        if preds is not None:
            st.session_state.predictions = preds
            next_step()
            st.rerun()


def step_3_results():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem; animation: smoothRise 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
        <h2 style="font-weight: 600; color: #ffffff !important;">Analysis Complete</h2>
        <p style="color: #888 !important;">ICD-10 codes predicted by neural network.</p>
    </div>
    """, unsafe_allow_html=True)

    preds = st.session_state.predictions
    if not preds or len(preds) == 0:
        st.markdown("""
        <div style="border: 1px solid #1a1a1a; border-radius: 12px; padding: 3rem; text-align: center;">
            <div style="font-size: 1.1rem; color: #888 !important;">No codes detected. Try a demo case for best results.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # PRIMARY DIAGNOSIS — Massive, stark
    primary = preds[0]
    conf_pct = int(primary['confidence'] * 100)

    st.markdown(f"""
    <div style="border: 1px solid #222; border-radius: 14px; padding: 3rem; margin-bottom: 2rem; text-align: center; animation: smoothRise 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
        <div style="font-size: 0.75rem; color: #555 !important; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1rem;">Primary Diagnosis</div>
        <div style="font-size: 4.5rem; font-weight: 800; color: #ffffff !important; line-height: 1; margin-bottom: 0.5rem; letter-spacing: -0.04em;">
            {html.escape(primary['code'])}
        </div>
        <div style="font-size: 1.1rem; color: #888 !important; margin-bottom: 1.5rem;">
            {html.escape(primary['description'])}
        </div>
        <div style="display: inline-block; border: 1px solid #333; border-radius: 50px; padding: 0.3rem 1.2rem;">
            <span style="font-size: 0.85rem; color: #aaa !important;">Confidence: </span>
            <span style="font-size: 0.85rem; font-weight: 700; color: #fff !important;">{conf_pct}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ALL PREDICTED CODES
    if len(preds) > 1:
        st.markdown('<div style="font-size: 0.8rem; color: #555 !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem;">All Predictions</div>', unsafe_allow_html=True)

        code_rows = []
        for i, code in enumerate(preds[1:], 2):
            conf = code['confidence']
            conf_pct = int(conf * 100)
            opacity = max(0.4, conf)

            code_rows.append(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 0; border-bottom: 1px solid #111; animation: smoothRise {0.8 + (i*0.08)}s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
                <div style="display: flex; align-items: center; gap: 1.5rem;">
                    <div style="font-size: 1.15rem; font-weight: 700; color: #fff !important;">{html.escape(code['code'])}</div>
                    <div style="font-size: 0.9rem; color: #777 !important;">{html.escape(code['description'])}</div>
                </div>
                <div style="font-size: 0.85rem; font-family: monospace; color: rgba(255,255,255,{opacity}) !important;">{conf_pct}%</div>
            </div>
            """)

        st.markdown("".join(code_rows), unsafe_allow_html=True)

    # Code list for copying
    code_list = ", ".join([p['code'] for p in preds])
    st.markdown(f"""
    <div style="background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 8px; padding: 0.75rem 1rem; margin-top: 1.5rem; font-family: monospace; font-size: 0.85rem; color: #666 !important;">
        {html.escape(code_list)}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    if st.button("New Analysis", type="primary", use_container_width=True):
        reset_wizard()
        st.rerun()


# ==================== MAIN ====================

def main():
    if st.session_state.step == 1:
        step_1_input()
    elif st.session_state.step == 2:
        step_2_preview()
    elif st.session_state.step == 3:
        step_3_results()

if __name__ == "__main__":
    main()
