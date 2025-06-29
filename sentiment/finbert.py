from transformers import pipeline
from huggingface_hub import login
import os

login(os.getenv("HF_API_KEY"))

def load_finbert_model():
    """
    Load the FinBERT sentiment analysis model.
    Returns:
        classifier: A sentiment analysis pipeline using the FinBERT model.
    """
    model_name = "ProsusAI/finbert"
    classifier = pipeline("sentiment-analysis", model=model_name, truncation=True, max_length=512)
    return classifier

def analyze_sentiment(text):
    """
    Analyze the sentiment of a given text using the FinBERT model.
    Args:
        text (str): The input text to analyze.
    Returns:
        dict: A dictionary containing the sentiment label and score.
    """
    classifier = load_finbert_model()
    result = classifier(text)[0]  # Pipeline handles truncation internally
    return {"label": result["label"], "score": result["score"]}


# Example usage
# if __name__ == "__main__":
#     sample_text = "The stock market is looking bullish today."
#     sentiment = analyze_sentiment(sample_text)
#     print(f"Text: {sample_text}")
#     print(f"Sentiment: {sentiment['label']}, Score: {sentiment['score']:.4f}")