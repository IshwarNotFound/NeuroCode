"""
NeuroCode - Neural Networks for Medical Coding
Secure AI-Powered ICD-10 Auto-Coding System

This module serves as the primary entry point for the Streamlit web application.
It manages the user interface, session state for the multi-step wizard, 
file uploads, layout rendering, and coordinates with the security module 
and the backend model inference scripts.
"""

import streamlit as st
import sys
import time
import random
import html
from pathlib import Path
import os
import logging

# Initialize module-level logger for application events
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Path Resolution
# Ensure the parent directory (project root) is in the Python path so that
# imports from the `src` and `config` packages work correctly regardless of 
# where this script is executed from.
# -------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import Vocabulary. It MUST be imported before unpickling the model vocabulary
# to ensure the unpickler can find the exact class definition.
from src.vocabulary import Vocabulary

# Import UI helpers and synthetic data
from streamlit_app.case_data import get_case, get_case_titles
from streamlit_app.icd10_descriptions import get_code_color, get_chapter_name

# Import custom security middleware for input validation, rate limiting, and XSS defense
from streamlit_app.security import (
    InputValidator, SessionSecurity, 
    secure_analysis_check, inject_security_headers
)

# -------------------------------------------------------------------------
# Page Configuration
# Set the initial layout, title, and favicon. 'centered' layout is used 
# to maintain a clean, focused, minimalist design aesthetic.
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="NeuroCode | AI",
    page_icon="⚫",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inject security headers (like noindex robots tag) early in page load
inject_security_headers()

def load_css():
    """
    Reads the custom styles.css file and injects it into the Streamlit app.
    This provides all the custom UI components, hover effects, and typography.
    """
    css_path = Path(__file__).parent / "styles.css"
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Apply CSS immediately
load_css()

# Initialize session persistence tracking to prevent timeout/hijacking
SessionSecurity.init_session()

# -------------------------------------------------------------------------
# Session State Variables
# Streamlit re-runs the entire script on every interaction. We use 
# st.session_state to persist data across these re-runs.
# -------------------------------------------------------------------------
if 'step' not in st.session_state:
    st.session_state.step = 1                # Tracks current wizard page (1, 2, or 3)
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""     # Holds the medical test to analyze
if 'source_type' not in st.session_state:
    st.session_state.source_type = None      # Tracks origin ('text', 'pdf', or 'demo')
if 'predictions' not in st.session_state:
    st.session_state.predictions = None      # Stores the final array of ICD-10 prediction objects

# -------------------------------------------------------------------------
# Navigation Helpers
# Functions to move back and forth through the application wizard states.
# -------------------------------------------------------------------------
def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

def reset_wizard():
    st.session_state.step = 1
    st.session_state.extracted_text = ""
    st.session_state.predictions = None

# -------------------------------------------------------------------------
# Core Analysis Logic
# This function acts as the bridge between the UI and the ML model.
# It also handles security scanning, rate limiting, and the terminal animation.
# -------------------------------------------------------------------------
def run_analysis(text):
    # 1. Security Check: Enforce rate limiting to prevent abuse/dos
    allowed, error = secure_analysis_check()
    if not allowed:
        st.error(f"⚠️ {error}")
        return []
    
    # 2. Security Check: Validate payload size and hunt for XSS/injection patterns
    is_valid, error, sanitized_text = InputValidator.validate_text_input(text)
    if not is_valid:
        st.error(f"⚠️ {error}")
        return []
    
    # 3. Terminal Animation UI System
    # Creates an empty placeholder and sequentially updates it to mimic a booting console.
    terminal = st.empty()
    completed_lines = []
    
    def render_terminal(active_line=""):
        """Renders the fake terminal UI, stacking completed lines and blinking an active cursor."""
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
    
    # Define the sequence of fake processing steps for visual feedback
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
    
    # Execute terminal animation loops with artificial delays
    render_terminal("Initializing neural network...")
    time.sleep(0.5)
    completed_lines.append("Neural network initialized")
    
    for step_text in steps:
        render_terminal(step_text)
        time.sleep(random.uniform(0.2, 0.5))
        completed_lines.append(step_text.replace("...", ""))
    
    render_terminal("Compiling results...")
    time.sleep(0.3)
    
    # 4. Actual Model Inference
    try:
        from src.model_inference import predict_icd10
        # Call the singleton predictor and get top 50 codes
        # Evidence is now returned directly from the inference engine's keyword matching layer
        predictions = predict_icd10(sanitized_text, top_k=50)
        
        terminal.empty()  # Clear the terminal UI once done

        # Return only the top 10 most confident predictions for the UI
        return predictions[:10]
        
    except Exception as e:
        terminal.empty()
        logger.exception("Analysis failed during model inference")
        st.error("Analysis failed. Please try again or use a demo case.")
        return None

# ==================== WIZARD UI DEFINITIONS ====================

def render_step_indicator():
    """Renders the top navigation dots indicating Input -> Preview -> Results"""
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
    """
    Step 1: The landing page.
    Allows user to provide data via free text, PDF upload, or pre-loaded demo selection.
    """
    # HERO section — Branding block
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">NeuroCode.</h1>
        <p class="hero-subtitle">Clinical Text to ICD-10. Powered by Deep Learning.</p>
    </div>
    """, unsafe_allow_html=True)

    # PRIMARY INPUT — Free text field
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
            st.rerun()  # Forces immediate layout update
        else:
            st.warning("Please enter at least a few sentences of clinical text.")

    # Visual OR DIVIDER
    st.markdown('<div class="minimal-divider">or</div>', unsafe_allow_html=True)

    # SECONDARY INPUTS — PDF & Demo side by side
    col_pdf, col_demo = st.columns(2, gap="large")

    with col_pdf:
        # PDF Upload Block
        st.markdown("""
        <div class="ghost-card">
            <span class="ghost-icon">📄</span>
            <div style="font-size: 0.9rem; font-weight: 500; color: #ccc !important;">Upload PDF</div>
            <div style="font-size: 0.75rem; color: #555 !important;">Max 4MB · Medical records</div>
        </div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=['pdf'], label_visibility="collapsed", key="pdf_upload")
        
        if uploaded_file:
            # Validate PDF size and MIME type
            is_valid, file_error = InputValidator.validate_file(uploaded_file)
            if not is_valid:
                st.error(f"⚠️ {file_error}")
            else:
                with st.spinner("Extracting text..."):
                    tmp_path = None
                    try:
                        # Streamlit passes files as bytes in memory. We must save them to disk
                        # temporarily so pdfplumber/pytesseract can read them.
                        from src.pdf_extractor import HybridPDFExtractor
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        # Use the hybrid native/OCR extractor
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
                        # Always clean up the temporary PDF file to prevent disk fill-up
                        if tmp_path and os.path.exists(tmp_path):
                            os.unlink(tmp_path)

    with col_demo:
        # Demo Cases Block
        st.markdown("""
        <div class="ghost-card">
            <span class="ghost-icon">⚡</span>
            <div style="font-size: 0.9rem; font-weight: 500; color: #ccc !important;">Try a Demo</div>
            <div style="font-size: 0.75rem; color: #555 !important;">Pre-loaded clinical cases</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Populate selectbox with titles from case_data.py
        case_titles = get_case_titles()
        options = ["Choose a clinical case"] + case_titles
        selected = st.selectbox("", options, index=0, label_visibility="collapsed", key="case_sel")
        
        if st.button("Load Case", key="btn_demo", use_container_width=True):
            if selected != "Choose a clinical case":
                selected_idx = options.index(selected) - 1
                # Retrieve the full text for the selected case
                case_data = get_case(selected_idx + 1)
                st.session_state.extracted_text = case_data['text']
                st.session_state.source_type = 'demo'
                next_step()
                st.rerun()
            else:
                st.warning("Please select a case first.")


def step_2_preview():
    """
    Step 2: Preview the Extracted Text.
    Allows user to verify the input before sending it to the model. 
    Crucial for PDF uploads to ensure OCR worked.
    """
    # Create an empty placeholder container that can be cleared when the terminal boots up.
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

        # Display metadata
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

        # Minimum length validation 
        if text_len < 50:
            st.warning("Document too short — need at least 50 characters.")
            if st.button("Back", use_container_width=True):
                prev_step()
                st.rerun()
            st.stop() # Halts execution and prevents rendering the Analyze button

        # Text Display Box — ESCAPED for XSS prevention using html.escape
        st.markdown(f"""
        <div style="background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; animation: smoothRise 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
            <p style="color: #a1a1aa !important; font-size: 0.95rem; line-height: 1.7; max-height: 350px; overflow-y: auto; white-space: pre-wrap; margin: 0;">
{html.escape(st.session_state.extracted_text)}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Bottom buttons
        col_back, col_analyze = st.columns([1, 3])
        with col_back:
            if st.button("Back", use_container_width=True):
                prev_step()
                st.rerun()
        with col_analyze:
            analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)
    
    # State transition logic: When Analyze is clicked, clear the preview UI instantly
    # and swap into the terminal animation mode entirely.
    if analyze_clicked:
        preview_container.empty()
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem; margin-top: 3rem; animation: smoothRise 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
            <h2 style="font-weight: 600; color: #ffffff !important;">Processing</h2>
            <p style="color: #555 !important;">Neural network inference in progress.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Trigger the blocking prediction pipeline
        preds = run_analysis(st.session_state.extracted_text)
        
        if preds is not None:
            # Once ML completes, proceed to final step
            st.session_state.predictions = preds
            next_step()
            st.rerun()


def step_3_results():
    """
    Step 3: Render the Output.
    Displays the primary predicted diagnosis prominently, followed by a list 
    of secondary diagnoses and their confidence scores.
    """
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

    # PRIMARY DIAGNOSIS — Extract the highest confidence result and render it huge.
    primary = preds[0]
    conf_pct = int(primary['confidence'] * 100)
    primary_evidence = html.escape(primary.get('evidence', 'CNN pattern match'))

    st.markdown(f"""
    <div style="border: 1px solid #222; border-radius: 14px; padding: 3rem; margin-bottom: 2rem; text-align: center; animation: smoothRise 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
        <div style="font-size: 0.75rem; color: #555 !important; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1rem;">Primary Diagnosis</div>
        <div style="font-size: 4.5rem; font-weight: 800; color: #ffffff !important; line-height: 1; margin-bottom: 0.5rem; letter-spacing: -0.04em;">
            {html.escape(primary['code'])}
        </div>
        <div style="font-size: 1.1rem; color: #888 !important; margin-bottom: 1rem;">
            {html.escape(primary['description'])}
        </div>
        <div style="font-size: 0.75rem; color: #10b981 !important; margin-bottom: 1.5rem; font-style: italic;">
            Evidence: {primary_evidence}
        </div>
        <div style="display: inline-block; border: 1px solid #333; border-radius: 50px; padding: 0.3rem 1.2rem;">
            <span style="font-size: 0.85rem; color: #aaa !important;">Confidence: </span>
            <span style="font-size: 0.85rem; font-weight: 700; color: #fff !important;">{conf_pct}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ALL PREDICTED CODES — Render the remaining predictions in a compact list format.
    if len(preds) > 1:
        st.markdown('<div style="font-size: 0.8rem; color: #555 !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem;">All Predictions</div>', unsafe_allow_html=True)

        code_rows = []
        for i, code in enumerate(preds[1:], 2):
            conf = code['confidence']
            conf_pct = int(conf * 100)
            
            # Fade out lower-confidence predictions by dropping row opacity
            opacity = max(0.4, conf)

            code_rows.append(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 0; border-bottom: 1px solid #111; animation: smoothRise {0.8 + (i*0.08)}s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
                <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                    <div style="display: flex; align-items: center; gap: 1.5rem;">
                        <div style="font-size: 1.15rem; font-weight: 700; color: #fff !important;">{html.escape(code['code'])}</div>
                        <div style="font-size: 0.9rem; color: #777 !important;">{html.escape(code['description'])}</div>
                    </div>
                    <div style="font-size: 0.7rem; color: #555 !important; font-style: italic; padding-left: 0.1rem;">matched: {html.escape(code.get('evidence', 'CNN pattern match'))}</div>
                </div>
                <div style="font-size: 0.85rem; font-family: monospace; color: rgba(255,255,255,{opacity}) !important;">{conf_pct}%</div>
            </div>
            """)

        st.markdown("".join(code_rows), unsafe_allow_html=True)

    # Copyable code list block (e.g., "Z91.81, I10, E78.5")
    code_list = ", ".join([p['code'] for p in preds])
    st.markdown(f"""
    <div style="background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 8px; padding: 0.75rem 1rem; margin-top: 1.5rem; font-family: monospace; font-size: 0.85rem; color: #666 !important;">
        {html.escape(code_list)}
    </div>
    """, unsafe_allow_html=True)

    # Start over button
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    if st.button("New Analysis", type="primary", use_container_width=True):
        reset_wizard()
        st.rerun()


# ==================== MAIN DISPATCHER ====================

def main():
    """
    Main entry point for the Streamlit application.
    Checks the session state 'step' and routes to the appropriate UI rendering function.
    """
    if st.session_state.step == 1:
        step_1_input()
    elif st.session_state.step == 2:
        step_2_preview()
    elif st.session_state.step == 3:
        step_3_results()

if __name__ == "__main__":
    main()
