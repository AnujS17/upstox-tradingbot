import pandas as pd

# Replace with your downloaded file path
csv_file = "EQUITY_L.csv"

# Read the CSV
df = pd.read_csv(csv_file)

# Preview columns
print(df.columns)

# Create a symbol-to-ISIN mapping
symbol_to_isin = dict(zip(df['SYMBOL'], df[' ISIN_NUMBER']))

# Get all tickers
tickers = list(symbol_to_isin.keys())

print("Sample tickers:", tickers)
