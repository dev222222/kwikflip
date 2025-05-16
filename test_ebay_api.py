import streamlit as st
import pandas as pd
from src.api.ebay import EbayAPI
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="KwikFlip - eBay API Test",
    page_icon="🔍",
    layout="wide"
)

# Create API instance
ebay_api = EbayAPI()

# Display header
st.title("🔍 KwikFlip eBay API Test")
st.markdown("Test the eBay API integration with real data")

# Check environment
api_env = "PRODUCTION" if os.getenv("EBAY_USE_SANDBOX", "False").lower() == "false" else "SANDBOX"
st.info(f"Using eBay {api_env} environment")

# Display credentials status
col1, col2 = st.columns(2)
with col1:
    st.subheader("Credentials")
    app_id = os.getenv("EBAY_APP_ID", "")
    cert_id = os.getenv("EBAY_CERT_ID", "")
    
    if app_id and cert_id:
        st.success("✅ Credentials configured")
        st.markdown(f"App ID: `{app_id[:5]}...{app_id[-5:]}`")
        st.markdown(f"Cert ID: `{cert_id[:5]}...{cert_id[-5:]}`")
    else:
        st.error("❌ Credentials missing")

# Test connection
with col2:
    st.subheader("Connection Test")
    if st.button("Test eBay API Connection"):
        with st.spinner("Testing connection..."):
            success, message = ebay_api.test_connection()
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")

# Search form
st.subheader("Search eBay")
with st.form("search_form"):
    query = st.text_input("Search Query", "iphone")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sold = st.checkbox("Show Sold Items", value=False)
    
    with col2:
        limit = st.slider("Result Limit", 1, 50, 10)
    
    with col3:
        min_price = st.number_input("Min Price", 0, 1000, 0)
    
    submitted = st.form_submit_button("Search")
    
    if submitted:
        with st.spinner("Fetching eBay data..."):
            # Create filters
            filters = {
                "min_price": min_price,
                "condition": "any"
            }
            
            # Fetch items
            items, error = ebay_api.fetch_items(query, sold=sold, filters=filters, limit=limit)
            
            if error:
                st.error(f"Error fetching items: {error}")
            elif not items:
                st.warning("No items found")
            else:
                st.success(f"Found {len(items)} items")
                
                # Convert to DataFrame for display
                df = pd.DataFrame(items)
                
                # Display as table
                st.dataframe(df)
                
                # Display first item details
                if len(items) > 0:
                    st.subheader("First Item Details")
                    item = items[0]
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.image(item["image"], width=200)
                    
                    with col2:
                        st.markdown(f"**Title:** {item['title']}")
                        st.markdown(f"**Price:** ${item['price']:.2f}")
                        st.markdown(f"**Shipping:** ${item['shipping']:.2f}")
                        st.markdown(f"**Condition:** {item['condition']}")
                        st.markdown(f"**URL:** [View on eBay]({item['url']})")