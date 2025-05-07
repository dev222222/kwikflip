
import streamlit as st
import requests
from bs4 import BeautifulSoup
import statistics

st.set_page_config(page_title="QuickFlip Price Checker", layout="centered")
st.title("🔍 QuickFlip: eBay Price Checker")
st.markdown("Enter a product name or UPC below to find recent eBay sold prices and get a suggested resale range.")

query = st.text_input("Product Name or UPC")

if query:
    st.info(f"Searching eBay for: {query}")
    
    # Construct search URL (sold listings only)
    url = f"https://www.ebay.com/sch/i.html?_nkw={query}&_sop=13&LH_Sold=1&LH_Complete=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.select("li.s-item")[:10]
        prices = []

        for item in listings:
            title_tag = item.select_one(".s-item__title")
            price_tag = item.select_one(".s-item__price")
            date_tag = item.select_one(".s-item__title--tag")

            if title_tag and price_tag:
                title = title_tag.get_text()
                price_text = price_tag.get_text().replace("$", "").replace(",", "")
                try:
                    price = float(price_text.split(" ")[0])
                    prices.append(price)

                    st.markdown(f"**{title}**  ")
                    st.write(f"💰 ${price:.2f}")
                except:
                    continue

        if prices:
            avg_price = statistics.mean(prices)
            st.success(f"🔢 **Average Sold Price:** ${avg_price:.2f}")
            st.markdown(f"Resale Range: ${min(prices):.2f} - ${max(prices):.2f}")
        else:
            st.warning("No valid prices found.")
    else:
        st.error("Failed to retrieve data from eBay. Try again later.")
