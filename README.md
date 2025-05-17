# KwikFlip - eBay Research Tool

KwikFlip is a powerful tool for researching and analyzing eBay listings to help you make informed decisions about flipping items. It provides market analysis, profit calculations, and tracking capabilities for your flips.

## Features

- 🔍 Search eBay listings with text or image recognition
- 📊 Market analysis with active and sold item statistics
- 💰 Profit calculator with ROI analysis
- 📈 Visual charts for price distribution and sales volume
- 📱 Support for multiple selling platforms
- 📝 Track and analyze your flips over time

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/kwikflip.git
cd kwikflip
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your eBay API credentials:
```
EBAY_APP_ID=your_app_id_here
EBAY_CERT_ID=your_cert_id_here
EBAY_USE_SANDBOX=True
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Enter a search term or upload an image to begin researching items

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
