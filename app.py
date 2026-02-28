import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates # <--- Added for better Time axis handling
import time

# --- Layout config
st.set_page_config(page_title="Live Crypto Analytics", layout="wide", page_icon="📈")
st.title("⚡ Real-Time Cryptocurrency Analytics Dashboard")

# --- Fetch Data ---
def get_db_connection():
    return sqlite3.connect('crypto_data.db', check_same_thread=False)

def load_data():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM crypto_metrics ORDER BY timestamp ASC", conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        return pd.DataFrame() 

data = load_data()

if data.empty:
    st.warning("⚠️ No data yet. Run `python etl_pipeline.py` and wait roughly 30 seconds.")
else:
    # Get latest snapshot
    latest_time = data['timestamp'].max()
    latest_data = data[data['timestamp'] == latest_time]

    st.caption(f"Last updated: {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # KPI Metrics
    st.subheader("🌐 Current Market Metrics")
    kpi_cols = st.columns(len(latest_data['name'].unique()))
    
    for i, row in enumerate(latest_data.itertuples()):
        kpi_cols[i].metric(
            label=f"{row.name} ({row.symbol.upper()})",
            value=f"${row.current_price:,.2f}",
            delta=f"{row.price_change_24h:,.2f}% in 24h"
        )
    st.markdown("---")

    # Select Box for Analysis
    coin_list = data['name'].unique()
    selected_coin = st.selectbox("📌 Select a Coin to perform Analysis:", coin_list)
    
    filtered_data = data[data['name'] == selected_coin].copy()

    # Layout for plot vs statistics
    col1, col2 = st.columns([2, 1]) 

    with col1:
        st.subheader(f"📈 30-Sec Interval Price Trend: {selected_coin}")
        
        # Building the Plot properly mapped for short-term time gaps
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(filtered_data['timestamp'], filtered_data['current_price'], marker='o', color='#3d5bf9', linewidth=2)
        
        # PROPERLY FORMAT X-AXIS FOR TIME
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S')) 
        
        # Design adjustments
        ax.set_ylabel("Price (USD)", color="black", fontsize=10)
        ax.set_xlabel("Live Time Updates", fontsize=10)
        ax.grid(color='grey', linestyle='--', linewidth=0.5, alpha=0.4)
        plt.xticks(rotation=45)
        
        plt.tight_layout() # THIS FIXES THE WEIRD CUTOFF LABELS 
        st.pyplot(fig)

    with col2:
        st.subheader("🔢 Statistical Analysis")
        prices_array = filtered_data['current_price'].to_numpy()

        if len(prices_array) > 0:
            mean_price = np.mean(prices_array)
            std_deviation = np.std(prices_array)
            max_price = np.max(prices_array)
            min_price = np.min(prices_array)

            st.write(f"**Mean Avg Price:** `${mean_price:,.3f}`")
            st.write(f"**Max Peak Price:** `${max_price:,.3f}`")
            st.write(f"**Min Low Price:** `${min_price:,.3f}`")
            st.write(f"**Tracked Datapoints:** `{len(prices_array)} checks`")
            st.info(f"**Volatility (Std Dev):** `${std_deviation:,.4f}`")

    with st.expander("Show Raw Structured Database Logs"):
        st.dataframe(data.sort_values(by='timestamp', ascending=False), use_container_width=True)

# Loop update matching ETL time logic
time.sleep(15) # Check Streamlit every 15 secs so we don't miss any new 30 sec db dumps
st.rerun()