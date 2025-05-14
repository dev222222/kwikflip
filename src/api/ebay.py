import os
import time
import requests
import traceback
from datetime import datetime, timedelta
import random
from utils.logging import log_debug

class EbayAPI:
    def __init__(self):
        self.app_id = os.getenv("EBAY_APP_ID")
        self.cert_id = os.getenv("EBAY_CERT_ID")
        self.dev_id = os.getenv("EBAY_DEV_ID")
        self.finding_api_url = "https://svcs.ebay.com/services/search/FindingService/v1"
        self.trading_api_url = "https://api.ebay.com/ws/api.dll"
        self.api_timeout = 15

    def check_credentials(self):
        """Check if eBay credentials are available and valid"""
        has_app_id = self.app_id is not None and self.app_id != ""
        has_cert_id = self.cert_id is not None and self.cert_id != ""
        log_debug(f"EBAY_APP_ID exists: {has_app_id}")
        log_debug(f"EBAY_CERT_ID exists: {has_cert_id}")
        if has_app_id and has_cert_id:
            log_debug("eBay credentials verification: PASS")
        else:
            log_debug("eBay credentials verification: FAIL")
        return has_app_id and has_cert_id

    def get_auth_token(self):
        """Get static Auth'n'Auth token"""
        token = "v^1.1#f^1#r^1#f^0#i^3#p^3#f^UI4xMF8xMTo4MjAyNzk4RkY2NjY3QTBGRUJDMjAxMEQzMUU5MDc1NF8xXzEjRV4yNjA="
        log_debug("Using Auth'n'Auth token")
        return token, None

    def search_traditional(self, query, sold=False, filters=None, limit=30):
        """Search for items using eBay traditional API with Auth'n'Auth"""
        try:
            log_debug(f"Searching eBay with Auth'n'Auth for '{query}' (sold={sold})")
            
            # Get Auth token
            token = self.get_auth_token()[0]
            
            # Set up the request
            headers = {
                "X-EBAY-API-IAF-TOKEN": token,
                "X-EBAY-API-SITE-ID": "0",  # US site
                "X-EBAY-API-CALL-NAME": "findItemsByKeywords" if not sold else "findCompletedItems",
                "X-EBAY-API-VERSION": "1.13.0",
                "Content-Type": "application/xml"
            }
            
            # Build the XML request
            xml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
            <findItemsByKeywordsRequest xmlns="http://www.ebay.com/marketplace/search/v1/services">
                <keywords>{query}</keywords>
                <paginationInput>
                    <entriesPerPage>{limit}</entriesPerPage>
                    <pageNumber>1</pageNumber>
                </paginationInput>
                <sortOrder>BestMatch</sortOrder>
            </findItemsByKeywordsRequest>"""
            
            # Make the request
            response = requests.post(self.finding_api_url, headers=headers, data=xml_request, timeout=self.api_timeout)
            
            if response.status_code != 200:
                error_msg = f"eBay API returned status code {response.status_code}"
                log_debug(f"{error_msg}: {response.text[:500]}")
                return None, error_msg
            
            # Parse the XML response
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                # Extract items
                items = []
                for item in root.findall(".//{http://www.ebay.com/marketplace/search/v1/services}item"):
                    try:
                        item_data = {
                            "id": item.find(".//{http://www.ebay.com/marketplace/search/v1/services}itemId").text,
                            "title": item.find(".//{http://www.ebay.com/marketplace/search/v1/services}title").text,
                            "url": item.find(".//{http://www.ebay.com/marketplace/search/v1/services}viewItemURL").text,
                            "image": item.find(".//{http://www.ebay.com/marketplace/search/v1/services}galleryURL").text,
                            "price": float(item.find(".//{http://www.ebay.com/marketplace/search/v1/services}currentPrice").text),
                            "shipping": float(item.find(".//{http://www.ebay.com/marketplace/search/v1/services}shippingServiceCost").text),
                            "end_time": item.find(".//{http://www.ebay.com/marketplace/search/v1/services}endTime").text,
                            "condition": item.find(".//{http://www.ebay.com/marketplace/search/v1/services}condition").find(".//{http://www.ebay.com/marketplace/search/v1/services}conditionDisplayName").text,
                            "watchers": int(item.find(".//{http://www.ebay.com/marketplace/search/v1/services}watchCount").text) if item.find(".//{http://www.ebay.com/marketplace/search/v1/services}watchCount") is not None else 0,
                            "sold": sold
                        }
                        items.append(item_data)
                    except Exception as e:
                        log_debug(f"Error processing item: {e}")
                        continue
                
                return items, None
                
            except Exception as e:
                error_msg = f"Error parsing eBay API response: {e}"
                log_debug(error_msg)
                return None, error_msg
                
        except Exception as e:
            error_msg = f"Error calling eBay API: {e}"
            log_debug(error_msg)
            log_debug(traceback.format_exc())
            return None, error_msg

    def fetch_items(self, query, sold=False, filters=None, limit=30):
        """Fetch items from eBay API or generate mock data"""
        try:
            log_debug(f"Fetching {'sold' if sold else 'active'} items for query: '{query}'")
            
            if self.check_credentials():
                log_debug("Attempting to use eBay traditional API")
                try:
                    items, error = self.search_traditional(query, sold, filters, limit)
                    
                    if items is not None:
                        log_debug(f"Successfully retrieved {len(items)} items from eBay API")
                        return items, None
                    else:
                        error_msg = f"eBay API error: {error}. Falling back to mock data."
                        log_debug(error_msg)
                        return self.generate_mock_items(count=limit, sold=sold), None
                except Exception as e:
                    error_msg = f"Error with eBay API: {e}. Falling back to mock data."
                    log_debug(error_msg)
                    log_debug(traceback.format_exc())
                    return self.generate_mock_items(count=limit, sold=sold), None
            else:
                log_debug("eBay credentials not found or invalid")
                return self.generate_mock_items(count=limit, sold=sold), None
                
        except Exception as e:
            error_msg = f"Error in fetch_items: {e}"
            log_debug(error_msg)
            log_debug(traceback.format_exc())
            return None, error_msg

    def generate_mock_items(self, count, sold=False):
        """Generate mock item data for demonstration purposes"""
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

    def process_image_search(self, image_data):
        """Process image for search (simulated)"""
        log_debug("Processing image for search")
        
        categories = [
            "Electronics", "Clothing", "Collectibles", 
            "Home & Garden", "Toys", "Books", "Other"
        ]
        
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