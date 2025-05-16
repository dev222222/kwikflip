"""
app.py - Main application file for KwikFlip
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os
import json
import traceback
import base64
from pathlib import Path
from dotenv import load_dotenv

# Import custom API module
from src.api.ebay_api import EbayAPI

# --- SETUP ---
# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
FLIPS_FILE = DATA_DIR / "flips.csv"
SEARCHES_FILE = DATA_DIR / "searches.json"
MAX_RECENT_SEARCHES = 10

# Set page config
st.set_page_config(
    page_title="KwikFlip - eBay Research Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
DATA_DIR = Path("data")
def ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

 # Call this early in your app initialization
ensure_data_dir()

# --- SESSION STATE INITIALIZATION ---
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
if "ebay_api" not in st.session_state:
    st.session_state.ebay_api = EbayAPI()
if "ebay_oauth_token" not in st.session_state:
    st.session_state.ebay_oauth_token = None
if "ebay_token_expiry" not in st.session_state:
    st.session_state.ebay_token_expiry = 0

# --- LOGGING FUNCTION ---
def log_debug(message):
    """Add message to debug log and print to console"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    formatted_message = f"[{timestamp}] {message}"
    
    # Add to session state debug info
    if len(st.session_state.debug_info) > 100:
        st.session_state.debug_info = st.session_state.debug_info[-100:]
    st.session_state.debug_info.append(formatted_message)
    
    # Also print to standard output for server logs
    print(formatted_message)

# --- DATA FUNCTIONS ---
def load_recent_searches():
    """Load recent searches from file"""
    if SEARCHES_FILE.exists():
        try:
            with open(SEARCHES_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            log_debug(f"Could not load recent searches: {e}")
            return []
    return []

def save_recent_searches():
    """Save recent searches to file"""
    try:
        with open(SEARCHES_FILE, "w") as f:
            json.dump(st.session_state.recent_searches, f)
        
        log_debug(f"Saved {len(st.session_state.recent_searches)} recent searches to {SEARCHES_FILE}")
        return True
    except Exception as e:
        error_msg = f"Error saving recent searches: {e}"
        log_debug(error_msg)
        st.error(error_msg)
        return False

def load_flips():
    """Load saved flips from CSV file"""
    if not FLIPS_FILE.exists():
        # Create empty DataFrame with expected columns
        return pd.DataFrame(columns=[
            "timestamp", "title", "query", "category", "flip_type", "platform",
            "cost", "selling_price", "shipping_cost", "shipping_revenue",
            "platform_fee", "additional_fee", "net_profit", "roi", "sold_date", "notes"
        ])
    
    try:
        return pd.read_csv(FLIPS_FILE)
    except Exception as e:
        log_debug(f"Error loading flips data: {e}")
        st.warning(f"Error loading flips data: {e}")
        return pd.DataFrame()

def save_flip(data):
    """Save a flip to the CSV file"""
    try:
        df = load_flips()
        # Add timestamp
        data["timestamp"] = datetime.now().isoformat()
        
        # Append new flip
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        
        # Save to CSV
        df.to_csv(FLIPS_FILE, index=False)
        
        log_debug(f"Saved flip '{data.get('title', 'Unnamed')}' to {FLIPS_FILE}")
        return True
    except Exception as e:
        error_msg = f"Error saving flip: {e}"
        log_debug(error_msg)
        st.warning(error_msg)
        return False

def calculate_stats(items):
    """Calculate statistics for a list of items"""
    if not items:
        return {
            "count": 0,
            "avg_price": 0.0,
            "median_price": 0.0,
            "min_price": 0.0,
            "max_price": 0.0,
            "total_value": 0.0,
            "avg_total": 0.0  # Price + shipping
        }
    
    try:
        prices = [item["price"] for item in items]
        totals = [item["price"] + item["shipping"] for item in items]
        
        return {
            "count": len(items),
            "avg_price": sum(prices) / len(prices) if prices else 0.0,
            "median_price": sorted(prices)[len(prices) // 2] if prices else 0.0,
            "min_price": min(prices) if prices else 0.0,
            "max_price": max(prices) if prices else 0.0,
            "total_value": sum(prices),
            "avg_total": sum(totals) / len(totals) if totals else 0.0
        }
    except Exception as e:
        error_msg = f"Error calculating stats: {e}"
        log_debug(error_msg)
        st.error(error_msg)
        return {
            "count": len(items),
            "avg_price": 0.0,
            "median_price": 0.0,
            "min_price": 0.0,
            "max_price": 0.0,
            "total_value": 0.0,
            "avg_total": 0.0
        }

# --- UI FUNCTIONS ---
def display_header():
    """Display app header with logo and title"""
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <h1 style="margin: 0;">📊 KwikFlip</h1>
    </div>
    <p style="margin-top: 0;">Research, track, and analyze your eBay flips</p>
    """, unsafe_allow_html=True)

def display_sidebar():
    """Display sidebar with filters and settings"""
    with st.sidebar:
        st.header("🔍 Search Filters")
        
        st.session_state.filter_settings["min_price"] = st.slider(
            "Minimum Price ($)", 0, 1000, st.session_state.filter_settings["min_price"]
        )
        
        st.session_state.filter_settings["max_price"] = st.slider(
            "Maximum Price ($)", 0, 10000, st.session_state.filter_settings["max_price"]
        )
        
        st.session_state.filter_settings["condition"] = st.selectbox(
            "Item Condition",
            ["any", "new", "used", "for parts or not working"],
            index=["any", "new", "used", "for parts or not working"].index(st.session_state.filter_settings["condition"])
        )
        
        st.session_state.filter_settings["days_sold"] = st.slider(
            "Days Back (Sold Items)", 1, 90, st.session_state.filter_settings["days_sold"]
        )
        
        st.session_state.filter_settings["exclude_words"] = st.text_input(
            "Exclude Words (comma separated)",
            value=st.session_state.filter_settings["exclude_words"]
        )
        
        # eBay API status
        st.markdown("---")
        st.subheader("API Status")
        
        # Check eBay credentials
        api = st.session_state.ebay_api
        has_credentials = api.check_credentials()
        
        if has_credentials:
            st.success("✅ eBay API credentials configured")
            
            # Test API connection
            if st.button("Test eBay Connection"):
                with st.spinner("Testing connection..."):
                    token, error = api.get_oauth_token(force_refresh=True)
                    if token:
                        st.success("✅ eBay API connection successful")
                    else:
                        st.error(f"❌ {error}")
        else:
            st.warning("⚠️ eBay API credentials not found")
            
            # Show what's missing
            if not api.client_id:
                st.error("EBAY_APP_ID is missing")
            if not api.client_secret:
                st.error("EBAY_CERT_ID is missing")
            
            # Help section
            with st.expander("How to fix"):
                st.markdown("""
                1. Create an eBay Developer account at [developer.ebay.com](https://developer.ebay.com)
                2. Create a new application and get your App ID (Client ID) and Cert ID (Client Secret)
                3. Add these values to your .env file:
                ```
                EBAY_APP_ID=your_app_id_here
                EBAY_CERT_ID=your_cert_id_here
                EBAY_USE_SANDBOX=True
                ```
                """)
        
        # Debug info
        with st.expander("Debug Info", expanded=False):
            if st.button("Clear Logs"):
                st.session_state.debug_info = []
                st.rerun()
            
            st.text_area("Debug Log", value="\n".join(st.session_state.debug_info), height=300)

def show_recent_searches():
    """Display recent searches with improved UI"""
    if not st.session_state.recent_searches:
        # Load saved searches if none in session state
        try:
            saved_searches = load_recent_searches()
            if saved_searches:
                st.session_state.recent_searches = saved_searches
                log_debug(f"Loaded {len(saved_searches)} saved searches")
        except Exception as e:
            log_debug(f"Could not load recent searches: {e}")
            st.session_state.recent_searches = []
    
    # Display recent searches if there are any
    if st.session_state.recent_searches:
        with st.expander("📜 Recent Searches", expanded=False):
            for i, search in enumerate(st.session_state.recent_searches):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                # Query and category
                col1.markdown(f"""
                <div style="padding: 10px 0;">
                    <div style="font-weight: 600;">{search['query']}</div>
                    <div style="font-size: 0.8rem; color: #777;">{search.get('category', 'Unknown')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Timestamp
                timestamp = "N/A"
                if 'timestamp' in search:
                    try:
                        timestamp_str = search['timestamp']
                        if isinstance(timestamp_str, str):
                            timestamp = datetime.fromisoformat(timestamp_str).strftime("%m/%d/%Y %I:%M %p")
                        else:
                            timestamp = str(timestamp_str)
                    except Exception:
                        timestamp = str(search.get('timestamp', 'N/A'))
                
                col2.markdown(f"""
                <div style="padding: 10px 0; font-size: 0.9rem; color: #777;">
                    {timestamp}
                </div>
                """, unsafe_allow_html=True)
                
                # Load button
                if col3.button("Load", key=f"load_search_{i}"):
                    st.session_state.last_search = search
                    log_debug(f"Loaded search: {search['query']}")
                    st.rerun()

def display_search_form():
    """Display search form and handle submission"""
    st.markdown("### 🔎 Search for Items")
    
    # Create tabs for text and image search
    search_tab, camera_tab = st.tabs(["Text Search", "Image Search"])
    
    with search_tab:
        with st.form(key="search_form", clear_on_submit=False):
            col1, col2 = st.columns([3, 1])
            
            query = col1.text_input("Search Query or UPC", 
                                value="" if not st.session_state.last_search else st.session_state.last_search["query"])
            
            is_upc = col2.checkbox("Is UPC?", 
                                value=False if not st.session_state.last_search else st.session_state.last_search.get("is_upc", False))
            
            col1, col2, col3 = st.columns(3)
            
            flip_type = col1.selectbox("Flip Type", 
                                    ["Retail Arbitrage", "Online Arbitrage", "Thrift Flip", "Garage Sale", "Other"],
                                    index=0 if not st.session_state.last_search else 
                                    ["Retail Arbitrage", "Online Arbitrage", "Thrift Flip", "Garage Sale", "Other"].index(
                                        st.session_state.last_search.get("flip_type", "Retail Arbitrage")))
            
            cost = col2.number_input("Your Cost ($)", 
                                min_value=0.0, value=0.0 if not st.session_state.last_search else float(st.session_state.last_search.get("cost", 0.0)),
                                format="%.2f")
            
            category = col3.selectbox("Category", 
                                    ["Electronics", "Clothing", "Collectibles", "Home & Garden", "Toys", "Books", "Other"],
                                    index=0 if not st.session_state.last_search else 
                                    ["Electronics", "Clothing", "Collectibles", "Home & Garden", "Toys", "Books", "Other"].index(
                                        st.session_state.last_search.get("category", "Electronics")))
            
            photo = st.file_uploader("Upload Item Photo (optional)", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("Search eBay")
            
            if submitted and query:
                # Save the search
                search_data = {
                    "query": query,
                    "is_upc": is_upc,
                    "flip_type": flip_type,
                    "cost": cost,
                    "category": category,
                    "photo": None,  # We'll handle the photo separately if needed
                    "timestamp": datetime.now().isoformat()
                }
                
                st.session_state.last_search = search_data
                
                # Save to recent searches
                if not any(s["query"] == query for s in st.session_state.recent_searches):
                    st.session_state.recent_searches.insert(0, search_data)
                    if len(st.session_state.recent_searches) > MAX_RECENT_SEARCHES:
                        st.session_state.recent_searches = st.session_state.recent_searches[:MAX_RECENT_SEARCHES]
                    
                    # Save to file
                    save_recent_searches()
                
                log_debug(f"Submitted search: {query}")
                return True
    
    with camera_tab:
        st.markdown("### 📸 Take a Photo to Search")
        
        # Use st.camera_input for webcam capture
        camera_input = st.camera_input("Take a picture of your item")
        
        if camera_input is not None:
            # Store photo in session state
            st.session_state.camera_photo = camera_input
            
            # Display a preview
            st.image(camera_input, caption="Captured Image", use_column_width=True)
            
            if st.button("Search with this Image"):
                # Process the image
                with st.spinner("Analyzing image..."):
                    # Process the image
                    recognition_result = st.session_state.ebay_api.process_image_search(camera_input)
                    
                    # Create a search based on the image recognition
                    image_search = {
                        "query": recognition_result["query"],
                        "is_upc": False,
                        "flip_type": "Thrift Flip",  # Default for image searches
                        "cost": 0.0,
                        "category": recognition_result["category"],
                        "photo": None,  # We don't need to store the photo again
                        "timestamp": datetime.now().isoformat(),
                        "image_search": True         # Flag to indicate this was an image search
                    }
                    
                    st.session_state.last_search = image_search
                    
                    # Save to recent searches
                    if not any(s.get("query") == recognition_result["query"] and s.get("image_search", False) for s in st.session_state.recent_searches):
                        st.session_state.recent_searches.insert(0, image_search)
                        if len(st.session_state.recent_searches) > MAX_RECENT_SEARCHES:
                            st.session_state.recent_searches = st.session_state.recent_searches[:MAX_RECENT_SEARCHES]
                        
                        # Save to file
                        save_recent_searches()
                    
                    st.success(f"Image recognized as: '{recognition_result['query']}' (Confidence: {recognition_result['confidence']:.0%})")
                    log_debug(f"Image search completed: {recognition_result['query']}")
                    st.rerun()
    
    return False

def display_items(items, title, sort_options=False, pagination=True, page_size=5):
    """Display items with modern card-based UI"""
    if not items:
        st.info(f"No {title.lower()} found.")
        return
    
    try:
        # Header section
        st.markdown(f"### {title} ({len(items)})")
        
        # Sorting options with improved UI
        if sort_options:
            sort_by = st.selectbox(
                f"Sort {title} by",
                ["Price (Low to High)", "Price (High to Low)", "End Date", "Watchers"],
                key=f"sort_{title}"
            )
            
            # Apply sorting
            if sort_by == "Price (Low to High)":
                items = sorted(items, key=lambda x: x["price"])
            elif sort_by == "Price (High to Low)":
                items = sorted(items, key=lambda x: x["price"], reverse=True)
            elif sort_by == "End Date":
                items = sorted(items, key=lambda x: x.get("end_time", ""))
            elif sort_by == "Watchers":
                items = sorted(items, key=lambda x: x.get("watchers", 0), reverse=True)
        
        # Pagination with improved UI
        if pagination and len(items) > page_size:
            page_count = (len(items) + page_size - 1) // page_size
            
            # Create page selector
            col1, col2 = st.columns([4, 1])
            page = col1.select_slider(
                f"Page",
                options=range(1, page_count + 1),
                value=1,
                key=f"page_{title}"
            )
            
            # Display page info
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, len(items))
            col2.caption(f"Showing {start_idx + 1}-{end_idx} of {len(items)}")
            
            page_items = items[start_idx:end_idx]
        else:
            page_items = items
        
        # Display items in modern card layout
        for item in page_items:
            # Format end time
            formatted_date = ""
            end_time = item.get("end_time", "")
            if end_time:
                try:
                    end_date = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.000Z")
                    formatted_date = end_date.strftime("%b %d, %Y")
                except:
                    formatted_date = end_time
            
            # Create a card for each item
            st.markdown(f"""
            <div style="display: flex; border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                <div style="flex: 0 0 120px; margin-right: 15px;">
                    <img src="{item.get('image', 'https://via.placeholder.com/150')}" style="max-width: 100%; border-radius: 5px;" alt="{item.get('title', 'Item')}">
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 1.1rem;">{item.get('title', 'Untitled Item')}</div>
                    <div style="font-size: 0.9rem; color: #666;">Condition: {item.get('condition', 'N/A')}</div>
                    <div style="font-size: 0.9rem; color: #666;">{'Sold on' if item.get('sold') else 'Ends'}: {formatted_date}</div>
                    {f'<div style="font-size: 0.9rem; color: #666;">Watchers: {item["watchers"]}</div>' if item.get('watchers', 0) > 0 else ''}
                </div>
                <div style="flex: 0 0 100px; text-align: right;">
                    <div style="font-weight: bold; font-size: 1.2rem;">${item.get('price', 0):.2f}</div>
                    {f'<div style="font-size: 0.9rem; color: #666;">+${item["shipping"]:.2f} shipping</div>' if item.get('shipping', 0) > 0 else ''}
                    <a href="{item.get('url', '#')}" target="_blank" style="display: inline-block; margin-top: 10px; color: #1e88e5; text-decoration: none;">View Item</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        error_msg = f"Error displaying items: {e}"
        log_debug(error_msg)
        st.error(error_msg)

def display_metrics(active_stats, sold_stats, fee_rate):
    """Display metrics cards with item statistics"""
    st.markdown("### 📈 Market Analysis")
    
    # Calculate key metrics
    sell_through_rate = (sold_stats['count'] / (active_stats['count'] + sold_stats['count'])) * 100 if (active_stats['count'] + sold_stats['count']) > 0 else 0
    price_diff = sold_stats['avg_price'] - active_stats['avg_price'] if active_stats['avg_price'] > 0 else 0
    price_diff_percent = (price_diff / active_stats['avg_price']) * 100 if active_stats['avg_price'] > 0 else 0
    
    # Create a row of metrics with improved styling
    cols = st.columns(4)
    
    # Metric 1: Active Listings
    cols[0].metric(
        "Active Listings",
        f"{active_stats['count']}",
        f"Avg: ${active_stats['avg_price']:.2f}"
    )
    
    # Metric 2: Sold Listings
    cols[1].metric(
        "Sold Listings",
        f"{sold_stats['count']}",
        f"Avg: ${sold_stats['avg_price']:.2f}"
    )
    
    # Metric 3: Sell-Through Rate
    cols[2].metric(
        "Sell-Through Rate",
        f"{sell_through_rate:.1f}%",
        f"Last {st.session_state.filter_settings['days_sold']} days"
    )
    
    # Metric 4: Price Difference
    delta_color = "normal" if price_diff >= 0 else "inverse"
    cols[3].metric(
        "Price Difference",
        f"${abs(price_diff):.2f}",
        f"{abs(price_diff_percent):.1f}% {'higher' if price_diff >= 0 else 'lower'} when sold",
        delta_color=delta_color
    )

def generate_price_chart(active_items, sold_items):
    """Generate price distribution chart"""
    if not active_items and not sold_items:
        return None
    
    try:
        # Prepare data
        active_prices = [item["price"] for item in active_items]
        sold_prices = [item["price"] for item in sold_items]
        
        fig = go.Figure()
        # Add histograms for price distribution
        if active_prices:
            fig.add_trace(go.Histogram(
                x=active_prices,
                nbinsx=10,
                name="Active Listings",
                marker_color="#1e88e5",
                opacity=0.7
            ))
        if sold_prices:
            fig.add_trace(go.Histogram(
                x=sold_prices,
                nbinsx=10,
                name="Sold Listings",
                marker_color="#43a047",
                opacity=0.7
            ))
        
        # Update layout with improved styling
        fig.update_layout(
            title="Price Distribution",
            title_font_size=16,
            xaxis_title="Price ($)",
            yaxis_title="Count",
            bargroupgap=0.1,
            barmode="overlay",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=400,
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        
        return fig
    except Exception as e:
        error_msg = f"Error generating price chart: {e}"
        log_debug(error_msg)
        st.error(error_msg)
        return None

def generate_volume_chart(active_items, sold_items):
    """Generate sales volume chart by day"""
    if not sold_items:
        return None
    
    try:
        # Extract dates from sold items with safer date parsing
        dates = []
        for item in sold_items:
            if item.get("end_time"):
                try:
                    date = datetime.strptime(item["end_time"], "%Y-%m-%dT%H:%M:%S.000Z")
                    dates.append(date)
                except ValueError:
                    pass
        
        # Group by date
        date_counts = {}
        for date in dates:
            key = date.strftime("%Y-%m-%d")
            date_counts[key] = date_counts.get(key, 0) + 1
        
        # Sort dates chronologically
        sorted_dates = sorted(date_counts)
        
        # Create bar chart with improved styling
        fig = go.Figure(go.Bar(
            x=sorted_dates,
            y=[date_counts[d] for d in sorted_dates],
            name="Sales Volume",
            marker_color="#43a047",
            hovertemplate='Date: %{x}<br>Units Sold: %{y}<extra></extra>'
        ))
        
        # Update layout with improved styling
        fig.update_layout(
            title="Sales Volume by Day",
            title_font_size=16,
            xaxis_title="Date",
            yaxis_title="Units Sold",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=400,
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        # Improve axis styling
        fig.update_xaxes(
            tickangle=-45,
            gridcolor="rgba(0,0,0,0.1)"
        )
        fig.update_yaxes(
            gridcolor="rgba(0,0,0,0.1)"
        )
        
        return fig
    except Exception as e:
        error_msg = f"Error generating volume chart: {e}"
        log_debug(error_msg)
        st.error(error_msg)
        return None

def display_profit_calculator(active_stats, sold_stats, cost, category, flip_type):
    """Display profit calculator with improved UI and market suggestions"""
    st.markdown("### 💰 Profit Calculator")
    
    # Create tabs for calculator and market insights
    calc_tab, insights_tab = st.tabs(["Calculator", "Market Insights"])
    
    with calc_tab:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Item Details")
            
            your_cost = st.number_input("Your Cost ($)", value=float(cost), min_value=0.0, step=0.01, format="%.2f")
            selling_price = st.number_input("Selling Price ($)", value=float(sold_stats["avg_price"]), min_value=0.0, step=0.01, format="%.2f")
            shipping_cost = st.number_input("Shipping Cost ($)", value=5.0, min_value=0.0, step=0.01, format="%.2f")
            shipping_rev = st.number_input("Shipping Revenue ($)", value=float(shipping_cost), min_value=0.0, step=0.01, format="%.2f")
            
            # Add platform selection
            platform = st.selectbox(
                "Selling Platform",
                ["eBay", "Facebook Marketplace", "Craigslist", "Etsy", "Amazon", "Mercari"],
                index=0
            )
            
            # Platform-specific fee calculation
            fee_rates = {
                "eBay": st.session_state.ebay_api.get_fee_rate(category),
                "Facebook Marketplace": 0.05,  # 5% fee
                "Craigslist": 0.00,          # No fee
                "Etsy": 0.065,              # 6.5% fee + listing fee
                "Amazon": 0.15,             # 15% fee (approximate)
                "Mercari": 0.10,            # 10% fee
            }
            
            fee_rate = fee_rates[platform]
            item_title = st.text_input("Item Title (for your records)", value=st.session_state.last_search["query"] if st.session_state.last_search else "")
            notes = st.text_area("Notes", placeholder="Add any notes about this flip...")
        
        with col2:
            # Calculate profit metrics
            total_rev = selling_price + shipping_rev
            platform_fee = total_rev * fee_rate
            
            # Additional fees for specific platforms
            additional_fee = 0.0
            if platform == "Etsy":
                additional_fee = 0.20  # $0.20 listing fee
            
            # Calculate final profit
            total_fee = platform_fee + additional_fee
            net_profit = total_rev - total_fee - shipping_cost - your_cost
            roi = (net_profit / your_cost) * 100 if your_cost > 0 else 0
            
            # Display profit breakdown
            st.markdown("#### Profit Analysis")
            
            # Create profit breakdown card
            profit_color = "#43a047" if net_profit > 0 else "#e53935"
            
            st.markdown(f"""
            <div style="border: 1px solid {profit_color}; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                <h4 style="margin-top: 0; color: {profit_color};">Profit Breakdown</h4>
                <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                    <span>Item Price:</span>
                    <span>${selling_price:.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                    <span>+ Shipping Revenue:</span>
                    <span>${shipping_rev:.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 10px 0; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 10px;">
                    <span><b>= Total Revenue:</b></span>
                    <span><b>${total_rev:.2f}</b></span>
                </div>
                
                <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                    <span>{platform} Fee ({fee_rate*100:.1f}%):</span>
                    <span>-${platform_fee:.2f}</span>
                </div>
                {f'<div style="display: flex; justify-content: space-between; margin: 10px 0;"><span>Listing Fee:</span><span>-${additional_fee:.2f}</span></div>' if additional_fee > 0 else ''}
                <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                    <span>Shipping Cost:</span>
                    <span>-${shipping_cost:.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 10px 0; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 10px;">
                    <span>Your Cost:</span>
                    <span>-${your_cost:.2f}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; margin: 10px 0; font-weight: 700; font-size: 1.2rem; color: {profit_color};">
                    <span>Net Profit:</span>
                    <span>${net_profit:.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                    <span>ROI:</span>
                    <span>{roi:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Save button
            if st.button("Save This Flip", type="primary"):
                # Collect data to save
                flip_data = {
                    "title": item_title,
                    "query": st.session_state.last_search["query"] if st.session_state.last_search else "",
                    "category": category,
                    "flip_type": flip_type,
                    "platform": platform,
                    "cost": your_cost,
                    "selling_price": selling_price,
                    "shipping_cost": shipping_cost,
                    "shipping_revenue": shipping_rev,
                    "platform_fee": platform_fee,
                    "additional_fee": additional_fee,
                    "net_profit": net_profit,
                    "roi": roi,
                    "sold_date": datetime.now().strftime("%Y-%m-%d"),
                    "notes": notes
                }
                
                # Save the flip
                if save_flip(flip_data):
                    st.success("Flip saved successfully!")
                else:
                    st.error("Failed to save flip. Please try again.")
    
    with insights_tab:
        # Market recommendations
        st.markdown("#### Market-Based Recommendations")
        
        # Calculate platform recommendations
        best_platform, reason = get_recommended_platform(category, sold_stats["avg_price"], st.session_state.filter_settings["condition"])
        
        # Display recommendation
        st.info(f"Recommended Platform: **{best_platform}**\n\n{reason}")
        
        # Add price recommendation
        target_price = sold_stats["avg_price"]
        if sold_stats["median_price"] > sold_stats["avg_price"]:
            # If median is higher than average, suggest a price between them
            target_price = (sold_stats["median_price"] + sold_stats["avg_price"]) / 2
        
        price_rec = max(target_price * 0.95, your_cost * 1.3)  # Ensure at least 30% ROI
        
        st.markdown("#### Pricing Strategy")
        st.markdown(f"""
        Based on market data, we recommend pricing at **${price_rec:.2f}**
        
        * Market average is ${sold_stats["avg_price"]:.2f}
        * Median sold price is ${sold_stats["median_price"]:.2f}
        * Competitive pricing may increase sell-through rate
        """)

def get_recommended_platform(category, avg_price, condition):
    """Get recommended selling platform based on item details"""
    # Default recommendation
    platform = "eBay"
    reason = "General recommendation based on market size and visibility."
    
    # Customize based on category and price
    if category == "Electronics" and avg_price > 100:
        platform = "eBay"
        reason = "Electronics over $100 typically perform well on eBay due to buyer trust and protection."
    elif category == "Home & Garden" and avg_price < 50:
        platform = "Facebook Marketplace"
        reason = "Bulky home items are often best sold locally to avoid shipping costs."
    elif category == "Clothing" and condition.lower() != "new":
        platform = "Facebook Marketplace"
        reason = "Used clothing often sells better locally without shipping costs."
    elif category == "Collectibles":
        platform = "eBay"
        reason = "Collectibles reach the largest collector audience on eBay with auction options."
    elif category == "Books":
        platform = "Amazon"
        reason = "Books typically reach more targeted buyers on Amazon."
    
    return platform, reason

def display_analytics(df):
    """Display analytics for saved flips with improved visualizations"""
    st.markdown("### 📊 Your Flip Analytics")
    
    if df.empty:
        st.info("No flips saved yet. Save some flips to see analytics.")
        return
    
    try:
        # Convert columns to numeric
        numeric_cols = ["cost", "selling_price", "shipping_cost", "shipping_revenue", 
                      "platform_fee", "additional_fee", "net_profit", "roi"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Add date column if timestamp exists
        if "timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_flips = len(df)
        total_profit = df["net_profit"].sum() if "net_profit" in df.columns else 0
        avg_roi = df["roi"].mean() if "roi" in df.columns else 0
        total_invested = df["cost"].sum() if "cost" in df.columns else 0
        
        col1.metric("Total Flips", total_flips)
        col2.metric("Total Profit", f"${total_profit:.2f}")
        col3.metric("Average ROI", f"{avg_roi:.1f}%")
        col4.metric("Total Invested", f"${total_invested:.2f}")
        
        # Create tabs for different analytics views
        tab1, tab2, tab3, tab4 = st.tabs([
            "Profit by Category", 
            "Profit Over Time", 
            "Platform Comparison", 
            "All Flips"
        ])
        
        with tab1:
            if "category" in df.columns and "net_profit" in df.columns:
                category_profit = df.groupby("category")["net_profit"].sum().reset_index()
                
                # Create a bar chart for profit by category
                fig = px.bar(
                    category_profit, 
                    x="category", 
                    y="net_profit",
                    title="Profit by Category",
                    labels={"category": "Category", "net_profit": "Net Profit ($)"},
                    color="net_profit",
                    color_continuous_scale=px.colors.sequential.Blues,
                    text="net_profit"
                )
                
                fig.update_traces(
                    texttemplate='$%{text:.2f}', 
                    textposition='outside'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            if "date" in df.columns and "net_profit" in df.columns:
                # Group by date and calculate cumulative profit
                time_profit = df.sort_values("date").groupby("date")["net_profit"].sum().reset_index()
                time_profit["cumulative_profit"] = time_profit["net_profit"].cumsum()
                
                # Create a subplot with daily profit and cumulative profit
                fig = go.Figure()
                
                # Add bar chart for daily profit
                fig.add_trace(go.Bar(
                    x=time_profit["date"],
                    y=time_profit["net_profit"],
                    name="Daily Profit",
                    marker_color="#1e88e5"
                ))
                
                # Add line chart for cumulative profit
                fig.add_trace(go.Scatter(
                    x=time_profit["date"],
                    y=time_profit["cumulative_profit"],
                    name="Cumulative Profit",
                    mode="lines+markers",
                    line=dict(color="#43a047", width=3),
                    marker=dict(size=8),
                    yaxis="y2"
                ))
                
                # Update layout with dual y-axes
                fig.update_layout(
                    title="Profit Over Time",
                    xaxis_title="Date",
                    yaxis_title="Daily Profit ($)",
                    yaxis2=dict(
                        title="Cumulative Profit ($)",
                        overlaying="y",
                        side="right",
                        showgrid=False
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Platform comparison
            if "platform" in df.columns and "net_profit" in df.columns:
                platform_data = df.groupby("platform").agg({
                    "net_profit": ["sum", "mean", "count"],
                    "roi": "mean"
                }).reset_index()
                
                platform_data.columns = ["platform", "total_profit", "avg_profit", "count", "avg_roi"]
                
                # Create a comparison table
                st.markdown("#### Platform Performance Comparison")
                
                # Format the data for display
                table_data = []
                for _, row in platform_data.iterrows():
                    table_data.append({
                        "Platform": row["platform"],
                        "Items Sold": int(row["count"]),
                        "Total Profit": f"${row['total_profit']:.2f}",
                        "Avg. Profit": f"${row['avg_profit']:.2f}",
                        "Avg. ROI": f"{row['avg_roi']:.1f}%"
                    })
                
                # Display as a styled dataframe
                st.dataframe(
                    pd.DataFrame(table_data).sort_values("Platform"),
                    use_container_width=True
                )
        
        with tab4:
            # Display all flips in a table
            if not df.empty:
                # Format columns for display
                display_df = df.copy()
                
                # Sort by timestamp (most recent first)
                if "timestamp" in display_df.columns:
                    display_df = display_df.sort_values("timestamp", ascending=False)
                
                # Format numeric columns
                for col in ["selling_price", "cost", "net_profit"]:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}" if not pd.isna(x) else "")
                
                if "roi" in display_df.columns:
                    display_df["roi"] = display_df["roi"].apply(lambda x: f"{x:.1f}%" if not pd.isna(x) else "")
                
                # Select columns to display
                display_cols = ["title", "category", "platform", "selling_price", "cost", "net_profit", "roi", "sold_date"]
                display_cols = [col for col in display_cols if col in display_df.columns]
                
                # Rename columns for display
                rename_dict = {
                    "title": "Item",
                    "category": "Category",
                    "platform": "Platform",
                    "selling_price": "Selling Price",
                    "cost": "Cost",
                    "net_profit": "Profit",
                    "roi": "ROI",
                    "sold_date": "Date Sold"
                }
                
                display_df = display_df[display_cols].rename(columns={k: v for k, v in rename_dict.items() if k in display_cols})
                
                # Display the dataframe
                st.dataframe(
                    display_df,
                    use_container_width=True
                )
                
                # Export options
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Export to CSV",
                        data=csv,
                        file_name="kwikflip_data.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Create Excel file in memory
                    from io import BytesIO
                    import pandas as pd
                    
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df.to_excel(writer, index=False, sheet_name="Flips")
                    
                    excel_data = buffer.getvalue()
                    st.download_button(
                        label="Export to Excel",
                        data=excel_data,
                        file_name="kwikflip_data.xlsx",
                        mime="application/vnd.ms-excel"
                    )
    except Exception as e:
        error_msg = f"Error displaying analytics: {e}"
        log_debug(error_msg)
        st.error(error_msg)
        st.error(traceback.format_exc())

def display_marketplace_comparison():
    """Display marketplace comparison information"""
    st.markdown("### 🛍️ Marketplace Comparison")
    
    # Create comparison data
    platforms = [
        {
            "Platform": "eBay",
            "Fee Rate": "12-15%",
            "Audience": "Global",
            "Best For": "Electronics, Collectibles, Specialty items",
            "Payment": "Secure through platform",
            "Integration": "Full API integration available"
        },
        {
            "Platform": "Facebook Marketplace",
            "Fee Rate": "0% for local, 5% for shipped",
            "Audience": "Local primarily",
            "Best For": "Furniture, Home goods, Local pickup items",
            "Payment": "Cash or peer-to-peer",
            "Integration": "No public API available"
        },
        {
            "Platform": "Craigslist",
            "Fee Rate": "$0-5 posting fee",
            "Audience": "Local only",
            "Best For": "Furniture, Free items, Local services",
            "Payment": "Cash only (typically)",
            "Integration": "No public API available"
        },
        {
            "Platform": "Amazon",
            "Fee Rate": "15% + additional fees",
            "Audience": "Global",
            "Best For": "Books, New products, High volume",
            "Payment": "Secure through platform",
            "Integration": "API available"
        },
        {
            "Platform": "Mercari",
            "Fee Rate": "10%",
            "Audience": "National",
            "Best For": "Clothing, Small items, Used goods",
            "Payment": "Secure through platform",
            "Integration": "Limited API"
        }
    ]
    
    # Display as a table
    st.table(pd.DataFrame(platforms))

def display_quick_start_guide():
    """Display quick start guide"""
    with st.expander("📚 Quick Start Guide", expanded=False):
        st.markdown("""
        ### How to Use KwikFlip
        
        1. **Search for an Item**: Enter a search term or UPC, or use Image Search to identify an item
        2. **Analyze the Results**: Review active and sold listings to understand the market
        3. **Calculate Profit**: Use the profit calculator to determine potential profit margins
        4. **Track Your Flips**: Save successful flips to track your performance over time
        5. **Make Data-Driven Decisions**: Use analytics to identify your most profitable categories and selling platforms
        
        ### Tips for Successful Flipping
        
        - **Research Thoroughly**: Always check sold prices, not just active listings
        - **Consider All Costs**: Include shipping, fees, and your time in profit calculations
        - **Start Small**: Begin with items you know well or have low investment requirements
        - **Be Platform-Flexible**: Different items sell better on different marketplaces
        """)

def main():
    """Main application function"""
    try:
        # Display header and sidebar
        display_header()
        display_sidebar()
        
        # Show recent searches
        show_recent_searches()
        
        # Show the search form
        did_search = display_search_form()
        
        # Show marketplace information if no search
        if not did_search and not st.session_state.last_search:
            st.info("🔍 Enter a search above to begin")
            
            # Display platform comparison
            display_marketplace_comparison()
            
            # Display quickstart guide
            display_quick_start_guide()
            
            return

        # Get search parameters from session state
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

        # Fetch data
        with st.spinner("Fetching data..."):
            api = st.session_state.ebay_api
            active_items, active_error = api.search_listings(query, sold=False, filters=filters)
            sold_items, sold_error = api.search_listings(query, sold=True, filters=filters)
            
            # Store items in session state
            st.session_state.active_items = active_items
            st.session_state.sold_items = sold_items
            
            # Show any errors
            if active_error:
                st.warning(f"Notice for active items: {active_error}")
            if sold_error:
                st.warning(f"Notice for sold items: {sold_error}")

        # Compute statistics
        active_stats = calculate_stats(active_items)
        sold_stats = calculate_stats(sold_items)

        # Display metrics and charts
        display_metrics(active_stats, sold_stats, api.get_fee_rate(category))
        
        # Show price distribution chart
        price_fig = generate_price_chart(active_items, sold_items)
        if price_fig:
            st.plotly_chart(price_fig, use_container_width=True)

        # Show volume chart for sold items
        volume_fig = generate_volume_chart(active_items, sold_items)
        if volume_fig:
            st.plotly_chart(volume_fig, use_container_width=True)

        # Display item listings
        st.markdown("### eBay Results")
        display_items(active_items, "Active eBay Listings", sort_options=True, pagination=True, page_size=10)
        display_items(sold_items, "Sold eBay Items (30d)", sort_options=True, pagination=True, page_size=10)

        # Show profit calculator
        display_profit_calculator(active_stats, sold_stats, cost, category, flip_type)

        # Display analytics on saved flips
        df = load_flips()
        if not df.empty:
            display_analytics(df)
        
        # Display footer
        st.markdown("""
        <div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #888; font-size: 0.8rem;">
            <p>KwikFlip - Research and track your eBay flips</p>
            <p>Version 1.0</p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        error_msg = f"An error occurred in the main function: {e}"
        log_debug(error_msg)
        log_debug(traceback.format_exc())
        st.error(error_msg)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.error(traceback.format_exc())

def test_ebay_connection():
    """Test connection to eBay API"""
    try:
        log_debug("Testing eBay API connection")
        ebay_api = EbayAPI()
        success, message = ebay_api.test_connection()
        log_debug(f"Connection test result: {success}, {message}")
        return success, message
    except Exception as e:
        error_msg = f"Error testing eBay connection: {str(e)}"
        log_debug(error_msg)
        return False, error_msg
    