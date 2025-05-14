import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def generate_price_chart(active_items, sold_items):
    """Generate price distribution chart"""
    if not active_items and not sold_items:
        return None
    
    # Create DataFrame for active items
    active_df = pd.DataFrame(active_items)
    active_df["type"] = "Active"
    
    # Create DataFrame for sold items
    sold_df = pd.DataFrame(sold_items)
    sold_df["type"] = "Sold"
    
    # Combine DataFrames
    df = pd.concat([active_df, sold_df])
    
    # Create histogram
    fig = px.histogram(
        df,
        x="price",
        color="type",
        barmode="overlay",
        title="Price Distribution",
        labels={"price": "Price ($)", "type": "Listing Type"},
        nbins=20
    )
    
    # Update layout
    fig.update_layout(
        showlegend=True,
        legend_title="Listing Type",
        xaxis_title="Price ($)",
        yaxis_title="Count"
    )
    
    return fig

def generate_volume_chart(active_items, sold_items):
    """Generate sales volume chart"""
    if not active_items and not sold_items:
        return None
    
    # Create DataFrame for sold items
    sold_df = pd.DataFrame(sold_items)
    
    # Convert end_time to datetime
    sold_df["end_time"] = pd.to_datetime(sold_df["end_time"])
    
    # Group by date and count
    daily_sales = sold_df.groupby(sold_df["end_time"].dt.date).size().reset_index()
    daily_sales.columns = ["date", "count"]
    
    # Create line chart
    fig = px.line(
        daily_sales,
        x="date",
        y="count",
        title="Sales Volume Over Time",
        labels={"date": "Date", "count": "Number of Sales"}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Sales",
        showlegend=False
    )
    
    return fig

def generate_profit_chart(flips_df):
    """Generate profit over time chart"""
    if flips_df.empty:
        return None
    
    # Convert date to datetime
    flips_df["date"] = pd.to_datetime(flips_df["date"])
    
    # Sort by date
    flips_df = flips_df.sort_values("date")
    
    # Calculate cumulative profit
    flips_df["cumulative_profit"] = flips_df["profit"].cumsum()
    
    # Create line chart
    fig = px.line(
        flips_df,
        x="date",
        y="cumulative_profit",
        title="Cumulative Profit Over Time",
        labels={"date": "Date", "cumulative_profit": "Cumulative Profit ($)"}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative Profit ($)",
        showlegend=False
    )
    
    return fig

def generate_category_chart(flips_df):
    """Generate profit by category chart"""
    if flips_df.empty:
        return None
    
    # Group by category and sum profits
    category_profit = flips_df.groupby("category")["profit"].sum().reset_index()
    
    # Create bar chart
    fig = px.bar(
        category_profit,
        x="category",
        y="profit",
        title="Profit by Category",
        labels={"category": "Category", "profit": "Total Profit ($)"}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Total Profit ($)",
        showlegend=False
    )
    
    return fig 