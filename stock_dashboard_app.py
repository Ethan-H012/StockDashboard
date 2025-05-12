import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

ticker_map = {
    "TSLL": "Direxion Tesla 2x ETF",
    "TSLA": "Tesla",
    "VRTX": "Vertex Pharmaceuticals",
    "MSFT": "Microsoft",
    "AAPL": "Apple",
    "SRPT": "Sarepta Therapeutics",
    "QSI": "Quantum-Si",
    "PFE": "Pfizer",
    "REKR": "Rekor Systems"
}

st.set_page_config(layout="wide")
st.title("📈 전체 주식 포트폴리오 대시보드")

end_date = datetime.today()
start_date = end_date - timedelta(days=120)

# 종목을 3개씩 묶어서 표시
tickers = list(ticker_map.keys())
rows = [tickers[i:i+3] for i in range(0, len(tickers), 3)]

for row in rows:
    cols = st.columns(len(row))
    for i, ticker in enumerate(row):
        with cols[i]:
            raw = yf.download(ticker, start=start_date, end=end_date)
            if raw.empty:
                st.error(f"{ticker} 데이터 없음")
                continue

            # 다중 컬럼 대응
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            data = raw[["Close"]].copy()
            data.rename(columns={"Close": "Adj Close"}, inplace=True)
            data["SMA15"] = data["Adj Close"].rolling(window=15).mean()
            data["Upper"] = data["SMA15"] * 1.05
            data["Lower"] = data["SMA15"] * 0.95

            # 현재가 및 변동률
            try:
                current = data["Adj Close"].dropna().iloc[-1]
                prev = data["Adj Close"].dropna().iloc[-2]
                pct = (current - prev) / prev * 100
            except:
                current = pct = None

            st.subheader(ticker)
            if current:
                st.metric("현재가", f"${current:.2f}", f"{pct:.2f}%", delta_color="normal")

            # Plotly 그래프
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data["Adj Close"], name="Adj Close", line=dict(color="blue")))
            fig.add_trace(go.Scatter(x=data.index, y=data["SMA15"], name="SMA15", line=dict(color="orange")))
            fig.add_trace(go.Scatter(x=data.index, y=data["Upper"], name="Upper", line=dict(color="red", dash="dot")))
            fig.add_trace(go.Scatter(x=data.index, y=data["Lower"], name="Lower", line=dict(color="red", dash="dot")))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
