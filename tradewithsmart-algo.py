import streamlit as st
import yfinance as yf
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="TradeWithSmart - Algo Engine", layout="wide", page_icon="📈")

st.title("📈 TradeWithSmart - Indian Stock Algo Engine")
st.caption("Advanced Screener Matrix Linked with Master Sheet Engine")

# --- SMART GOOGLE SHEETS PIPELINE ---
SHEET_ID = "1gkeak0btfUWZW2-6UkpWG4D6R20tCNyuGOh0YE3uGdM"

@st.cache_data(ttl=600)  # 10 minutes cache to keep layout fast and responsive
def fetch_symbols_from_sheet():
    try:
        # Fetching directly from the Nifty 50 tab where core matrix is maintained
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=657405355"
        df = pd.read_csv(url)
        
        # Clean data: Select only rows where SYMBOL is valid and not empty
        df = df.dropna(subset=['SYMBOL']).reset_index(drop=True)
        return df[['SYMBOL', 'Company Name']]
    except Exception as e:
        # High reliability fallback in case of connection latency
        return pd.DataFrame({
            'SYMBOL': ['SUZLON', 'DBL', 'OIL', 'RVNL'],
            'Company Name': ['Suzlon Energy Ltd', 'Dilip Buildcon Ltd', 'Oil India Ltd', 'Rail Vikas Nigam Ltd']
        })

# Load the verified database
master_stock_df = fetch_symbols_from_sheet()

# --- SIDEBAR STRATEGY CONTROL PANEL ---
st.sidebar.header("⚙️ Strategy Parameters")

# Create a clean display string for dropdown: "SYMBOL - Company Name"
master_stock_df['Dropdown_Display'] = master_stock_df['SYMBOL'].astype(str) + " - " + master_stock_df['Company Name'].fillna('').astype(str)

selected_stock = st.sidebar.selectbox(
    "Select Target Stock (from Nifty 500 Matrix):",
    master_stock_df['Dropdown_Display'].tolist(),
    index=0
)

# Extract raw symbol for Yahoo Finance mapping
raw_symbol = master_stock_df[master_stock_df['Dropdown_Display'] == selected_stock]['SYMBOL'].values[0]
ticker = f"{str(raw_symbol).strip()}.NS"

# Technical Inputs
st.sidebar.markdown("---")
interval_choice = st.sidebar.selectbox("Select Candle Timeframe:", ["1d", "1h", "15m", "5m"], index=0)
rsi_period = st.sidebar.slider("RSI Length", min_value=5, max_value=25, value=14)

# --- TECHNICAL ANALYSIS MATHEMATICS ---
def run_indicator_engine(symbol, timeframe, rsi_len):
    # Pull trailing 60 days historical data for accurate calculation rolling windows
    df = yf.download(tickers=symbol, period="60d", interval=timeframe)
    if df.empty:
        return pd.DataFrame()
        
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    analysis_df = df.copy()
    
    # 1. RSI Formula implementation
    change = analysis_df['Close'].diff()
    gain = (change.where(change > 0, 0)).rolling(window=rsi_len).mean()
    loss = (-change.where(change < 0, 0)).rolling(window=rsi_len).mean()
    rs = gain / (loss + 1e-10)
    analysis_df['RSI'] = 100 - (100 / (1 + rs))
    
    # 2. MACD Trend Engine
    analysis_df['EMA12'] = analysis_df['Close'].ewm(span=12, adjust=False).mean()
    analysis_df['EMA26'] = analysis_df['Close'].ewm(span=26, adjust=False).mean()
    analysis_df['MACD'] = analysis_df['EMA12'] - analysis_df['EMA26']
    analysis_df['Signal_Line'] = analysis_df['MACD'].ewm(span=9, adjust=False).mean()
    
    return analysis_df

# Run calculations
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
    c2.metric(label="Live RSI (14)", value=f"{rsi_val:.2f}")
    c3.metric(label="MACD Momentum Spread", value=f"{(macd_val - sig_val):.3f}")
    
    # --- LOGIC VERDICT (RSI + MACD CROSSOVER) ---
    st.subheader("🚨 Real-Time Execution Signal")
    
    trade_status = "NEUTRAL HOLD ⚪"
    logic_explanation = "The stock is currently trading within a stable baseline consolidation zone."
    
    # BUY CRITERIA: RSI oversold (<30) OR Bullish MACD Crossover
    if rsi_val <= 30 or (prev_bar['MACD'] < prev_bar['Signal_Line'] and macd_val > sig_val):
        trade_status = "BUY SIGNAL TRIGGERED 🟢"
        logic_explanation = f"Technical confluence reached. RSI is at {rsi_val:.1f} (Undervalued) or a structural Bullish MACD Crossover has occurred."
        
    # SELL CRITERIA: RSI overbought (>70) OR Bearish MACD Crossover
    elif rsi_val >= 70 or (prev_bar['MACD'] > prev_bar['Signal_Line'] and macd_val < sig_val):
        trade_status = "SELL / TAKE PROFIT TRIGGERED 🔴"
        logic_explanation = f"Resistance or overextension detected. RSI is at {rsi_val:.1f} (Overbought) or a structural Bearish MACD Crossover has completed."
        
    st.info(f"**Engine Verdict:** {trade_status}")
    st.markdown(f"🔬 **Mathematical Justification:** {logic_explanation}")
    
    # --- HISTORICAL GRID ---
    st.subheader("📊 Engine Historical Log View")
    st.dataframe(data_matrix[['Open', 'High', 'Low', 'Close', 'RSI', 'MACD', 'Signal_Line']].tail(10))

else:
    st.error(f"Data stream offline for {ticker}. Ensure token formatting matches NSE standards.")