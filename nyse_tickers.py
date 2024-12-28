import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL for NYSE company listings
NYSE_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

def get_nyse_tickers():
    """
    Scrape NYSE tickers from the Wikipedia page for S&P 500 companies.
    Returns:
        DataFrame containing tickers and company information.
    """
    response = requests.get(NYSE_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Locate the table containing the S&P 500 companies
    table = soup.find("table", {"class": "wikitable"})
    if not table:
        raise ValueError("Could not find the table on the page.")
    
    rows = table.find_all("tr")
    data = []
    
    # Extract table headers (if needed)
    headers = [header.text.strip() for header in rows[0].find_all("th")]

    # Extract data rows
    for row in rows[1:]:
        cols = row.find_all("td")
        if cols:
            ticker = cols[0].text.strip()
            name = cols[1].text.strip()
            sector = cols[3].text.strip()
            data.append({"Ticker": ticker, "Company": name, "Sector": sector})
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df

def save_to_csv(df, filename="nyse_tickers.csv"):
    """
    Save the DataFrame to a CSV file.
    Args:
        df: DataFrame containing the tickers and information.
        filename: Filename for the CSV file.
    """
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} tickers to {filename}")

# Main execution
if __name__ == "__main__":
    try:
        nyse_tickers_df = get_nyse_tickers()
        save_to_csv(nyse_tickers_df)
        print(nyse_tickers_df.head())  # Show first few entries
    except Exception as e:
        print(f"Error: {e}")
