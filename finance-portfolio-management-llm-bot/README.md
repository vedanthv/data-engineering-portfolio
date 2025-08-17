## Finance Portfolio Management Chatbot

### Introduction

This is an Agentic AI that connects to **Zerodha API** to fetch your holdings and historic prices and has the following features. Its based on technical indicators and mathematical models.

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
