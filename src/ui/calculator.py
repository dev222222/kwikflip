import streamlit as st
from src.data.storage import save_flip

def display_profit_calculator(active_stats, sold_stats, cost, category, flip_type):
    """Display profit calculator with ROI analysis"""
    st.markdown("### 💰 Profit Calculator")
    
    # Create two columns for inputs and results
    col1, col2 = st.columns(2)
    
    with col1:
        # Input fields
        st.markdown("#### Inputs")
        
        # Cost
        cost = st.number_input(
            "Cost ($)",
            min_value=0.0,
            value=cost,
            step=0.01,
            key="calc_cost"
        )
        
        # Selling price
        selling_price = st.number_input(
            "Selling Price ($)",
            min_value=0.0,
            value=sold_stats["avg_price"] if sold_stats["count"] > 0 else 0.0,
            step=0.01,
            key="calc_price"
        )
        
        # Shipping cost
        shipping_cost = st.number_input(
            "Shipping Cost ($)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            key="calc_shipping"
        )
        
        # Additional costs
        additional_costs = st.number_input(
            "Additional Costs ($)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            key="calc_additional"
        )
    
    with col2:
        # Calculate results
        st.markdown("#### Results")
        
        # Calculate fees
        ebay_fee = selling_price * 0.13  # 13% fee rate
        paypal_fee = selling_price * 0.029 + 0.30  # 2.9% + $0.30
        
        # Calculate total costs
        total_costs = cost + shipping_cost + additional_costs + ebay_fee + paypal_fee
        
        # Calculate profit
        profit = selling_price - total_costs
        roi = (profit / cost) * 100 if cost > 0 else 0
        
        # Display results
        st.metric("Gross Profit", f"${profit:.2f}")
        st.metric("ROI", f"{roi:.1f}%")
        
        st.markdown("#### Cost Breakdown")
        st.markdown(f"**Item Cost:** ${cost:.2f}")
        st.markdown(f"**Shipping:** ${shipping_cost:.2f}")
        st.markdown(f"**Additional:** ${additional_costs:.2f}")
        st.markdown(f"**eBay Fee:** ${ebay_fee:.2f}")
        st.markdown(f"**PayPal Fee:** ${paypal_fee:.2f}")
        st.markdown(f"**Total Costs:** ${total_costs:.2f}")
    
    # Save flip button
    if st.button("Save Flip", type="primary"):
        flip_data = {
            "date": st.session_state.last_search.get("date", ""),
            "query": st.session_state.last_search.get("query", ""),
            "category": category,
            "flip_type": flip_type,
            "cost": cost,
            "selling_price": selling_price,
            "shipping_cost": shipping_cost,
            "additional_costs": additional_costs,
            "ebay_fee": ebay_fee,
            "paypal_fee": paypal_fee,
            "profit": profit,
            "roi": roi
        }
        
        save_flip(flip_data)
        st.success("Flip saved successfully!") 