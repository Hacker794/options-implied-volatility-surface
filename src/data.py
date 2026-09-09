import yfinance as yf

# Available option expiration dates for a given ticker symbol

def get_expiries(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    return ticker.options

if __name__ == "__main__":
    expiries = get_expiries("SPY")

    print(expiries)