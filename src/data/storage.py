import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# Configuration
DATA_DIR = Path("data")
FLIPS_FILE = DATA_DIR / "flips.csv"
SEARCHES_FILE = DATA_DIR / "searches.json"

def ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_flips():
    """Load saved flips from CSV file"""
    ensure_data_dir()
    
    if FLIPS_FILE.exists():
        try:
            return pd.read_csv(FLIPS_FILE)
        except Exception as e:
            print(f"Error loading flips: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

def save_flip(flip_data):
    """Save a new flip to CSV file"""
    ensure_data_dir()
    
    # Add date if not present
    if "date" not in flip_data or not flip_data["date"]:
        flip_data["date"] = datetime.now().strftime("%Y-%m-%d")
    
    # Convert to DataFrame
    new_flip = pd.DataFrame([flip_data])
    
    # Load existing data
    df = load_flips()
    
    # Append new flip
    df = pd.concat([df, new_flip], ignore_index=True)
    
    # Save to CSV
    df.to_csv(FLIPS_FILE, index=False)

def load_recent_searches():
    """Load recent searches from JSON file"""
    ensure_data_dir()
    
    if SEARCHES_FILE.exists():
        try:
            with open(SEARCHES_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading recent searches: {e}")
            return []
    else:
        return []

def save_recent_searches(searches):
    """Save recent searches to JSON file"""
    ensure_data_dir()
    
    try:
        with open(SEARCHES_FILE, "w") as f:
            json.dump(searches, f)
    except Exception as e:
        print(f"Error saving recent searches: {e}")

def export_flips():
    """Export flips to Excel file"""
    ensure_data_dir()
    
    df = load_flips()
    if not df.empty:
        export_file = DATA_DIR / f"flips_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(export_file, index=False)
        return export_file
    return None 