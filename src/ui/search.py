import streamlit as st
from src.utils.logging import log_debug
from src.data.storage import save_recent_searches

def display_search_form():
    """Display search form with text and image search options"""
    st.markdown("### 🔍 Search")
    
    # Create two columns for text and image search
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Text search
        query = st.text_input("Search Query", placeholder="Enter keywords or UPC")
        
        # Additional search options
        col1a, col1b = st.columns(2)
        with col1a:
            is_upc = st.checkbox("This is a UPC")
        with col1b:
            flip_type = st.selectbox(
                "Flip Type",
                ["Retail Arbitrage", "Thrift Store", "Garage Sale", "Other"]
            )
        
        # Cost and category
        col1c, col1d = st.columns(2)
        with col1c:
            cost = st.number_input("Cost ($)", min_value=0.0, value=0.0, step=0.01)
        with col1d:
            category = st.selectbox(
                "Category",
                ["Electronics", "Clothing", "Collectibles", "Home & Garden", "Toys", "Books", "Other"]
            )
    
    with col2:
        # Image search
        st.markdown("### 📸 Image Search")
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            st.session_state.camera_photo = uploaded_file
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    
    # Search button
    if st.button("Search", type="primary"):
        if query or uploaded_file is not None:
            # Store search parameters
            search_params = {
                "query": query,
                "is_upc": is_upc,
                "flip_type": flip_type,
                "cost": cost,
                "category": category,
                "image_search": uploaded_file is not None
            }
            
            # Save to session state
            st.session_state.last_search = search_params
            
            # Add to recent searches
            if query:
                st.session_state.recent_searches.insert(0, query)
                st.session_state.recent_searches = st.session_state.recent_searches[:10]
                save_recent_searches(st.session_state.recent_searches)
            
            return True
    
    return False

def show_recent_searches():
    """Display recent searches"""
    if st.session_state.recent_searches:
        st.markdown("### 🔍 Recent Searches")
        cols = st.columns(5)
        for i, search in enumerate(st.session_state.recent_searches):
            with cols[i % 5]:
                if st.button(search, key=f"recent_{i}"):
                    st.session_state.last_search = {"query": search}
                    st.experimental_rerun() 