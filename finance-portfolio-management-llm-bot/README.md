## Equity Portfolio Management Chatbot

### Introduction

This is an Agentic AI that connects to **Zerodha API** to fetch your holdings and historic prices and has the following features. Its based on technical indicators and mathematical models for equity only.

➡️ **Instrument Pricing** : Fetch historic prices for all your current holdings for 1 year used in downstream Agents.

➡️ **Risk Agent** : Scan entire portfolio and calculate risk at each symbol level or complete set of holdings.

➡️ **Predictive Analytics Agent** : Utilizes various features and ML models to give you BUY / SELL recommendations for your holdings over 3 Month window.

➡️ **Rebalancing Agent** - Get results on reblancing your portfolio based on current quantitative predictors.

The entire application is deployed on Streamlit with an easy to use and light interface.

### Demo

1. *Give me a summary of my portfolio as of today*

2. *Which pattern is TATAMOTORS forming from the past 2 month timeframe?*

3. *What are the most riskiest holdings that I have currently?*

4. *How can I rebalance my portfolio based on the ATR and 200MA of all shares?*

5. *What is the best date that I can buy INFY share a month from now?*

6. *What are the forecasted price of my JIOFIN 3 months from now?*

7. *What is the confidence that you can give about the forecasted share price for JIOFIN?*

### How things work?

#### 📌 Price Agent

The PriceAgent is a serverless component within this project that acts as a bridge between the Zerodha KiteConnect API and the wider system. Its primary role is to fetch live market prices and portfolio holdings from Zerodha, enrich the data, and expose it in a standardized JSON format for downstream agents, dashboards, or analytics workflows.

This agent is implemented as an Azure Function (HTTP-triggered), making it lightweight, scalable, and easy to integrate with other microservices or cloud-native components.

**🔑 Responsibilities of PriceAgent**

**Authentication & Secure Access**

- Reads Zerodha API credentials (ZERODHA_API_KEY, ZERODHA_ACCESS_TOKEN) from environment variables.
- Ensures no sensitive data is hardcoded.

**Holdings Retrieval**

Calls the kite.holdings() endpoint to fetch the user’s portfolio (symbols, quantities, and average buy price).

**Live Market Data Enrichment**

- For each stock, fetches the latest market price (LTP) via kite.quote().
- Combines holdings with real-time price updates.

**Standardized JSON Output**

Returns structured portfolio data containing:

```
qty (quantity held)

average_price (buy price per stock)

last_price (live market price)
```

**Error Handling & Observability**

- Logs function execution for monitoring in Azure.
- Returns clear error responses in JSON format for resilience.

**📡 Example Output from PriceAgent**

```json
{
  "INFY": {
    "qty": 10,
    "average_price": 1400.5,
    "last_price": 1523.0
  },
  "TCS": {
    "qty": 5,
    "average_price": 3120.0,
    "last_price": 3255.6
  }
}
```

#### 📌 Predictive Analytics Agent

The Predictive Analytics Agent transforms raw market and portfolio data into forecasts, trade signals, and risk insights. It leverages statistical and machine learning models — ARIMA, Random Forest, and Prophet — to generate actionable intelligence.

**🔑 1. Data Ingestion & Feature Engineering**

- Pulls historical OHLCV (Open, High, Low, Close, Volume) data.

- Engineers technical indicators like moving averages, momentum, volatility.

- Encodes candlestick structures numerically:
  
```
body_size, upper_wick_ratio, lower_wick_ratio.

Bullish vs bearish body colors → signal direction.

Detects chart patterns such as Doji, Hammer, Engulfing → converts to binary features for ML models.
```

**🔑 2. Predictive Modeling**

The agent applies three models:

**📈 ARIMA (Time-Series Forecasting)**

- Learns from autocorrelations in price movements.

- Models differencing (trends), autoregressive lags, moving average shocks.

- Good for short-term price prediction.

Example Output:

```json
{
  "model": "ARIMA(2,1,2)",
  "forecast_days": 5,
  "predicted_prices": [487.3, 489.8, 491.2, 490.7, 492.5]
}
```

**🌲 Random Forest (Classification of Signals)**

- Uses ensemble decision trees → reduces overfitting.

- Learns relationships between indicators, candlestick patterns, volume surges and future price movements.

- Produces Buy/Sell/Hold signals with confidence levels.

Example Output:

```json
{
  "model": "Random Forest",
  "features_used": ["RSI", "MACD", "body_ratio", "upper_wick_ratio"],
  "prediction": "BUY",
  "confidence": 0.82
}
```

**📊 Prophet (Trend + Seasonality Forecasting)**

- Decomposes time series into trend + seasonality + holidays.

- Handles weekly, monthly cycles (earnings, Friday volatility, etc.).

- Robust to outliers and missing values.

Example Output:

```
{
  "model": "Prophet",
  "forecast_horizon": "30 days",
  "trend": "Uptrend",
  "predicted_range": {
    "lower": 510.2,
    "upper": 548.9
  },
  "seasonality_effects": ["weekly volatility", "earnings spike"]
}
```

**🔑 3. Financial Indicators & Candlestick Analysis (In-Depth)**

**📌 Trend Indicators**

- SMA (Simple Moving Average): Smooths price over n days. Example: SMA-50 above SMA-200 = Golden Cross (bullish).

- EMA (Exponential Moving Average): Faster-reacting than SMA. Example: EMA-20 rising = short-term bullish momentum.

**📌 Momentum Indicators**

- **RSI (Relative Strength Index)**: Measures overbought/oversold conditions. 70 = Overbought (sell signal), <30 = Oversold (buy signal).

- **MACD (Moving Average Convergence Divergence)**: Trend + momentum. Bullish when MACD line crosses above signal line.

**📌 Volatility Indicators**

- Bollinger Bands: Price relative to volatility envelope. Touching lower band → oversold, upper band → overbought.

- ATR (Average True Range): Measures market turbulence. High ATR = volatile environment → wider stop-losses.

**📌 Volume Indicators**

- **On-Balance Volume (OBV)**: Confirms price moves with buying/selling pressure.

- **Volume Surges**: When price rises with strong volume → stronger bullish signal.

**📊 Candlestick Patterns (Key Market Psychology Signals)**

- Doji: Open ≈ Close, market indecision. Often reversal point.

- Hammer: Small body, long lower wick → bears pushed down but bulls recovered → bullish reversal.

- Engulfing (Bullish): Large green candle fully covers previous red → strong uptrend signal.

- Shooting Star: Small body, long upper wick → failed rally → bearish reversal.

Example Encoding:

```json
{
  "pattern": "Hammer",
  "body_size": 0.6,
  "lower_wick_ratio": 2.8,
  "signal": "Bullish reversal"
}
```

**🔑 4. Integrated Multi-Model Decision**

By blending model forecasts + indicator insights + candlestick psychology, the agent produces an ensemble trading signal:

```json
{
  "symbol": "TCS",
  "date": "2025-08-17",
  "signals": {
    "ARIMA": {"next_5_days": [487.3, 489.8, 491.2, 490.7, 492.5]},
    "RandomForest": {"signal": "BUY", "confidence": 0.82},
    "Prophet": {"trend": "Uptrend", "30d_range": [510.2, 548.9]}
  },
  "final_decision": "BUY",
  "reasoning": "All three models converge on bullish sentiment. Hammer pattern + RSI oversold further support a long entry."
}
```
