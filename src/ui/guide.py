import streamlit as st

def display_quick_start_guide():
    """Display quick start guide for new users"""
    st.markdown("### 🚀 Quick Start Guide")
    
    st.markdown("""
    #### How to Use KwikFlip
    
    1. **Search for Items**
       - Enter keywords or UPC in the search box
       - Upload an image for visual search
       - Use filters to narrow down results
    
    2. **Analyze Market**
       - View active and sold listings
       - Check price trends and sell-through rates
       - Compare with similar items
    
    3. **Calculate Profit**
       - Enter your cost and expected selling price
       - Include shipping and additional costs
       - View ROI and profit breakdown
    
    4. **Track Performance**
       - Save successful flips
       - Monitor profit by category
       - Compare performance across platforms
    
    #### Tips for Success
    
    - Start with items you know well
    - Research market trends before buying
    - Consider shipping costs in your calculations
    - Track all expenses for accurate ROI
    - Use filters to find the best opportunities
    """)

def display_marketplace_comparison():
    """Display marketplace comparison guide"""
    st.markdown("### 🏪 Marketplace Comparison")
    
    # Create comparison table
    st.markdown("""
    | Platform | Pros | Cons | Best For |
    |----------|------|------|----------|
    | **eBay** | • Large audience<br>• Built-in shipping<br>• Seller protection | • Higher fees<br>• More competition<br>• Longer shipping times | • Collectibles<br>• Electronics<br>• Vintage items |
    | **Facebook Marketplace** | • No fees<br>• Local pickup<br>• Quick sales | • Limited reach<br>• No shipping<br>• Less protection | • Furniture<br>• Large items<br>• Local sales |
    | **Craigslist** | • No fees<br>• Local sales<br>• Cash transactions | • Limited features<br>• Safety concerns<br>• No shipping | • Large items<br>• Local pickup<br>• Quick cash sales |
    """)
    
    st.markdown("""
    #### Choosing the Right Platform
    
    1. **Consider Your Item**
       - Size and shipping costs
       - Target audience
       - Price point
    
    2. **Evaluate Costs**
       - Platform fees
       - Shipping expenses
       - Time investment
    
    3. **Think About Logistics**
       - Shipping capabilities
       - Storage space
       - Time to sell
    
    4. **Assess Risk**
       - Seller protection
       - Payment security
       - Buyer reliability
    """) 