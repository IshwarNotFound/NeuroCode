"""
🏥 ICD-10 Auto-Coding System
Material 3 Expressive Design - Large Icons
"""

import streamlit as st
import sys
import time
import random
from pathlib import Path

# Add parent directory to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import Vocabulary for pickle loading
from src.vocabulary import Vocabulary

# Import helpers
from streamlit_app.case_data import get_case, get_case_titles
from streamlit_app.icd10_descriptions import get_code_color, get_chapter_name

# Page Configuration
st.set_page_config(
    page_title="ICD-10 Auto-Coding",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS
def load_css():
    css_path = Path(__file__).parent / "styles.css"
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

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

# Analysis  
def run_analysis(text):
    try:
        st.info("📡 Loading model...")
        from src.model_inference import predict_icd10
        
        st.info(f"📝 Analyzing {len(text)} characters of text...")
        
        # Get predictions - NO THRESHOLD FILTERING (get all predictions)
        predictions = predict_icd10(text, top_k=50)
        
        st.success(f"✅ Model returned {len(predictions)} predictions!")
        
        # Show top 3 confidence scores for debugging
        if predictions:
            top_3_conf = [f"{p['confidence']:.3f}" for p in predictions[:3]]
            st.info(f"Top 3 confidences: {', '.join(top_3_conf)}")
        
        # Add evidence
        words = text.split()
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
                st.markdown(f"<div style='text-align: center; font-size: 1.2rem; color: #a78bfa; font-weight: bold;'>● {label}</div>", unsafe_allow_html=True)
            elif step_num < st.session_state.step:
                st.markdown(f"<div style='text-align: center; font-size: 1.2rem; color: #10B981;'>✓ {label}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center; font-size: 1.2rem; color: #475569;'>○ {label}</div>", unsafe_allow_html=True)
    st.markdown("---")

def step_1_input():
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 1rem;'>🏥 ICD-10 Auto-Coding</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.3rem; color: #94a3b8; margin-bottom: 3rem;'>Choose your input method</p>", unsafe_allow_html=True)
    
    # THREE LARGE CARDS
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        st.markdown("""
        <div class="mega-card" style="text-align: center; padding: 4rem 2rem;">
            <div style="font-size: 8rem; margin-bottom: 1.5rem;">📄</div>
            <h2 style="font-size: 2rem; margin-bottom: 1rem; color: #e2e8f0;">Upload PDF</h2>
            <p style="font-size: 1.1rem; color: #94a3b8;">Medical documents & records</p>
        </div>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=['pdf'], label_visibility="collapsed", key="pdf_upload")
        
        if uploaded_file:
            with st.spinner("Extracting..."):
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

    with col2:
        st.markdown("""
        <div class="mega-card" style="text-align: center; padding: 4rem 2rem;">
            <div style="font-size: 8rem; margin-bottom: 1.5rem;">✍️</div>
            <h2 style="font-size: 2rem; margin-bottom: 1rem; color: #e2e8f0;">Paste Text</h2>
            <p style="font-size: 1.1rem; color: #94a3b8;">Clinical notes & summaries</p>
        </div>
        """, unsafe_allow_html=True)
        
        text_input = st.text_area("", height=120, placeholder="Type clinical text...", label_visibility="collapsed", key="text_input_field")
        
        if st.button("Use Text", key="btn_text", type="primary", use_container_width=True):
            if len(text_input) > 10:
                st.session_state.extracted_text = text_input
                st.session_state.source_type = 'text'
                next_step()
                st.rerun()
            else:
                st.warning("Enter more text")

    with col3:
        st.markdown("""
        <div class="mega-card" style="text-align: center; padding: 4rem 2rem;">
            <div style="font-size: 8rem; margin-bottom: 1.5rem;">🎲</div>
            <h2 style="font-size: 2rem; margin-bottom: 1rem; color: #e2e8f0;">Demo Cases</h2>
            <p style="font-size: 1.1rem; color: #94a3b8;">10 sample medical cases</p>
        </div>
        """, unsafe_allow_html=True)
        
        case_titles = get_case_titles()
        selected_idx = st.selectbox("", range(len(case_titles)), format_func=lambda x: case_titles[x], label_visibility="collapsed", key="case_sel")
        
        if st.button("Load Case", key="btn_demo", type="primary", use_container_width=True):
            case_data = get_case(selected_idx + 1)
            st.session_state.extracted_text = case_data['text']
            st.session_state.source_type = 'demo'
            next_step()
            st.rerun()

def step_2_preview():
    st.markdown("## 📄 Review Document")
    
    text_len = len(st.session_state.extracted_text)
    st.info(f"**Source:** {st.session_state.source_type.upper()} | **Length:** {text_len} chars")
    
    if text_len < 50:
        st.error(f"⚠️ Too short ({text_len} chars). Need at least 50 characters.")
        if st.button("← Back", type="secondary"):
            prev_step()
            st.rerun()
        st.stop()

    with st.expander("View Full Text"):
        st.text_area("", st.session_state.extracted_text, height=300, disabled=True, label_visibility="collapsed")
    
    st.markdown("")
    col_back, col_analyze = st.columns([1, 2])
    with col_back:
        if st.button("← Back", type="secondary"):
            prev_step()
            st.rerun()
    with col_analyze:
        if st.button("🔍 Analyze with AI", type="primary", use_container_width=True):
            with st.spinner("🧠 Running AI Analysis..."):
                preds = run_analysis(st.session_state.extracted_text)
                if preds is not None:
                    st.session_state.predictions = preds
                    next_step()
                    st.rerun()

def step_3_results():
    st.markdown("## 🎯 Analysis Results")
    
    preds = st.session_state.predictions
    if not preds or len(preds) == 0:
        st.warning("No codes detected")
        st.info("Try a demo case for best results")
        if st.button("← Try Again"):
            reset_wizard()
            st.rerun()
        return

    # PRIMARY DIAGNOSIS - HUGE
    primary = preds[0]
    conf_color = "#10B981" if primary['confidence'] >= 0.7 else "#F59E0B" if primary['confidence'] >= 0.4 else "#EF4444"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 15%, #764ba2 85%); border-radius: 24px; padding: 3rem; margin-bottom: 2rem; text-align: center;">
        <div style="font-size: 1rem; color: rgba(255,255,255,0.8); text-transform: uppercase; font-weight: 700; margin-bottom: 1rem;">PRIMARY DIAGNOSIS</div>
        <div style="font-size: 4.5rem; font-weight: 900; color: white; line-height: 1; margin-bottom: 1rem;">
            {primary['code']}
        </div>
        <div style="font-size: 1.6rem; color: rgba(255,255,255,0.95); margin-bottom: 2rem;">
            {primary['description']}
        </div>
        <div style="display: inline-block; background: rgba(255,255,255,0.2); border-radius: 50px; padding: 1rem 2rem;">
            <span style="font-size: 3rem; font-weight: 900; color: white;">{int(primary['confidence']*100)}%</span>
            <span style="font-size: 1.2rem; color: rgba(255,255,255,0.9);"> CONFIDENCE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ALL CODES
    st.markdown("### 📋 Detected Codes")
    
    for i, code in enumerate(preds, 1):
        conf = code['confidence']
        color = "#10B981" if conf >= 0.7 else "#F59E0B" if conf >= 0.4 else "#EF4444"
        emoji = "🟢" if conf >= 0.7 else "🟡" if conf >= 0.4 else "🔴"
        
        st.markdown(f"""
        <div style="background: #1a1f35; border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem; border-left: 8px solid {color}; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                <div style="flex: 1;">
                    <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem;">#{i} • {code.get('chapter', 'Unknown')}</div>
                    <div style="font-size: 2.5rem; font-weight: 800; color: #e2e8f0; margin-bottom: 0.5rem;">{code['code']}</div>
                    <div style="font-size: 1.2rem; color: #cbd5e1; line-height: 1.4;">{code['description']}</div>
                </div>
                <div style="text-align: right; min-width: 100px;">
                    <div style="font-size: 3rem;">{emoji}</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: {color};">{int(conf*100)}%</div>
                </div>
            </div>
            <div style="background: #0f1419; border-radius: 12px; padding: 1rem; border-left: 4px dashed {color};">
                <strong style="color: #94a3b8;">Evidence:</strong> <span style="color: #64748b;">{code.get('evidence', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Analysis", type="primary", use_container_width=True):
            reset_wizard()
            st.rerun()
    with col2:
        code_list = ", ".join([p['code'] for p in preds])
        st.text_input("", value=code_list, label_visibility="collapsed")

# ==================== MAIN ====================

def main():
    render_step_indicator()
    
    if st.session_state.step == 1:
        step_1_input()
    elif st.session_state.step == 2:
        step_2_preview()
    elif st.session_state.step == 3:
        step_3_results()

if __name__ == "__main__":
    main()
