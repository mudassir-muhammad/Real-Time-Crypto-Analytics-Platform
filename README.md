ETL_PIPELINE.py code:

import requests
import pandas as pd
import sqlite3
import time
from datetime import datetime

def init_db():
    conn = sqlite3.connect('crypto_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crypto_metrics (
            timestamp TEXT,
            coin_id TEXT,
            symbol TEXT,
            name TEXT,
            current_price REAL,
            market_cap REAL,
            total_volume REAL,
            price_change_24h REAL
        )
    ''')
    conn.commit()
    return conn

def fetch_live_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": "bitcoin,ethereum,solana,binancecoin,cardano",
        "order": "market_cap_desc"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def transform_data(raw_data):
    if not raw_data:
        return pd.DataFrame()
    df = pd.DataFrame(raw_data)
    cols =['id', 'symbol', 'name', 'current_price', 'market_cap', 'total_volume', 'price_change_percentage_24h']
    df = df[cols].copy()
    df.fillna(0, inplace=True)
    df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df.rename(columns={'id': 'coin_id', 'price_change_percentage_24h': 'price_change_24h'}, inplace=True)
    return df

def load_data(df, conn):
    if not df.empty:
        df.to_sql('crypto_metrics', conn, if_exists='append', index=False)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Inserted records. Next update in 30 secs.")

def run_pipeline():
    conn = init_db()
    print("🚀 Starting 30-Second interval ETL pipeline... Press Ctrl+C to stop.")
    
    while True:
        raw_data = fetch_live_data()
        clean_df = transform_data(raw_data)
        load_data(clean_df, conn)
        
        # CHANGED: Now sleeping for exactly 30 seconds
        time.sleep(30)



      APP.py code:

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


time.sleep(15) # Check Streamlit every 15 secs so we don't miss any new 30 sec db dumps
st.rerun()

if __name__ == "__main__":
    run_pipeline()
