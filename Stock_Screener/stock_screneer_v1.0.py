import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# Page Setup
st.set_page_config(page_title="Pro Stock Screener", layout="wide")

# --- 1. DATA INFRASTRUCTURE ---

@st.cache_data
def get_sp500_tickers():
    """Pulls tickers from Wikipedia with a browser header to avoid 403 errors."""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers)
    table = pd.read_html(response.text)
    # yfinance uses '-' instead of '.' for tickers like BRK.B
    return table[0]['Symbol'].str.replace('.', '-', regex=False).tolist()

@st.cache_data
def fetch_base_data(tickers):
    """Fetches fundamental and descriptive data for a list of stocks."""
    
    stock_list = []
    
    # Limit to first 500 for performance; increase as your internet speed allows
    
    for ticker in tickers[:500]:
        try:
            s = yf.Ticker(ticker)
            info = s.info
            stock_list.append({
                "Ticker": ticker,
                "Sector": info.get("sector"),
                "Industry": info.get("industry"),
                "Price": info.get("currentPrice"),
                "P/E": info.get("forwardPE"),
                "Debt/Equity": info.get("debtToEquity"),
                "Gross Margin %": (info.get("grossMargins", 0) or 0) * 100,
                "Profit Margin %": (info.get("profitMargins", 0) or 0) * 100,
                "Div Yield %": (info.get("dividendYield", 0) or 0) * 100,
            })
        except:
            continue
    return pd.DataFrame(stock_list)

def check_ma_crossover(ticker, interval="1d", period="2y"):
    """Logic for MA 314 crossing UNDER MA 30."""
    try:
        data = yf.Ticker(ticker).history(period=period, interval=interval)
        if len(data) < 315:
            return False
        
        ma30 = data['Close'].rolling(window=30).mean()
        ma314 = data['Close'].rolling(window=314).mean()
        
        # Check the last two completed candles
        curr_30, prev_30 = ma30.iloc[-1], ma30.iloc[-2]
        curr_314, prev_314 = ma314.iloc[-1], ma314.iloc[-2]
        
        # Crossover Under: Slow (314) was above Fast (30), now it is below
        return (prev_314 >= prev_30) and (curr_314 < curr_30)
    except:
        return False

# --- 2. SIDEBAR NAVIGATION & FILTERS ---

st.sidebar.title("Screener Controls")
tickers = get_sp500_tickers()
df = fetch_base_data(tickers)

# Tabs mimic the buttons in your screenshots
category = st.sidebar.radio("Filter Category", ["Descriptive", "Fundamental", "Technical"])
filtered_df = df.copy()

if category == "Descriptive":
    sectors = st.sidebar.multiselect("Sector", options=df['Sector'].unique())
    if sectors:
        filtered_df = filtered_df[filtered_df['Sector'].isin(sectors)]
    industries = st.sidebar.multiselect("Industry", options=df['Industry'].unique())
    if industries:
        filtered_df = filtered_df[filtered_df['Industry'].isin(industries)]

elif category == "Fundamental":
    max_pe = st.sidebar.slider("Max Forward P/E", 0.0, 100.0, 50.0)
    filtered_df = filtered_df[filtered_df['P/E'] <= max_pe]
    
    min_profit = st.sidebar.slider("Min Profit Margin (%)", -20.0, 50.0, 0.0)
    filtered_df = filtered_df[filtered_df['Profit Margin %'] >= min_profit]
    
    max_debt = st.sidebar.number_input("Max Debt/Equity", value=2.0)
    filtered_df = filtered_df[filtered_df['Debt/Equity'] <= max_debt]

elif category == "Technical":
    st.sidebar.subheader("SMA Crossover (314 Under 30)")
    daily_cross = st.sidebar.checkbox("Daily Crossover")
    four_hour_cross = st.sidebar.checkbox("4H Crossover")
    
    # Process crossovers only if checked (this can be slow)
    if daily_cross or four_hour_cross:
        with st.spinner("Analyzing chart patterns..."):
            valid_tickers = []
            for t in filtered_df['Ticker']:
                is_valid = True
                if daily_cross and not check_ma_crossover(t, interval="1d", period="2y"):
                    is_valid = False
                if is_valid and four_hour_cross and not check_ma_crossover(t, interval="4h", period="60d"):
                    is_valid = False
                
                if is_valid:
                    valid_tickers.append(t)
            filtered_df = filtered_df[filtered_df['Ticker'].isin(valid_tickers)]

# --- 3. MAIN DASHBOARD ---

st.header(f"Results ({len(filtered_df)} stocks)")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)

if not filtered_df.empty:
    st.divider()
    selected_ticker = st.selectbox("Select Ticker for Chart Analysis", filtered_df['Ticker'])
    
    # Charting
    hist = yf.Ticker(selected_ticker).history(period="2y")
    hist['MA30'] = hist['Close'].rolling(30).mean()
    hist['MA314'] = hist['Close'].rolling(314).mean()
    
    fig = go.Figure()
    # Candlesticks
    fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], 
                                 low=hist['Low'], close=hist['Close'], name="Price"))
    # MAs
    fig.add_trace(go.Scatter(x=hist.index, y=hist['MA30'], line=dict(color='yellow', width=1), name="MA 30"))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['MA314'], line=dict(color='purple', width=2), name="MA 314"))
    
    fig.update_layout(title=f"{selected_ticker} Technical View", template="plotly_dark", 
                      xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No stocks match the selected criteria.")