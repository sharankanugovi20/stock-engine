import praw
import pandas as pd
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sentiment.finbert import analyze_sentiment

# ✅ Load Reddit API credentials from .env file
load_dotenv()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

def fetch_daily_reddit_posts(client_id, client_secret, user_agent, keyword, subreddits, start_date, end_date):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    all_posts = []
    current_date = start_date

    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        after = int(current_date.timestamp())
        before = int(next_date.timestamp())

        for sub in subreddits:
            print(f"🔍 Fetching r/{sub} posts on {current_date.strftime('%Y-%m-%d')} for '{keyword}'")

            try:
                subreddit = reddit.subreddit(sub)
                posts = subreddit.search(keyword, sort='new', time_filter='all', limit=100)

                count = 0
                for post in posts:
                    if after <= int(post.created_utc) < before and count < 5:
                        all_posts.append({
                            'date': datetime.utcfromtimestamp(post.created_utc).date(),
                            'author': post.author.name if post.author else "N/A",
                            'title': post.title,
                            'text': post.selftext,
                            'url': post.url,
                            'score': post.score,
                            'num_comments': post.num_comments,
                            'subreddit': sub,
                            'source': 'Reddit'
                        })
                        count += 1

                time.sleep(1.5)  # polite delay
            except Exception as e:
                print(f"❌ Error fetching from r/{sub}: {e}")

        current_date = next_date

    df = pd.DataFrame(all_posts)
    return df

def sentiment_reddit(df):
    print("📘 Analyzing Reddit posts...")

    if 'text' not in df.columns or 'title' not in df.columns:
        print("Error: Required columns 'text' or 'title' not found in Reddit data.")
        return

    sentiment_scores = []
    sentiment_labels = []
    for _, row in df.iterrows():
        combined_text = f"{row['title']} {row['text']}"

        if pd.isna(combined_text.strip()):
            sentiment_scores.append(None)
            sentiment_labels.append(None)
            continue

        try:
            sentiment = analyze_sentiment(combined_text)
            sentiment_scores.append(sentiment['score'])
            sentiment_labels.append(sentiment['label'])
        except Exception as e:
            print(f"❌ Error analyzing Reddit sentiment: {e}")
            sentiment_scores.append(None)
            sentiment_labels.append(None)

    df['sentiment_score'] = sentiment_scores
    df['sentiment_label'] = sentiment_labels
    return df

def calculate_daily_stats(df):
    print("📊 Calculating daily statistics...")

    # Convert date to datetime and drop rows with missing sentiment
    df['date'] = pd.to_datetime(df['date'])
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

    # Group by day: mean sentiment and post volume
    daily_stats = (
        df.groupby(df['date'].dt.date)['signed_sentiment']
        .agg(['mean', 'count'])
        .reset_index()
    )

    # Rename columns
    daily_stats.columns = ['date', 'average_signed_sentiment', 'reddit_post_volume']

    print(daily_stats.to_string(index=False))

    return daily_stats

if __name__ == "__main__":
    start_date = datetime(2025, 5, 10)
    end_date = datetime(2025, 5, 17)
    subreddits = ["stocks", "investing", "wallstreetbets", "technology"]
    keyword = "Apple"

    posts_df = fetch_daily_reddit_posts(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
        keyword=keyword,
        subreddits=subreddits,
        start_date=start_date,
        end_date=end_date
    )

    sentiment_df = sentiment_reddit(posts_df)
    calculate_daily_stats(sentiment_df)