import streamlit as st
import yfinance as yf
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TradeWithSmart - Algo Engine", layout="wide", page_icon="📈")

st.title("📈 TradeWithSmart - Indian Stock Algo Engine")
st.caption("Advanced Screener Matrix - Manual Ticker Engine Ready")

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("⚙️ Trading Parameters")

# 1. Custom Stock Input & Core List Selection combined
popular_stocks = ["SUZLON", "DBL", "OIL", "RVNL", "ADANIENT", "TATAMOTORS", "RELIANCE", "SBIN", "INFY", "ITC"]

st.sidebar.markdown("### 🔍 Select or Type Stock Ticker")
selected_option = st.sidebar.selectbox(
    "Quick Pick Popular Stocks:",
    options=popular_stocks,
    index=0
)

# User can type ANY ticker freely here if it's not in the quick list
custom_ticker = st.sidebar.text_input("Or Type Any NSE Symbol Manually:", value=selected_option)

# Standardizing ticker for Yahoo Finance (Adding .NS automatically)
raw_symbol = custom_ticker.strip().upper()
if raw_symbol:
    ticker = f"{raw_symbol}.NS"
else:
    ticker = "SUZLON.NS"  # Safeguard baseline

# 2. Technical Chart Configurations
st.sidebar.markdown("---")
interval_choice = st.sidebar.selectbox("Select Candle Timeframe:", ["1d", "1h", "15m", "5m"], index=3) # Default 5m
rsi_period = st.sidebar.slider("RSI Length", min_value=5, max_value=25, value=14)

# --- TECHNICAL ANALYSIS MATHEMATICS ENGINE ---
def run_indicator_engine(symbol, timeframe, rsi_len):
    try:
        # Pull trailing 60 days historical data matching input params
        df = yf.download(tickers=symbol, period="60d", interval=timeframe, progress=False)
        if df.empty:
            return pd.DataFrame()
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        analysis_df = df.copy()
        
        # RSI Engine Formula
        change = analysis_df['Close'].diff()
        gain = (change.where(change > 0, 0)).rolling(window=rsi_len).mean()
        loss = (-change.where(change < 0, 0)).rolling(window=rsi_len).mean()
        rs = gain / (loss + 1e-10)
        analysis_df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD Engine Architecture
        analysis_df['EMA12'] = analysis_df['Close'].ewm(span=12, adjust=False).mean()
        analysis_df['EMA26'] = analysis_df['Close'].ewm(span=26, adjust=False).mean()
        analysis_df['MACD'] = analysis_df['EMA12'] - analysis_df['EMA26']
        analysis_df['Signal_Line'] = analysis_df['MACD'].ewm(span=9, adjust=False).mean()
        
        return analysis_df
    except Exception as e:
        return pd.DataFrame()

# Execute calculations
with st.spinner(f"Fetching real-time streams for {ticker}..."):
    data_matrix = run_indicator_engine(ticker, interval_choice, rsi_period)

if not data_matrix.empty:
    latest_bar = data_matrix.iloc[-1]
    prev_bar = data_matrix.iloc[-2]
    
    live_ltp = float(latest_bar['Close'])
    rsi_val = float(latest_bar['RSI'])
    macd_val = float(latest_bar['MACD'])
    sig_val = float(latest_bar['Signal_Line'])
    
    # --- LIVE DISPLAY METRICS ---
    c1, c2, c3 = st.columns(3)
    c1.metric(label=f"Current Market Price ({ticker})", value=f"₹{live_ltp:,.2f}")
    c2.metric(label=f"Live RSI ({rsi_period})", value=f"{rsi_val:.2f}")
    c3.metric(label="MACD Momentum Spread", value=f"{(macd_val - sig_val):.3f}")
    
    # --- LOGIC VERDICT (RSI + MACD CROSSOVER) ---
    st.subheader("🚨 Real-Time Execution Signal")
    
    trade_status = "NEUTRAL HOLD ⚪"
    logic_explanation = "The stock is currently trading within a stable baseline consolidation zone."
    
    if rsi_val <= 30 or (prev_bar['MACD'] < prev_bar['Signal_Line'] and macd_val > sig_val):
        trade_status = "BUY SIGNAL TRIGGERED 🟢"
        logic_explanation = f"Technical confluence reached. RSI is at {rsi_val:.1f} (Oversold Zone) or a structural Bullish MACD Crossover has occurred."
        
    elif rsi_val >= 70 or (prev_bar['MACD'] > prev_bar['Signal_Line'] and macd_val < sig_val):
        trade_status = "SELL / TAKE PROFIT TRIGGERED 🔴"
        logic_explanation = f"Resistance detected. RSI is at {rsi_val:.1f} (Overbought Zone) or a structural Bearish MACD Crossover has completed."
        
    st.info(f"**Engine Verdict:** {trade_status}")
    st.markdown(f"🔬 **Mathematical Justification:** {logic_explanation}")
    
    # --- HISTORICAL GRID ---
    st.subheader("📊 Engine Historical Log View")
    st.dataframe(data_matrix[['Open', 'High', 'Low', 'Close', 'RSI', 'MACD', 'Signal_Line']].tail(10))

else:
    st.error(f"⚠️ Stock Engine Offline for '{raw_symbol}'. Please verify if the NSE ticker symbol is typed correctly (e.g., ACC, INFY, 3MINDIA).")
