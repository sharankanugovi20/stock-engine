import requests
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import time
from sentiment.finbert import analyze_sentiment

def fetch_fmp_news_daily(symbol="AAPL", start_date="2025-05-10", end_date="2025-06-10", api_key="YOUR_API_KEY", limit_per_day=150):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    all_articles = []

    for i in tqdm(range((end - start).days + 1)):
        day = start + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")

        url = (
            f"https://financialmodelingprep.com/stable/news/stock?apikey={api_key}"
            f"&symbols={symbol}&from={day_str}&to={day_str}&limit={limit_per_day}"
        )

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Extract relevant fields from each article
            for article in data:
                all_articles.append({
                    "symbol": article.get("symbol"),
                    "publishedDate": article.get("publishedDate"),
                    "publisher": article.get("publisher"),
                    "title": article.get("title"),
                    "image": article.get("image"),
                    "site": article.get("site"),
                    "text": article.get("text"),
                    "url": article.get("url"),
                })

        except Exception as e:
            print(f"❌ Failed on {day_str}: {e}")

        # optional: prevent hammering the API
        time.sleep(0.3)  # adjust this if you hit rate limits

    # Create a DataFrame from the collected articles
    df = pd.DataFrame(all_articles)
    return df

def sentiment_news(df):
    print("📰 Analyzing News Sentiment...")

    if 'text' not in df.columns:
        print("Error: 'text' column not found in the DataFrame.")
        return

    sentiment_scores = []
    sentiment_labels = []
    for text in df['text']:
        if pd.isna(text):
            sentiment_scores.append(None)
            sentiment_labels.append(None)
            continue

        try:
            sentiment = analyze_sentiment(text)
            sentiment_scores.append(sentiment['score'])
            sentiment_labels.append(sentiment['label'])
        except Exception as e:
            print(f"❌ Error analyzing sentiment: {e}")
            sentiment_scores.append(None)
            sentiment_labels.append(None)

    df['sentiment_score'] = sentiment_scores
    df['sentiment_label'] = sentiment_labels
    return df

def calculate_daily_stats(df):
    print("📊 Calculating daily statistics...")

    # Convert publishedDate to datetime and drop rows with missing sentiment
    df['publishedDate'] = pd.to_datetime(df['publishedDate'])
    df = df.dropna(subset=['sentiment_score', 'sentiment_label'])

    # Map label to signed score
    def signed_score(row):
        if row['sentiment_label'] == 'positive':
            return row['sentiment_score']
        elif row['sentiment_label'] == 'negative':
            return -row['sentiment_score']
        else:
            return 0

    df['signed_sentiment'] = df.apply(signed_score, axis=1)

    # Group by day: mean sentiment and article volume
    daily_stats = (
        df.groupby(df['publishedDate'].dt.date)['signed_sentiment']
        .agg(['mean', 'count'])
        .reset_index()
    )

    # Rename columns
    daily_stats.columns = ['date', 'average_signed_sentiment', 'num_articles']

    print(daily_stats.to_string(index=False))

    return daily_stats

# ▶️ Run the function
if __name__ == "__main__":
    news_df = fetch_fmp_news_daily(
        symbol="AAPL",
        start_date="2025-05-08",
        end_date="2025-05-12",
        api_key="q3C1tfT5hbzLrWsxBXHNkWqku3hYCHc6",  # replace with your real key
        limit_per_day=20
    )

    sentiment_df = sentiment_news(news_df)
    calculate_daily_stats(sentiment_df)
    print("✅ News sentiment analysis completed.")