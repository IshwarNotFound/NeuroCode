"""
Security Module for ICD-10 Auto-Coding System
Implements multi-layered security defenses targeted at web vulnerabilities:
- Rate limiting (DoS defense)
- Input Validation (Injection, Overflow, XSS surface reduction)
- Sanitization & Encoding
- Session hijacking / Timeout management
"""

import time
import re
import hashlib
import html
import logging
from functools import wraps
from datetime import datetime, timedelta
from typing import Optional, Tuple
import streamlit as st

logger = logging.getLogger(__name__)

# ==================== RATE LIMITING ====================

class RateLimiter:
    """
    Simple sliding-window rate limiter utilizing Streamlit session state.
    Prevents abuse (like automated spamming or brute force model inference)
    by limiting the number of API/Model requests per specified time window.
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initializes the limiter settings.
        :param max_requests: Absolute limit of actions allowed.
        :param window_seconds: The duration of the tracking window.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._init_session()
    
    def _init_session(self):
        """Initialize rate limiting arrays and timers natively in the session"""
        if 'rate_limit_requests' not in st.session_state:
            st.session_state.rate_limit_requests = []
        if 'rate_limit_blocked_until' not in st.session_state:
            st.session_state.rate_limit_blocked_until = None
    
    def _cleanup_old_requests(self):
        """Sweep pass: Remove request timestamps older than the window_seconds"""
        cutoff = time.time() - self.window_seconds
        st.session_state.rate_limit_requests = [
            t for t in st.session_state.rate_limit_requests if t > cutoff
        ]
    
    def check_rate_limit(self) -> Tuple[bool, Optional[str]]:
        """
        Evaluate if the current transaction should proceed based on historical volume.
        Returns: (is_allowed: bool, error_message: str)
        """
        self._init_session()
        
        # 1. State check: See if user is currently serving a timeout sentence
        if st.session_state.rate_limit_blocked_until:
            if time.time() < st.session_state.rate_limit_blocked_until:
                remaining = int(st.session_state.rate_limit_blocked_until - time.time())
                return False, f"Rate limit exceeded. Please wait {remaining} seconds."
            else:
                # Ban has expired, lift it
                st.session_state.rate_limit_blocked_until = None
        
        self._cleanup_old_requests()
        
        # 2. Limit check: Check if current valid requests hit ceiling
        if len(st.session_state.rate_limit_requests) >= self.max_requests:
            # Drop the hammer -> Block for window_seconds
            st.session_state.rate_limit_blocked_until = time.time() + self.window_seconds
            return False, f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s."
        
        # 3. Log clearance and let request pass
        st.session_state.rate_limit_requests.append(time.time())
        logger.info("Analysis request allowed (rate limit check passed)")
        return True, None

# Singleton global instance restricting ML inference to 10 queries per minute
analysis_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


# ==================== INPUT VALIDATION ====================

class InputValidator:
    """
    Validates and sanitizes untrusted user inputs to prevent:
    - Buffer overflows / out-of-memory errors
    - Script injection attacks (XSS)
    - OS command injection and path traversal
    """
    
    # Restrict arbitrary file length scaling (Defense against Resource Exhaustion)
    MAX_TEXT_LENGTH = 50000  # 50KB character limit
    MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB hard physical limit
    ALLOWED_FILE_TYPES = ['pdf']
    
    # Dangerous pattern blocklist (Defense-in-Depth Layer)
    # While html.escape handles UI rendering, this catches specifically malicious payloads
    # before they can interact with the Python backend or ML model serialization logic.
    DANGEROUS_PATTERNS = [
        r'<script',              # Script tags (XSS)
        r'javascript\s*:',       # JS protocol (XSS)
        r'on\w+\s*=',            # HTML Event handlers (onclick, onerror, etc.)
        r'data\s*:text/html',    # Data URL execution
        r'eval\s*\(',            # Code execution
        r'exec\s*\(',            # Code execution
        r'__import__',           # Internal Python module hijacking
        r'subprocess',           # OS Subprocess command injection
        r'os\.system',           # OS System wrapper injection
        r'<iframe',              # Iframe injection (Clickjacking)
        r'<object',              # Object injection
        r'<embed',               # Embed injection
        r'<svg[\s/>]',           # SVG-based XSS payloads
        r'<math[\s/>]',          # MathML-based XSS payloads
        r'<meta\s',              # Meta tag injection (Refresh hacks)
        r'srcdoc\s*=',           # srcdoc attribute XSS
        r'<link[\s]',            # External link injection
        r'<base[\s/>]',          # Base tag navigation hijacking
        r'expression\s*\(',      # IE specific CSS expression execution
        r'url\s*\(\s*["\']?javascript',  # CSS url() XSS injection
        r'import\s*\(',          # CSS import side-loading
    ]
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitize text intended for the ML model.
        1. Strips null bytes (C-string terminators)
        2. Truncates length strictly
        3. Drops non-printable control characters
        
        CRITICAL: We do NOT use html.escape() here. Model needs raw clinical text.
        Escaping is done elsewhere purely for display logic.
        """
        if not text:
            return ""
        
        # Hard truncate to prevent Regex DoS or OOM scaling
        text = text[:cls.MAX_TEXT_LENGTH]
        
        # Remove null bytes (common injection strategy for circumventing filters)
        text = text.replace('\x00', '')
        
        # Remove unprintable control chars (keep standard formatting chars)
        text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
        
        return text
    
    @classmethod
    def validate_text_input(cls, text: str) -> Tuple[bool, Optional[str], str]:
        """
        Perform safety checks on arbitrary block text.
        Returns: (is_valid: bool, error_message: str, sanitized_text: str)
        """
        if not text or not text.strip():
            return False, "Text input cannot be empty", ""
        
        if len(text) > cls.MAX_TEXT_LENGTH:
            return False, f"Text too long. Maximum {cls.MAX_TEXT_LENGTH} characters allowed.", ""
        
        # Regex Scan: Iterate over blocklist and fail fast if malicious signatures detected
        text_lower = text.lower()
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Dangerous input pattern detected: {pattern}")
                return False, "Invalid input detected. Please provide valid medical text.", ""
        
        # Input passes tests, construct sanitized version.
        sanitized = cls.sanitize_text(text)
        return True, None, sanitized
    
    @classmethod
    def sanitize_for_display(cls, text: str) -> str:
        """
        Escape hazardous HTML entities (<, >, &, ", ')
        This is the PRIMARY defense against Reflected and Stored Cross Site Scripting (XSS).
        Always run this when pushing un-trusted strings to the Streamlit DOM.
        """
        return html.escape(text, quote=True)
    
    @classmethod
    def validate_file(cls, uploaded_file) -> Tuple[bool, Optional[str]]:
        """
        Inspect physical file headers and metadata to catch malformed or malicious uploads.
        Returns: (is_valid: bool, error_message: str)
        """
        if not uploaded_file:
            return False, "No file uploaded"
        
        # 1. Enforce strict physical filesize bounds
        if uploaded_file.size > cls.MAX_FILE_SIZE:
            return False, f"File too large. Maximum {cls.MAX_FILE_SIZE // (1024*1024)}MB allowed."
        
        # 2. Naive extension check
        file_name = uploaded_file.name.lower()
        file_ext = file_name.split('.')[-1] if '.' in file_name else ''
        
        if file_ext not in cls.ALLOWED_FILE_TYPES:
            return False, f"Invalid file type. Only {', '.join(cls.ALLOWED_FILE_TYPES).upper()} allowed."
        
        # 3. Magic Bytes verification (ensure a .pdf is ACTUALLY a PDF, not an exe renamed to pdf)
        file_bytes = uploaded_file.getvalue()
        if not file_bytes.startswith(b'%PDF'):
            return False, "Invalid PDF file. File content does not match PDF format."
        
        # Reset file pointer for downstream consumers (like PyPDF/pdfplumber)
        uploaded_file.seek(0)
        
        logger.info(f"File validation passed: {uploaded_file.name} ({uploaded_file.size} bytes)")
        return True, None
    
    @classmethod
    def validate_case_selection(cls, selected: str, valid_options: list) -> Tuple[bool, Optional[str]]:
        """
        Ensure user didn't modify the HTML dropdown options via DevTools to send garbage to the server.
        """
        if not selected or selected not in valid_options:
            return False, "Invalid case selection"
        
        if selected == "-- Select a case --":
            return False, "Please select a case first"
        
        return True, None


# ==================== SESSION SECURITY ====================

class SessionSecurity:
    """
    Manages session lifecycle enforcement to drop dead connections, 
    lowering the attack window for session hijacking or replay attacks.
    """
    
    SESSION_TIMEOUT_MINUTES = 30
    
    @classmethod
    def init_session(cls):
        """Instantiate tracking heartbeat timers"""
        if 'session_created' not in st.session_state:
            st.session_state.session_created = time.time()
        if 'last_activity' not in st.session_state:
            st.session_state.last_activity = time.time()
    
    @classmethod
    def check_session_timeout(cls) -> bool:
        """
        Evaluates elapsed time against timeout constant.
        Returns True if session is valid, False if it has expired and terminated.
        """
        cls.init_session()
        
        timeout_seconds = cls.SESSION_TIMEOUT_MINUTES * 60
        if time.time() - st.session_state.last_activity > timeout_seconds:
            # Lifecycle exceeded -> Wipe session entirely
            cls.reset_session()
            return False
        
        # Record this interaction as a heartbeat to bump the timeout window
        st.session_state.last_activity = time.time()
        return True
    
    @classmethod
    def reset_session(cls):
        """Securely iterate and purge all sensitive artifacts from the user's state memory."""
        keys_to_clear = ['step', 'extracted_text', 'source_type', 'predictions']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


# ==================== SECURE HEADERS ====================

def inject_security_headers():
    """
    Attempts to apply browser security directives via HTML meta tags.
    
    NOTE: As documented, robust headers (CSP, HSTS, X-Frame-Options) cannot be properly
    enforced by meta tags. This is a partial solution (robots directive). Real deployment
    requires configuring the network edge (e.g. Nginx, Apache) to enforce TCP security headers.
    """
    # Instructs aggressive web scrapers / search engines to ignore this application.
    st.markdown(
        '<meta name="robots" content="noindex, nofollow">',
        unsafe_allow_html=True
    )


# ==================== CONVENIENCE FUNCTIONS ====================

def secure_analysis_check() -> Tuple[bool, Optional[str]]:
    """
    Middleware pipeline check. Validates both rate limit quota and session validity
    before permitting heavy server-side processing to occur.
    Returns: (is_allowed: bool, error_message: str)
    """
    # Gate 1: Rate limit evaluation
    allowed, error = analysis_rate_limiter.check_rate_limit()
    if not allowed:
        return False, error
    
    # Gate 2: Session timeout
    if not SessionSecurity.check_session_timeout():
        return False, "Session expired. Please refresh the page."
    
    return True, None


def validate_and_sanitize_text(text: str) -> Tuple[bool, Optional[str], str]:
    """Shorthand wrapper proxy for InputValidator text pipeline"""
    return InputValidator.validate_text_input(text)


def validate_uploaded_file(uploaded_file) -> Tuple[bool, Optional[str]]:
    """Shorthand wrapper proxy for InputValidator file inspection pipeline"""
    return InputValidator.validate_file(uploaded_file)
