
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
import requests

st.set_page_config(layout="wide")
st.title("📊 Smart Stock Dashboard (No Push Alerts)")

# Load secrets for Finnhub only
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY"]

# Show dual timezone timestamp
ny_time = datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M")
kr_time = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%H:%M")
st.caption(f"⏱ Last update: {ny_time} (ROK {kr_time})")

# Initialize ticker list
if "tickers" not in st.session_state:
    st.session_state.tickers = ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

# Stock input
st.subheader("🔍 Add a Stock")
top = st.columns([5, 1])
new_ticker = top[0].text_input("Enter a stock ticker", label_visibility="collapsed")
if top[1].button("Add") and new_ticker:
    ticker = new_ticker.strip().upper()
    if ticker and ticker not in st.session_state.tickers:
        st.session_state.tickers.append(ticker)

# Date range
end = datetime.today()
start = end - timedelta(days=365)

# Render charts
cols = st.columns(3)
for i, ticker in enumerate(st.session_state.tickers):
    with cols[i % 3]:
        try:
            df = yf.Ticker(ticker).history(start=start, end=end)
            if df.empty or "Close" not in df.columns:
                st.error(f"⚠️ {ticker}: No valid data.")
                continue

            df["Adj Close"] = df["Close"]
            df["SMA15"] = df["Adj Close"].rolling(window=15).mean()
            df["Upper"] = df["SMA15"] * 1.05
            df["Lower"] = df["SMA15"] * 0.95
            current = df["Adj Close"].iloc[-1]
            previous = df["Adj Close"].iloc[-2] if len(df) >= 2 else current
            change = ((current - previous) / previous * 100) if previous != 0 else 0

            st.metric(label=f"{ticker}", value=f"${current:.2f}", delta=f"{change:.2f}%")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["Adj Close"], name="Adj Close"))
            fig.add_trace(go.Scatter(x=df.index, y=df["SMA15"], name="SMA15"))
            fig.add_trace(go.Scatter(x=df.index, y=df["Upper"], name="Upper", line=dict(dash="dot")))
            fig.add_trace(go.Scatter(x=df.index, y=df["Lower"], name="Lower", line=dict(dash="dot")))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10), showlegend=True)

            st.plotly_chart(fig, use_container_width=True)

            st.markdown(
                f"<div style='text-align:right;'>"
                f"<form action='' method='post'>"
                f"<button name='remove_{ticker}' type='submit' style='background-color:#ff4b4b;color:white;border:none;padding:2px 6px;border-radius:4px;font-size:12px;'>Remove</button>"
                f"</form></div>",
                unsafe_allow_html=True,
            )

            if st.session_state.get(f"remove_{ticker}"):
                st.session_state.tickers.remove(ticker)
                st.experimental_rerun()

            with st.expander(f"Details for {ticker}"):
                st.markdown("**Latest News Headlines**")
                from_date = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
                to_date = datetime.today().strftime('%Y-%m-%d')
                news_url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
                news_resp = requests.get(news_url)
                if news_resp.status_code == 200:
                    news_items = news_resp.json()[:5]
                    if news_items:
                        for article in news_items:
                            st.markdown(f"- [{article['headline']}]({article['url']})")
                    else:
                        st.info("No recent headlines found.")
                else:
                    st.warning("News service unavailable.")

                st.markdown("**Analyst Recommendations**")
                rec_url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={ticker}&token={FINNHUB_API_KEY}"
                rec_resp = requests.get(rec_url)
                if rec_resp.status_code == 200 and rec_resp.json():
                    latest = rec_resp.json()[0]
                    st.write({
                        "Strong Buy": latest.get("strongBuy", "N/A"),
                        "Buy": latest.get("buy", "N/A"),
                        "Hold": latest.get("hold", "N/A"),
                        "Sell": latest.get("sell", "N/A"),
                        "Strong Sell": latest.get("strongSell", "N/A")
                    })
                else:
                    st.info("No analyst recommendation data found.")

        except Exception as e:
            st.error(f"{ticker}: error - {e}")
