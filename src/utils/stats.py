def calculate_stats(items):
    """Calculate statistics for a list of items"""
    if not items:
        return {
            "count": 0,
            "avg_price": 0,
            "min_price": 0,
            "max_price": 0,
            "total_watchers": 0
        }
    
    prices = [item["price"] for item in items]
    watchers = [item["watchers"] for item in items]
    
    return {
        "count": len(items),
        "avg_price": sum(prices) / len(prices) if prices else 0,
        "min_price": min(prices) if prices else 0,
        "max_price": max(prices) if prices else 0,
        "total_watchers": sum(watchers)
    }

def calculate_sell_through_rate(active_items, sold_items):
    """Calculate sell-through rate"""
    total_items = len(active_items) + len(sold_items)
    if total_items == 0:
        return 0
    return (len(sold_items) / total_items) * 100

def calculate_price_trend(active_items, sold_items):
    """Calculate price trend between active and sold items"""
    if not active_items or not sold_items:
        return 0
    
    active_avg = sum(item["price"] for item in active_items) / len(active_items)
    sold_avg = sum(item["price"] for item in sold_items) / len(sold_items)
    
    if sold_avg == 0:
        return 0
    
    return ((active_avg - sold_avg) / sold_avg) * 100

def calculate_roi(cost, selling_price, fees, shipping_cost=0, additional_costs=0):
    """Calculate ROI for a flip"""
    if cost == 0:
        return 0
    
    total_costs = cost + shipping_cost + additional_costs + fees
    profit = selling_price - total_costs
    
    return (profit / cost) * 100 