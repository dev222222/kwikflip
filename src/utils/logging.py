import streamlit as st
from datetime import datetime

def log_debug(message):
    """Log debug message to session state"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    debug_message = f"[{timestamp}] {message}"
    
    # Add to session state debug info
    if "debug_info" not in st.session_state:
        st.session_state.debug_info = []
    
    st.session_state.debug_info.append(debug_message)
    
    # Keep only last 100 messages
    st.session_state.debug_info = st.session_state.debug_info[-100:]

def clear_debug_log():
    """Clear debug log"""
    st.session_state.debug_info = []

def get_debug_log():
    """Get debug log"""
    return st.session_state.debug_info if "debug_info" in st.session_state else [] 