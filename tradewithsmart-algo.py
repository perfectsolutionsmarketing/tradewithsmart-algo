import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TradeWithSmart - Algo Engine", layout="wide", page_icon="📈")

# Custom CSS for Premium Trading View UI
st.markdown("""
    <style>
    .stMetric {
        background-color: #1e293b;
        padding: 12px;
        border-radius: 8px;
        color: white;
    }
    div[data-testid="stNotification"] {
        border-radius: 10px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 TradeWithSmart - Pro Indian Stock Algo Engine")
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
            
        # Clear DataFrame structure
        if 'SYMBOL' in df.columns:
            # Drop null values and clean up rows
            df = df.dropna(subset=['SYMBOL'])
            df = df[df['SYMBOL'].astype(str).str.strip() != '']
            df['SYMBOL'] = df['SYMBOL'].astype(str).str.strip().str.upper()
            
            # Match Company Name
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
        
    return pd.DataFrame({'SYMBOL': ['SUZLON', 'DBL', 'OIL', 'RVNL'], 'Company Name': ['Suzlon Energy', 'Dilip Buildcon', 'Oil India', 'RVNL']})

master_stock_df = fetch_symbols_from_sheet()

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("⚙️ Trading Parameters")

# Creating dropdown strings: "SYMBOL - Company Name"
master_stock_df['Dropdown_Display'] = master_stock_df['SYMBOL'].astype(str) + " - " + master_stock_df['Company Name'].astype(str)
stock_options = sorted(master_stock_df['Dropdown_Display'].unique().tolist())

# Dynamic Ticker Selector
selected_stock = st.sidebar.selectbox(
    "Select Target NSE Stock (Nifty Universe):",
    stock_options,
    index=0
)

raw_symbol = master_stock_df[master_stock_df['Dropdown_Display'] == selected_stock]['SYMBOL'].values[0]
ticker = f"{raw_symbol}.NS"

# Technical Configurations
st.sidebar.markdown("---")
st.sidebar.subheader("⏱️ Chart Timeframe")
interval_choice = st.sidebar.selectbox("Select Candle Timeframe:", ["1d", "1h", "15m", "5m"], index=3) # 5m default

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Indicator Rules")
rsi_period = st.sidebar.slider("RSI Length", min_value=5, max_value=25, value=14)
st.sidebar.caption("Trend Strategy: Buy if RSI<30 or Bullish MACD Crossover")

# --- TECHNICAL ANALYSIS MATHEMATICS ---
def run_indicator_engine(symbol, timeframe, rsi_len):
    df = yf.download(tickers=symbol, period="60d", interval=timeframe)
    if df.empty:
        return pd.DataFrame()
        
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    analysis_df = df.copy()
    
    # RSI Engine
    change = analysis_df['Close'].diff()
    gain = (change.where(change > 0, 0)).rolling(window=rsi_len).mean()
    loss = (-change.where(change < 0, 0)).rolling(window=rsi_len).mean()
    rs = gain / (loss + 1e-10)
    analysis_df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD Trend Engine
    analysis_df['EMA12'] = analysis_df['Close'].ewm(span=12, adjust=False).mean()
    analysis_df['EMA26'] = analysis_df['Close'].ewm(span=26, adjust=False).mean()
    analysis_df['MACD'] = analysis_df['EMA12'] - analysis_df['EMA26']
    analysis_df['Signal_Line'] = analysis_df['MACD'].ewm(span=9, adjust=False).mean()
    
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
    
    # --- PRO LIVE DISPLAY METRICS ---
    st.markdown("### 🔄 Active Multi-Signal parameters")
    c1, c2, c3 = st.columns(3)
    c1.metric(label=f"Current Market Price ({ticker})", value=f"₹{live_ltp:,.2f}")
    c2.metric(label=f"Calculated RSI ({rsi_period})", value=f"{rsi_val:.2f}")
    c3.metric(label="MACD Spread (vs Signal)", value=f"{(macd_val - sig_val):.3f}")
    
    # --- ALGORITHMIC TRIGGER SIGNAL ---
    st.markdown("---")
    st.subheader("🚨 Real-Time Execution Signal")
    
    trade_status = "NEUTRAL HOLD ⚪"
    
    # Strategy Rules Confluence
    if rsi_val <= 30 or (prev_bar['MACD'] < prev_bar['Signal_Line'] and macd_val > sig_val):
        trade_status = "BUY SIGNAL TRIGGERED 🟢"
        st.success(f"### Engine Verdict: {trade_status}")
    
    elif rsi_val >= 70 or (prev_bar['MACD'] > prev_bar['Signal_Line'] and macd_val < sig_val):
        trade_status = "SELL / TAKE PROFIT TRIGGERED 🔴"
        st.error(f"### Engine Verdict: {trade_status}")
        
    else:
        st.info(f"### Engine Verdict: {trade_status}")

    # --- NEW: INTERACTIVE CANDLESTICK CHART SETUP ---
    st.markdown("---")
    st.subheader("📉 Advanced Charting View")
    
    # Prepare trailing view (last 60 candles to avoid layout clutter)
    chart_df = data_matrix.tail(60)
    
    # Create interactive Trading View style plot
    fig = go.Figure(data=[go.Candlestick(
        x=chart_df.index,
        open=chart_df['Open'],
        high=chart_df['High'],
        low=chart_df['Low'],
        close=chart_df['Close'],
        name="Price Action",
        increasing_line_color='#26a69a', # Teal for green candles
        decreasing_line_color='#ef5350' # Red for red candles
    )])
    
    # Chart Styling
    fig.update_layout(
        title=f"{selected_stock} ({interval_choice}) Live Streams",
        yaxis_title="Stock Price (₹)",
        xaxis_rangeslider_visible=False, # Hides the messy small slider
        height=600,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_dark' # Use dark template for better contrast
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # --- HISTORICAL VERIFICATION GRID ---
    st.markdown("---")
    st.subheader("📊 Engine Historical Log View (Last 10 Candles)")
    st.dataframe(data_matrix[['Open', 'High', 'Low', 'Close', 'RSI', 'MACD', 'Signal_Line']].tail(10))

else:
    st.error(f"⚠️ Stock Engine Offline for '{ticker}'. Verify formatting parameters.")
