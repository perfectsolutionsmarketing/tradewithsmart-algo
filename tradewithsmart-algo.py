import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_ta as ta  # For fast indicator mathematics

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TradeWithSmart - Unified Algo Engine", layout="wide", page_icon="📈")

# Custom CSS for Premium Trading View UI - Text color issue fixed
st.markdown("""
    <style>
    /* Fixed Dark Metrics Text Color issue highlighted in image_16.png */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: white !important;
    }
    .stMetric {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    div[data-testid="stNotification"] {
        padding: 20px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 TradeWithSmart - Pro Unified Algo Engine")
st.caption("Central Matrix with dynamic parameters & execution signal stream")

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("⚙️ Trading Strategy Parameters")

st.sidebar.markdown("### 🔍 Stock Asset Selection")
popular_stocks = ["SUZLON", "DBL", "OIL", "RVNL", "ADANIENT", "TATAMOTORS", "RELIANCE", "SBIN", "INFY", "ITC"]
selected_option = st.sidebar.selectbox("Quick Pick Master Stocks:", options=popular_stocks, index=1)
custom_ticker = st.sidebar.text_input("Or Type Custom NSE Ticker:", value=selected_option)

# Format Ticker
raw_symbol = custom_ticker.strip().upper()
ticker = f"{raw_symbol}.NS" if raw_symbol else "DBL.NS"

# Timeframe Selector (Optimized for Scalping)
st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Chart Timeframe")
interval_choice = st.sidebar.selectbox("Select Candle Timeframe:", ["1d", "1h", "15m", "5m"], index=3)

# 1. NEW COMPACT DROPDOWN CONTAINERS FOR INDICATORS requested in image_17.png
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Advanced Indicator Suite")

with st.sidebar.expander("📊 1. RSI Rules (Dropdown for image_17.png)", expanded=True):
    rsi_period = st.slider("RSI Length", min_value=5, max_value=25, value=14)
    rsi_oversold = st.slider("Oversold (Buy)", min_value=10, max_value=40, value=30)
    rsi_overbought = st.slider("Overbought (Sell)", min_value=60, max_value=90, value=70)

with st.sidebar.expander("📊 2. MACD Parameters"):
    macd_fast = st.number_input("Fast EMA", value=12)
    macd_slow = st.number_input("Slow EMA", value=26)
    macd_signal = st.number_input("Smoothing", value=9)

with st.sidebar.expander("📊 3. EMA Overlay Lines (on Chart)"):
    ema_fast_len = st.number_input("Fast (EMA 9)", value=9)
    ema_slow_len = st.number_input("Slow (EMA 21)", value=21)

with st.sidebar.expander("📊 4. NEW: Bollinger Bands Overlay (on Chart)"):
    bb_period = st.number_input("BB Period", value=20)
    bb_std_dev = st.number_input("BB Std Dev", value=2.0)

with st.sidebar.expander("📊 5. NEW: Moving Average Overlay (on Chart)"):
    sma_period = st.number_input("SMA 1 Length", value=50)
    sma_period_2 = st.number_input("SMA 2 Length", value=200)

# --- TECHNICAL MATHEMATICS ENGINE WITH CHART OVERLAYS ---
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
        analysis_df.ta.rsi(length=rsi_period, append=True)
        analysis_df.rename(columns={f'RSI_{rsi_period}': 'RSI'}, inplace=True)
        
        # Math 2: MACD Calculation
        analysis_df.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True)
        analysis_df.rename(columns={f'MACD_{macd_fast}_{macd_slow}_{macd_signal}': 'MACD', f'MACDs_{macd_fast}_{macd_slow}_{macd_signal}': 'Signal_Line'}, inplace=True)
        
        # Math 3: EMA Overlays requested in image_17.png
        analysis_df.ta.ema(length=ema_fast_len, append=True)
        analysis_df.rename(columns={f'EMA_{ema_fast_len}': 'EMA_9'}, inplace=True)
        analysis_df.ta.ema(length=ema_slow_len, append=True)
        analysis_df.rename(columns={f'EMA_{ema_slow_len}': 'EMA_21'}, inplace=True)

        # NEW Math 4: Bollinger Bands for Chart Overlay requested in image_17.png
        analysis_df.ta.bbands(length=bb_period, std=bb_std_dev, append=True)
        analysis_df.rename(columns={f'BBL_{bb_period}_{bb_std_dev}': 'BB_Lower', f'BBM_{bb_period}_{bb_std_dev}': 'BB_Middle', f'BBU_{bb_period}_{bb_std_dev}': 'BB_Upper'}, inplace=True)

        # NEW Math 5: SMA for Chart Overlay requested in image_17.png
        analysis_df.ta.sma(length=sma_period, append=True)
        analysis_df.rename(columns={f'SMA_{sma_period}': 'SMA_1'}, inplace=True)
        analysis_df.ta.sma(length=sma_period_2, append=True)
        analysis_df.rename(columns={f'SMA_{sma_period_2}': 'SMA_2'}, inplace=True)
        
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
    bb_lower = float(latest_bar['BB_Lower'])
    bb_upper = float(latest_bar['BB_Upper'])
    
    # --- PRO LIVE DASHBOARD METRICS - TEXT COLOR ISSUES FIXED for image_16.png ---
    st.markdown("### 🔄 Unified Signal Stream Matrix")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label=f"🔄 LTP ({ticker})", value=f"₹{live_ltp:,.2f}")
    col2.metric(label=f"📊 RSI ({rsi_period})", value=f"{rsi_val:.2f}")
    col3.metric(label="📉 MACD Histogram", value=f"{(macd_val - sig_val):.3f}")
    col4.metric(label="Trend EMA (9 vs 21)", value=f"₹{ema9_val:.1f} / ₹{ema21_val:.1f}")
    
    # --- AUTOMATIC HIGHLIGHT BUTTON LOGIC ---
    st.markdown("---")
    st.subheader("🚨 Real-Time Execution Signal")
    
    # Strategy Rules Confluence
    is_rsi_buy = rsi_val <= rsi_oversold
    is_macd_buy = (prev_bar['MACD'] < prev_bar['Signal_Line'] and macd_val > sig_val)
    is_ema_buy = (prev_bar['EMA_9'] < prev_bar['EMA_21'] and ema9_val > ema21_val)
    is_bb_buy = live_ltp <= bb_lower # Buying at BB lower band
    
    is_rsi_sell = rsi_val >= rsi_overbought
    is_macd_sell = (prev_bar['MACD'] > prev_bar['Signal_Line'] and macd_val < sig_val)
    is_ema_sell = (prev_bar['EMA_9'] > prev_bar['EMA_21'] and ema9_val < ema21_val)
    is_bb_sell = live_ltp >= bb_upper # Selling at BB upper band
    
    if is_rsi_buy or is_macd_buy or is_ema_buy or is_bb_buy:
        st.success(f"### 🟢 HIGHLIGHT SIGNAL: BUY TRIGGERED ({interval_choice} Timeframe)")
        reasons = []
        if is_rsi_buy: reasons.append(f"RSI Oversold ({rsi_val:.1f})")
        if is_macd_buy: reasons.append("Bullish MACD Line Crossover")
        if is_ema_buy: reasons.append("Golden Cross (EMA 9 > 21)")
        if is_bb_buy: reasons.append("Below BB Lower Band")
        st.markdown("**📌 BUY Justification:** " + " + ".join(reasons))
        
    elif is_rsi_sell or is_macd_sell or is_ema_sell or is_bb_sell:
        st.error(f"### 🔴 HIGHLIGHT SIGNAL: SELL / TAKE PROFIT TRIGGERED ({interval_choice} Timeframe)")
        reasons = []
        if is_rsi_sell: reasons.append(f"RSI Overbought ({rsi_val:.1f})")
        if is_macd_sell: reasons.append("Bearish MACD Line Crossover")
        if is_ema_sell: reasons.append(" EMA Breakdown (9 < 21)")
        if is_bb_sell: reasons.append("Above BB Upper Band")
        st.markdown("**📌 SELL Justification:** " + " + ".join(reasons))
        
    else:
        st.info(f"### ⚪ HIGHLIGHT SIGNAL: NEUTRAL HOLD (No Breakout Detected)")
        st.markdown("**📌 HOLD Justification:** Key indicator confluences have not completed a structural crossover.")

    # --- NEW: ADVANCED CANDLESTICK CHART OVERLAY requested in image_17.png ---
    st.markdown("---")
    st.subheader("📉 Complete Unified Chart (Overlays & Momentum View)")
    
    # Filter trailing data for the unified view
    unified_df = data_matrix.tail(100) # Last 100 candles
    
    # Create interactive Trading View style plot with Subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
    
    # Trace 1: Professional Candlestick chart
    fig.add_trace(go.Candlestick(
        x=unified_df.index,
        open=unified_df['Open'],
        high=unified_df['High'],
        low=unified_df['Low'],
        close=unified_df['Close'],
        name="Price Action",
        increasing_line_color='#26a69a', # Teal Green
        decreasing_line_color='#ef5350' # Pro Red
    ), row=1, col=1)
    
    # NEW Chart Overlays requested in image_17.png
    # 1. EMA Overlays
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['EMA_9'], mode='lines', line=dict(color='#ff9800', width=1.5), name='EMA 9'), row=1, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['EMA_21'], mode='lines', line=dict(color='#f44336', width=1.5), name='EMA 21'), row=1, col=1)
    
    # 2. Bollinger Bands Overlays
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['BB_Upper'], mode='lines', line=dict(color='#607d8b', width=1.5, dash='dash'), name='BB Upper'), row=1, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['BB_Lower'], mode='lines', line=dict(color='#607d8b', width=1.5, dash='dash'), name='BB Lower'), row=1, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['BB_Upper'], mode='lines', line=dict(color='rgba(0,0,0,0)'), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name='BB Band', showlegend=False), row=1, col=1)

    # 3. SMA Overlays
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['SMA_1'], mode='lines', line=dict(color='#3f51b5', width=1), name=f'SMA {sma_period}'), row=1, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['SMA_2'], mode='lines', line=dict(color='#9c27b0', width=1), name=f'SMA {sma_period_2}'), row=1, col=1)
    
    # Row 2: Momentum View
    # Trace 2: MACD Indicator
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['MACD'], line=dict(color='#2196f3', width=1.5), name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['Signal_Line'], line=dict(color='#ff5722', width=1.5), name='MACD Signal'), row=2, col=1)
    macd_hist_colors = ['rgba(0,255,0,0.4)' if val > 0 else 'rgba(255,0,0,0.4)' for val in unified_df['MACD'] - unified_df['Signal_Line']]
    fig.add_trace(go.Bar(x=unified_df.index, y=unified_df['MACD'] - unified_df['Signal_Line'], name='MACD Hist', marker_color=macd_hist_colors), row=2, col=1)

    # Unified Layout Styling
    fig.update_layout(
        title=f"{raw_symbol} ({interval_choice}) Pro Unified Chart",
        yaxis_title="Price (₹)",
        xaxis_rangeslider_visible=False,
        height=750,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_dark'  # Keeps UI premium with dark charts
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="MACD Spread", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

    # --- HISTORICAL VERIFICATION GRID ---
    st.markdown("---")
    st.subheader("📊 Engine Master Log View (Last 10 Candles)")
    st.dataframe(data_matrix[['Open', 'High', 'Low', 'Close', 'RSI', 'MACD', 'Signal_Line', 'EMA_9', 'EMA_21', 'BB_Upper', 'BB_Lower', 'SMA_1', 'SMA_2']].tail(10))

else:
    st.error(f"⚠️ Stock Engine Offline for '{ticker}'. Verify formatting parameters.")
