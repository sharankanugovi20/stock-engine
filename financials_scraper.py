import requests
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

def fetch_market_cap(ticker, start_date, end_date, api_key):
    print(f"📊 Fetching market capitalization data for {ticker} from {start_date} to {end_date}...")
    url = f"https://financialmodelingprep.com/stable/historical-market-capitalization?symbol={ticker}&from={start_date}&to={end_date}&apikey={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    print(data)
    df = pd.DataFrame(data)
    df.rename(columns={"date": "date", "marketCap": "market_cap"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    df["market_cap"] = df["market_cap"].astype(float).astype(int)
    return df[["date", "market_cap"]]

def fetch_eps_and_revenue(ticker, start_date, end_date, api_key):
    print(f"📈 Fetching EPS and Revenue data for {ticker}...")
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    diff = relativedelta(end, start)
    total_quarters = diff.years * 4 + diff.months // 3 + 1
    print(f"Total quarters to fetch: {total_quarters}")
    limit = total_quarters + 4  # includes a few future EPS

    url = "https://financialmodelingprep.com/stable/earnings"
    params = {
        "symbol": ticker,
        "from": (start - relativedelta(months=6)).strftime("%Y-%m-%d"),
        "to": end_date,
        "limit": limit,
        "apikey": api_key
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"API failed: {response.status_code} - {response.text}")

    data = response.json()
    # print(data)
    df = pd.DataFrame(data)

    if df.empty:
        return pd.DataFrame(columns=["date", "eps", "revenue"])

    # Filter out rows where eps or revenue is NaN (i.e., future earnings)
    df = df[["date", "epsActual", "revenueActual"]]
    df.rename(columns={"epsActual": "eps", "revenueActual": "revenue"}, inplace=True)

    df = df.dropna(subset=["eps", "revenue"])
    # Convert revenue from scientific to int
    df["revenue"] = df["revenue"].astype(float).astype(int)
    print(df)
    # Resample to daily, forward fill EPS and revenue
    print("🔍 Earnings raw DataFrame:\n", df)
    df = df.sort_values("date").set_index("date")
    print(df)
    daily_index = pd.date_range(start=start_date, end=end_date, freq="D")
    df = df.reindex(daily_index).ffill().reset_index().rename(columns={"index": "date"})
    print(df)
    return df

def fetch_stock_price(ticker, start_date, end_date, api_key):
    print(f"📊 Fetching stock price data for {ticker} from {start_date} to {end_date}...")
    url = f"https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted?symbol={ticker}&from={start_date}&to={end_date}&apikey={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    print(data)
    if not isinstance(data, list) or not data:
        raise ValueError("❌ Unexpected or empty response from stock price endpoint.")

    df = pd.DataFrame(data)
    df.rename(columns={"date": "date", "adjClose": "stock_price"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date", "stock_price"]].sort_values("date")
    df["stock_return"] = df["stock_price"].pct_change()
    return df

def fetch_financials_data(ticker, start_date, end_date, api_key):
    print(f"📈 Fetching financial data for {ticker}...")

    # Fetch all parts
    price_df = fetch_stock_price(ticker, start_date, end_date, api_key)
    cap_df = fetch_market_cap(ticker, start_date, end_date, api_key)
    # earnings_df = fetch_eps_and_revenue(ticker, start_date, end_date, api_key)

    # Merge market cap
    df = pd.merge(price_df, cap_df, on="date", how="left")

    # # Forward-fill earnings based on announcement date
    # earnings_df = earnings_df.sort_values("date")
    # earnings_df["date"] = pd.to_datetime(earnings_df["date"])
    # earnings_df = earnings_df.set_index("date").resample("D").ffill().reset_index()
    # df = pd.merge(df, earnings_df, on="date", how="left")
    # df[["eps", "revenue"]] = df[["eps", "revenue"]].ffill()

    return df

if __name__ == "__main__":
    ticker = "AAPL"
    start_date = "2025-04-05"
    end_date = "2025-05-15"
    api_key = "q3C1tfT5hbzLrWsxBXHNkWqku3hYCHc6"  # Replace with your actual key

    final_df = fetch_financials_data(ticker, start_date, end_date, api_key)
    print(final_df)
