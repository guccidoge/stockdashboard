import sqlite3
import yfinance as yf
import pandas as pd

# Connect to SQLite database (or any other DB you're using)
conn = sqlite3.connect('klse_tickers.db')  # Replace with your DB name
cursor = conn.cursor()

# 1. Define Table Creation Queries (for companies and financials)
def create_tables():
    # Create companies table
    cursor.execute('''CREATE TABLE IF NOT EXISTS companies (
                        ticker TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        category TEXT
                    )''')

    # Create financials table
    cursor.execute('''CREATE TABLE IF NOT EXISTS financials (
                        ticker TEXT,
                        date DATE,
                        market_cap REAL,
                        pe_ratio REAL,
                        revenue REAL,
                        net_income REAL,
                        earnings_per_share REAL,
                        PRIMARY KEY (ticker, date),
                        FOREIGN KEY (ticker) REFERENCES companies(ticker)
                    )''')

    conn.commit()

# 2. Load tickers and their categories from klse_tickers.csv
def load_tickers_and_categories_from_csv(file_path='klse_tickers.csv'):
    # Read tickers and categories from the CSV
    df = pd.read_csv(file_path)
    return df[['Ticker', 'Category']].to_dict('records')  

# 3. Fetch Data from Yahoo Finance and Insert Into Tables
def fetch_and_insert_data(tickers_with_categories):
    error_occurred = False  # To track if any error happens
    
    for record in tickers_with_categories:
        ticker = record['Ticker']
        category_from_csv = record['Category']  # Use Category from CSV

        try:
            # Fetch basic company info (name, ticker)
            company = yf.Ticker(ticker)
            info = company.info
            name = info.get('longName', 'N/A')
            
            # Use Category from CSV (fall back to Yahoo Finance only if CSV Category is missing)
            category = category_from_csv if category_from_csv else info.get('sector', 'N/A')

            # Insert basic info into companies table
            cursor.execute('''INSERT OR IGNORE INTO companies (ticker, name, category)
                              VALUES (?, ?, ?)''', (ticker, name, category))
            
            # Fetch financial data directly from company.info
            market_cap = info.get('marketCap', 0)
            pe_ratio = info.get('trailingPE', 0)
            revenue = info.get('totalRevenue', 0)
            net_income = info.get('netIncomeToCommon', 0)
            eps = info.get('trailingEps', 0)

            # Insert the financial data into the financials table
            cursor.execute('''INSERT OR REPLACE INTO financials (ticker, date, market_cap, pe_ratio, revenue, net_income, earnings_per_share)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                           (ticker, pd.to_datetime('today').date(), market_cap, pe_ratio, revenue, net_income, eps))

            conn.commit()
            
        except Exception as e:
            error_occurred = True
            print(f"Error occurred while processing {ticker}: {e}")

    if not error_occurred:
        print("All data fetched and inserted successfully.")
    else:
        print("Some errors occurred during the process. Please check the logs.")

# Main Function
if __name__ == "__main__":
    try:
        # Load tickers and their categories from the CSV file
        tickers_with_categories = load_tickers_and_categories_from_csv('klse_tickers.csv')  # Specify your CSV path if needed
        
        # Create tables (if not already created)
        create_tables()
        
        # Fetch data from Yahoo Finance and insert into database
        fetch_and_insert_data(tickers_with_categories)

    except Exception as e:
        print(f"An error occurred during the setup or execution: {e}")
    
    finally:
        conn.close()
