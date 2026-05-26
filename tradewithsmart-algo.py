import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_ta as ta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TradeWithSmart - Unified Algo Engine", layout="wide", page_icon="📈")

# Custom CSS for Premium UI / Fix dark metrics text color issues requested in image_20.png
st.markdown("""
    <style>
    /* Fixed White metrics cards with black text for image_20.png */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: black !important;
    }
    .stMetric {
        background-color: white;  /* Dark mode removed requested in image_20.png */
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        border: 1px solid #ddd;
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
st.caption("Central Matrix linked with dynamic parameters & auto-execution signals")

# --- SMART GOOGLE SHEETS PIPELINE ---
SHEET_ID = "1gkeak0btfUWZW2-6UkpWG4D6R20tCNyuGOh0YE3uGdM"

@st.cache_data(ttl=60)
def fetch_symbols_from_sheet():
    try:
        # Directly target 'List' tab (gid=0)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
        df = pd.read_csv(url)
        
        # Clean column spaces and force string matching
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
        if 'SYMBOL' not in df.columns:
            # Shift headers down by 1 row dynamically
            df.columns = df.iloc[0].astype(str).str.strip().str.upper()
            df = df[1:]
            
        # Clearing empty rows
        if 'SYMBOL' in df.columns:
            # Drop null values and clean up rows
            df = df.dropna(subset=['SYMBOL'])
            df = df[df['SYMBOL'].astype(str).str.strip() != '']
            df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip().str.upper()
            
            # Match Company Name column
            name_col = 'COMPANY NAME'
            if name_col not in df.columns:
                for col in df.columns:
                    if 'NAME' in str(col):
                        name_col = col
                        break
            
            df[name_col] = df[name_col].fillna('Nifty Component').astype(str).str.strip()
            return pd.DataFrame({'SYMBOL': df['SYMBOL'].values, 'Company Name': df[name_col].values})
            
    except Exception as e:
        st.sidebar.warning(f"Connection Notice: {str(e)}")
        
    # hardcoded baseline for failsafe
    return pd.DataFrame({'SYMBOL': ['SUZLON', 'DBL', 'OIL', 'RVNL'], 'Company Name': ['Suzlon Energy', 'Dilip Buildcon', 'Oil India', 'RVNL']})

master_stock_df = fetch_symbols_from_sheet()

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("⚙️ Trading Parameters")

# Creating dropdown strings: "SYMBOL - Company Name"
master_stock_df['Dropdown_Display'] = master_stock_df['SYMBOL'].astype(str) + " - " + master_stock_df['Company Name'].astype(str)
stock_options = sorted(master_stock_df['Dropdown_Display'].unique().tolist())

# Dynamic Ticker Selector with Text Input option
st.sidebar.markdown("### 🔍 Select or Type NSE Ticker")
selected_stock = st.sidebar.selectbox(
    "Quick Pick Master Stocks:",
    stock_options,
    index=0
)

# Extract raw symbol for yfinance parsing
raw_symbol = master_stock_df[master_stock_df['Dropdown_Display'] == selected_stock]['SYMBOL'].values[0]
ticker = f"{raw_symbol}.NS"

# Technical Configurations
st.sidebar.markdown("---")
st.sidebar.subheader("⏱️ Chart Timeframe")
interval_choice = st.sidebar.selectbox("Select Candle Timeframe:", ["1d", "1h", "15m", "5m"], index=3) # 5m default

# 1. Compact Dropdown Expanders for Indicator Parameters
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Advanced Indicator Suite")

with st.sidebar.expander("RSI Parameters", expanded=True):
    rsi_period = st.slider("RSI Length", min_value=5, max_value=25, value=14)
    rsi_oversold = st.slider("Oversold (Buy)", min_value=10, max_value=40, value=30)
    rsi_overbought = st.slider("Overbought (Sell)", min_value=60, max_value=90, value=70)

with st.sidebar.expander("MACD & EMA Strategy"):
    macd_fast = st.number_input("Fast EMA Length", value=12)
    macd_slow = st.number_input("Slow EMA Length", value=26)
    macd_signal = st.number_input("Signal Smoothing", value=9)
    st.markdown("---")
    ema_fast_len = st.number_input("Fast Trend (EMA 9)", value=9)
    ema_slow_len = st.number_input("Slow Trend (EMA 21)", value=21)

with st.sidebar.expander("BB & SMA Overlays"):
    bb_period = st.number_input("BB Period", value=20)
    bb_std_dev = st.number_input("BB Std Dev", value=2.0)
    st.markdown("---")
    sma_period = st.number_input("SMA 1 Length", value=50)
    sma_period_2 = st.number_input("SMA 2 Length", value=200)

# --- TECHNICAL ANALYSIS MATHEMATICS ENGINE ---
def run_indicator_engine(symbol, timeframe, rsi_len):
    df = yf.download(tickers=symbol, period="60d", interval=timeframe)
    if df.empty:
        return pd.DataFrame()
        
    if isinstance(df.columns, pd.MultiIndex):
        # Flattening multi-level columns caused by text input tickers in image_20.png
        df.columns = df.columns.get_level_values(0)
    
    analysis_df = df.copy()
    
    # RSI Calculation
    analysis_df.ta.rsi(length=rsi_len, append=True)
    analysis_df.rename(columns={f'RSI_{rsi_len}': 'RSI'}, inplace=True)
    
    # MACD Calculation
    analysis_df.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True)
    analysis_df.rename(columns={f'MACD_{macd_fast}_{macd_slow}_{macd_signal}': 'MACD', f'MACDs_{macd_fast}_{macd_slow}_{macd_signal}': 'Signal_Line'}, inplace=True)
    
    # EMA Trend Indicators requested in image_17.png
    analysis_df.ta.ema(length=ema_fast_len, append=True)
    analysis_df.rename(columns={f'EMA_{ema_fast_len}': 'EMA_9'}, inplace=True)
    analysis_df.ta.ema(length=ema_slow_len, append=True)
    analysis_df.rename(columns={f'EMA_{ema_slow_len}': 'EMA_21'}, inplace=True)

    # Bollinger Bands for Chart Overlay requested in image_17.png
    analysis_df.ta.bbands(length=bb_period, std=bb_std_dev, append=True)
    analysis_df.rename(columns={f'BBL_{bb_period}_{bb_std_dev}': 'BB_Lower', f'BBM_{bb_period}_{bb_std_dev}': 'BB_Middle', f'BBU_{bb_period}_{bb_std_dev}': 'BB_Upper'}, inplace=True)

    # SMA Overlays requested in image_17.png
    analysis_df.ta.sma(length=sma_period, append=True)
    analysis_df.rename(columns={f'SMA_{sma_period}': 'SMA_1'}, inplace=True)
    analysis_df.ta.sma(length=sma_period_2, append=True)
    analysis_df.rename(columns={f'SMA_{sma_period_2}': 'SMA_2'}, inplace=True)
    
    return analysis_df

# Execute calculations
data_matrix = run_indicator_engine(ticker, interval_choice, rsi_period)

if not data_matrix.empty:
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
    
    # --- FIXED PRO Metric Cards displaying in White requested in image_20.png ---
    st.markdown("### 🔄 Active Multi-Signal parameters")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label=f"🔄 LTP ({ticker})", value=f"₹{live_ltp:,.2f}")
    col2.metric(label=f"📊 RSI ({rsi_period})", value=f"{rsi_val:.2f}")
    col3.metric(label="📉 MACD Histogram", value=f"{(macd_val - sig_val):.3f}")
    col4.metric(label="Trend EMA (9 vs 21)", value=f"₹{ema9_val:.1f} / ₹{ema21_val:.1f}")
    
    # --- ALGORITHMIC TRIGGER SIGNAL ---
    st.markdown("---")
    st.subheader("🚨 Real-Time Scalping Execution Signal")
    
    trade_status = "NEUTRAL HOLD ⚪"
    
    # Strategy Rules Confluence
    is_rsi_buy = rsi_val <= rsi_oversold
    is_macd_buy = (prev_bar['MACD'] < prev_bar['Signal_Line'] and macd_val > sig_val)
    is_ema_buy = (prev_bar['EMA_9'] < prev_bar['EMA_21'] and ema9_val > ema21_val)
    is_bb_buy = live_ltp <= bb_lower
    
    is_rsi_sell = rsi_val >= rsi_overbought
    is_macd_sell = (prev_bar['MACD'] > prev_bar['Signal_Line'] and macd_val < sig_val)
    is_ema_sell = (prev_bar['EMA_9'] > prev_bar['EMA_21'] and ema9_val < ema21_val)
    is_bb_sell = live_ltp >= bb_upper
    
    if is_rsi_buy or is_macd_buy or is_ema_buy or is_bb_buy:
        trade_status = "BUY SIGNAL TRIGGERED 🟢"
        st.success(f"### Engine Verdict: {trade_status}")
        reasons = []
        if is_rsi_buy: reasons.append(f"RSI Oversold ({rsi_val:.1f})")
        if is_macd_buy: reasons.append("Bullish MACD Line Crossover")
        if is_ema_buy: reasons.append("Fast EMA Golden Cross (EMA 9 > 21)")
        if is_bb_buy: reasons.append("Ticker trading near Bollinger Band Bottom")
        st.markdown("**📌 BUY Justification Confluence:** " + " + ".join(reasons))
        
    elif is_rsi_sell or is_macd_sell or is_ema_sell or is_bb_sell:
        trade_status = "SELL / TAKE PROFIT TRIGGERED 🔴"
        st.error(f"### Engine Verdict: {trade_status}")
        reasons = []
        if is_rsi_sell: reasons.append(f"RSI Overbought ({rsi_val:.1f})")
        if is_macd_sell: reasons.append("Bearish MACD Line Crossover")
        if is_ema_sell: reasons.append(" EMA Breakdown (9 < 21)")
        if is_bb_sell: reasons.append("Ticker trading near Bollinger Band Top")
        st.markdown("**📌 SELL Justification Confluence:** " + " + ".join(reasons))
        
    else:
        st.info(f"### Engine Verdict: {trade_status}")
        st.markdown("**📌 Justification:** The asset parameters have not completed a significant structural breakout from neutral zones.")

    # --- ADVANCED UNIFIED CHART OVERLAYrequested in image_17.png ---
    st.markdown("---")
    st.subheader("📉 Advanced Unified Chart (Overlays & Momentum View)")
    
    # Filter trailing view (last 100 candles to avoid layout clutter)
    unified_df = data_matrix.tail(100)
    
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
    
    # Trace Overlays requested in image_17.png
    # 1. EMA Overlays
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['EMA_9'], mode='lines', line=dict(color='#ff9800', width=1.5), name='EMA 9'), row=1, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['EMA_21'], mode='lines', line=dict(color='#f44336', width=1.5), name='EMA 21'), row=1, col=1)
    
    # 2. Bollinger Bands Overlays
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['BB_Upper'], mode='lines', line=dict(color='#607d8b', width=1.5, dash='dash'), name='BB Upper'), row=1, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['BB_Lower'], mode='lines', line=dict(color='#607d8b', width=1.5, dash='dash'), name='BB Lower'), row=1, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['BB_Upper'], mode='lines', line=dict(color='rgba(0,0,0,0)'), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name='BB Band', showlegend=False), row=1, col=1)

    # SMA Overlays
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['SMA_1'], mode='lines', line=dict(color='#3f51b5', width=1), name=f'SMA {sma_period}'), row=1, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['SMA_2'], mode='lines', line=dict(color='#9c27b0', width=1), name=f'SMA {sma_period_2}'), row=1, col=1)
    
    # Row 2: Momentum View
    # Trace 2: MACD Indicator
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['MACD'], line=dict(color='#2196f3', width=1.5), name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=unified_df.index, y=unified_df['Signal_Line'], line=dict(color='#ff5722', width=1.5), name='MACD Signal'), row=2, col=1)
    # Histogram colors based on momentum
    macd_hist_colors = ['rgba(0,255,0,0.4)' if val > 0 else 'rgba(255,0,0,0.4)' for val in unified_df['MACD'] - unified_df['Signal_Line']]
    fig.add_trace(go.Bar(x=unified_df.index, y=unified_df['MACD'] - unified_df['Signal_Line'], name='MACD Hist', marker_color=macd_hist_colors), row=2, col=1)

    # Chart Styling
    fig.update_layout(
        title=f"{selected_stock} ({interval_choice}) Live Technical Streams",
        yaxis_title="Stock Price (₹)",
        xaxis_rangeslider_visible=False,
        height=750,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_dark' # Pro trading theme
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="MACD Spread", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

    # --- HISTORICAL VERIFICATION GRID ---
    st.markdown("---")
    st.subheader("📊 Engine Master Log View (Last 10 Candles)")
    # Headers causing clutter in image_20.png cleaned dynamically requested in image_20.png
    historical_log = data_matrix[['Open', 'High', 'Low', 'Close', 'RSI', 'MACD', 'Signal_Line', 'EMA_9', 'EMA_21', 'BB_Upper', 'BB_Lower', 'SMA_1', 'SMA_2']].tail(10)
    st.dataframe(historical_log)

else:
    st.error(f"⚠️ Stock Engine Offline for '{ticker}'. Verify formatting parameters.")
