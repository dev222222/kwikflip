import streamlit as st

def display_header():
    """Display app header with logo and title"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 KwikFlip</h1>
        <p>Research, track, and analyze your eBay flips</p>
    </div>
    """, unsafe_allow_html=True) 