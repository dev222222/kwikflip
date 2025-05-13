import time
import datetime as dt
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import requests
from io import BytesIO
from PIL import Image
import os
import json
import traceback
import uuid
import sys
import base64

# Set Streamlit page config
st.set_page_config(
    page_title="KwikFlip - eBay Research Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# For Render deployment - get PORT from environment
PORT = int(os.environ.get("PORT", 8501))

# Load environment variables from .env file if it exists
load_dotenv()

# Configuration
EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")
EBAY_DEV_ID = os.getenv("EBAY_DEV_ID")
DATA_DIR = Path("data")
FLIPS_FILE = DATA_DIR / "flips.csv"
SEARCHES_FILE = DATA_DIR / "searches.json"
MAX_RECENT_SEARCHES = 10
API_TIMEOUT = 15  # Reduced timeout for API calls

# Debug - Print environment variables to logs (not visible to users)
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"EBAY_APP_ID exists: {EBAY_APP_ID is not None and EBAY_APP_ID != ''}")
print(f"EBAY_CERT_ID exists: {EBAY_CERT_ID is not None and EBAY_CERT_ID != ''}")
print(f"EBAY_DEV_ID exists: {EBAY_DEV_ID is not None and EBAY_DEV_ID != ''}")

# eBay API endpoints - Browse API requires OAuth
EBAY_OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_BROWSE_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
EBAY_SOLD_API_URL = "https://api.ebay.com/buy/marketplace-insights/v1_beta/item_sales/search"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# Default theme colors
THEME = {
    "primary": "#1e88e5",       # Blue
    "primary_dark": "#1565c0",  # Darker blue
    "secondary": "#7cd6ef",     # Light blue
    "accent": "#ff8a65",        # Coral 
    "bg": "#ffffff",            # White
    "text": "#212121",          # Dark grey
    "light_text": "#757575",    # Medium grey
    "success": "#4caf50",       # Green
    "warning": "#ffc107",       # Yellow
    "danger": "#f44336",        # Red
    "card_bg": "#f9f9f9",       # Light grey
    "card_border": "#e0e0e0"    # Grey
}

# Custom styles
st.markdown(f"""
<style>
    /* Base styles */
    body {{
        font-family: 'Inter', sans-serif;
        color: {THEME["text"]};
        background-color: {THEME["bg"]};
    }}
    
    /* Header */
    .main-header {{
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem 0;
        background: linear-gradient(135deg, {THEME["primary"]}, {THEME["secondary"]});
        color: white;
        border-radius: 10px;
    }}
    .main-header h1 {{
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.05em;
    }}
    .main-header p {{
        opacity: 0.9;
        font-weight: 400;
    }}
    
    /* Cards */
    .card {{
        background-color: {THEME["bg"]};
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid {THEME["card_border"]};
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
    }}
    
    /* Metric cards */
    .metric-card {{
        background-color: {THEME["bg"]};
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.7rem 0;
        border-left: 4px solid {THEME["primary"]};
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }}
    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {THEME["primary"]};
        margin: 0.5rem 0;
    }}
    .metric-label {{
        font-size: 0.9rem;
        color: {THEME["light_text"]};
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Profit card */
    .profit-card {{
        background-color: rgba(76, 175, 80, 0.1);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.7rem 0;
        border-left: 4px solid {THEME["success"]};
    }}
    
    /* Loss card */
    .loss-card {{
        background-color: rgba(244, 67, 54, 0.1);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.7rem 0;
        border-left: 4px solid {THEME["danger"]};
    }}
    
    /* Item cards */
    .item-card {{
        display: flex;
        border: 1px solid {THEME["card_border"]};
        border-radius: 8px;
        padding: 1rem;
        margin: 0.7rem 0;
        background-color: {THEME["bg"]};
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .item-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
    }}
    .item-image {{
        width: 120px;
        height: 120px;
        object-fit: contain;
        border-radius: 4px;
    }}
    .item-details {{
        flex: 1;
        padding: 0 1rem;
    }}
    .item-title {{
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: {THEME["text"]};
    }}
    .item-meta {{
        font-size: 0.9rem;
        color: {THEME["light_text"]};
    }}
    .item-price {{
        font-size: 1.4rem;
        font-weight: 700;
        color: {THEME["primary"]};
        white-space: nowrap;
    }}
    .item-shipping {{
        font-size: 0.8rem;
        color: {THEME["light_text"]};
    }}
    
    /* Search form */
    .search-form {{
        background-color: {THEME["card_bg"]};
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border: 1px solid {THEME["card_border"]};
    }}
    
    /* Buttons */
    .stButton>button {{
        background-color: {THEME["primary"]};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.2s ease;
    }}
    .stButton>button:hover {{
        background-color: {THEME["primary_dark"]};
    }}
    
    /* Camera button */
    .camera-button {{
        background-color: {THEME["accent"]};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }}
    .camera-button:hover {{
        background-color: #f4511e;
    }}
    
    /* Footer */
    .footer {{
        text-align: center;
        margin-top: 3rem;
        padding: 1.5rem 0;
        font-size: 0.9rem;
        color: {THEME["light_text"]};
        border-top: 1px solid {THEME["card_border"]};
    }}
    
    /* Mobile optimizations */
    @media (max-width: 768px) {{
        .item-card {{
            flex-direction: column;
        }}
        .item-image {{
            width: 100%;
            height: auto;
            margin-bottom: 1rem;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# Session state initialization
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

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# OAuth token storage
if "ebay_oauth_token" not in st.session_state:
    st.session_state.ebay_oauth_token = None

if "ebay_token_expiry" not in st.session_state:
    st.session_state.ebay_token_expiry = 0

# --- EBAY API FUNCTIONS ---

def check_ebay_credentials():
    """Check if eBay credentials are available and valid"""
    has_app_id = EBAY_APP_ID is not None and EBAY_APP_ID != ""
    has_cert_id = EBAY_CERT_ID is not None and EBAY_CERT_ID != ""
    
    # Add to debug info
    log_debug(f"EBAY_APP_ID exists: {has_app_id}")
    log_debug(f"EBAY_CERT_ID exists: {has_cert_id}")
    
    if has_app_id and has_cert_id:
        log_debug("eBay credentials verification: PASS")
    else:
        log_debug("eBay credentials verification: FAIL")
    
    return has_app_id and has_cert_id

def log_debug(message):
    """Add message to debug log and print to console"""
    timestamp = dt.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    formatted_message = f"[{timestamp}] {message}"
    
    # Add to session state debug info
    if len(st.session_state.debug_info) > 100:
        st.session_state.debug_info = st.session_state.debug_info[-100:]
    st.session_state.debug_info.append(formatted_message)
    
    # Also print to standard output for server logs
    print(formatted_message)

def get_ebay_oauth_token():
    """Get OAuth 2.0 token from eBay"""
    try:
        log_debug("Requesting OAuth token from eBay")
        
        if not EBAY_APP_ID or not EBAY_CERT_ID:
            log_debug("Missing eBay credentials for OAuth")
            return None, "Missing eBay credentials"
        
        # Endpoint for OAuth token
        oauth_endpoint = EBAY_OAUTH_URL
        
        # Create the authorization string (Basic Auth with client ID:secret)
        auth_string = f"{EBAY_APP_ID}:{EBAY_CERT_ID}"
        encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        
        # Headers for the request
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_auth}"
        }
        
        # Request body for client credentials grant type
        # These scopes are required for the Browse API and Marketplace Insights API
        payload = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.browse https://api.ebay.com/oauth/api_scope/buy.marketplace.insights"
        }
        
        # Make the request
        response = requests.post(oauth_endpoint, headers=headers, data=payload, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            token_data = response.json()
            log_debug("Successfully retrieved OAuth token")
            
            # Store token in session state with expiration
            st.session_state.ebay_oauth_token = token_data["access_token"]
            st.session_state.ebay_token_expiry = time.time() + token_data["expires_in"] - 300  # 5 min buffer
            
            return token_data["access_token"], None
        else:
            error_msg = f"Failed to get OAuth token: HTTP {response.status_code}"
            log_debug(f"{error_msg}: {response.text[:500]}")
            return None, error_msg
    
    except Exception as e:
        error_msg = f"Error getting OAuth token: {str(e)}"
        log_debug(error_msg)
        log_debug(traceback.format_exc())
        return None, error_msg

def ensure_oauth_token():
    """Make sure we have a valid OAuth token, refresh if needed"""
    # Check if we have a token and it's not expired
    if (st.session_state.ebay_oauth_token and 
        time.time() < st.session_state.ebay_token_expiry):
        log_debug("Using existing OAuth token")
        return st.session_state.ebay_oauth_token, None
    
    # Get a new token
    log_debug("OAuth token missing or expired, requesting new one")
    return get_ebay_oauth_token()

def test_ebay_connection():
    """Test eBay API connection and return status"""
    if not check_ebay_credentials():
        return False, "Missing eBay API credentials"
    
    try:
        # Test OAuth token acquisition first
        token, error = get_ebay_oauth_token()
        if not token:
            return False, f"OAuth authentication failed: {error}"
        
        # Test a simple Browse API request
        api_endpoint = EBAY_BROWSE_API_URL
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
        
        params = {
            "q": "test",
            "limit": 1
        }
        
        log_debug("Testing eBay Browse API connection...")
        response = requests.get(api_endpoint, headers=headers, params=params, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            log_debug(f"eBay Browse API connection test: SUCCESS (Status: {response.status_code})")
            return True, "Connection successful"
        else:
            log_debug(f"eBay Browse API connection test: FAILED (Status: {response.status_code})")
            log_debug(f"Response: {response.text[:500]}")
            return False, f"eBay Browse API returned status code {response.status_code}"
    
    except Exception as e:
        error_message = f"eBay Browse API connection test: ERROR ({str(e)})"
        log_debug(error_message)
        log_debug(traceback.format_exc())
        return False, error_message

def search_ebay_browse(query, sold=False, filters=None, limit=30):
    """Search for items using eBay Browse API"""
    try:
        log_debug(f"Searching eBay Browse API for '{query}' (sold={sold})")
        
        # Get OAuth token - Browse API requires OAuth 2.0 authentication
        token, error = ensure_oauth_token()
        if not token:
            return None, f"Failed to authenticate with eBay: {error}"
        
        # Endpoint URLs - different for active vs sold items
        if sold:
            # For sold items we need to use the Marketplace Insights API
            api_endpoint = EBAY_SOLD_API_URL
            log_debug(f"Using Marketplace Insights API for sold items")
        else:
            # For active items we use the Browse API
            api_endpoint = EBAY_BROWSE_API_URL
            log_debug(f"Using Browse API for active items")
        
        # Headers for the request
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
        
        # Base parameters
        params = {
            "q": query,
            "limit": min(limit, 200)  # API max is 200
        }
        
        # Add filters based on provided parameters
        filter_array = []
        
        if filters:
            # Price filters
            if filters.get('min_price') is not None and filters.get('min_price') > 0:
                if filters.get('max_price') is not None:
                    filter_array.append(f"price:[{filters['min_price']}..{filters['max_price']}]")
                else:
                    filter_array.append(f"price:[{filters['min_price']}..)")
            elif filters.get('max_price') is not None:
                filter_array.append(f"price:[..{filters['max_price']}]")
            
            # Condition filters - convert to Browse API format
            if filters.get('condition') and filters['condition'] != 'any':
                condition_map = {
                    'new': 'NEW',
                    'used': 'USED',
                    'for parts or not working': 'FOR_PARTS_OR_NOT_WORKING'
                }
                cond = condition_map.get(filters['condition'])
                if cond:
                    filter_array.append(f"conditions:{{{cond}}}")
        
        # Join all filters with comma
        if filter_array:
            params["filter"] = ",".join(filter_array)
        
        log_debug(f"Making eBay Browse API request to: {api_endpoint}")
        log_debug(f"Browse API params: {params}")
        
        # Make the request
        response = requests.get(api_endpoint, headers=headers, params=params, timeout=API_TIMEOUT)
        
        # Log response status
        log_debug(f"eBay Browse API response status: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"eBay Browse API returned status code {response.status_code}"
            log_debug(error_msg)
            
            # Try to get more info from the response
            try:
                error_details = response.text[:500]  # Get first 500 chars
                log_debug(f"Response content: {error_details}")
            except:
                pass
                
            return None, error_msg
        
        # Parse the response
        data = response.json()
        
        # The structure is different between active and sold APIs
        if sold:
            # For sold items (Marketplace Insights API)
            items_list = data.get("itemSales", [])
            total_items = data.get("total", 0)
        else:
            # For active items (Browse API)
            items_list = data.get("itemSummaries", [])
            total_items = data.get("total", 0)
        
        log_debug(f"Found {len(items_list)} items in Browse API response (total available: {total_items})")
        
        if not items_list:
            return [], "No items found matching your search criteria"
        
        # Convert to our standard format
        items = []
        for item in items_list:
            try:
                # Extract common data first
                item_id = item.get("itemId", "")
                title = item.get("title", "Untitled Item")
                
                # Then handle differences between active and sold items
                if sold:
                    # For sold items
                    url = f"https://www.ebay.com/itm/{item_id}" # Construct URL
                    image_url = item.get("image", {}).get("imageUrl", "https://via.placeholder.com/150")
                    price = float(item.get("lastSoldPrice", {}).get("value", 0))
                    shipping = float(item.get("shippingCost", {}).get("value", 0)) if item.get("shippingCost") else 0.0
                    end_time = item.get("lastSoldDate", dt.datetime.now().isoformat())
                    condition = item.get("condition", "Not Specified")
                    watchers = 0  # Not available for sold items
                else:
                    # For active items
                    url = item.get("itemWebUrl", f"https://www.ebay.com/itm/{item_id}")
                    image_url = item.get("image", {}).get("imageUrl", "https://via.placeholder.com/150")
                    price = float(item.get("price", {}).get("value", 0))
                    shipping = float(item.get("shippingOptions", [{}])[0].get("shippingCost", {}).get("value", 0)) if item.get("shippingOptions") else 0.0
                    end_time = item.get("itemEndDate", dt.datetime.now().isoformat())
                    condition = item.get("condition", "Not Specified")
                    watchers = item.get("watchCount", 0)
                
                # Build item dictionary in our standard format
                item_data = {
                    "id": item_id,
                    "title": title,
                    "url": url,
                    "image": image_url,
                    "price": price,
                    "shipping": shipping,
                    "end_time": end_time,
                    "watchers": watchers,
                    "condition": condition,
                    "sold": sold
                }
                
                items.append(item_data)
                
            except Exception as e:
                error_msg = f"Error processing Browse API item: {e}"
                log_debug(error_msg)
                log_debug(traceback.format_exc())
                # Continue processing other items
        
        return items, None
        
    except Exception as e:
        error_msg = f"Error calling eBay Browse API: {e}"
        log_debug(error_msg)
        log_debug(traceback.format_exc())
        
        return None, error_msg

def process_image_search(image_data):
    """
    Process image for search (in a real implementation, this would
    use eBay's Image Recognition API or a similar service)
    """
    log_debug("Processing image for search")
    
    # In a real implementation, we would send the image to eBay's API
    # For now, we'll just return a simulated result
    categories = [
        "Electronics", "Clothing", "Collectibles", 
        "Home & Garden", "Toys", "Books", "Other"
    ]
    
    import random
    
    # Simulate API recognition result
    simulated_results = {
        "query": random.choice([
            "vintage camera", "smartphone", "retro game console", 
            "designer watch", "collectible figurine"
        ]),
        "category": random.choice(categories),
        "confidence": random.uniform(0.65, 0.95)
    }
    
    log_debug(f"Image recognition result: {simulated_results}")
    
    return simulated_results

def generate_mock_items(count, sold=False):
    """Generate mock item data for demonstration purposes"""
    import random
    from datetime import datetime, timedelta
    
    log_debug(f"Generating {count} mock {'sold' if sold else 'active'} items")
    
    items = []
    conditions = ["New", "Used", "Like New", "For parts or not working"]
    
    for i in range(count):
        # Create random end time within the last 30 days if sold, or future date if active
        if sold:
            days_ago = random.randint(1, 30)
            end_time = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        else:
            days_future = random.randint(1, 7)
            end_time = (datetime.now() + timedelta(days=days_future)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Create random price between $10 and $100
        price = round(random.uniform(10, 100), 2)
        
        # Create random shipping cost between $0 and $15
        shipping = round(random.uniform(0, 15), 2)
        
        # Generate item
        item = {
            "id": f"mock-{i}-{random.randint(10000, 99999)}",
            "title": f"Mock Item {i+1} - Demo Product",
            "url": "https://www.ebay.com",
            "image": "https://via.placeholder.com/150",
            "price": price,
            "shipping": shipping,
            "end_time": end_time,
            "watchers": random.randint(0, 20),
            "condition": random.choice(conditions),
            "sold": sold
        }
        
        items.append(item)
    
    return items

def get_fee_rate(category):
    """Get eBay fee rate for a category"""
    fee_rates = {
        "Electronics": 0.12,
        "Clothing": 0.13,
        "Collectibles": 0.125,
        "Home & Garden": 0.12,
        "Toys": 0.125,
        "Books": 0.145,
        "Other": 0.13
    }
    return fee_rates.get(category, 0.13)

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

# --- DATA HANDLING FUNCTIONS ---

def load_recent_searches():
    """Load recent searches from file"""
    if os.path.exists(SEARCHES_FILE):
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
        # Create directory if it doesn't exist
        DATA_DIR.mkdir(exist_ok=True)
        
        with open(SEARCHES_FILE, "w") as f:
            json.dump(st.session_state.recent_searches, f)
        
        log_debug(f"Saved {len(st.session_state.recent_searches)} recent searches to {SEARCHES_FILE}")
        return True
    except Exception as e:
        error_msg = f"Error saving recent searches: {e}"
        log_debug(error_msg)
        st.error(error_msg)
        return False

def fetch_items(query, sold=False, filters=None, limit=30):
    """Fetch items from eBay API or generate mock data"""
    try:
        # Log start of fetch operation
        log_debug(f"Fetching {'sold' if sold else 'active'} items for query: '{query}'")
        
        # Check if eBay credentials are available
        has_credentials = check_ebay_credentials()
        
        if has_credentials:
            log_debug("Attempting to use eBay Browse API")
            try:
                # Attempt to use the eBay Browse API
                items, error = search_ebay_browse(query, sold, filters, limit)
                
                if items is not None:
                    log_debug(f"Successfully retrieved {len(items)} items from eBay Browse API")
                    return items, None
                else:
                    error_msg = f"eBay Browse API error: {error}. Falling back to mock data."
                    log_debug(error_msg)
                    st.warning(error_msg)
                    # Fall through to mock data
            except Exception as e:
                error_msg = f"Error with eBay Browse API: {e}. Falling back to mock data."
                log_debug(error_msg)
                
                # Get full traceback
                tb = traceback.format_exc()
                log_debug(f"Traceback: {tb}")
                
                st.warning(error_msg)
                # Fall through to mock data
        else:
            log_debug("eBay credentials not found or invalid")
            st.info("Using mock data for demonstration. eBay API integration is being configured.")
        
        # Generate mock items as fallback
        mock_items = []
        try:
            log_debug("Generating mock data as fallback")
            mock_items = generate_mock_items(count=limit, sold=sold)
            log_debug(f"Generated {len(mock_items)} mock items")
        except Exception as e:
            error_msg = f"Error generating mock items: {e}"
            log_debug(error_msg)
            st.error(error_msg)
            
            # Provide basic fallback items
            for i in range(3):
                mock_items.append({
                    "id": f"fallback-{i}",
                    "title": f"Sample Item {i+1}",
                    "url": "https://www.ebay.com",
                    "image": "https://via.placeholder.com/150",
                    "price": 29.99,
                    "shipping": 4.99,
                    "end_time": dt.datetime.now().isoformat(),
                    "watchers": 5,
                    "condition": "Used",
                    "sold": sold
                })
        
        return mock_items, None
    except Exception as e:
        error_msg = f"Error in fetch_items: {e}"
        log_debug(error_msg)
        log_debug(traceback.format_exc())
        
        st.error(error_msg)
        return [], None

def load_flips():
    """Load saved flips from CSV file"""
    if not os.path.exists(FLIPS_FILE):
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
        data["timestamp"] = dt.datetime.now().isoformat()
        
        # Append new flip
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        
        # Create directory if it doesn't exist
        DATA_DIR.mkdir(exist_ok=True)
        
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

# --- UI AND DISPLAY FUNCTIONS ---

def display_header():
    """Display app header with logo and title"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 KwikFlip</h1>
        <p>Research, track, and analyze your eBay flips</p>
    </div>
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
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("KwikFlip helps you research potential flips on eBay and track your profits.")
        
        # Show eBay API status
        st.markdown("---")
        has_credentials = check_ebay_credentials()
        if has_credentials:
            st.success("✅ eBay API credentials configured")
            
            # Add API test button
            if st.button("Test eBay Connection"):
                with st.spinner("Testing connection..."):
                    success, message = test_ebay_connection()
                    if success:
                        st.success("✅ eBay API connection successful")
                    else:
                        st.error(f"❌ {message}")
        else:
            st.warning("⚠️ eBay API credentials not found")
            if EBAY_APP_ID is None or EBAY_APP_ID == "":
                st.error("EBAY_APP_ID is missing")
            if EBAY_CERT_ID is None or EBAY_CERT_ID == "":
                st.error("EBAY_CERT_ID is missing")
        
        # Debug info
        with st.expander("Show Debug Info", expanded=False):
            st.markdown("### Debug Information")
            
            # System info
            st.markdown("#### System Info")
            st.text(f"Session ID: {st.session_state.session_id[:8]}...")
            st.text(f"Python: {sys.version.split(' ')[0]}")
            
            # Environment variables (sanitized)
            st.markdown("#### Environment Variables")
            st.text(f"EBAY_APP_ID: {'✓ Set' if EBAY_APP_ID else '✗ Missing'}")
            st.text(f"EBAY_CERT_ID: {'✓ Set' if EBAY_CERT_ID else '✗ Missing'}")
            st.text(f"EBAY_DEV_ID: {'✓ Set' if EBAY_DEV_ID else '✗ Missing'}")
            
            # OAuth Token status
            st.markdown("#### OAuth Token Status")
            has_token = st.session_state.ebay_oauth_token is not None
            token_valid = (has_token and time.time() < st.session_state.ebay_token_expiry)
            st.text(f"OAuth Token: {'✓ Valid' if token_valid else '✗ Invalid or Missing'}")
            if token_valid:
                expires_in = int(st.session_state.ebay_token_expiry - time.time())
                st.text(f"Token expires in: {expires_in} seconds")
            
            # Refresh token button
            if st.button("Refresh OAuth Token"):
                with st.spinner("Getting new token..."):
                    token, error = get_ebay_oauth_token()
                    if token:
                        st.success("✅ New OAuth token acquired")
                    else:
                        st.error(f"❌ Failed to get token: {error}")
            
            # Log display
            st.markdown("#### Log")
            st.text_area("Debug Log", value="\n".join(st.session_state.debug_info), height=400)
            
            # Clear logs button
            if st.button("Clear Logs"):
                st.session_state.debug_info = []
                st.rerun()

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
                    end_date = dt.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.000Z")
                    formatted_date = end_date.strftime("%b %d, %Y")
                except:
                    formatted_date = end_time
            
            # Create a card for each item
            st.markdown(f"""
            <div class="item-card">
                <div style="flex: 0 0 120px; margin-right: 15px;">
                    <img src="{item.get('image', 'https://via.placeholder.com/150')}" class="item-image" alt="{item.get('title', 'Item')}">
                </div>
                <div style="flex: 1;">
                    <div class="item-title">{item.get('title', 'Untitled Item')}</div>
                    <div class="item-meta">Condition: {item.get('condition', 'N/A')}</div>
                    <div class="item-meta">{'Sold on' if item.get('sold') else 'Ends'}: {formatted_date}</div>
                    {f'<div class="item-meta">Watchers: {item["watchers"]}</div>' if item.get('watchers', 0) > 0 else ''}
                </div>
                <div style="flex: 0 0 100px; text-align: right;">
                    <div class="item-price">${item.get('price', 0):.2f}</div>
                    {f'<div class="item-shipping">+${item["shipping"]:.2f} shipping</div>' if item.get('shipping', 0) > 0 else ''}
                    <a href="{item.get('url', '#')}" target="_blank" class="st-emotion-cache-19rxjzo e1ewe7hr1" style="display: inline-block; margin-top: 10px;">View Item</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        error_msg = f"Error displaying items: {e}"
        log_debug(error_msg)
        st.error(error_msg)

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
    
    # Only display if we have searches
    if st.session_state.recent_searches:
        with st.expander("📜 Recent Searches", expanded=False):
            for i, search in enumerate(st.session_state.recent_searches):
                # Display search info with better styling
                try:
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    # Query and category
                    col1.markdown(f"""
                    <div style="padding: 10px 0;">
                        <div style="font-weight: 600;">{search['query']}</div>
                        <div style="font-size: 0.8rem; color: {THEME['light_text']};">{search.get('category', 'Unknown')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Timestamp
                    timestamp = "N/A"
                    if 'timestamp' in search:
                        try:
                            timestamp_str = search['timestamp']
                            if isinstance(timestamp_str, str):
                                try:
                                    timestamp = dt.datetime.fromisoformat(timestamp_str).strftime("%m/%d/%Y %I:%M %p")
                                except ValueError:
                                    timestamp = timestamp_str
                            else:
                                timestamp = str(timestamp_str)
                        except Exception:
                            timestamp = str(search.get('timestamp', 'N/A'))
                    
                    col2.markdown(f"""
                    <div style="padding: 10px 0; font-size: 0.9rem; color: {THEME['light_text']};">
                        {timestamp}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Load button
                    if col3.button("Load", key=f"load_search_{i}"):
                        st.session_state.last_search = search
                        log_debug(f"Loaded search: {search['query']}")
                        st.rerun()
                
                except Exception as e:
                    error_msg = f"Error displaying search #{i+1}: {str(e)}"
                    log_debug(error_msg)
                    st.warning(error_msg)

def display_search_form():
    """Display search form and handle submission"""
    st.markdown("### 🔎 Search for Items")
    
    # Tab-based search options
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
                    "timestamp": dt.datetime.now().isoformat()
                }
                
                st.session_state.last_search = search_data
                
                # Save to recent searches
                if search_data not in st.session_state.recent_searches:
                    st.session_state.recent_searches.insert(0, search_data)
                    if len(st.session_state.recent_searches) > MAX_RECENT_SEARCHES:
                        st.session_state.recent_searches = st.session_state.recent_searches[:MAX_RECENT_SEARCHES]
                    
                    # Save to file
                    save_recent_searches()
                
                log_debug(f"Submitted search: {query}")
                return True
    
    with camera_tab:
        process_camera_photo()
    
    return False

def process_camera_photo():
    """Capture and process a photo from the webcam"""
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
                # In a real implementation, this would call eBay's image recognition API
                # For now, we'll use our simulated function
                recognition_result = process_image_search(camera_input)
                
                # Create a search based on the image recognition
                image_search = {
                    "query": recognition_result["query"],
                    "is_upc": False,
                    "flip_type": "Thrift Flip",  # Default for image searches
                    "cost": 0.0,
                    "category": recognition_result["category"],
                    "photo": None,  # We don't need to store the photo again
                    "timestamp": dt.datetime.now().isoformat(),
                    "image_search": True         # Flag to indicate this was an image search
                }
                
                st.session_state.last_search = image_search
                
                # Save to recent searches
                if image_search not in st.session_state.recent_searches:
                    st.session_state.recent_searches.insert(0, image_search)
                    if len(st.session_state.recent_searches) > MAX_RECENT_SEARCHES:
                        st.session_state.recent_searches = st.session_state.recent_searches[:MAX_RECENT_SEARCHES]
                    
                    # Save to file
                    save_recent_searches()
                
                st.success(f"Image recognized as: '{recognition_result['query']}' (Confidence: {recognition_result['confidence']:.0%})")
                log_debug(f"Image search completed: {recognition_result['query']}")
                st.rerun()

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
    cols[0].markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Active Listings</div>
        <div class="metric-value">{active_stats['count']}</div>
        <div>Avg: ${active_stats['avg_price']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metric 2: Sold Listings
    cols[1].markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sold Listings</div>
        <div class="metric-value">{sold_stats['count']}</div>
        <div>Avg: ${sold_stats['avg_price']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metric 3: Sell-Through Rate
    cols[2].markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sell-Through Rate</div>
        <div class="metric-value">{sell_through_rate:.1f}%</div>
        <div>In the last {st.session_state.filter_settings["days_sold"]} days</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metric 4: Price Difference
    card_class = "profit-card" if price_diff >= 0 else "loss-card"
    cols[3].markdown(f"""
    <div class="{card_class}">
        <div class="metric-label">Price Difference</div>
        <div class="metric-value">${abs(price_diff):.2f}</div>
        <div>{price_diff_percent:.1f}% {'higher' if price_diff >= 0 else 'lower'} when sold</div>
    </div>
    """, unsafe_allow_html=True)

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
                marker_color=THEME["primary"],
                opacity=0.7
            ))
        if sold_prices:
            fig.add_trace(go.Histogram(
                x=sold_prices,
                nbinsx=10,
                name="Sold Listings",
                marker_color=THEME["success"],
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
                    date = dt.datetime.strptime(item["end_time"], "%Y-%m-%dT%H:%M:%S.000Z")
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
            marker_color=THEME["success"],
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
            st.markdown("""
            <div style="padding: 10px 0; margin-bottom: 15px;">
                <div style="font-weight: 600; font-size: 1.1rem;">Item Details</div>
            </div>
            """, unsafe_allow_html=True)
            
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
                "eBay": get_fee_rate(category),
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
            
            # Determine card style based on profit
            card_class = "profit-card" if net_profit > 0 else "loss-card"
            
            st.markdown("""
            <div style="padding: 10px 0; margin-bottom: 15px;">
                <div style="font-weight: 600; font-size: 1.1rem;">Profit Analysis</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display profit breakdown with improved styling
            st.markdown(f"""
            <div class="{card_class}">
                <h4 style="margin-top: 0;">Profit Breakdown</h4>
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
                
                <div style="display: flex; justify-content: space-between; margin: 10px 0; font-weight: 700; font-size: 1.2rem;">
                    <span>Net Profit:</span>
                    <span>${net_profit:.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                    <span>ROI:</span>
                    <span>{roi:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add platform comparison
            if platform != "eBay":
                ebay_fee_rate = get_fee_rate(category)
                ebay_fee = total_rev * ebay_fee_rate
                ebay_profit = total_rev - ebay_fee - shipping_cost - your_cost
                
                if ebay_profit > net_profit:
                    st.markdown(f"""
                    <div style="background-color: rgba(255, 193, 7, 0.1); border-left: 4px solid {THEME["warning"]}; padding: 10px; margin-top: 15px; border-radius: 4px;">
                        <div style="font-weight: 600;">Platform Insight</div>
                        <p>Selling on eBay might give you ${ebay_profit - net_profit:.2f} more profit for this item.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Save button with improved styling
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
                    "sold_date": dt.datetime.now().strftime("%Y-%m-%d"),
                    "notes": notes
                }
                
                # Save the flip
                if save_flip(flip_data):
                    st.success("Flip saved successfully!")
                else:
                    st.error("Failed to save flip. Please try again.")
    
    with insights_tab:
        # Market-based suggestions
        st.markdown("""
        <div style="padding: 10px 0;">
            <div style="font-weight: 600; font-size: 1.1rem;">Market-Based Recommendations</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate platform recommendations based on item category
        best_platform, reason = get_recommended_platform(category, sold_stats["avg_price"], st.session_state.filter_settings["condition"])
        
        # Display recommendation
        st.markdown(f"""
        <div class="card" style="margin-bottom: 20px;">
            <div style="font-weight: 600; margin-bottom: 10px;">Recommended Platform: {best_platform}</div>
            <p>{reason}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add price recommendation
        target_price = sold_stats["avg_price"]
        if sold_stats["median_price"] > sold_stats["avg_price"]:
            # If median is higher than average, suggest a price between them
            target_price = (sold_stats["median_price"] + sold_stats["avg_price"]) / 2
        
        price_rec = max(target_price * 0.95, your_cost * 1.3)  # Ensure at least 30% ROI
        
        st.markdown(f"""
        <div class="card">
            <div style="font-weight: 600; margin-bottom: 10px;">Pricing Strategy</div>
            <p>Based on market data, we recommend pricing at <b>${price_rec:.2f}</b></p>
            <ul style="padding-left: 20px;">
                <li>Market average is ${sold_stats["avg_price"]:.2f}</li>
                <li>Median sold price is ${sold_stats["median_price"]:.2f}</li>
                <li>Competitive pricing may increase sell-through rate</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

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
        
        # Key metrics with improved styling
        col1, col2, col3, col4 = st.columns(4)
        
        total_flips = len(df)
        total_profit = df["net_profit"].sum() if "net_profit" in df.columns else 0
        avg_roi = df["roi"].mean() if "roi" in df.columns else 0
        total_invested = df["cost"].sum() if "cost" in df.columns else 0
        
        col1.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Flips</div>
            <div class="metric-value">{total_flips}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col2.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Profit</div>
            <div class="metric-value">${total_profit:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col3.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Average ROI</div>
            <div class="metric-value">{avg_roi:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        col4.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Invested</div>
            <div class="metric-value">${total_invested:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
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
                
                # Create an improved bar chart for profit by category
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
                
                # Improve the figure styling
                fig.update_traces(
                    texttemplate='$%{text:.2f}', 
                    textposition='outside'
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=40, r=40, t=60, b=40),
                    title_font_size=16
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add additional insight
                if len(category_profit) > 1:
                    best_category = category_profit.loc[category_profit["net_profit"].idxmax()]
                    st.markdown(f"""
                    <div style="background-color: rgba(76, 175, 80, 0.1); border-left: 4px solid {THEME["success"]}; padding: 10px; margin-top: 15px; border-radius: 4px;">
                        <div style="font-weight: 600;">Category Insight</div>
                        <p>Your most profitable category is <b>{best_category['category']}</b> with ${best_category['net_profit']:.2f} in profits. Consider focusing more on this category.</p>
                    </div>
                    """, unsafe_allow_html=True)
        
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
                    marker_color=THEME["primary"]
                ))
                
                # Add line chart for cumulative profit
                fig.add_trace(go.Scatter(
                    x=time_profit["date"],
                    y=time_profit["cumulative_profit"],
                    name="Cumulative Profit",
                    mode="lines+markers",
                    line=dict(color=THEME["success"], width=3),
                    marker=dict(size=8),
                    yaxis="y2"
                ))
                
                # Update layout with dual y-axes
                fig.update_layout(
                    title="Profit Over Time",
                    title_font_size=16,
                    xaxis_title="Date",
                    yaxis_title="Daily Profit ($)",
                    yaxis2=dict(
                        title="Cumulative Profit ($)",
                        overlaying="y",
                        side="right",
                        showgrid=False
                    ),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=40, r=40, t=60, b=40),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    ),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add trend analysis if we have at least 3 data points
                if len(time_profit) >= 3:
                    recent_trend = time_profit.iloc[-3:]["net_profit"].mean()
                    overall_avg = time_profit["net_profit"].mean()
                    
                    trend_text = "Your recent profit trend is similar to your overall average."
                    if recent_trend > overall_avg * 1.2:
                        trend_text = "Your profits are trending upward! Your recent average is higher than your overall average."
                    elif recent_trend < overall_avg * 0.8:
                        trend_text = "Your profits are trending downward. Your recent average is lower than your overall average."
                    
                    st.markdown(f"""
                    <div style="background-color: rgba(33, 150, 243, 0.1); border-left: 4px solid {THEME["primary"]}; padding: 10px; margin-top: 15px; border-radius: 4px;">
                        <div style="font-weight: 600;">Trend Analysis</div>
                        <p>{trend_text}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab3:
            # Platform comparison (if we have platform data)
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
                    use_container_width=True,
                    hide_index=True
                )
                
                # Create a pie chart for platform distribution
                fig = px.pie(
                    platform_data,
                    values="count",
                    names="platform",
                    title="Sales by Platform",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=40, b=20),
                    title_font_size=16
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add bubble chart for profit vs. ROI by platform
                fig = px.scatter(
                    platform_data,
                    x="avg_profit",
                    y="avg_roi",
                    size="count",
                    color="total_profit",
                    hover_name="platform",
                    text="platform",
                    title="Platform Comparison: Profit vs. ROI",
                    labels={
                        "avg_profit": "Average Profit per Item ($)",
                        "avg_roi": "Average ROI (%)",
                        "count": "Number of Items Sold"
                    },
                    color_continuous_scale=px.colors.sequential.Blues
                )
                
                fig.update_traces(
                    textposition="top center",
                    marker=dict(sizemode="area", sizeref=0.1)
                )
                
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=40, r=40, t=60, b=40),
                    title_font_size=16
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            # Display all flips in a table with improved UI
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
                    use_container_width=True,
                    hide_index=True
                )
                
                # Export options
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Export Flips to CSV", type="primary"):
                        # Export full data
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name="kwikflip_data.csv",
                            mime="text/csv"
                        )
                
                with col2:
                    # Add Excel export option
                    if st.button("Export Flips to Excel"):
                        # Create Excel file in memory
                        excel_buffer = BytesIO()
                        with pd.ExcelWriter(excel_buffer) as writer:
                            df.to_excel(writer, index=False, sheet_name="Flips")
                        
                        excel_data = excel_buffer.getvalue()
                        st.download_button(
                            label="Download Excel",
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
            "platform": "eBay",
            "fee_rate": "12-15%",
            "audience": "Global",
            "best_for": "Electronics, Collectibles, Specialty items",
            "payment": "Secure through platform",
            "integration": "Full API integration available"
        },
        {
            "platform": "Facebook Marketplace",
            "fee_rate": "0% for local, 5% for shipped",
            "audience": "Local primarily",
            "best_for": "Furniture, Home goods, Local pickup items",
            "payment": "Cash or peer-to-peer",
            "integration": "No public API available"
        },
        {
            "platform": "Craigslist",
            "fee_rate": "$0-5 posting fee",
            "audience": "Local only",
            "best_for": "Furniture, Free items, Local services",
            "payment": "Cash only (typically)",
            "integration": "No public API available"
        }
    ]
    
    # Display as a table
    st.dataframe(
        pd.DataFrame(platforms),
        use_container_width=True,
        hide_index=True
    )

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

# --- DEBUG ROUTE ---

def debug_page():
    """Display debug information page"""
    st.title("🔍 KwikFlip Debug Page")
    
    st.write("### System Information")
    st.code(f"""
Python Version: {sys.version}
Working Directory: {os.getcwd()}
Data Directory: {DATA_DIR}
Session ID: {st.session_state.session_id}
    """)
    
    st.write("### Environment Variables")
    st.code(f"""
EBAY_APP_ID: {'✓ Set' if EBAY_APP_ID else '✗ Missing'}
EBAY_CERT_ID: {'✓ Set' if EBAY_CERT_ID else '✗ Missing'}
EBAY_DEV_ID: {'✓ Set' if EBAY_DEV_ID else '✗ Missing'}
    """)
    
    # Test eBay connection
    st.write("### eBay API Connection")
    if st.button("Test eBay API Connection"):
        with st.spinner("Testing connection..."):
            success, message = test_ebay_connection()
            if success:
                st.success(f"✅ Connection successful: {message}")
            else:
                st.error(f"❌ Connection failed: {message}")
    
    # OAuth token detail section
    st.write("### OAuth Token Status")
    
    has_token = st.session_state.ebay_oauth_token is not None
    token_valid = (has_token and time.time() < st.session_state.ebay_token_expiry)
    
    if has_token:
        # Show token info (partially masked)
        token_sample = f"{st.session_state.ebay_oauth_token[:10]}...{st.session_state.ebay_oauth_token[-10:]}"
        st.write(f"Token: {token_sample}")
        
        # Show expiry info
        if token_valid:
            expires_in = int(st.session_state.ebay_token_expiry - time.time())
            st.success(f"Token is valid for {expires_in} more seconds")
        else:
            st.error("Token has expired")
    else:
        st.warning("No OAuth token in session")
    
    # Button to get a new token
    if st.button("Get New OAuth Token"):
        with st.spinner("Requesting OAuth token..."):
            token, error = get_ebay_oauth_token()
            if token:
                st.success("Successfully acquired OAuth token")
            else:
                st.error(f"Failed to get token: {error}")
    
    # Session state explorer
    st.write("### Session State")
    with st.expander("Session State Explorer", expanded=False):
        session_dict = {k: v for k, v in st.session_state.items() if k not in ["debug_info", "ebay_oauth_token"]}
        st.json(session_dict)
    
    # Debug log
    st.write("### Debug Log")
    st.code("\n".join(st.session_state.debug_info))
    
    # Data files
    st.write("### Data Files")
    if os.path.exists(FLIPS_FILE):
        st.write(f"Flips file exists: {FLIPS_FILE}")
        df = load_flips()
        st.write(f"Contains {len(df)} flips")
    else:
        st.write(f"Flips file does not exist: {FLIPS_FILE}")
    
    if os.path.exists(SEARCHES_FILE):
        st.write(f"Searches file exists: {SEARCHES_FILE}")
        try:
            with open(SEARCHES_FILE, "r") as f:
                searches = json.load(f)
            st.write(f"Contains {len(searches)} saved searches")
        except Exception as e:
            st.write(f"Error reading searches file: {e}")
    else:
        st.write(f"Searches file does not exist: {SEARCHES_FILE}")

# --- MAIN APPLICATION FUNCTION ---

def main():
    """Main application function"""
    try:
        # Show debug page if query parameter is present
        params = st.query_params  # QueryParams proxy object
        if params.get("debug") is not None:  # works for ?debug or ?debug=1
            debug_page()
            return
            
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
            
            # Display platform comparison
            display_marketplace_comparison()
            
            # Display quickstart guide
            display_quick_start_guide()
            
            return

        # 4) Get search parameters from session state
        search = st.session_state.last_search
        query     = search["query"]
        is_upc    = search.get("is_upc", False)
        flip_type = search.get("flip_type", "Retail Arbitrage")
        cost      = search.get("cost", 0.0)
        category  = search.get("category", "Electronics")
        filters   = st.session_state.filter_settings
        
        # Check if this was an image search
        is_image_search = search.get("image_search", False)
        if is_image_search:
            st.info(f"📸 Image Search: Recognized as '{query}'")

        # 5) Fetch data  
        with st.spinner("Fetching data..."):
            active_items, active_error = fetch_items(query, sold=False, filters=filters)
            sold_items, sold_error = fetch_items(query, sold=True, filters=filters)
            
            # Store items in session state
            st.session_state.active_items = active_items
            st.session_state.sold_items = sold_items
            
            # Show any errors
            if active_error:
                st.warning(f"Notice for active items: {active_error}")
            if sold_error:
                st.warning(f"Notice for sold items: {sold_error}")

        # 6) Compute statistics  
        active_stats = calculate_stats(active_items)
        sold_stats   = calculate_stats(sold_items)

        # 7) Display metrics and charts  
        display_metrics(active_stats, sold_stats, get_fee_rate(category))
        
        # 8) Show price distribution chart
        price_fig = generate_price_chart(active_items, sold_items)
        if price_fig:
            st.plotly_chart(price_fig, use_container_width=True)

        # 9) Show volume chart for sold items
        volume_fig = generate_volume_chart(active_items, sold_items)
        if volume_fig:
            st.plotly_chart(volume_fig, use_container_width=True)

        # 10) Display item listings
        st.markdown("### eBay Results")
        display_items(active_items, "Active eBay Listings", sort_options=True, pagination=True, page_size=10)
        display_items(sold_items, "Sold eBay Items (30d)", sort_options=True, pagination=True, page_size=10)

        # 11) Show profit calculator  
        display_profit_calculator(active_stats, sold_stats, cost, category, flip_type)

        # 12) Display analytics on saved flips  
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
        log_debug(traceback.format_exc())
        st.error(error_msg)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.error(traceback.format_exc())
