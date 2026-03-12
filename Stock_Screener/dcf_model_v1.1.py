# Stefan Screener and DCF valuation model
# NYSE + Nasdaq universe (NasdaqTrader)
# Tab 1: Screener
#   - Market cap filter
#   - MA200 crosses UNDER MA30 within last N trading days (default 7)
#   - Matched tickers in dropdown -> selecting shows chart
#   - Export screener results to Excel
#
# Tab 2: DCF (EXACT Excel Sheet 1 logic)
#   - Only input: WACC in %
#   - Shows Undervalued/Overvalued badge (green/red)
#   - Export DCF to Excel (inputs + forecast + totals)
#
# DCF model = Method (4 years + terminal at year 4):
#   g = (TTM Revenue - Prior Year Revenue) / Prior Year Revenue
#   FCF Margin = TTM FCF / TTM Revenue
#   Revenue_t = Revenue_{t-1} * (1 + g) for 4 years (year1 from TTM)
#   FCF_t = Revenue_t * margin
#   PV = sum(FCF_t/(1+WACC)^t) + TV/(1+WACC)^4
#   TV = FCF_4*(1+TerminalGrowth)/(WACC-TerminalGrowth), TerminalGrowth = 1%
#   Shares (millions) = MarketCap(millions) / Price
#   Intrinsic = PV(millions) / Shares(millions)
#
# Units:
# - Convert market cap, revenues, FCF to MILLIONS (USD) by /1e6, due to the data are in thousands
# - Price stays USD/share

import time
from io import BytesIO, StringIO

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="NYSE+Nasdaq Screener + DCF", layout="wide")

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"


# -----------------------------
# Universe: NYSE + Nasdaq
# -----------------------------
@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def load_nyse_nasdaq_universe() -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}

    nasdaq_txt = requests.get(NASDAQ_LISTED_URL, headers=headers, timeout=30).text
    nasdaq_df = pd.read_csv(StringIO(nasdaq_txt), sep="|")
    nasdaq_df = nasdaq_df[~nasdaq_df["Symbol"].astype(str).str.contains("File Creation Time", na=False)]
    nasdaq_df = nasdaq_df.rename(columns={"Symbol": "symbol", "Security Name": "name"})
    nasdaq_df["exchange"] = "NASDAQ"
    nasdaq_df = nasdaq_df[["symbol", "name", "exchange"]]

    other_txt = requests.get(OTHER_LISTED_URL, headers=headers, timeout=30).text
    other_df = pd.read_csv(StringIO(other_txt), sep="|")
    other_df = other_df[~other_df["ACT Symbol"].astype(str).str.contains("File Creation Time", na=False)]
    other_df = other_df.rename(columns={"ACT Symbol": "symbol", "Security Name": "name", "Exchange": "exchange_code"})
    other_df = other_df[other_df["exchange_code"] == "N"].copy()  # NYSE
    other_df["exchange"] = "NYSE"
    other_df = other_df[["symbol", "name", "exchange"]]

    uni = pd.concat([nasdaq_df, other_df], ignore_index=True)
    uni["symbol"] = uni["symbol"].astype(str).str.upper().str.replace(".", "-", regex=False)
    uni = uni[uni["symbol"].str.len().between(1, 10)]
    uni = uni.drop_duplicates(subset=["symbol"]).sort_values("symbol").reset_index(drop=True)
    return uni


# -----------------------------
# Utility
# -----------------------------
def safe_float(x):
    try:
        if x is None:
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def fmt_money_short(x):
    if pd.isna(x):
        return ""
    x = float(x)
    for unit, div in [("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)]:
        if abs(x) >= div:
            return f"{x/div:.2f}{unit}"
    return f"{x:.0f}"


def valuation_label(intrinsic: float, price: float) -> tuple[str, str]:
    if np.isnan(intrinsic) or np.isnan(price) or price <= 0:
        return "N/A", "#6b7280"  # gray
    if intrinsic >= price:
        return "Undervalued", "#16a34a"  # green
    return "Overvalued", "#dc2626"      # red


def render_badge(text: str, color: str):
    st.markdown(
        f"""
        <div style="
            display:inline-block;
            padding:8px 12px;
            border-radius:999px;
            background:{color}1A;
            border:1px solid {color}66;
            color:{color};
            font-weight:700;">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def df_to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()


# -----------------------------
# Prices + MA (robust)
# -----------------------------
@st.cache_data(show_spinner=False, ttl=60 * 30)
def get_prices(symbol: str, period: str) -> pd.DataFrame:
    df = yf.download(
        symbol,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=False,
    )
    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    if "Close" not in df.columns:
        return pd.DataFrame()

    df = df.dropna(subset=["Close"]).copy()
    df["MA30"] = df["Close"].rolling(30, min_periods=30).mean()
    df["MA200"] = df["Close"].rolling(200, min_periods=200).mean()
    return df


def cross_under_in_last_n_trading_days(df: pd.DataFrame, n_days: int = 3) -> bool:
    if df is None or df.empty:
        return False
    if "MA30" not in df.columns or "MA200" not in df.columns:
        return False

    d = df.dropna(subset=["MA30", "MA200"]).copy()
    if len(d) < max(205, n_days + 2):
        return False

    prev200 = d["MA200"].shift(1)
    prev30 = d["MA30"].shift(1)
    cross = (prev200 >= prev30) & (d["MA200"] < d["MA30"])
    return bool(cross.tail(n_days).any())


def plot_price_ma(df: pd.DataFrame, title: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA30"], name="MA30"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA200"], name="MA200"))
    fig.update_layout(height=450, title=title, xaxis_title="Date", yaxis_title="Price")
    return fig


# -----------------------------
# Yahoo getters for Sheet 1 DCF
# -----------------------------
@st.cache_data(show_spinner=False, ttl=60 * 60 * 6)
def get_market_cap_price_name(symbol: str) -> tuple[float, float, str]:
    t = yf.Ticker(symbol)
    try:
        info = t.info or {}
    except Exception:
        info = {}

    market_cap = safe_float(info.get("marketCap"))
    price = safe_float(info.get("currentPrice"))
    if np.isnan(price):
        price = safe_float(info.get("regularMarketPrice"))

    name = info.get("shortName") or info.get("longName") or ""

    if np.isnan(price) or price <= 0:
        try:
            hist = t.history(period="10d")
            if hist is not None and not hist.empty:
                price = float(hist["Close"].iloc[-1])
        except Exception:
            pass

    return market_cap, price, str(name)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 6)
def get_ttm_revenue(symbol: str) -> float:
    t = yf.Ticker(symbol)
    try:
        q = t.quarterly_financials
    except Exception:
        return np.nan
    if q is None or q.empty:
        return np.nan

    for row in ["Total Revenue", "TotalRevenue", "Revenue"]:
        if row in q.index:
            s = q.loc[row].dropna().astype(float)
            idx = pd.to_datetime(s.index, errors="coerce")
            if idx.notna().any():
                s.index = idx
                s = s.sort_index()
                if len(s) >= 4:
                    return float(s.iloc[-4:].sum())
            else:
                if len(s) >= 4:
                    return float(s.iloc[:4].sum())
    return np.nan


@st.cache_data(show_spinner=False, ttl=60 * 60 * 6)
def get_prior_year_revenue(symbol: str) -> float:
    t = yf.Ticker(symbol)
    try:
        a = t.financials
    except Exception:
        return np.nan
    if a is None or a.empty:
        return np.nan

    for row in ["Total Revenue", "TotalRevenue", "Revenue"]:
        if row in a.index:
            s = a.loc[row].dropna().astype(float)
            idx = pd.to_datetime(s.index, errors="coerce")
            if idx.notna().any():
                s.index = idx
                s = s.sort_index()
                return float(s.iloc[-1])
            return float(s.iloc[0])
    return np.nan


@st.cache_data(show_spinner=False, ttl=60 * 60 * 6)
def get_ttm_fcf(symbol: str) -> float:
    t = yf.Ticker(symbol)
    try:
        qcf = t.quarterly_cashflow
    except Exception:
        return np.nan
    if qcf is None or qcf.empty:
        return np.nan

    ocf_rows = [
        "Total Cash From Operating Activities",
        "Operating Cash Flow",
        "Net Cash Provided By Operating Activities",
    ]
    capex_rows = ["Capital Expenditures", "Capital Expenditure"]

    ocf_row = next((r for r in ocf_rows if r in qcf.index), None)
    capex_row = next((r for r in capex_rows if r in qcf.index), None)
    if ocf_row is None or capex_row is None:
        return np.nan

    ocf = qcf.loc[ocf_row].dropna().astype(float)
    capex = qcf.loc[capex_row].dropna().astype(float)

    try:
        ocf.index = pd.to_datetime(ocf.index, errors="coerce")
        capex.index = pd.to_datetime(capex.index, errors="coerce")
        ocf = ocf.sort_index()
        capex = capex.sort_index()
        if len(ocf) < 4 or len(capex) < 4:
            return np.nan
        return float(np.nansum(ocf.iloc[-4:].values - capex.iloc[-4:].values))
    except Exception:
        if len(ocf) < 4 or len(capex) < 4:
            return np.nan
        return float(np.nansum(ocf.iloc[:4].values - capex.iloc[:4].values))


# -----------------------------
# Excel Sheet 1 DCF implementation (exact structure)
# -----------------------------
def sheet1_dcf_price(
    market_cap_usd: float,
    price_usd: float,
    ttm_rev_usd: float,
    prior_rev_usd: float,
    ttm_fcf_usd: float,
    wacc: float,               # decimal
    terminal_growth: float = 0.01
) -> dict:
    market_cap_m = market_cap_usd / 1e6
    ttm_rev_m = ttm_rev_usd / 1e6
    prior_rev_m = prior_rev_usd / 1e6
    ttm_fcf_m = ttm_fcf_usd / 1e6

    if any(np.isnan([market_cap_m, price_usd, ttm_rev_m, prior_rev_m, ttm_fcf_m])) or price_usd <= 0:
        return {"ok": False, "reason": "Missing/invalid Market Cap, Price, Revenue, or FCF."}
    if prior_rev_m == 0 or ttm_rev_m == 0:
        return {"ok": False, "reason": "Revenue is zero/missing."}
    if terminal_growth >= wacc:
        return {"ok": False, "reason": "Terminal growth must be < WACC."}

    g = (ttm_rev_m - prior_rev_m) / prior_rev_m
    fcf_margin = ttm_fcf_m / ttm_rev_m

    rev1 = ttm_rev_m * (1 + g)
    rev2 = rev1 * (1 + g)
    rev3 = rev2 * (1 + g)
    rev4 = rev3 * (1 + g)
    revs = [rev1, rev2, rev3, rev4]

    fcfs = [r * fcf_margin for r in revs]

    dfs = [(1 + wacc) ** i for i in [1, 2, 3, 4]]
    pv_fcfs = [fcfs[i] / dfs[i] for i in range(4)]
    pv_sum = float(np.nansum(pv_fcfs))

    fcf4 = fcfs[-1]
    terminal_val = fcf4 * (1 + terminal_growth) / (wacc - terminal_growth)
    terminal_pv = terminal_val / dfs[-1]

    pv_total = pv_sum + terminal_pv  # millions
    shares_m = market_cap_m / price_usd
    intrinsic = pv_total / shares_m  # USD/share

    return {
        "ok": True,
        "intrinsic": float(intrinsic),
        "pv_sum_m": float(pv_sum),
        "terminal_val_m": float(terminal_val),
        "terminal_pv_m": float(terminal_pv),
        "pv_total_m": float(pv_total),
        "shares_m": float(shares_m),
        "market_cap_m": float(market_cap_m),
        "ttm_rev_m": float(ttm_rev_m),
        "prior_rev_m": float(prior_rev_m),
        "ttm_fcf_m": float(ttm_fcf_m),
        "g": float(g),
        "fcf_margin": float(fcf_margin),
        "revs_m": revs,
        "fcfs_m": fcfs,
        "pv_fcfs_m": pv_fcfs,
    }


# -----------------------------
# App UI
# -----------------------------
st.title("📈 NYSE + Nasdaq: Screener + DCF (Excel Sheet Method)")

uni = load_nyse_nasdaq_universe()
all_symbols = uni["symbol"].tolist()

tab_screener, tab_dcf = st.tabs(["🔎 Screener", "💰 DCF (Excel Sheet 1)"])

# =============================
# TAB 1: Screener
# =============================
with tab_screener:
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.caption(f"Universe loaded: **{len(uni):,}** tickers (NYSE + Nasdaq)")

        st.subheader("Filters")
        min_mcap_b = st.number_input("Min Market Cap (USD, billions)", 0.0, 5000.0, 10.0, 1.0)
        max_mcap_b = st.number_input("Max Market Cap (USD, billions)", 0.0, 5000.0, 5000.0, 10.0)
        min_mcap = min_mcap_b * 1e9
        max_mcap = max_mcap_b * 1e9

        lookback_days = st.slider("Cross-under lookback (trading days)", 1, 30, 7)
        period = st.selectbox("Price history period", ["1y", "2y", "5y"], index=1)

        st.subheader("Performance controls")
        max_to_scan = st.slider("Max tickers to scan", 50, len(all_symbols), min(800, len(all_symbols)))

        run_btn = st.button("Run Screener", type="primary")

    with right:
        st.subheader("Matches")

        if "screen_df" not in st.session_state:
            st.session_state.screen_df = pd.DataFrame()
        if "screen_selected" not in st.session_state:
            st.session_state.screen_selected = None

        if run_btn:
            tickers = all_symbols[:max_to_scan]
            results = []

            progress = st.progress(0)
            status = st.empty()

            for i, sym in enumerate(tickers, start=1):
                status.write(f"Scanning {sym} ({i}/{len(tickers)})...")
                progress.progress(i / len(tickers))

                market_cap, price, name = get_market_cap_price_name(sym)
                if np.isnan(market_cap) or market_cap < min_mcap or market_cap > max_mcap:
                    continue

                price_df = get_prices(sym, period)
                if price_df.empty or len(price_df) < 205:
                    continue

                if not cross_under_in_last_n_trading_days(price_df, n_days=int(lookback_days)):
                    continue

                last_close = float(price_df["Close"].iloc[-1])
                exchange = uni.loc[uni["symbol"] == sym, "exchange"].iloc[0]

                results.append({
                    "Ticker": sym,
                    "Name": name,
                    "Exchange": exchange,
                    "MarketCap_fmt": fmt_money_short(market_cap),
                    "Last_Close": last_close,
                })

                time.sleep(0.005)

            status.empty()
            progress.empty()

            df = pd.DataFrame(results)
            st.session_state.screen_df = df
            st.session_state.screen_selected = df["Ticker"].iloc[0] if not df.empty else None

        df = st.session_state.screen_df

        if df is None or df.empty:
            st.info("Run the screener to see matched tickers in a dropdown.")
        else:
            st.dataframe(df, use_container_width=True)

            # Export screener results to Excel
            excel_bytes = df_to_excel_bytes({"Screener Results": df})
            st.download_button(
                "⬇️ Download Screener Results (Excel)",
                data=excel_bytes,
                file_name="screener_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.divider()
            st.subheader("Chart (select a matched ticker)")
            options = df["Ticker"].tolist()
            selected = st.selectbox(
                "Matched tickers",
                options,
                index=options.index(st.session_state.screen_selected) if st.session_state.screen_selected in options else 0
            )
            st.session_state.screen_selected = selected

            chart_df = get_prices(selected, period)
            if chart_df.empty:
                st.error("No price data for selected ticker.")
            else:
                st.plotly_chart(plot_price_ma(chart_df, f"{selected} — Daily Close with MA30 & MA200"), use_container_width=True)

# =============================
# TAB 2: DCF
# =============================
with tab_dcf:
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader("Inputs")
        ticker = st.selectbox(
            "Ticker",
            all_symbols,
            index=all_symbols.index("AAPL") if "AAPL" in all_symbols else 0
        )
        wacc_pct = st.number_input("WACC (%)", min_value=0.0, max_value=50.0, value=11.0, step=0.25)
        wacc = float(wacc_pct) / 100.0
        terminal_growth = 0.01

        run_dcf = st.button("Calculate DCF", type="primary")
        st.caption("DCF matches Excel Sheet 1 (4 years + terminal at year 4, g from TTM vs prior, FCF margin from TTM FCF / TTM rev).")

    with right:
        st.subheader("DCF Output")

        if run_dcf:
            market_cap, price, name = get_market_cap_price_name(ticker)
            ttm_rev = get_ttm_revenue(ticker)
            prior_rev = get_prior_year_revenue(ticker)
            ttm_fcf = get_ttm_fcf(ticker)

            model = sheet1_dcf_price(
                market_cap_usd=market_cap,
                price_usd=price,
                ttm_rev_usd=ttm_rev,
                prior_rev_usd=prior_rev,
                ttm_fcf_usd=ttm_fcf,
                wacc=wacc,
                terminal_growth=terminal_growth,
            )

            if not model.get("ok"):
                st.error(model.get("reason", "DCF failed."))
            else:
                intrinsic = model["intrinsic"]
                upside = (intrinsic / price - 1) if (not np.isnan(price) and price > 0) else np.nan

                label, color = valuation_label(intrinsic, price)
                render_badge(label, color)

                c1, c2, c3 = st.columns(3)
                c1.metric("Intrinsic Value / Share (USD)", f"{intrinsic:,.2f}")
                c2.metric("Price (USD)", f"{price:,.2f}" if not np.isnan(price) else "N/A")
                c3.metric("Upside vs Price", f"{upside:.1%}" if not np.isnan(upside) else "N/A")

                inputs_df = pd.DataFrame({
                    "Metric": [
                        "Ticker", "Name",
                        "Market Cap (M)", "Shares (M)=MarketCap/Price",
                        "TTM Revenue (M)", "Prior Year Revenue (M)",
                        "Growth g", "TTM FCF (M)", "FCF Margin",
                        "WACC", "Terminal Growth"
                    ],
                    "Value": [
                        ticker, name,
                        f"{model['market_cap_m']:,.2f}",
                        f"{model['shares_m']:,.2f}",
                        f"{model['ttm_rev_m']:,.2f}",
                        f"{model['prior_rev_m']:,.2f}",
                        f"{model['g']:.2%}",
                        f"{model['ttm_fcf_m']:,.2f}",
                        f"{model['fcf_margin']:.2%}",
                        f"{wacc:.2%}",
                        f"{terminal_growth:.2%}",
                    ]
                })

                forecast = pd.DataFrame({
                    "Year": ["Year 1", "Year 2", "Year 3", "Year 4"],
                    "Revenue (M)": model["revs_m"],
                    "FCF (M)": model["fcfs_m"],
                    "PV of FCF (M)": model["pv_fcfs_m"],
                })

                totals = pd.DataFrame({
                    "Component": ["PV Sum (Years 1–4)", "Terminal Value (Year 4)", "PV Terminal", "Total PV (Equity)"],
                    "Value (M)": [model["pv_sum_m"], model["terminal_val_m"], model["terminal_pv_m"], model["pv_total_m"]],
                })

                st.divider()
                st.dataframe(inputs_df, use_container_width=True)
                st.dataframe(forecast, use_container_width=True)
                st.dataframe(totals, use_container_width=True)

                # Export DCF to Excel
                excel_bytes = df_to_excel_bytes({
                    "DCF Inputs": inputs_df,
                    "DCF Forecast": forecast,
                    "DCF Totals": totals
                })
                st.download_button(
                    "⬇️ Download DCF (Excel)",
                    data=excel_bytes,
                    file_name=f"dcf_{ticker}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                price_df = get_prices(ticker, "2y")
                if price_df is not None and not price_df.empty:
                    st.divider()
                    st.subheader("Price chart (daily) with MA30 & MA200")
                    st.plotly_chart(plot_price_ma(price_df, f"{ticker} — Daily Close with MA30 & MA200"), use_container_width=True)