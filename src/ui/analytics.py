import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def display_analytics(df):
    """Display analytics charts and insights"""
    st.markdown("### 📈 Analytics")
    
    # Convert date column to datetime
    df["date"] = pd.to_datetime(df["date"])
    
    # Create tabs for different analytics views
    tab1, tab2, tab3 = st.tabs(["Profit Analysis", "Category Analysis", "Platform Comparison"])
    
    with tab1:
        # Profit over time
        st.markdown("#### Profit Over Time")
        fig = px.line(
            df,
            x="date",
            y="profit",
            title="Profit Over Time",
            labels={"date": "Date", "profit": "Profit ($)"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # ROI distribution
        st.markdown("#### ROI Distribution")
        fig = px.histogram(
            df,
            x="roi",
            title="ROI Distribution",
            labels={"roi": "ROI (%)"},
            nbins=20
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Profit by category
        st.markdown("#### Profit by Category")
        category_profit = df.groupby("category")["profit"].sum().reset_index()
        fig = px.bar(
            category_profit,
            x="category",
            y="profit",
            title="Total Profit by Category",
            labels={"category": "Category", "profit": "Total Profit ($)"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # ROI by category
        st.markdown("#### ROI by Category")
        category_roi = df.groupby("category")["roi"].mean().reset_index()
        fig = px.bar(
            category_roi,
            x="category",
            y="roi",
            title="Average ROI by Category",
            labels={"category": "Category", "roi": "Average ROI (%)"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Platform comparison
        st.markdown("#### Platform Comparison")
        
        # Create sample data for platform comparison
        platforms = ["eBay", "Facebook Marketplace", "Craigslist"]
        platform_data = {
            "Platform": platforms,
            "Average Fee": [0.13, 0.0, 0.0],
            "Average Shipping": [5.0, 0.0, 0.0],
            "Average Time to Sell": [7, 3, 5]
        }
        
        platform_df = pd.DataFrame(platform_data)
        
        # Fee comparison
        fig = px.bar(
            platform_df,
            x="Platform",
            y="Average Fee",
            title="Platform Fee Comparison",
            labels={"Platform": "Platform", "Average Fee": "Fee Rate (%)"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Time to sell comparison
        fig = px.bar(
            platform_df,
            x="Platform",
            y="Average Time to Sell",
            title="Average Time to Sell",
            labels={"Platform": "Platform", "Average Time to Sell": "Days"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Summary metrics
    st.markdown("### 📊 Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Profit",
            f"${df['profit'].sum():.2f}",
            f"Avg: ${df['profit'].mean():.2f}"
        )
    
    with col2:
        st.metric(
            "Average ROI",
            f"{df['roi'].mean():.1f}%",
            f"Best: {df['roi'].max():.1f}%"
        )
    
    with col3:
        st.metric(
            "Total Flips",
            len(df),
            f"Last 30d: {len(df[df['date'] > datetime.now() - timedelta(days=30)])}"
        ) 