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
        Ticker TEXT,
        Company_Name TEXT,
        Category TEXT,
        Date TEXT,
        Open REAL,
        High REAL,
        Low REAL,
        Close REAL,
        Volume INTEGER,
        PRIMARY KEY (Ticker, Date)
    )
    ''')
    conn.commit()

    for _, ticker_row in tickers_df.iterrows():
        ticker = ticker_row['ticker']
        company_name = ticker_row['Name']  
        category = ticker_row['Category']  

        try:
            print(f"Fetching daily data for {ticker} ({company_name})...")
            
            data = yf.download(tickers=ticker, interval='1d', period='1d')  
            if data.empty:
                print(f"No data found for {ticker}. Skipping.")
                continue

            
            data.reset_index(inplace=True)

            
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [' '.join(col).strip() for col in data.columns]

            
            data.columns = [col.replace(f" {ticker}", "") for col in data.columns]

            
            column_mapping = {
                'Date': 'Date',
                'Adj Close': 'Adj Close',
                'Close': 'Close',
                'High': 'High',
                'Low': 'Low',
                'Open': 'Open',
                'Volume': 'Volume'
            }
            data.rename(columns=column_mapping, inplace=True)

            
            required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_columns):
                print(f"Missing required columns for {ticker}. Skipping.")
                continue

            
            data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            data = data[pd.to_numeric(data['Open'], errors='coerce').notna()] 

            
            for _, row in data.iterrows():
                try:
                    
                    date = row['Date'].strftime('%Y-%m-%d') if isinstance(row['Date'], pd.Timestamp) else str(row['Date'])

                    
                    open_price = round(float(row['Open']), 2) if pd.notna(row['Open']) else None
                    high = round(float(row['High']), 2) if pd.notna(row['High']) else None
                    low = round(float(row['Low']), 2) if pd.notna(row['Low']) else None
                    close = round(float(row['Close']), 2) if pd.notna(row['Close']) else None
                    volume = int(row['Volume']) if pd.notna(row['Volume']) else None

                    
                    cursor.execute('''
                    INSERT OR REPLACE INTO stock_data (Ticker, Company_Name, Category, Date, Open, High, Low, Close, Volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (ticker, company_name, category, date, open_price, high, low, close, volume))
                except Exception as row_error:
                    print(f"Error processing row for {ticker}: {row_error}")
        except Exception as fetch_error:
            print(f"Error fetching data for {ticker}: {fetch_error}")

    
    conn.commit()
    conn.close()
    print("Data fetching and storing completed!")


print("Fetching data now...")
fetch_and_store_data()


schedule.every().day.at("09:00").do(fetch_and_store_data)

print("Scheduler started. Waiting for the next run...")


while True:
    schedule.run_pending()
    time.sleep(1)
