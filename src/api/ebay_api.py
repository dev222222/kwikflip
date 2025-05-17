"""Minimal eBay API implementation"""

class EbayAPI:
    def __init__(self):
        self.name = "EbayAPI"
    
    def get_oauth_token(self):
        return None, None
        
    def fetch_items(self, query, sold=False, filters=None, limit=30):
        return [], None
    
    def get_fee_rate(self, category):
        return 0.13
