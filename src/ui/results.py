import streamlit as st
import pandas as pd
from datetime import datetime

def display_items(items, title, sort_options=True, pagination=True, page_size=10):
    """Display a list of items with optional sorting and pagination"""
    if not items:
        st.info(f"No {title.lower()} found")
        return
    
    st.markdown(f"### {title}")
    
    # Convert items to DataFrame for easier manipulation
    df = pd.DataFrame(items)
    
    # Add sorting options
    if sort_options:
        sort_by = st.selectbox(
            "Sort by",
            ["Price", "Watchers", "End Time"],
            key=f"sort_{title}"
        )
        
        if sort_by == "Price":
            df = df.sort_values("price", ascending=False)
        elif sort_by == "Watchers":
            df = df.sort_values("watchers", ascending=False)
        else:  # End Time
            df = df.sort_values("end_time", ascending=True)
    
    # Add pagination
    if pagination:
        total_pages = (len(df) + page_size - 1) // page_size
        page = st.selectbox("Page", range(1, total_pages + 1), key=f"page_{title}")
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        df = df.iloc[start_idx:end_idx]
    
    # Display items
    for _, item in df.iterrows():
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.image(item["image"], width=150)
            
            with col2:
                st.markdown(f"#### [{item['title']}]({item['url']})")
                st.markdown(f"**Price:** ${item['price']:.2f}")
                st.markdown(f"**Shipping:** ${item['shipping']:.2f}")
                st.markdown(f"**Condition:** {item['condition']}")
                st.markdown(f"**Watchers:** {item['watchers']}")
                
                # Format end time
                end_time = datetime.strptime(item["end_time"], "%Y-%m-%dT%H:%M:%S.000Z")
                st.markdown(f"**Ends:** {end_time.strftime('%Y-%m-%d %H:%M')}")
            
            st.markdown("---")

def display_metrics(active_stats, sold_stats, fee_rate):
    """Display key metrics and statistics"""
    st.markdown("### 📊 Market Analysis")
    
    # Create metrics columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Active Listings",
            active_stats["count"],
            f"Avg: ${active_stats['avg_price']:.2f}"
        )
    
    with col2:
        st.metric(
            "Sold Items (30d)",
            sold_stats["count"],
            f"Avg: ${sold_stats['avg_price']:.2f}"
        )
    
    with col3:
        sell_through = (sold_stats["count"] / (active_stats["count"] + sold_stats["count"])) * 100 if (active_stats["count"] + sold_stats["count"]) > 0 else 0
        st.metric(
            "Sell-Through Rate",
            f"{sell_through:.1f}%"
        )
    
    with col4:
        st.metric(
            "eBay Fee Rate",
            f"{fee_rate * 100:.1f}%"
        )
    
    # Additional metrics
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("#### Price Range")
        st.markdown(f"**Active:** ${active_stats['min_price']:.2f} - ${active_stats['max_price']:.2f}")
        st.markdown(f"**Sold:** ${sold_stats['min_price']:.2f} - ${sold_stats['max_price']:.2f}")
    
    with col6:
        st.markdown("#### Market Health")
        if active_stats["count"] > 0 and sold_stats["count"] > 0:
            price_diff = ((active_stats["avg_price"] - sold_stats["avg_price"]) / sold_stats["avg_price"]) * 100
            st.markdown(f"**Price Trend:** {'📈' if price_diff > 0 else '📉'} {abs(price_diff):.1f}%")
        else:
            st.markdown("**Price Trend:** Insufficient data") 