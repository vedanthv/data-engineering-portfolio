import logging
import azure.functions as func
import os
import requests
import pandas as pd
import numpy as np
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from azure.storage.blob import BlobServiceClient
import json

# ---------- helpers ----------
def safe_mean(series):
    if series is None:
        return None
    s = pd.Series(series).dropna()
    return float(s.mean()) if len(s) > 0 else None

def rmse_from_arrays(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    mask = ~np.isnan(a) & ~np.isnan(b)
    if mask.sum() == 0:
        return None
    return float(np.sqrt(((a[mask] - b[mask])**2).mean()))

def directional_accuracy(actual, predicted):
    actual_diff = np.diff(actual)
    predicted_diff = np.diff(predicted)
    mask = ~np.isnan(actual_diff) & ~np.isnan(predicted_diff)
    if mask.sum() == 0:
        return None
    correct = np.sum((actual_diff[mask] * predicted_diff[mask]) > 0)
    return correct / mask.sum()

def kelly_fraction(expected_return, variance):
    if variance <= 0:
        return 0
    return max(0, expected_return / variance)

def compute_best_dates(forecast_series, current_price):
    buy_date = forecast_series.idxmin().strftime("%Y-%m-%d")
    sell_date = forecast_series.idxmax().strftime("%Y-%m-%d")
    return buy_date, sell_date

def categorize_risk(volatility, atr_risk):
    score = (volatility or 0) + (atr_risk or 0)
    if score < 0.2:
        return "Low"
    elif score < 0.5:
        return "Medium"
    else:
        return "High"

# ---------- portfolio & historical helpers ----------
def fetch_portfolio(price_agent_url):
    resp = requests.get(price_agent_url, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"PriceAgent error: {resp.status_code}")
    return resp.json()

def fetch_historical(kite, symbol, start_date, end_date, exchange="NSE"):
    instrument_key = f"{exchange}:{symbol}"
    ltp_info = kite.ltp(instrument_key)
    token_info = ltp_info.get(instrument_key)
    if not token_info:
        raise Exception("ltp_missing")
    instrument_token = token_info.get("instrument_token")
    historical = kite.historical_data(instrument_token, start_date, end_date, interval="day")
    df = pd.DataFrame(historical)
    if df.empty:
        raise Exception("no_historical")
    df["date"] = pd.to_datetime(df["date"])
    try: df["date"] = df["date"].dt.tz_localize(None)
    except: pass
    df.set_index("date", inplace=True)
    df = df.sort_index()
    df["close"] = df["close"].astype(float)
    return df

# ---------- forecast ensemble ----------
def weighted_forecast(models_dict, errors_dict):
    inv_rmse = {k: 1/v if v else 0 for k,v in errors_dict.items()}
    total = sum(inv_rmse.values())
    weights = {k: inv_rmse[k]/total for k in inv_rmse} if total>0 else {k: 1/len(models_dict) for k in models_dict}
    forecast_combined = sum(models_dict[k]*weights.get(k,0) for k in models_dict)
    return forecast_combined, weights

# ---------- rebalancing calculation ----------
def compute_rebalance(symbol, df, forecast_models, pattern_strength, volatility_lookback=30):
    current_price = df["close"].iloc[-1]
    last_actuals = df["close"].tail(volatility_lookback)
    n = len(last_actuals)

    # ---------- model errors ----------
    errors = {}
    for name, series in forecast_models.items():
        try:
            if series is None or len(series)<n: continue
            pred_vals = np.array(series.iloc[:n].astype(float))
            act_vals = np.array(last_actuals.values.astype(float))
            errors[name] = rmse_from_arrays(act_vals, pred_vals)
        except: continue

    # ---------- weighted forecast ----------
    forecast_series, model_weights = weighted_forecast(forecast_models, errors)
    forecast_avg = safe_mean(forecast_series)

    # ---------- directional accuracy ----------
    dir_acc = {}
    for name, series in forecast_models.items():
        try:
            dir_acc[name] = directional_accuracy(last_actuals.values, series.iloc[:n].values)
        except: dir_acc[name] = None

    # ---------- risk ----------
    df['returns'] = df['close'].pct_change().fillna(0)
    volatility = df['returns'].std() * np.sqrt(252)
    atr_risk = df['close'].diff().abs().rolling(14,min_periods=1).mean().iloc[-1]/current_price if current_price>0 else 0
    risk_category = categorize_risk(volatility, atr_risk)

    # ---------- best buy/sell ----------
    best_buy_date, best_sell_date = compute_best_dates(forecast_series, current_price)

    # ---------- expected return ----------
    expected_return = (forecast_avg - current_price)/current_price if current_price>0 else 0
    confidence_score = expected_return

    # ---------- position sizing ----------
    alloc_pct = kelly_fraction(expected_return, volatility**2) * 100

    # ---------- patterns ----------
    best_pattern = max(pattern_strength.keys(), key=lambda p: abs(pattern_strength.get(p,0))) if pattern_strength else None
    strength = pattern_strength.get(best_pattern,0) if best_pattern else 0

    # ---------- final JSON without simulations ----------
    out = {
        "current_price": current_price,
        "forecast_price": round(forecast_avg,2) if forecast_avg else None,
        "expected_return_pct": round(expected_return*100,2),
        "weighted_confidence": round(confidence_score,2),
        "best_buy_date": best_buy_date,
        "best_sell_date": best_sell_date,
        "recommended_allocation_pct": round(alloc_pct,2),
        "risk_category": risk_category,
        "pattern_detected": best_pattern,
        "pattern_strength": strength,
        "directional_accuracy": dir_acc,
        "rmse_accuracy": errors,
        "model_weights": model_weights
    }
    return out

# ---------- main Azure Function ----------
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("RebalancingAgent triggered")
    try:
        api_key = os.getenv("ZERODHA_API_KEY")
        access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
        price_agent_url = os.getenv("PRICE_AGENT_URL")
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("REBALANCE_CONTAINER", "rebalancing-output") 

        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        portfolio = fetch_portfolio(price_agent_url)
        blob_client_svc = BlobServiceClient.from_connection_string(conn_str)
        try: blob_client_svc.create_container(container_name)
        except: pass

        # --- delete old blobs to avoid seeing previous scenario_simulations ---
        container_client = blob_client_svc.get_container_client(container_name)
        for blob in container_client.list_blobs():
            container_client.delete_blob(blob.name)

        results = {}
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=365)
        pattern_strength = {} # optional pattern strength dictionary

        for symbol in portfolio.keys():
            try:
                df = fetch_historical(kite, symbol, start_date, end_date)
                forecast_models = {
                    "ARIMA": df["close"],  # placeholder, replace with real forecasts
                    "Prophet": df["close"],
                    "RF": df["close"]
                }
                out = compute_rebalance(symbol, df, forecast_models, pattern_strength)

                # store in blob
                date_str = datetime.utcnow().strftime('%Y%m%d')
                blob_name = f"{date_str}.json"
                blob_client = blob_client_svc.get_blob_client(container=container_name, blob=blob_name)
                blob_client.upload_blob(json.dumps(out), overwrite=True)

                results[symbol] = out
            except Exception as e:
                logging.error(f"Symbol {symbol} error: {str(e)}")
                results[symbol] = {"error": str(e)}

        return func.HttpResponse(json.dumps(results), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
