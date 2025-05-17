import streamlit as st
from src.utils.logging import log_debug

def display_sidebar():
    """Display sidebar with filter settings and debug info"""
    with st.sidebar:
        st.markdown("### 🔍 Filter Settings")
        
        # Price range
        min_price, max_price = st.slider(
            "Price Range ($)",
            min_value=0,
            max_value=10000,
            value=(st.session_state.filter_settings["min_price"], 
                  st.session_state.filter_settings["max_price"])
        )
        
        # Condition filter
        condition = st.selectbox(
            "Condition",
            ["any", "new", "used"],
            index=["any", "new", "used"].index(st.session_state.filter_settings["condition"])
        )
        
        # Days sold filter
        days_sold = st.slider(
            "Days Sold",
            min_value=1,
            max_value=90,
            value=st.session_state.filter_settings["days_sold"]
        )
        
        # Exclude words
        exclude_words = st.text_input(
            "Exclude Words (comma-separated)",
            value=st.session_state.filter_settings["exclude_words"]
        )
        
        # Update filter settings
        st.session_state.filter_settings.update({
            "min_price": min_price,
            "max_price": max_price,
            "condition": condition,
            "days_sold": days_sold,
            "exclude_words": exclude_words
        })
        
        # Mock/Real data toggle
        if "use_mock" not in st.session_state:
            st.session_state.use_mock = True
        use_mock = st.checkbox(
            "Use Mock eBay Data (for testing)",
            value=st.session_state.use_mock,
            help="Turn off to use real eBay API data (requires valid credentials)"
        )
        st.session_state.use_mock = use_mock
        if "ebay_api" in st.session_state:
            st.session_state.ebay_api.set_mock_mode(use_mock)
        
        # Debug section
        if st.checkbox("Show Debug Info"):
            st.markdown("### 🐛 Debug Info")
            for info in st.session_state.debug_info:
                st.text(info) 