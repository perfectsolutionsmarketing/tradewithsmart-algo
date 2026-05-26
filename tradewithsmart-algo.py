import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go  # Line 4: Added for Candlestick Chart

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TradeWithSmart - Pro Algo Matrix", layout="wide", page_icon="📈")

# Custom CSS for Premium UI / Fix dark metrics text color issues
st.markdown("""
    <style>
    /* Fixed White metrics cards with dark text for clear visibility */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #1e293b !important;
    }
    .stMetric {
        background-color: #ffffff;  /* Removed dark background, made it crisp white */
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    div[data-testid="stNotification"] {
        padding: 20px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 TradeWithSmart - Pro Algorithmic Engine")
st.caption("Multi-Indicator Strategy Matrix with Auto-Highlight Signals")

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("⚙️ Trading Strategy Parameters")

st.sidebar.markdown("### 🔍 Stock Asset Selection")
popular_stocks = ["SUZLON", "DBL", "OIL", "RVNL", "ADANIENT", "TATAMOTORS", "RELIANCE", "SBIN", "INFY", "ITC"]
selected_option = st.sidebar.selectbox("Quick Pick Master Stocks:", options=popular_stocks, index=1) # Default DBL
custom_ticker = st.sidebar.text_input("Or Type Custom NSE Ticker:", value=selected_option)

# Format Ticker
raw_symbol = custom_ticker.strip().upper()
ticker = f"{raw_symbol}.NS" if raw_symbol else "DBL.NS"

# Timeframe Selector (Optimized for Scalping)
st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Chart Timeframe")
interval_choice = st.sidebar.selectbox(
    "Select Candle Timeframe:", 
    ["1d", "1h", "15m", "5m"], 
    index=3  # Default 5 min for intra-day alerts
)

# 1. RSI Indicator Inputs
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 1. RSI Parameters")
rsi_period = st.sidebar.slider("RSI Length", min_value=5, max_value=25, value=14)
rsi_oversold = st.sidebar.slider("RSI Oversold Level (Buy)", min_value=10, max_value=40, value=30)
rsi_overbought = st.sidebar.slider("RSI Overbought Level (Sell)", min_value=60, max_value=90, value=70)

# 2. MACD Indicator Inputs
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 2. MACD Parameters")
macd_fast = st.sidebar.number_input("Fast EMA Length", value=12)
macd_slow = st.sidebar.number_input("Slow EMA Length", value=26)
macd_signal = st.sidebar.number_input("Signal Smoothing", value=9)

# 3. Moving Average Trend Inputs
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 3. Trend EMA Lines")
ema_fast_len = st.sidebar.number_input("Fast Trend (EMA 9)", value=9)
ema_slow_len = st.sidebar.number_input("Slow Trend (EMA 21)", value=21)


# --- TECHNICAL MATHEMATICS ENGINE ---
def calculate_signals(symbol, timeframe):
    try:
        # Download trailing 60 days structural matrix
        df = yf.download(tickers=symbol, period="60d", interval=timeframe, progress=False)
        if df.empty:
            return pd.DataFrame()
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        analysis_df = df.copy()
        
        # Math 1: RSI Calculation
        change = analysis_df['Close'].diff()
        gain = (change.where(change > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-change.where(change < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / (loss + 1e-10)
        analysis_df['RSI'] = 100 - (100 / (1 + rs))
        
        # Math 2: MACD Calculation
        analysis_df['EMA_Fast'] = analysis_df['Close'].ewm(span=macd_fast, adjust=False).mean()
        analysis_df['EMA_Slow'] = analysis_df['Close'].ewm(span=macd_slow, adjust=False).mean()
        analysis_df['MACD'] = analysis_df['EMA_Fast'] - analysis_df['EMA_Slow']
        analysis_df['Signal_Line'] = analysis_df['MACD'].ewm(span=macd_signal, adjust=False).mean()
        
        # Math 3: Moving Averages for Trend Confirmation
        analysis_df['EMA_9'] = analysis_df['Close'].ewm(span=ema_fast_len, adjust=False).mean()
        analysis_df['EMA_21'] = analysis_df['Close'].ewm(span=ema_slow_len, adjust=False).mean()
        
        return analysis_df
    except Exception as e:
        return pd.DataFrame()

# Execute Data Processing
with st.spinner(f"Analyzing multi-indicator streams for {ticker}..."):
    data_matrix = calculate_signals(ticker, interval_choice)

if not data_matrix.empty:
    # Get last 2 bars for crossover analysis
    latest_bar = data_matrix.iloc[-1]
    prev_bar = data_matrix.iloc[-2]
    
    live_ltp = float(latest_bar['Close'])
    rsi_val = float(latest_bar['RSI'])
    macd_val = float(latest_bar['MACD'])
    sig_val = float(latest_bar['Signal_Line'])
    ema9_val = float(latest_bar['EMA_9'])
    ema21_val = float(latest_bar['EMA_21'])
    
    # --- PRO LIVE DASHBOARD METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label=f"🔄 LTP ({ticker})", value=f"₹{live_ltp:,.2f}")
    col2.metric(label=f"📊 RSI ({rsi_period})", value=f"{rsi_val:.2f}")
    col3.metric(label="📉 MACD Histogram", value=f"{(macd_val - sig_val):.3f}")
    col4.metric(label="📈 Trend (EMA 9 vs 21)", value=f"₹{ema9_val:.1f} / ₹{ema21_val:.1f}")
    
    # --- AUTOMATIC HIGHLIGHT BUTTON LOGIC ---
    st.markdown("---")
    st.subheader("🚨 Real-Time Scalping Execution Signal")
    
    # Strategy Rules Confluence
    is_rsi_buy = rsi_val <= rsi_oversold
    is_macd_buy = (prev_bar['MACD'] < prev_bar['Signal_Line'] and macd_val > sig_val)
    is_ema_buy = (prev_bar['EMA_9'] < prev_bar['EMA_21'] and ema9_val > ema21_val)
    
    # SELL: RSI Overbought OR MACD Bearish Crossover OR EMA9 crosses below EMA21
    is_rsi_sell = rsi_val >= rsi_overbought
    is_macd_sell = (prev_bar['MACD'] > prev_bar['Signal_Line'] and macd_val < sig_val)
    is_ema_sell = (prev_bar['EMA_9'] > prev_bar['EMA_21'] and ema9_val < ema21_val)
    
    if is_rsi_buy or is_macd_buy or is_ema_buy:
        st.success(f"### 🟢 HIGHLIGHT SIGNAL: BUY TRIGGERED ({interval_choice} Timeframe)")
        explanation = "📌 **Reason for BUY:** "
        reasons = []
        if is_rsi_buy: reasons.append(f"RSI Oversold ({rsi_val:.1f})")
        if is_macd_buy: reasons.append("Bullish MACD Line Crossover")
        if is_ema_buy: reasons.append("Fast EMA Golden Cross (EMA 9 > 21)")
        st.markdown(explanation + " + ".join(reasons))
        
    elif is_rsi_sell or is_macd_sell or is_ema_sell:
        st.error(f"### 🔴 HIGHLIGHT SIGNAL: SELL / TAKE PROFIT TRIGGERED ({interval_choice} Timeframe)")
        explanation = "📌 **Reason for SELL:** "
        reasons = []
        if is_rsi_sell: reasons.append(f"RSI Overbought ({rsi_val:.1f})")
        if is_macd_sell: reasons.append("Bearish MACD Line Crossover")
        if is_ema_sell: reasons.append("Trend Breakdown (EMA 9 < 21)")
        st.markdown(explanation + " + ".join(reasons))
        
    else:
        st.info(f"### ⚪ HIGHLIGHT SIGNAL: NEUTRAL HOLD (No Active Crossover)")
        st.markdown("📌 **Reason for HOLD:** Indicators are in a neutral zone. Moving averages are running parallel without a breakout.")

    # --- NEW: INTERACTIVE CANDLESTICK CHART SETUP ---
    st.markdown("---")
    st.subheader("📉 Live Candlestick Stream (Price Action View)")
    
    # Filtering last 60 candles to avoid overlapping on UI
    chart_df = data_matrix.tail(60)
    
    fig = go.Figure(data=[go.Candlestick(
        x=chart_df.index,
        open=chart_df['Open'],
        high=chart_df['High'],
        low=chart_df['Low'],
        close=chart_df['Close'],
        name="Price Action",
        increasing_line_color='#26a69a',  # Teal Green
        decreasing_line_color='#ef5350'   # Pro Red
    )])
    
    fig.update_layout(
        title=f"{raw_symbol} ({interval_choice}) Live Technical View",
        yaxis_title="Price (₹)",
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_dark'  # Keeping UI premium with dark charts
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- HISTORICAL VERIFICATION GRID ---
    st.markdown("---")
    st.subheader("📊 Multi-Indicator Master Log View (Last 10 Candles)")
    st.dataframe(data_matrix[['Open', 'High', 'Low', 'Close', 'RSI', 'MACD', 'Signal_Line', 'EMA_9', 'EMA_21']].tail(10))

else:
    st.error(f"⚠️ Error opening data stream for '{raw_symbol}'. Please input a valid stock code.")
