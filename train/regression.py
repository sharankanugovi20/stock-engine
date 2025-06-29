# stock_regression.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Load dataset (adjust relative path for Codespaces or Colab)
df = pd.read_excel("data/AAPL_final_data.xlsx")  # <-- ensure the file is in the right location

# Drop missing rows
df.dropna(inplace=True)

# Define features and target
features = [
    "news_sentiment",
    "num_articles",
    "reddit_sentiment",
    "reddit_post_volume",
    "market_cap",
    "time"
]

X = df[features]
y = df["stock_return"]

# Add constant (intercept term)
X = sm.add_constant(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = sm.OLS(y_train, X_train).fit()

# Predict
y_pred = model.predict(X_test)

# Evaluate
r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

# Output results
print("✅ Model trained!")
print(f"R² Score: {r2:.4f}")
print(f"RMSE: {rmse:.6f}\n")
print(model.summary())

# Plot
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.7, color='dodgerblue')
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
plt.xlabel("Actual Stock Return")
plt.ylabel("Predicted Stock Return")
plt.title("📈 Actual vs Predicted Stock Returns")
plt.grid(True)
plt.tight_layout()
plt.show()
