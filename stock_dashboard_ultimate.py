
import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("📊 Smart Stock Dashboard")

# 초기 종목
if "tickers" not in st.session_state:
    st.session_state.tickers = ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

# 종목 검색/추가 UI
st.subheader("🔍 Add a Stock")
top = st.columns([5, 1])
new_ticker = top[0].text_input("Enter a stock ticker", label_visibility="collapsed")
if top[1].button("Add") and new_ticker:
    ticker = new_ticker.strip().upper()
    if ticker and ticker not in st.session_state.tickers:
        st.session_state.tickers.append(ticker)

# 종목 제거
st.markdown("### Current Portfolio")
del_cols = st.columns(len(st.session_state.tickers))
for i, tk in enumerate(st.session_state.tickers):
    with del_cols[i]:
        if st.button(f"❌ {tk}"):
            st.session_state.tickers.remove(tk)

# 기간 설정
end = datetime.today()
start = end - timedelta(days=60)
cols = st.columns(3)

# 종목 반복
for i, ticker in enumerate(st.session_state.tickers):
    with cols[i % 3]:
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, threads=False)
            if df.empty or "Adj Close" not in df.columns:
                st.error(f"{ticker}: No valid data.")
                continue

            # 계산
            df["SMA15"] = df["Adj Close"].rolling(window=15).mean()
            df["Upper"] = df["SMA15"] * 1.05
            df["Lower"] = df["SMA15"] * 0.95
            current = df["Adj Close"].iloc[-1]
            previous = df["Adj Close"].iloc[-2] if len(df) >= 2 else current
            change = ((current - previous) / previous * 100) if previous != 0 else 0

            # 메트릭
            st.metric(label=f"{ticker}", value=f"${current:.2f}", delta=f"{change:.2f}%")

            # 차트
            chart_df = df[["Adj Close", "SMA15", "Upper", "Lower"]].dropna().reset_index().melt("Date")
            if chart_df.empty:
                st.warning("No chart data.")
                continue

            chart = alt.Chart(chart_df).mark_line().encode(
                x=alt.X("Date:T", title=None),
                y=alt.Y("value:Q", title=None),
                color=alt.Color("variable:N", title="Legend")
            ).properties(height=160)
            st.altair_chart(chart, use_container_width=True)

            # 상세정보 확장
            with st.expander(f"Details for {ticker}"):
                st.markdown("**News & Headlines**")
                st.markdown(f"- [Yahoo Finance: {ticker}](https://finance.yahoo.com/quote/{ticker})")
                st.markdown(f"- [MarketWatch: {ticker}](https://www.marketwatch.com/investing/stock/{ticker.lower()})")

                st.markdown("**Analyst Estimates (Demo)**")
                st.write({
                    "Buy": "65%",
                    "Hold": "25%",
                    "Sell": "10%",
                    "Target Price": f"${(current * 1.15):.2f}"
                })

        except Exception as e:
            st.error(f"{ticker}: error - {e}")
