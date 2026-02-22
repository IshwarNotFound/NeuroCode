"""
Security Module for ICD-10 Auto-Coding System
Implements: Rate limiting, Input validation, Sanitization, and Session security
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
    Simple rate limiter using session state.
    Prevents abuse by limiting requests per time window.
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._init_session()
    
    def _init_session(self):
        """Initialize rate limiting state in session"""
        if 'rate_limit_requests' not in st.session_state:
            st.session_state.rate_limit_requests = []
        if 'rate_limit_blocked_until' not in st.session_state:
            st.session_state.rate_limit_blocked_until = None
    
    def _cleanup_old_requests(self):
        """Remove expired request timestamps"""
        cutoff = time.time() - self.window_seconds
        st.session_state.rate_limit_requests = [
            t for t in st.session_state.rate_limit_requests if t > cutoff
        ]
    
    def check_rate_limit(self) -> Tuple[bool, Optional[str]]:
        """
        Check if rate limit is exceeded.
        Returns: (is_allowed, error_message)
        """
        self._init_session()
        
        # Check if blocked
        if st.session_state.rate_limit_blocked_until:
            if time.time() < st.session_state.rate_limit_blocked_until:
                remaining = int(st.session_state.rate_limit_blocked_until - time.time())
                return False, f"Rate limit exceeded. Please wait {remaining} seconds."
            else:
                st.session_state.rate_limit_blocked_until = None
        
        self._cleanup_old_requests()
        
        if len(st.session_state.rate_limit_requests) >= self.max_requests:
            # Block for window_seconds
            st.session_state.rate_limit_blocked_until = time.time() + self.window_seconds
            return False, f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s."
        
        # Record this request
        st.session_state.rate_limit_requests.append(time.time())
        logger.info("Analysis request allowed (rate limit check passed)")
        return True, None

# Global rate limiter instance (10 analysis requests per minute)
analysis_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


# ==================== INPUT VALIDATION ====================

class InputValidator:
    """
    Validates and sanitizes user inputs to prevent injection attacks.
    """
    
    # Maximum input sizes
    MAX_TEXT_LENGTH = 50000  # 50KB of text
    MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB
    ALLOWED_FILE_TYPES = ['pdf']
    
    # Dangerous patterns to detect — defense-in-depth layer
    # Primary XSS defense is html.escape() at the rendering boundary.
    # This blocklist catches obviously malicious inputs before they reach the model.
    DANGEROUS_PATTERNS = [
        r'<script',              # Script tags
        r'javascript\s*:',       # JS protocol
        r'on\w+\s*=',            # Event handlers (onclick, onerror, etc.)
        r'data\s*:text/html',    # Data URL XSS
        r'eval\s*\(',            # Code execution
        r'exec\s*\(',            # Code execution
        r'__import__',           # Python injection
        r'subprocess',           # System command
        r'os\.system',           # System command
        r'<iframe',              # Iframe injection
        r'<object',              # Object injection
        r'<embed',               # Embed injection
        r'<svg[\s/>]',           # SVG-based XSS
        r'<math[\s/>]',          # MathML-based XSS
        r'<meta\s',              # Meta refresh injection
        r'srcdoc\s*=',           # srcdoc XSS
        r'<link[\s]',            # Link injection
        r'<base[\s/>]',          # Base tag hijacking
        r'expression\s*\(',      # CSS expression (IE)
        r'url\s*\(\s*["\']?javascript',  # CSS url() XSS
        r'import\s*\(',          # CSS import injection
    ]
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitize text input by:
        1. Removing null bytes
        2. Limiting length
        3. Removing control characters
        
        NOTE: We do NOT HTML-escape here because this text goes to the ML model.
        HTML escaping should only be done when displaying in the UI.
        """
        if not text:
            return ""
        
        # Limit length
        text = text[:cls.MAX_TEXT_LENGTH]
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters (except newlines and tabs)
        text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
        
        return text
    
    @classmethod
    def validate_text_input(cls, text: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate text input.
        Returns: (is_valid, error_message, sanitized_text)
        """
        if not text or not text.strip():
            return False, "Text input cannot be empty", ""
        
        if len(text) > cls.MAX_TEXT_LENGTH:
            return False, f"Text too long. Maximum {cls.MAX_TEXT_LENGTH} characters allowed.", ""
        
        # Check for dangerous patterns (case insensitive)
        text_lower = text.lower()
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Dangerous input pattern detected: {pattern}")
                return False, "Invalid input detected. Please provide valid medical text.", ""
        
        # Sanitize and return
        sanitized = cls.sanitize_text(text)
        return True, None, sanitized
    
    @classmethod
    def sanitize_for_display(cls, text: str) -> str:
        """
        Escape text for safe HTML rendering.
        This is the PRIMARY XSS defense — always call at the rendering boundary.
        """
        return html.escape(text, quote=True)
    
    @classmethod
    def validate_file(cls, uploaded_file) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        Returns: (is_valid, error_message)
        """
        if not uploaded_file:
            return False, "No file uploaded"
        
        # Check file size
        if uploaded_file.size > cls.MAX_FILE_SIZE:
            return False, f"File too large. Maximum {cls.MAX_FILE_SIZE // (1024*1024)}MB allowed."
        
        # Check file type by extension
        file_name = uploaded_file.name.lower()
        file_ext = file_name.split('.')[-1] if '.' in file_name else ''
        
        if file_ext not in cls.ALLOWED_FILE_TYPES:
            return False, f"Invalid file type. Only {', '.join(cls.ALLOWED_FILE_TYPES).upper()} allowed."
        
        # Check magic bytes for PDF
        file_bytes = uploaded_file.getvalue()
        if not file_bytes.startswith(b'%PDF'):
            return False, "Invalid PDF file. File content does not match PDF format."
        
        # Reset file pointer
        uploaded_file.seek(0)
        
        logger.info(f"File validation passed: {uploaded_file.name} ({uploaded_file.size} bytes)")
        return True, None
    
    @classmethod
    def validate_case_selection(cls, selected: str, valid_options: list) -> Tuple[bool, Optional[str]]:
        """
        Validate case selection to prevent injection.
        Returns: (is_valid, error_message)
        """
        if not selected or selected not in valid_options:
            return False, "Invalid case selection"
        
        if selected == "-- Select a case --":
            return False, "Please select a case first"
        
        return True, None


# ==================== SESSION SECURITY ====================

class SessionSecurity:
    """
    Implements session security measures.
    """
    
    SESSION_TIMEOUT_MINUTES = 30
    
    @classmethod
    def init_session(cls):
        """Initialize secure session state"""
        if 'session_created' not in st.session_state:
            st.session_state.session_created = time.time()
        if 'last_activity' not in st.session_state:
            st.session_state.last_activity = time.time()
    
    @classmethod
    def check_session_timeout(cls) -> bool:
        """
        Check if session has timed out.
        Returns True if session is valid, False if expired.
        """
        cls.init_session()
        
        timeout_seconds = cls.SESSION_TIMEOUT_MINUTES * 60
        if time.time() - st.session_state.last_activity > timeout_seconds:
            # Session expired - reset state
            cls.reset_session()
            return False
        
        # Update last activity
        st.session_state.last_activity = time.time()
        return True
    
    @classmethod
    def reset_session(cls):
        """Reset session state securely"""
        keys_to_clear = ['step', 'extracted_text', 'source_type', 'predictions']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


# ==================== SECURE HEADERS ====================

def inject_security_headers():
    """
    Security headers placeholder.
    
    NOTE: Effective security headers (X-Frame-Options, CSP, HSTS, etc.) 
    MUST be set at the HTTP server level (nginx, Cloudflare, etc.), 
    not via <meta> tags which browsers largely ignore for these headers.
    
    For production deployment, configure your reverse proxy:
      add_header X-Frame-Options "DENY" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header Content-Security-Policy "default-src 'self'" always;
      add_header Strict-Transport-Security "max-age=31536000" always;
    """
    # robots noindex is the only tag that works reliably as a meta tag
    st.markdown(
        '<meta name="robots" content="noindex, nofollow">',
        unsafe_allow_html=True
    )


# ==================== CONVENIENCE FUNCTIONS ====================

def secure_analysis_check() -> Tuple[bool, Optional[str]]:
    """
    Combined security check before running analysis.
    Returns: (is_allowed, error_message)
    """
    # Check rate limit
    allowed, error = analysis_rate_limiter.check_rate_limit()
    if not allowed:
        return False, error
    
    # Check session
    if not SessionSecurity.check_session_timeout():
        return False, "Session expired. Please refresh the page."
    
    return True, None


def validate_and_sanitize_text(text: str) -> Tuple[bool, Optional[str], str]:
    """
    Convenience function for text validation.
    Returns: (is_valid, error_message, sanitized_text)
    """
    return InputValidator.validate_text_input(text)


def validate_uploaded_file(uploaded_file) -> Tuple[bool, Optional[str]]:
    """
    Convenience function for file validation.
    Returns: (is_valid, error_message)
    """
    return InputValidator.validate_file(uploaded_file)
