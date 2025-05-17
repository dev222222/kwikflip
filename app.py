import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import main function from modular src/app.py
from src.app import main

# Run the application
if __name__ == "__main__":
    main()