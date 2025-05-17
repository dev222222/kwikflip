import os
from dotenv import load_dotenv
import traceback

# Import our EbayAPI class
from src.api.ebay_api import EbayAPI

def test_ebay_api():
    """Test eBay API integration"""
    print("Testing eBay API integration...")
    
    # Load environment variables
    load_dotenv()
    
    # Print environment variables (masked)
    app_id = os.getenv("EBAY_APP_ID")
    cert_id = os.getenv("EBAY_CERT_ID")
    dev_id = os.getenv("EBAY_DEV_ID")
    
    print(f"EBAY_APP_ID: {'✓ Set' if app_id else '✗ Missing'}")
    print(f"EBAY_CERT_ID: {'✓ Set' if cert_id else '✗ Missing'}")
    print(f"EBAY_DEV_ID: {'✓ Set' if dev_id else '✗ Missing'}")
    
    # Create a mock session state
    import streamlit as st
    if not hasattr(st, 'session_state'):
        class SessionState:
            pass
        st.session_state = SessionState()
        st.session_state.ebay_oauth_token = None
        st.session_state.ebay_token_expiry = 0
    
    # Initialize API
    api = EbayAPI()
    
    # Test OAuth token generation
    print("\n1. Testing OAuth token generation...")
    token, error = api.get_oauth_token()
    
    if error:
        print(f"❌ Error getting OAuth token: {error}")
    else:
        print(f"✅ Successfully obtained OAuth token: {token[:10]}...")
        
        # Test fetching active items
        print("\n2. Testing fetching active items...")
        items, error = api.fetch_items("iphone", sold=False)
        
        if error:
            print(f"❌ Error fetching active items: {error}")
        else:
            print(f"✅ Successfully fetched {len(items)} active items")
            
            # Print first item
            if items:
                print("\nSample item:")
                for key, value in items[0].items():
                    print(f"  {key}: {value}")

if __name__ == "__main__":
    try:
        test_ebay_api()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()