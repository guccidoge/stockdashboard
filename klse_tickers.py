import pandas as pd
import sqlite3
import yfinance as yf
import schedule
import time

csv_file_path = 'klse_converted.csv'  
db_file_path = 'daily_stock_data.db'

def fetch_and_store_data():
    
    tickers_df = pd.read_csv(csv_file_path)
    print("Column names in the CSV file:", tickers_df.columns)
    tickers = tickers_df.dropna(subset=['ticker'])  

    
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()

    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_data (
        Company_Name TEXT,
        Category TEXT,
        Open REAL,
        High REAL,
        Low REAL,
        Close REAL,
        Volume INTEGER,
        Dividend REAL,
        Stock_Split REAL,
        Ticker TEXT,
        Timestamp TEXT,
        PRIMARY KEY (Ticker, Timestamp)
    )
    ''')
    conn.commit()

    for _, ticker_row in tickers_df.iterrows():
        ticker = ticker_row['ticker']
        company_name = ticker_row['Name']  
        category = ticker_row['Category']  

        try:
            print(f"Fetching weekly data for {ticker} ({company_name})...")
            
            data = yf.download(tickers=ticker, interval='1wk', period='1y', actions=True)  
            if data.empty:
                print(f"No data found for {ticker}. Skipping.")
                continue

            
            data.reset_index(inplace=True)

        
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [' '.join(col).strip() for col in data.columns]

            
            data.columns = [col.replace(f" {ticker}", "") for col in data.columns]


            column_mapping = {
                'Date': 'Timestamp',
                'Adj Close': 'Adj Close',
                'Close': 'Close',
                'High': 'High',
                'Low': 'Low',
                'Open': 'Open',
                'Volume': 'Volume',
                'Dividends': 'Dividend',
                'Stock Splits': 'Stock_Split'
            }
            data.rename(columns=column_mapping, inplace=True)

            
            required_columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividend', 'Stock_Split']
            for col in required_columns:
                if col not in data.columns:
                    data[col] = 0.0  

            
            data = data[['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividend', 'Stock_Split']]
            data = data[pd.to_numeric(data['Open'], errors='coerce').notna()]  
            
            for _, row in data.iterrows():
                try:
                    
                    timestamp = row['Timestamp'].strftime('%Y-%m-%d') if isinstance(row['Timestamp'], pd.Timestamp) else str(row['Timestamp'])

                    
                    open_price = round(float(row['Open']), 2) if pd.notna(row['Open']) else None
                    high = round(float(row['High']), 2) if pd.notna(row['High']) else None
                    low = round(float(row['Low']), 2) if pd.notna(row['Low']) else None
                    close = round(float(row['Close']), 2) if pd.notna(row['Close']) else None
                    volume = int(row['Volume']) if pd.notna(row['Volume']) else None
                    dividend = round(float(row['Dividend']), 2) if pd.notna(row['Dividend']) else 0.0
                    stock_split = round(float(row['Stock_Split']), 2) if pd.notna(row['Stock_Split']) else 0.0

                    
                    cursor.execute('''
                    INSERT OR REPLACE INTO stock_data (Company_Name, Category, Open, High, Low, Close, Volume, Dividend, Stock_Split, Ticker, Timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (company_name, category, open_price, high, low, close, volume, dividend, stock_split, ticker, timestamp))
                except Exception as row_error:
                    print(f"Error processing row for {ticker}: {row_error}")
        except Exception as fetch_error:
            print(f"Error fetching data for {ticker}: {fetch_error}")

    
    conn.commit()
    conn.close()
    print("Data fetching and storing completed!")


print("Fetching data now...")
fetch_and_store_data()


schedule.every().monday.at("09:00").do(fetch_and_store_data) 

print("Scheduler started. Waiting for the next weekly update...")


while True:
    schedule.run_pending()
    time.sleep(1)
