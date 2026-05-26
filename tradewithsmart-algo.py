import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# RSI Calculation (Standard Pandas)
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# MACD Calculation (Standard Pandas)
def calculate_macd(data, fast=12, slow=26, signal=9):
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

# App logic
st.title("TradeWithSmart - Pro Algorithmic Engine")
ticker = st.text_input("Enter Ticker (e.g., DBL.NS):", "DBL.NS")

if ticker:
    df = yf.download(ticker, period="1mo", interval="5m")
    
    if not df.empty:
        df['RSI'] = calculate_rsi(df)
        df['MACD'], df['Signal_Line'] = calculate_macd(df)
        
        # Display Data
        st.subheader("Engine Historical Log View")
        st.dataframe(df[['Open', 'High', 'Low', 'Close', 'RSI', 'MACD', 'Signal_Line']].tail(10))
        
        # Plotting
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        st.plotly_chart(fig)
    else:
        st.error("Data fetch failed. Check Ticker.")
