import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv

# Import local modules
from src.api.ebay_api import EbayAPI
from src.ui.header import display_header
from src.ui.sidebar import display_sidebar
from src.ui.search import display_search_form, show_recent_searches
from src.ui.results import display_items, display_metrics
from src.ui.calculator import display_profit_calculator
from src.ui.analytics import display_analytics
from src.ui.guide import display_quick_start_guide, display_marketplace_comparison
from src.data.storage import load_flips, save_flip, load_recent_searches, save_recent_searches
from src.utils.stats import calculate_stats
from src.utils.charts import generate_price_chart, generate_volume_chart
from src.utils.logging import log_debug

# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = Path("data")
FLIPS_FILE = DATA_DIR / "flips.csv"
SEARCHES_FILE = DATA_DIR / "searches.json"
MAX_RECENT_SEARCHES = 10

# Initialize session state
if "filter_settings" not in st.session_state:
    st.session_state.filter_settings = {
        "min_price": 0,
        "max_price": 10000,
        "condition": "any",
        "days_sold": 30,
        "exclude_words": "",
    }
if "last_search" not in st.session_state:
    st.session_state.last_search = None
if "active_items" not in st.session_state:
    st.session_state.active_items = []
if "sold_items" not in st.session_state:
    st.session_state.sold_items = []
if "recent_searches" not in st.session_state:
    st.session_state.recent_searches = []
if "camera_photo" not in st.session_state:
    st.session_state.camera_photo = None
if "debug_info" not in st.session_state:
    st.session_state.debug_info = []
if "use_mock" not in st.session_state:
    st.session_state.use_mock = True
if "ebay_api" not in st.session_state:
    from src.api.ebay_api import EbayAPI
    st.session_state.ebay_api = EbayAPI()
    st.session_state.ebay_api.set_mock_mode(st.session_state.use_mock)

# Set page config
st.set_page_config(
    page_title="KwikFlip - eBay Research Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
def test_ebay_connection():
    """Test the eBay API connection"""
    try:
        log_debug("Testing eBay API connection")
        
        # Get OAuth token
        api = st.session_state.ebay_api
        token, error = api.get_oauth_token(force_refresh=True)
        
        if token:
            log_debug("Successfully acquired OAuth token")
            return True, "Connection successful! OAuth token acquired."
        else:
            error_msg = f"Failed to get OAuth token: {error}"
            log_debug(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error testing eBay connection: {str(e)}"
        log_debug(error_msg)
        log_debug(traceback.format_exc())
        return False, error_msg
    
def main():
    """Main application function"""
    try:
        # 1) Display header and sidebar
        display_header()
        display_sidebar()
        
        # 2) Show recent searches
        show_recent_searches()
        
        # 3) Show the search form
        did_search = display_search_form()
        
        # Show marketplace information if no search
        if not did_search and not st.session_state.last_search:
            st.info("🔍 Enter a search above to begin")
            display_marketplace_comparison()
            display_quick_start_guide()
            return

        # 4) Get search parameters
        search = st.session_state.last_search
        query = search["query"]
        is_upc = search.get("is_upc", False)
        flip_type = search.get("flip_type", "Retail Arbitrage")
        cost = search.get("cost", 0.0)
        category = search.get("category", "Electronics")
        filters = st.session_state.filter_settings
        
        # Check if this was an image search
        is_image_search = search.get("image_search", False)
        if is_image_search:
            st.info(f"📸 Image Search: Recognized as '{query}'")

        # 5) Fetch data
        with st.spinner("Fetching data..."):
            ebay_api = st.session_state.ebay_api
            active_items, active_error = ebay_api.fetch_items(query, sold=False, filters=filters)
            sold_items, sold_error = ebay_api.fetch_items(query, sold=True, filters=filters)
            
            st.session_state.active_items = active_items
            st.session_state.sold_items = sold_items
            
            if active_error:
                st.warning(f"Notice for active items: {active_error}")
            if sold_error:
                st.warning(f"Notice for sold items: {sold_error}")

        # 6) Compute statistics
        active_stats = calculate_stats(active_items)
        sold_stats = calculate_stats(sold_items)

        # 7) Display metrics and charts
        display_metrics(active_stats, sold_stats, ebay_api.get_fee_rate(category))
        
        # 8) Show price distribution chart
        price_fig = generate_price_chart(active_items, sold_items)
        if price_fig:
            st.plotly_chart(price_fig, use_container_width=True)

        # 9) Show volume chart
        volume_fig = generate_volume_chart(active_items, sold_items)
        if volume_fig:
            st.plotly_chart(volume_fig, use_container_width=True)

        # 10) Display item listings
        st.markdown("### eBay Results")
        display_items(active_items, "Active eBay Listings", sort_options=True, pagination=True, page_size=10)
        display_items(sold_items, "Sold eBay Items (30d)", sort_options=True, pagination=True, page_size=10)

        # 11) Show profit calculator
        display_profit_calculator(active_stats, sold_stats, cost, category, flip_type)

        # 12) Display analytics
        df = load_flips()
        if not df.empty:
            display_analytics(df)
        
        # 13) Display footer
        st.markdown("""
        <div class="footer">
            <p>KwikFlip - Research and track your eBay flips</p>
            <p style="font-size: 0.8rem;">Version 1.0</p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        error_msg = f"An error occurred in the main function: {e}"
        log_debug(error_msg)
        st.error(error_msg)

if __name__ == "__main__":
    main() 