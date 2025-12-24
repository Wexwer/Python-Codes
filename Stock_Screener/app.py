import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# Set page configuration
st.set_page_config(page_title="Python Stock Screener", layout="wide")

# 1. DATA INFRASTRUCTURE
@st.cache_data
def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    # This 'header' makes the request look like it's coming from a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Download the page content first
    response = requests.get(url, headers=headers)
    
    # Use Pandas to read the table from the downloaded HTML text
    table = pd.read_html(response.text)
    return table[0]['Symbol'].tolist()

@st.cache_data
def fetch_stock_data(tickers):
    stock_list = []
    # We limit to 500 for speed in this example
    for ticker in tickers[:500]:
        try:
            s = yf.Ticker(ticker)
            info = s.info
            stock_list.append({
                "Ticker": ticker,
                "Price": info.get("currentPrice"),
                "P/E": info.get("forwardPE"),
                "Yield %": (info.get("dividendYield", 0) or 0) * 100,
                "Sector": info.get("sector")
            })
        except:
            continue
    return pd.DataFrame(stock_list)

# 2. APP FRONTEND
st.title("📊 Stefko Financial Screener")

# Load data
with st.spinner("Fetching market data..."):
    tickers = get_sp500_tickers()
    df = fetch_stock_data(tickers)

# 3. FILTERING LOGIC (The "Screener" Part)
st.sidebar.header("Filter Stocks")
target_sector = st.sidebar.multiselect("Sector", options=df['Sector'].unique())
max_pe = st.sidebar.slider("Maximum P/E Ratio", 0, 100, 100)

# Filter the dataframe based on user input
filtered_df = df[df['P/E'] <= max_pe]
if target_sector:
    filtered_df = filtered_df[filtered_df['Sector'].isin(target_sector)]

# 4. DISPLAY RESULTS
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Filtered Results")
    st.dataframe(filtered_df, hide_index=True)

with col2:
    st.subheader("Technical View")
    selected_stock = st.selectbox("Select ticker for chart", filtered_df['Ticker'])
    if selected_stock:
        hist = yf.Ticker(selected_stock).history(period="6mo")
        fig = go.Figure(data=[go.Candlestick(x=hist.index,
                        open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'])])
        fig.update_layout(xaxis_rangeslider_visible=False, height=400)
        st.plotly_chart(fig, use_container_width=True)