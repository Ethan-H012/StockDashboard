
import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("Stock Portfolio Dashboard - Full View")

# 초기 종목 목록
if "tickers" not in st.session_state:
    st.session_state.tickers = ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

# 상단 검색창
st.subheader("🔍 Add a Stock")
search_col = st.columns([4, 1])
new_ticker = search_col[0].text_input("Enter ticker to add (e.g., TSLA, AAPL, NVDA)", label_visibility="collapsed")
if search_col[1].button("Add") and new_ticker:
    t = new_ticker.strip().upper()
    if t and t not in st.session_state.tickers:
        st.session_state.tickers.append(t)

# 종목 삭제
st.write("### Current Portfolio")
remove_cols = st.columns(len(st.session_state.tickers))
for i, tkr in enumerate(st.session_state.tickers):
    with remove_cols[i]:
        if st.button(f"❌ {tkr}"):
            st.session_state.tickers.remove(tkr)

# 날짜 설정
end = datetime.today()
start = end - timedelta(days=60)

# 종목 카드 반복
cols = st.columns(3)
for i, ticker in enumerate(st.session_state.tickers):
    with cols[i % 3]:
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, threads=True)
            if df.empty or "Adj Close" not in df.columns:
                st.error(f"{ticker} has no data.")
                continue

            df["SMA15"] = df["Adj Close"].rolling(window=15).mean()
            df["Upper"] = df["SMA15"] * 1.05
            df["Lower"] = df["SMA15"] * 0.95

            current_price = df["Adj Close"].iloc[-1]
            past_price = df["Adj Close"].iloc[-2] if len(df) >= 2 else current_price
            delta = ((current_price - past_price) / past_price * 100) if past_price != 0 else 0

            st.metric(label=f"{ticker}", value=f"${current_price:.2f}", delta=f"{delta:.2f}%")

            chart_data = df[["Adj Close", "SMA15", "Upper", "Lower"]].dropna().reset_index().melt('Date')
            if chart_data.empty:
                st.warning(f"Insufficient data for {ticker}'s chart.")
                continue

            line_chart = alt.Chart(chart_data).mark_line().encode(
                x=alt.X('Date:T', title=None),
                y=alt.Y('value:Q', title=None),
                color=alt.Color('variable:N', title="Legend")
            ).properties(height=150)

            st.altair_chart(line_chart, use_container_width=True)

            with st.expander(f"Details for {ticker}"):
                st.markdown("##### Latest News (sample headlines)")
                st.markdown(f"- [Yahoo Finance News for {ticker}](https://finance.yahoo.com/quote/{ticker})")
                st.markdown(f"- [MarketWatch on {ticker}](https://www.marketwatch.com/investing/stock/{ticker.lower()})")

                st.markdown("##### Analyst Summary (sample data)")
                st.write({
                    "Buy": "63%",
                    "Hold": "29%",
                    "Sell": "8%",
                    "Target Price": f"${(current_price * 1.15):.2f}"
                })

        except Exception as e:
            st.error(f"Error loading {ticker}: {e}")
