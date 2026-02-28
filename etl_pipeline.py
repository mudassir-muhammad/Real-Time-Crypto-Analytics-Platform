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

if __name__ == "__main__":
    run_pipeline()