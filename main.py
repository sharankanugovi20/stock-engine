from reddit_scraper import fetch_daily_reddit_posts, sentiment_reddit, calculate_daily_stats as calculate_reddit_stats
import os
from dotenv import load_dotenv
from news_scraper import fetch_fmp_news_daily, sentiment_news, calculate_daily_stats as calculate_news_stats
from financials_scraper import fetch_financials_data
from sentiment.finbert import analyze_sentiment
import pandas as pd
from datetime import datetime

# Load credentials
load_dotenv()


# def fetch_financials_data(ticker="AAPL"):
#     print("📈 Fetching Financial Data for ticker:", ticker)
#     # Placeholder for financials data fetching logic
#     financials_data = pd.DataFrame({
#         "date": [],
#         "financial_metric": []
#     })
#     return financials_data


def create_mega_df(news_df, social_df, financials_df):#financials_df
    print("🔗 Combining News, Social, and Financial Data into Mega DataFrame...")

    # Merge DataFrames on the 'date' column
    mega_df = pd.merge(news_df, social_df, on="date", how="outer")
    financials_df["date"] = pd.to_datetime(financials_df["date"])
    mega_df["date"] = pd.to_datetime(mega_df["date"])
    mega_df = pd.merge(mega_df, financials_df, on="date", how="outer")

    mega_df.rename(columns={
        'average_signed_sentiment_x': 'news_sentiment',
        'average_signed_sentiment_y': 'reddit_sentiment'
    }, inplace=True)

    return mega_df


def analyze_stock(ticker="AAPL"):
    print("📊 Starting analysis for ticker:", ticker)

    # Fetch and process news data
    news_df = fetch_fmp_news_daily(
        symbol=ticker,
        start_date="2025-02-09",
        end_date="2025-06-09",
        api_key="q3C1tfT5hbzLrWsxBXHNkWqku3hYCHc6"
        # limit_per_day=20
    )
    if news_df is None or news_df.empty:
        print("❌ News DataFrame is empty or None.")
        return

    news_df = sentiment_news(news_df)
    if news_df is None or news_df.empty:
        print("❌ Sentiment analysis failed for News DataFrame.")
        return
    
     # Save news DataFrame to Excel before daily stats calculation
    news_filename = f"news/{ticker}_news_data.xlsx"
    try:
        news_df.to_excel(news_filename, index=False)
        print(f"✅ News DataFrame saved to {news_filename}")
    except Exception as e:
        print(f"❌ Error saving News DataFrame: {e}")

    news_df = calculate_news_stats(news_df)
    if news_df is None or news_df.empty:
        print("❌ Daily statistics calculation failed for News DataFrame.")
        return

    # Fetch and process social media data
    social_df = fetch_daily_reddit_posts(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
        keyword=ticker,
        subreddits=["stocks", "investing", "wallstreetbets", "technology"],
        start_date=datetime(2025, 2, 9),
        end_date=datetime(2025, 6, 9)
    )
    if social_df is None or social_df.empty:
        print("❌ Social DataFrame is empty or None.")
        return

    social_df = sentiment_reddit(social_df)  # Ensure sentiment analysis is performed
    if social_df is None or social_df.empty:
        print("❌ Sentiment analysis failed for Social DataFrame.")
        return

    # Save social DataFrame to Excel before daily stats calculation
    social_filename = f"reddit/{ticker}_social_data.xlsx"
    try:
        social_df.to_excel(social_filename, index=False)
        print(f"✅ Social DataFrame saved to {social_filename}")
    except Exception as e:
        print(f"❌ Error saving Social DataFrame: {e}")

    social_df = calculate_reddit_stats(social_df)
    if social_df is None or social_df.empty:
        print("❌ Daily statistics calculation failed for Social DataFrame.")
        return

# Fetch financial data using financials_scraper

    financials_df = fetch_financials_data(
        ticker=ticker,
        start_date="2025-02-09",
        end_date="2025-06-09",
        api_key="q3C1tfT5hbzLrWsxBXHNkWqku3hYCHc6"
    )
    if financials_df is None or financials_df.empty:
        print("❌ Financials DataFrame is empty or None.")
        return

    # Ensure the 'date' column in financials_df is of type datetime64[ns]
    financials_df['date'] = pd.to_datetime(financials_df['date'], errors='coerce')

    # Create mega DataFrame
    mega_df = create_mega_df(news_df, social_df,financials_df)

    # Save mega DataFrame to Excel
    filename = f"data/{ticker}_final_data.xlsx"
    try:
        mega_df.to_excel(filename, index=False)
        print(f"✅ Mega DataFrame saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving final DataFrame: {e}")

    # Train the model using the mega DataFrame
    # from train.regression import train_model

    # print("📈 Training regression model using Mega DataFrame...")
    # model_performance, graph_path = train_model(mega_df, save_graph_path="data/model_performance_graph.png")

    # print("✅ Model training completed!")
    # print(f"R² Score: {model_performance['r2']:.4f}")
    # print(f"RMSE: {model_performance['rmse']:.6f}")
    # print(f"Graph saved at: {graph_path}")


if __name__ == "__main__":
    analyze_stock("AAPL")