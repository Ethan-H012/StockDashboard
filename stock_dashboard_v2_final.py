
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 초기 종목 설정
if "tickers" not in st.session_state:
    st.session_state.tickers = ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

st.set_page_config(layout="wide")
st.title("Stock Portfolio Monitor")

# 종목 추가
new_ticker = st.text_input("Add a ticker (e.g., TSLA, AAPL, etc.)")
if st.button("Add Ticker") and new_ticker:
    ticker_upper = new_ticker.strip().upper()
    if ticker_upper not in st.session_state.tickers:
        st.session_state.tickers.append(ticker_upper)

# 종목 삭제 버튼
remove_cols = st.columns(len(st.session_state.tickers))
for i, tkr in enumerate(st.session_state.tickers):
    with remove_cols[i]:
        if st.button(f"❌ {tkr}"):
            st.session_state.tickers.remove(tkr)

# 데이터 로드
end = datetime.today()
start = end - timedelta(days=60)
raw_data = yf.download(st.session_state.tickers, start=start, end=end)

# 멀티인덱스 또는 단일 종목 대응
if isinstance(raw_data.columns, pd.MultiIndex):
    data = raw_data.xs("Adj Close", axis=1, level=1)
else:
    data = pd.DataFrame({"Adj Close": raw_data["Adj Close"]})
    data.columns = pd.MultiIndex.from_product([[st.session_state.tickers[0]], data.columns])

# Treemap 구성
latest_prices = data.iloc[-1]
previous_prices = data.iloc[-2]
returns = ((latest_prices - previous_prices) / previous_prices) * 100
treemap_df = pd.DataFrame({
    "Ticker": latest_prices.index,
    "Return": returns.values,
    "Price": latest_prices.values
})

fig = px.treemap(
    treemap_df,
    path=["Ticker"],
    values=[1] * len(treemap_df),
    color="Return",
    color_continuous_scale="RdYlGn",
    hover_data={"Price": True, "Return": True, "Ticker": False}
)
st.plotly_chart(fig, use_container_width=True)

# 종목 선택
selected_ticker = st.selectbox("View chart and signals for:", st.session_state.tickers)

# 상세 주가 및 시각 경고
df = yf.download(selected_ticker, start=start, end=end)
df["SMA15"] = df["Adj Close"].rolling(window=15).mean()
df["Upper"] = df["SMA15"] * 1.05
df["Lower"] = df["SMA15"] * 0.95

st.subheader(f"{selected_ticker} Price Chart with Moving Averages")
st.line_chart(df[["Adj Close", "SMA15", "Upper", "Lower"]])

# 시각 경고
current = df["Adj Close"].iloc[-1]
upper = df["Upper"].iloc[-1]
lower = df["Lower"].iloc[-1]
if current > upper:
    st.warning(f"{selected_ticker} is above the upper bound! ({current:.2f} > {upper:.2f})")
elif current < lower:
    st.warning(f"{selected_ticker} is below the lower bound! ({current:.2f} < {lower:.2f})")

# 뉴스 (링크 제공)
st.subheader("Latest News (Demo)")
st.markdown(f"- [View {selected_ticker} on Yahoo Finance](https://finance.yahoo.com/quote/{selected_ticker})")

st.caption("News API integration and email alerts coming soon...")
