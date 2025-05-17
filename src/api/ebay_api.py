# src/api/ebay_api.py
import os
import requests
import base64
import time
import json
from datetime import datetime
import streamlit as st

class EbayAPI:
    def __init__(self):
        self.app_id = os.getenv("EBAY_APP_ID")
        self.cert_id = os.getenv("EBAY_CERT_ID")
        self.dev_id = os.getenv("EBAY_DEV_ID")
        self.use_mock = True  # Toggle for using mock data
        
    def set_credentials(self, app_id=None, cert_id=None, dev_id=None):
        """Set eBay credentials programmatically."""
        if app_id is not None:
            self.app_id = app_id
        if cert_id is not None:
            self.cert_id = cert_id
        if dev_id is not None:
            self.dev_id = dev_id

    def get_credentials_status(self):
        """Return a dict with credential status and details (masked)."""
        return {
            "app_id": bool(self.app_id),
            "cert_id": bool(self.cert_id),
            "dev_id": bool(self.dev_id),
            "all_valid": self.check_credentials(),
            "details": {
                "app_id": (self.app_id[:4] + "..." if self.app_id else None),
                "cert_id": (self.cert_id[:4] + "..." if self.cert_id else None),
                "dev_id": (self.dev_id[:4] + "..." if self.dev_id else None),
            }
        }

    def check_credentials(self):
        """Check if eBay credentials are available and valid (not empty)."""
        return all([
            self.app_id is not None and self.app_id != "",
            self.cert_id is not None and self.cert_id != "",
            self.dev_id is not None and self.dev_id != ""
        ])

    def validate_credentials(self):
        """Try a real API call to validate credentials (if not in mock mode)."""
        if self.use_mock:
            return True, "Mock mode: credentials assumed valid."
        if not self.check_credentials():
            return False, "Missing one or more credentials."
        # Try to get a token
        token, error = self.get_oauth_token()
        if token:
            return True, "Successfully obtained OAuth token."
        return False, error
        
    def get_oauth_token(self):
        """Get OAuth token for eBay API"""
        if self.use_mock:
            return "mock-token", None
            
        if not self.check_credentials():
            return None, "Missing eBay credentials"
            
        try:
            auth_string = f"{self.app_id}:{self.cert_id}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded_auth}"
            }
            
            data = {
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            }
            
            response = requests.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                headers=headers,
                data=data,
                timeout=15
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data["access_token"], None
            else:
                return None, f"Failed to get token: {response.status_code}"
                
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def set_mock_mode(self, use_mock: bool):
        """Enable or disable mock mode."""
        self.use_mock = use_mock

    def fetch_sold_items_finding(self, query, limit=30):
        """Fetch sold items using the eBay Finding API (findCompletedItems)."""
        endpoint = "https://svcs.ebay.com/services/search/FindingService/v1"
        params = {
            "OPERATION-NAME": "findCompletedItems",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "keywords": query,
            "paginationInput.entriesPerPage": limit,
            "outputSelector": "SellerInfo"
        }
        response = requests.get(endpoint, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            items = []
            for item in data["findCompletedItemsResponse"][0]["searchResult"][0].get("item", []):
                items.append({
                    "id": item.get("itemId", [""])[0],
                    "title": item.get("title", [""])[0],
                    "url": item.get("viewItemURL", [""])[0],
                    "image": item.get("galleryURL", ["https://via.placeholder.com/150"])[0],
                    "price": float(item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", 0)),
                    "shipping": float(item.get("shippingInfo", [{}])[0].get("shippingServiceCost", [{}])[0].get("__value__", 0)),
                    "end_time": item.get("listingInfo", [{}])[0].get("endTime", ""),
                    "condition": item.get("condition", [{}])[0].get("conditionDisplayName", "N/A"),
                    "sold": True
                })
            return items, None
        else:
            return [], f"eBay Finding API error: {response.status_code} {response.text}"

    def fetch_items(self, query, sold=False, filters=None, limit=30):
        """Fetch items from eBay API (real or mock)."""
        if self.use_mock:
            return self._generate_mock_items(limit, sold), None

        if not self.check_credentials():
            return [], "Missing eBay credentials."

        if sold:
            return self.fetch_sold_items_finding(query, limit=limit)
        else:
            token, error = self.get_oauth_token()
            if not token:
                return [], f"OAuth error: {error}"
            try:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
                endpoint = "https://api.ebay.com/buy/browse/v1/item_summary/search"
                params = {
                    "q": query,
                    "filter": "soldStatus:{ACTIVE}",
                    "limit": limit
                }
                response = requests.get(endpoint, headers=headers, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    items = []
                    for item in data.get("itemSummaries", []):
                        items.append({
                            "id": item.get("itemId"),
                            "title": item.get("title"),
                            "url": item.get("itemWebUrl"),
                            "image": item.get("image", {}).get("imageUrl", "https://via.placeholder.com/150"),
                            "price": float(item.get("price", {}).get("value", 0)),
                            "shipping": float(item.get("shippingOptions", [{}])[0].get("shippingCost", {}).get("value", 0)),
                            "end_time": item.get("itemEndDate", ""),
                            "watchers": item.get("watchCount", 0),
                            "condition": item.get("condition", {}).get("conditionDisplayName", "N/A"),
                            "sold": False
                        })
                    return items, None
                else:
                    return [], f"eBay API error: {response.status_code} {response.text}"
            except Exception as e:
                return self._generate_mock_items(limit, False), f"Exception: {str(e)} (using mock data)"
    
    def _generate_mock_items(self, count, sold=False):
        """Generate mock item data for testing"""
        import random
        from datetime import datetime, timedelta
        
        items = []
        conditions = ["New", "Used", "Like New", "For parts or not working"]
        
        for i in range(count):
            if sold:
                days_ago = random.randint(1, 30)
                end_time = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            else:
                days_future = random.randint(1, 7)
                end_time = (datetime.now() + timedelta(days=days_future)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            price = round(random.uniform(10, 100), 2)
            shipping = round(random.uniform(0, 15), 2)
            
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
    
    def get_fee_rate(self, category):
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