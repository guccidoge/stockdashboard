#machine learning

import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def fetch_data_from_database(db_name="stock_data.db"):
    """
    Fetch data from the SQLite database for machine learning.
    Args:
        db_name: Name of the SQLite database file.
    Returns:
        DataFrame containing the stock data.
    """
    try:
        conn = sqlite3.connect(db_name)
        query = "SELECT * FROM stock_data;"
        data = pd.read_sql_query(query, conn)
        return data
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def calculate_metrics(data):
    """
    Add calculated fields like Volatility and Sharpe Ratio to the data.
    Args:
        data: DataFrame containing stock data.
    Returns:
        DataFrame with additional metrics.
    """
    # Calculate Volatility (e.g., based on High and Low prices)
    data['Volatility'] = data['High'] - data['Low']

    # Calculate Sharpe Ratio (e.g., based on Close prices)
    data['Daily_Return'] = data['Close'].pct_change()
    data['Sharpe_Ratio'] = data['Daily_Return'].mean() / data['Daily_Return'].std()

    # Define Low Risk Label (1 = Low Risk, 0 = High Risk)
    data['Low_Risk_Label'] = ((data['Volatility'] < 2) & (data['Sharpe_Ratio'] > 0.5)).astype(int)

    return data.dropna()  # Drop rows with NaN values (e.g., first row for pct_change)

def train_model(data):
    """
    Train a machine learning model to classify low-risk companies.
    Args:
        data: DataFrame containing risk metrics for all companies.
    Returns:
        model: Trained machine learning model.
    """
    # Prepare features (X) and target (y)
    X = data[['Volatility', 'Sharpe_Ratio']]
    y = data['Low_Risk_Label']

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Normalize the data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Initialize and train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)

    # Evaluate the model (optional)
    score = model.score(X_test_scaled, y_test)
    print(f"Model accuracy: {score * 100:.2f}%")

    return model, scaler

def predict_risk(model, scaler, data):
    """
    Predict the risk level of companies using the trained model.
    Args:
        model: Trained machine learning model.
        scaler: Scaler used for normalizing the data.
        data: DataFrame containing the features for prediction.
    Returns:
        DataFrame with predictions.
    """
    X = data[['Volatility', 'Sharpe_Ratio']]
    X_scaled = scaler.transform(X)
    data['Risk_Prediction'] = model.predict(X_scaled)
    return data

def get_top_5_low_risk(data):
    """
    Get the top 5 low-risk companies based on model predictions.
    Args:
        data: DataFrame with risk predictions.
    Returns:
        DataFrame with top 5 low-risk companies.
    """
    low_risk_companies = data[data['Risk_Prediction'] == 1]
    top_5 = low_risk_companies.sort_values(by='Sharpe_Ratio', ascending=False).head(5)
    return top_5
### edited