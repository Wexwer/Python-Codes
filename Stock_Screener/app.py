import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from io import StringIO
from math import isfinite

# ============================================================
#  Stefan Sivchev's: Pro Stock Screener & DCF (NYSE Universe)
#  TASK 1: Free universe beyond SPX (NYSE + market-cap filter)
#  TASK 2: DCF tab upgrades + WACC-based discounting
# ============================================================

st.set_page_config(
    page_title="Stefan Sivchev's: Pro Stock Screener & DCF",
    layout="wide"
)

# -----------------------------
# 1) DATA INFRASTRUCTURE
# -----------------------------

@st.cache_data(ttl=60 * 60 * 12)  # 12h
def get_us_listed_universe(include_nasdaq=False, include_amex=False):
    """
    FREE universe source: nasdaqtrader symbol directories
    - otherlisted.txt includes NYSE/AMEX/etc
    - nasdaqlisted.txt includes NASDAQ
    Exchange codes in otherlisted:
      N = NYSE
      A = NYSE American (AMEX)
      P = NYSE Arca
      Z = BATS (legacy)
      V = IEX (often)
      (varies, but N and A are the key ones here)
    """
    headers = {"User-Agent": "Mozilla/5.0"}

    # NYSE/AMEX/others
    other_url = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
    r_other = requests.get(other_url, headers=headers, timeout=30)
    r_other.raise_for_status()
    text_other = r_other.text

    # file has a footer line like "File Creation Time: ..."
    lines = [ln for ln in text_other.splitlines() if ln and not ln.startswith("File Creation Time")]
    # last line can be "File Creation Time:"; already removed above
    df_other = pd.read_csv(StringIO("\n".join(lines)), sep="|")

    tickers = []

    # Always include NYSE (N)
    if "Exchange" in df_other.columns and "ACT Symbol" in df_other.columns:
        nyse = df_other[df_other["Exchange"] == "N"]["ACT Symbol"].astype(str).tolist()
        tickers.extend(nyse)

        if include_amex:
            amex = df_other[df_other["Exchange"] == "A"]["ACT Symbol"].astype(str).tolist()
            tickers.extend(amex)

    # NASDAQ tickers (optional)
    if include_nasdaq:
        nasdaq_url = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
        r_nq = requests.get(nasdaq_url, headers=headers, timeout=30)
        r_nq.raise_for_status()
        text_nq = r_nq.text
        lines_nq = [ln for ln in text_nq.splitlines() if ln and not ln.startswith("File Creation Time")]
        df_nq = pd.read_csv(StringIO("\n".join(lines_nq)), sep="|")
        if "Symbol" in df_nq.columns:
            tickers.extend(df_nq["Symbol"].astype(str).tolist())

    # Clean
    tickers = [t.strip().upper() for t in tickers if isinstance(t, str) and t.strip()]
    tickers = sorted(set(tickers))
    return tickers


def safe_num(x):
    try:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        # yfinance sometimes returns numpy types
        return float(x)
    except:
        return None


def estimate_wacc(info: dict):
    """
    Free-tier, data-driven heuristic WACC estimate:
    - Uses market cap scale + leverage (debt/equity) + profitability hints (margins)
    - Clamped to 6%–12% (as requested).
    """
    mc = safe_num(info.get("marketCap"))
    de = safe_num(info.get("debtToEquity"))
    gross = safe_num(info.get("grossMargins"))
    profit = safe_num(info.get("profitMargins"))

    # Base by size
    if mc is None:
        wacc = 0.09
    elif mc >= 200e9:
        wacc = 0.065
    elif mc >= 50e9:
        wacc = 0.072
    elif mc >= 10e9:
        wacc = 0.085
    elif mc >= 2e9:
        wacc = 0.095
    else:
        wacc = 0.105

    # Leverage adjustment
    if de is not None:
        if de > 200:   # very levered
            wacc += 0.015
        elif de > 100:
            wacc += 0.010
        elif de < 30:
            wacc -= 0.005

    # Profitability / quality adjustment
    if profit is not None:
        if profit < 0:
            wacc += 0.015
        elif profit < 0.05:
            wacc += 0.005
        elif profit > 0.15:
            wacc -= 0.005

    if gross is not None and gross > 0.50:
        wacc -= 0.003

    # clamp 6%–12%
    wacc = min(max(wacc, 0.06), 0.12)
    return wacc


def get_ttm_fcf(s: yf.Ticker):
    """
    TTM Free Cash Flow:
    FCF = Operating Cash Flow + Capital Expenditures
    Note: CapEx is typically negative in cashflow, so OCF + CapEx is correct.
    """
    try:
        cf = s.cashflow
        if cf is None or cf.empty:
            return None
        if "Operating Cash Flow" not in cf.index or "Capital Expenditures" not in cf.index:
            return None

        ocf_series = cf.loc["Operating Cash Flow"]
        capex_series = cf.loc["Capital Expenditures"]

        # yfinance cashflow is annual for many tickers; sometimes quarterly exists in quarterly_cashflow.
        # We'll try quarterly first; fallback to annual.
        qcf = getattr(s, "quarterly_cashflow", None)
        if qcf is not None and isinstance(qcf, pd.DataFrame) and not qcf.empty:
            if "Operating Cash Flow" in qcf.index and "Capital Expenditures" in qcf.index:
                ocf_q = qcf.loc["Operating Cash Flow"].iloc[:4].sum()
                capex_q = qcf.loc["Capital Expenditures"].iloc[:4].sum()
                return safe_num(ocf_q + capex_q)

        # Fallback: use most recent annual
        ocf = safe_num(ocf_series.iloc[0])
        capex = safe_num(capex_series.iloc[0])
        if ocf is None or capex is None:
            return None
        return ocf + capex
    except:
        return None


def get_revenue_ttm_and_prior_year(s: yf.Ticker):
    """
    Revenue:
    - Prefer quarterly_income_stmt for TTM + prior-year (previous 4 quarters)
    - Fallback to annual income_stmt if quarterly not available
    """
    try:
        q_is = getattr(s, "quarterly_income_stmt", None)
        if q_is is not None and isinstance(q_is, pd.DataFrame) and not q_is.empty:
            if "Total Revenue" in q_is.index:
                rev = q_is.loc["Total Revenue"]
                if len(rev) >= 8:
                    ttm = safe_num(rev.iloc[:4].sum())
                    prior = safe_num(rev.iloc[4:8].sum())
                    return ttm, prior
                elif len(rev) >= 4:
                    ttm = safe_num(rev.iloc[:4].sum())
                    return ttm, None

        # Fallback: annual
        is_annual = getattr(s, "income_stmt", None)
        if is_annual is not None and isinstance(is_annual, pd.DataFrame) and not is_annual.empty:
            if "Total Revenue" in is_annual.index:
                rev = is_annual.loc["Total Revenue"]
                ttm = safe_num(rev.iloc[0])
                prior = safe_num(rev.iloc[1]) if len(rev) > 1 else None
                return ttm, prior
    except:
        pass
    return None, None


@st.cache_data(ttl=60 * 60 * 6)  # 6h
def fetch_base_data(tickers, max_scan=300, min_market_cap=2e9):
    """
    Fetches fundamental & descriptive data for a batch, then filters by market cap.
    NOTE: Free data sources (yfinance) can be slow; keep max_scan reasonable.
    """
    stock_list = []
    tickers = tickers[:max_scan]

    for ticker in tickers:
        try:
            s = yf.Ticker(ticker)
            info = s.info

            mc = safe_num(info.get("marketCap"))
            if mc is None or mc < min_market_cap:
                continue

            wacc = estimate_wacc(info)

            # Revenue & FCF
            ttm_rev, prior_rev = get_revenue_ttm_and_prior_year(s)
            ttm_fcf = get_ttm_fcf(s)

            stock_list.append({
                "Ticker": ticker,
                "Exchange": info.get("exchange"),
                "Sector": info.get("sector"),
                "Industry": info.get("industry"),
                "Market Cap": mc,
                "Price": safe_num(info.get("currentPrice")),
                "Shares Out": safe_num(info.get("sharesOutstanding")),
                "TTM Revenue": ttm_rev,
                "Prior Yr Revenue": prior_rev,
                "TTM FCF": ttm_fcf,
                "P/E (Forward)": safe_num(info.get("forwardPE")),
                "Debt/Equity": safe_num(info.get("debtToEquity")),
                "Gross Margin %": (safe_num(info.get("grossMargins")) or 0) * 100,
                "Profit Margin %": (safe_num(info.get("profitMargins")) or 0) * 100,
                "Div Yield %": (safe_num(info.get("dividendYield")) or 0) * 100,
                "WACC Est. %": wacc * 100
            })
        except:
            continue

    df = pd.DataFrame(stock_list)

    # Light cleaning / ordering
    if not df.empty:
        df = df.sort_values("Market Cap", ascending=False).reset_index(drop=True)
    return df


def check_ma_crossover(ticker, interval="1d", period="2y"):
    """Logic to detect when MA 314 crosses UNDER MA 30."""
    try:
        data = yf.Ticker(ticker).history(period=period, interval=interval)
        if data is None or data.empty or len(data) < 315:
            return False

        ma30 = data["Close"].rolling(window=30).mean()
        ma314 = data["Close"].rolling(window=314).mean()

        curr_30, prev_30 = ma30.iloc[-1], ma30.iloc[-2]
        curr_314, prev_314 = ma314.iloc[-1], ma314.iloc[-2]

        return (prev_314 >= prev_30) and (curr_314 < curr_30)
    except:
        return False


def calculate_dcf_upgraded(
    ticker,
    fcf_growth,
    wacc,
    terminal_growth=0.0175,
    years=5
):
    """
    Upgraded DCF:
    - Uses TTM FCF (or fallback annual)
    - Discount factor: (1 + WACC)^n
    - Terminal growth constrained (1.5%–2.0%), constant
    - Returns key data fields + valuation
    """
    try:
        s = yf.Ticker(ticker)
        info = s.info

        price = safe_num(info.get("currentPrice"))
        shares = safe_num(info.get("sharesOutstanding"))
        market_cap = safe_num(info.get("marketCap"))

        if shares is None or shares <= 0:
            return None

        ttm_rev, prior_rev = get_revenue_ttm_and_prior_year(s)
        ttm_fcf = get_ttm_fcf(s)

        # Must have FCF to run DCF
        if ttm_fcf is None or not isfinite(ttm_fcf):
            return None

        # Safety: terminal growth must be < WACC
        terminal_growth = min(max(terminal_growth, 0.015), 0.02)
        if terminal_growth >= wacc:
            terminal_growth = max(0.015, wacc - 0.01)  # force spacing if user pushes WACC very low

        # Project and discount
        pv_sum = 0.0
        projected_fcf = float(ttm_fcf)

        for year in range(1, years + 1):
            projected_fcf *= (1 + fcf_growth)
            discount_factor = (1 + wacc) ** year
            pv_sum += projected_fcf / discount_factor

        # Terminal Value
        final_year_fcf = projected_fcf
        terminal_value = final_year_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
        terminal_pv = terminal_value / ((1 + wacc) ** years)

        enterprise_value = pv_sum + terminal_pv
        intrinsic_per_share = enterprise_value / shares

        return {
            "Ticker": ticker,
            "MarketCap": market_cap,
            "CurrentPrice": price,
            "SharesOut": shares,
            "TTMRevenue": ttm_rev,
            "PriorYearRevenue": prior_rev,
            "TTMFCF": float(ttm_fcf),
            "WACC": wacc,
            "TerminalGrowth": terminal_growth,
            "PV_FCF_Sum": pv_sum,
            "TerminalValue": terminal_value,
            "TerminalPV": terminal_pv,
            "EnterpriseValue": enterprise_value,
            "Intrinsic": intrinsic_per_share
        }
    except:
        return None


def fmt_money(x):
    if x is None or not isfinite(x):
        return "—"
    absx = abs(x)
    if absx >= 1e12:
        return f"${x/1e12:,.2f}T"
    if absx >= 1e9:
        return f"${x/1e9:,.2f}B"
    if absx >= 1e6:
        return f"${x/1e6:,.2f}M"
    if absx >= 1e3:
        return f"${x:,.0f}"
    return f"${x:,.2f}"


def fmt_pct(x):
    if x is None or not isfinite(x):
        return "—"
    return f"{x*100:.2f}%"


# -----------------------------
# 2) SIDEBAR: UNIVERSE SETTINGS
# -----------------------------

st.sidebar.title("Finviz Clone Pro")

st.sidebar.subheader("Universe (Free)")
include_nasdaq = st.sidebar.checkbox("Include NASDAQ", value=False)
include_amex = st.sidebar.checkbox("Include AMEX (NYSE American)", value=False)

st.sidebar.subheader("Market Cap Filter")
min_mc_b = st.sidebar.slider("Min Market Cap ($B)", 2.0, 200.0, 2.0, 1.0)
min_market_cap = min_mc_b * 1e9

st.sidebar.subheader("Performance")
max_scan = st.sidebar.slider("Max tickers to scan (speed)", 50, 1200, 300, 50)

with st.spinner("Loading universe + fetching market data..."):
    universe = get_us_listed_universe(include_nasdaq=include_nasdaq, include_amex=include_amex)
    master_df = fetch_base_data(universe, max_scan=max_scan, min_market_cap=min_market_cap)

feature = st.sidebar.selectbox("Mode", ["Screener", "DCF Valuation"])


# -----------------------------
# 3) FEATURE: SCREENER
# -----------------------------

if feature == "Screener":
    st.header("Stock Screener & Technical Signals")

    if master_df.empty:
        st.warning("No stocks found with the current universe settings. Try increasing scan size or lowering min market cap.")
        st.stop()

    tab_select = st.sidebar.radio("Screener Tabs", ["Descriptive", "Fundamental", "Technical"])
    filtered_df = master_df.copy()

    if tab_select == "Descriptive":
        sectors = st.sidebar.multiselect("Sector", options=sorted([x for x in master_df["Sector"].dropna().unique()]))
        if sectors:
            filtered_df = filtered_df[filtered_df["Sector"].isin(sectors)]

        industries = st.sidebar.multiselect("Industry", options=sorted([x for x in master_df["Industry"].dropna().unique()])[:300])
        if industries:
            filtered_df = filtered_df[filtered_df["Industry"].isin(industries)]

    elif tab_select == "Fundamental":
        max_pe = st.sidebar.slider("Max Forward P/E", 0.0, 200.0, 50.0)
        filtered_df = filtered_df[(filtered_df["P/E (Forward)"].fillna(9999) <= max_pe)]

        max_de = st.sidebar.slider("Max Debt/Equity", 0.0, 500.0, 200.0)
        filtered_df = filtered_df[(filtered_df["Debt/Equity"].fillna(9999) <= max_de)]

        min_margin = st.sidebar.slider("Min Profit Margin %", -50.0, 50.0, 0.0)
        filtered_df = filtered_df[(filtered_df["Profit Margin %"].fillna(-9999) >= min_margin)]

    elif tab_select == "Technical":
        st.sidebar.subheader("SMA 314 Cross Under 30")
        do_daily = st.sidebar.checkbox("Daily Chart Cross", value=False)
        do_4h = st.sidebar.checkbox("4H Chart Cross", value=False)

        if do_daily or do_4h:
            with st.spinner("Scanning chart patterns (this can be slow)..."):
                hits = []
                for t in filtered_df["Ticker"]:
                    valid = True
                    if do_daily and not check_ma_crossover(t, "1d", "2y"):
                        valid = False
                    if valid and do_4h and not check_ma_crossover(t, "4h", "60d"):
                        valid = False
                    if valid:
                        hits.append(t)
                filtered_df = filtered_df[filtered_df["Ticker"].isin(hits)]

    # Display Table
    display_cols = [
        "Ticker", "Sector", "Industry", "Market Cap", "Price",
        "TTM Revenue", "TTM FCF", "P/E (Forward)", "Debt/Equity", "WACC Est. %"
    ]
    show_df = filtered_df.copy()
    if not show_df.empty:
        # Human-friendly formatting
        show_df["Market Cap"] = show_df["Market Cap"].apply(fmt_money)
        show_df["TTM Revenue"] = show_df["TTM Revenue"].apply(fmt_money)
        show_df["TTM FCF"] = show_df["TTM FCF"].apply(fmt_money)
        show_df["Price"] = show_df["Price"].apply(lambda x: f"${x:,.2f}" if x and isfinite(x) else "—")
        show_df["WACC Est. %"] = show_df["WACC Est. %"].apply(lambda x: f"{x:.2f}%" if x and isfinite(x) else "—")

    st.dataframe(show_df[display_cols] if not show_df.empty else show_df, use_container_width=True, hide_index=True)

    # Technical Charting
    if not filtered_df.empty:
        st.divider()
        sel = st.selectbox("View Technical Chart", filtered_df["Ticker"].tolist())
        hist = yf.Ticker(sel).history(period="2y")

        if hist is None or hist.empty:
            st.error("No chart data available for this ticker.")
        else:
            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=hist.index,
                        open=hist["Open"],
                        high=hist["High"],
                        low=hist["Low"],
                        close=hist["Close"],
                        name="Price"
                    )
                ]
            )
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"].rolling(30).mean(),
                                     line=dict(color="yellow", width=1), name="MA 30"))
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"].rolling(314).mean(),
                                     line=dict(color="purple", width=2), name="MA 314"))
            fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
            st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# 4) FEATURE: DCF VALUATION (UPGRADED)
# -----------------------------

elif feature == "DCF Valuation":
    st.header("5-Year DCF Analysis (Upgraded)")

    if master_df.empty:
        st.warning("No stocks found with the current universe settings. Try increasing scan size or lowering min market cap.")
        st.stop()

    target = st.selectbox("Select Ticker", master_df["Ticker"].tolist())

    # Pull computed WACC estimate from master_df for default
    row = master_df[master_df["Ticker"] == target].head(1)
    default_wacc = 0.09
    if not row.empty:
        try:
            default_wacc = float(row["WACC Est. %"].iloc[0]) / 100.0
        except:
            default_wacc = 0.09
    default_wacc = min(max(default_wacc, 0.06), 0.12)

    st.subheader("Assumptions")

    c1, c2, c3 = st.columns(3)

    # FCF growth (user-controlled)
    fcf_growth = c1.slider("FCF Growth (Annual)", 0.0, 0.40, 0.10, 0.01)

    # WACC (estimated, but adjustable within 6–12%)
    wacc = c2.slider("WACC (6%–12%)", 0.06, 0.12, float(default_wacc), 0.005)

    # Terminal growth constant band (1.5–2.0%)
    terminal_growth = c3.slider("Terminal Growth (Constant)", 0.015, 0.020, 0.0175, 0.0005)

    st.caption("Discounting uses: PV = FCF / (1 + WACC)^n (your requested formula).")

    if st.button("Run Valuation"):
        with st.spinner("Running DCF..."):
            res = calculate_dcf_upgraded(
                ticker=target,
                fcf_growth=fcf_growth,
                wacc=wacc,
                terminal_growth=terminal_growth,
                years=5
            )

        if not res:
            st.error("Financial statements unavailable or missing key fields (TTM FCF / shares). Try another ticker.")
            st.stop()

        # -----------------------------
        # DATA PANEL (requested fields)
        # -----------------------------
        st.subheader("Company Data")

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Market Cap", fmt_money(res["MarketCap"]))
        d2.metric("Current Price", f"${res['CurrentPrice']:.2f}" if res["CurrentPrice"] else "—")
        d3.metric("Shares Outstanding", f"{res['SharesOut']:,.0f}" if res["SharesOut"] else "—")
        d4.metric("TTM Free Cash Flow", fmt_money(res["TTMFCF"]))

        r1, r2, r3 = st.columns(3)
        r1.metric("TTM Revenue", fmt_money(res["TTMRevenue"]))
        r2.metric("Prior Year Revenue", fmt_money(res["PriorYearRevenue"]))
        if res["TTMRevenue"] and res["PriorYearRevenue"] and res["PriorYearRevenue"] != 0:
            yoy = (res["TTMRevenue"] - res["PriorYearRevenue"]) / abs(res["PriorYearRevenue"])
            r3.metric("Revenue YoY", f"{yoy*100:.2f}%")
        else:
            r3.metric("Revenue YoY", "—")

        # -----------------------------
        # VALUATION PANEL
        # -----------------------------
        st.subheader("Valuation Output")

        v1, v2, v3, v4 = st.columns(4)
        v1.metric("WACC", fmt_pct(res["WACC"]))
        v2.metric("Terminal Growth", fmt_pct(res["TerminalGrowth"]))
        v3.metric("PV of 5Y FCF", fmt_money(res["PV_FCF_Sum"]))
        v4.metric("Terminal Value (PV)", fmt_money(res["TerminalPV"]))

        st.divider()

        m1, m2, m3 = st.columns(3)
        m1.metric("Enterprise Value (DCF)", fmt_money(res["EnterpriseValue"]))
        m2.metric("Intrinsic Value / Share", f"${res['Intrinsic']:.2f}" if res["Intrinsic"] else "—")

        if res["CurrentPrice"] and res["CurrentPrice"] > 0 and res["Intrinsic"] and isfinite(res["Intrinsic"]):
            mos = (res["Intrinsic"] - res["CurrentPrice"]) / res["CurrentPrice"]
            m3.metric("Margin of Safety", f"{mos*100:.2f}%", delta=f"{mos*100:.2f}%")
            if res["Intrinsic"] > res["CurrentPrice"]:
                st.success(f"**{target}** appears **Undervalued** under these assumptions.")
            else:
                st.error(f"**{target}** appears **Overvalued** under these assumptions.")
        else:
            m3.metric("Margin of Safety", "—")
            st.info("Margin of Safety not available (missing current price or intrinsic).")
