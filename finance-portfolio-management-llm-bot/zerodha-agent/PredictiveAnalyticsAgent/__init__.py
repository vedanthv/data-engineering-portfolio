import logging
import azure.functions as func
import os
import requests
import pandas as pd
import numpy as np
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor
from azure.storage.blob import BlobServiceClient
import json

# ---------- helpers ----------
def make_future_index(last_date, days=30):
    start = pd.to_datetime(last_date) + pd.Timedelta(days=1)
    return pd.date_range(start=start, periods=days, freq="D")

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

# ---------- indicators ----------
def calculate_indicators(df):
    df = df.copy()
    df["MA50"] = df["close"].rolling(window=50, min_periods=1).mean()
    df["MA200"] = df["close"].rolling(window=200, min_periods=1).mean()
    
    # RSI (14)
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14, min_periods=1).mean()
    avg_loss = loss.rolling(window=14, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI"] = df["RSI"].fillna(method="ffill").fillna(50)
    
    # MACD & Signal
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df[["MACD", "Signal"]] = df[["MACD", "Signal"]].fillna(method="ffill").fillna(0)
    
    # ATR(14)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR14'] = tr.rolling(14, min_periods=1).mean()
    
    return df

# ---------- candlestick patterns ----------
def detect_patterns(df):
    patterns = {}
    df_recent = df.tail(63)
    if df_recent.empty or df_recent.shape[0] < 3:
        return patterns

    o = df_recent["open"]
    c = df_recent["close"]
    h = df_recent["high"]
    l = df_recent["low"]

    # 20 candlestick patterns
    if c.iloc[-2] < o.iloc[-2] and c.iloc[-1] > o.iloc[-1] and c.iloc[-1] > c.iloc[-2] and o.iloc[-1] < o.iloc[-2]:
        patterns["Bullish Engulfing"] = True
    if c.iloc[-2] > o.iloc[-2] and c.iloc[-1] < o.iloc[-1] and c.iloc[-1] < c.iloc[-2] and o.iloc[-1] > o.iloc[-2]:
        patterns["Bearish Engulfing"] = True
    if (c.iloc[-1] - l.iloc[-1]) > 2 * abs(o.iloc[-1] - c.iloc[-1]):
        patterns["Hammer"] = True
    if (c.iloc[-1] - l.iloc[-1]) > 2 * abs(o.iloc[-1] - c.iloc[-1]) and c.iloc[-1] < o.iloc[-1]:
        patterns["Hanging Man"] = True
    if (h.iloc[-1] - c.iloc[-1]) > 2 * abs(o.iloc[-1] - c.iloc[-1]) and c.iloc[-1] > o.iloc[-1]:
        patterns["Inverted Hammer"] = True
    if (h.iloc[-1] - c.iloc[-1]) > 2 * abs(o.iloc[-1] - c.iloc[-1]) and c.iloc[-1] < o.iloc[-1]:
        patterns["Shooting Star"] = True
    if c.iloc[-3] < o.iloc[-3] and abs(c.iloc[-2]-o.iloc[-2])/abs(c.iloc[-3]-o.iloc[-3]) < 0.5 and c.iloc[-1] > (o.iloc[-3]+c.iloc[-3])/2:
        patterns["Morning Star"] = True
    if c.iloc[-3] > o.iloc[-3] and abs(c.iloc[-2]-o.iloc[-2])/abs(c.iloc[-3]-o.iloc[-3]) < 0.5 and c.iloc[-1] < (o.iloc[-3]+c.iloc[-3])/2:
        patterns["Evening Star"] = True
    if c.iloc[-2] < o.iloc[-2] and c.iloc[-1] > o.iloc[-1] and c.iloc[-1] > c.iloc[-2] + (o.iloc[-2]-c.iloc[-2])/2:
        patterns["Piercing Line"] = True
    if c.iloc[-2] > o.iloc[-2] and c.iloc[-1] < o.iloc[-1] and c.iloc[-1] < c.iloc[-2] - (c.iloc[-2]-o.iloc[-2])/2:
        patterns["Dark Cloud Cover"] = True
    if c.iloc[-2] < o.iloc[-2] and o.iloc[-1] > c.iloc[-2] and c.iloc[-1] < o.iloc[-2]:
        patterns["Bullish Harami"] = True
    if c.iloc[-2] > o.iloc[-2] and o.iloc[-1] < c.iloc[-2] and c.iloc[-1] > o.iloc[-2]:
        patterns["Bearish Harami"] = True
    if c.iloc[-3] > o.iloc[-3] and c.iloc[-2] > o.iloc[-2] and c.iloc[-1] > o.iloc[-1] and c.iloc[-3]<c.iloc[-2]<c.iloc[-1]:
        patterns["Three White Soldiers"] = True
    if c.iloc[-3] < o.iloc[-3] and c.iloc[-2] < o.iloc[-2] and c.iloc[-1] < o.iloc[-1] and c.iloc[-3]>c.iloc[-2]>c.iloc[-1]:
        patterns["Three Black Crows"] = True
    if c.iloc[-2] < o.iloc[-2] and c.iloc[-1] > o.iloc[-1] and o.iloc[-1] > c.iloc[-2]:
        patterns["Bullish Kicker"] = True
    if c.iloc[-2] > o.iloc[-2] and c.iloc[-1] < o.iloc[-1] and o.iloc[-1] < c.iloc[-2]:
        patterns["Bearish Kicker"] = True
    hl_range = h.iloc[-1] - l.iloc[-1]
    if hl_range == 0 or abs(c.iloc[-1]-o.iloc[-1])/hl_range < 0.1:
        patterns["Doji"] = True
    if hl_range == 0 or (abs(c.iloc[-1]-o.iloc[-1])/hl_range < 0.05 and hl_range > 2*abs(c.iloc[-1]-o.iloc[-1])):
        patterns["Long-Legged Doji"] = True
    if c.iloc[-3]<o.iloc[-3] and c.iloc[-2]<o.iloc[-2] and o.iloc[-2]>c.iloc[-3] and c.iloc[-1]<o.iloc[-1] and o.iloc[-1]<c.iloc[-2]:
        patterns["Upside Gap Two Crows"] = True
    if c.iloc[-3]>o.iloc[-3] and c.iloc[-2]>o.iloc[-2] and o.iloc[-2]<c.iloc[-3] and c.iloc[-1]>o.iloc[-1] and o.iloc[-1]>c.iloc[-2]:
        patterns["Downside Gap Two Rabbits"] = True

    return patterns

# ---------- forecasting models ----------
def forecast_with_arima(series, last_date, days=30):
    try:
        if series.shape[0] < 10:
            fut_idx = make_future_index(last_date, days)
            return pd.Series([series.iloc[-1]] * days, index=fut_idx)
        model = ARIMA(series, order=(5,1,0))
        fit = model.fit()
        fc = fit.forecast(steps=days)
        fut_idx = make_future_index(last_date, days)
        return pd.Series(fc, index=fut_idx)
    except:
        fut_idx = make_future_index(last_date, days)
        return pd.Series([series.iloc[-1]] * days, index=fut_idx)

def forecast_with_prophet(df, last_date, days=30):
    try:
        prop_df = df.reset_index()[["date","close"]].rename(columns={"date":"ds","close":"y"})
        prop_df["ds"] = pd.to_datetime(prop_df["ds"])
        try: prop_df["ds"] = prop_df["ds"].dt.tz_localize(None)
        except: pass
        if prop_df.shape[0] < 10:
            fut_idx = make_future_index(last_date, days)
            return pd.Series([df["close"].iloc[-1]] * days, index=fut_idx)
        m = Prophet(daily_seasonality=True)
        m.fit(prop_df)
        future = m.make_future_dataframe(periods=days)
        try: future["ds"] = future["ds"].dt.tz_localize(None)
        except: pass
        forecast = m.predict(future)
        future_forecast = forecast[forecast["ds"] > pd.to_datetime(last_date)].head(days)
        vals = future_forecast["yhat"].tolist()
        if len(vals) < days:
            vals += [df["close"].iloc[-1]] * (days - len(vals))
        fut_idx = make_future_index(last_date, days)
        return pd.Series(vals, index=fut_idx)
    except:
        fut_idx = make_future_index(last_date, days)
        return pd.Series([df["close"].iloc[-1]] * days, index=fut_idx)

def forecast_with_rf(df, last_date, days=30):
    try:
        df_clean = df.copy()
        features = ["MA50","MA200","RSI","MACD","Signal"]
        df_clean = df_clean.dropna(subset=["close"])
        if df_clean.shape[0] < 20:
            fut_idx = make_future_index(last_date, days)
            return pd.Series([df_clean["close"].iloc[-1]] * days, index=fut_idx)
        X = df_clean[features].fillna(method="ffill").fillna(method="bfill")
        y = df_clean["close"]
        train_size = max(5, len(X)-30)
        X_train, y_train = X.iloc[:train_size], y.iloc[:train_size]
        model = RandomForestRegressor(n_estimators=200, random_state=42)
        model.fit(X_train, y_train)
        last_feats = X.iloc[-1].to_dict()
        future_feats = pd.DataFrame([last_feats]*days, index=make_future_index(last_date, days))
        preds = model.predict(future_feats)
        return pd.Series(preds, index=future_feats.index)
    except:
        fut_idx = make_future_index(last_date, days)
        return pd.Series([df["close"].iloc[-1]]*days, index=fut_idx)

# ---------- risk & decision helpers ----------
def categorize_risk(volatility, atr_risk):
    score = (volatility or 0) + (atr_risk or 0)
    if score < 0.2:
        return "Low"
    elif score < 0.5:
        return "Medium"
    else:
        return "High"

def decision_summary(expected_return, confidence_score, risk_category, best_pattern):
    summary = []
    if expected_return > 0:
        summary.append("Potential Buy")
    elif expected_return < 0:
        summary.append("Potential Sell")
    else:
        summary.append("Hold")
    summary.append(f"Confidence: {round(abs(confidence_score)*100,1)}%")
    summary.append(f"Risk: {risk_category}")
    if best_pattern:
        summary.append(f"Pattern: {best_pattern}")
    return " | ".join(summary)

# ---------- main function ----------
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("PredictiveAnalyticsAgent triggered")
    try:
        api_key = os.getenv("ZERODHA_API_KEY")
        access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
        price_agent_url = os.getenv("PRICE_AGENT_URL")
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("PREDICTIONS_CONTAINER", "predictive-output") 

        if not api_key or not access_token:
            return func.HttpResponse("Missing Zerodha credentials", status_code=400)
        if not price_agent_url:
            return func.HttpResponse("PRICE_AGENT_URL not set", status_code=400)
        if not conn_str:
            return func.HttpResponse("AZURE_STORAGE_CONNECTION_STRING not set", status_code=500)

        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        resp = requests.get(price_agent_url, timeout=15)
        if resp.status_code != 200:
            return func.HttpResponse(f"PriceAgent error: {resp.status_code}", status_code=500)
        portfolio = resp.json()

        blob_client_svc = BlobServiceClient.from_connection_string(conn_str)
        try: blob_client_svc.create_container(container_name)
        except Exception: pass 

        results = {}
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=365)

        pattern_strength = {
            "Bullish Marubozu": 2, "Bullish Engulfing": 2, "Morning Star": 2, "Hammer": 2,
            "Piercing Line": 1, "Bullish Harami": 1, "Bullish Kicker": 2, "Three White Soldiers": 2,
            "Upside Gap Two Crows": 1, "Bearish Marubozu": -2, "Bearish Engulfing": -2,
            "Evening Star": -2, "Shooting Star": -2, "Dark Cloud Cover": -1, "Bearish Harami": -1,
            "Bearish Kicker": -2, "Three Black Crows": -2, "Downside Gap Two Rabbits": -1,
            "Doji": 0, "Long-Legged Doji": 0
        }

        for symbol, pdata in portfolio.items():
            try:
                exchange = pdata.get("exchange", "NSE")
                instrument_key = f"{exchange}:{symbol}"
                ltp_info = kite.ltp(instrument_key)
                token_info = ltp_info.get(instrument_key)
                if not token_info:
                    results[symbol] = {"error": "ltp_missing"}
                    continue
                instrument_token = token_info.get("instrument_token")
                if not instrument_token:
                    results[symbol] = {"error": "instrument_token_missing"}
                    continue

                historical = kite.historical_data(instrument_token, start_date, end_date, interval="day")
                df = pd.DataFrame(historical)
                if df.empty:
                    results[symbol] = {"error": "no_historical"}
                    continue

                df["date"] = pd.to_datetime(df["date"])
                try: df["date"] = df["date"].dt.tz_localize(None)
                except: pass
                df.set_index("date", inplace=True)
                df = df.sort_index()
                df["close"] = df["close"].astype(float)
                if df.shape[0] < 2:
                    results[symbol] = {"error": "insufficient_history"}
                    continue

                df = calculate_indicators(df)
                last_date = df.index[-1]
                current_price = float(df["close"].iloc[-1])

                # ---------- forecasts ----------
                arima_fc = forecast_with_arima(df["close"], last_date, days=120)
                prophet_fc = forecast_with_prophet(df, last_date, days=120)
                rf_fc = forecast_with_rf(df, last_date, days=120)
                model_series = {"ARIMA": arima_fc, "Prophet": prophet_fc, "RF": rf_fc}

                last_actuals = df["close"].tail(30)
                n = len(last_actuals)
                errors = {}
                for name, series in model_series.items():
                    try:
                        if series is None or len(series) < n: continue
                        pred_vals = np.array(series.iloc[:n].astype(float))
                        act_vals = np.array(last_actuals.values.astype(float))
                        err = rmse_from_arrays(act_vals, pred_vals)
                        if err is not None:
                            errors[name] = err
                    except: continue

                best_model = min(errors, key=errors.get) if errors else None
                forecast_series = model_series.get(best_model) if best_model else prophet_fc or arima_fc or rf_fc
                forecast_avg = safe_mean(forecast_series)

                # ---------- patterns ----------
                patterns_detected = detect_patterns(df)
                best_pattern = None
                strength = 0
                if patterns_detected:
                    best_pattern = max(patterns_detected.keys(), key=lambda p: abs(pattern_strength.get(p,0)))
                    strength = pattern_strength.get(best_pattern,0)

                # ---------- expected return ----------
                expected_return = (forecast_avg - current_price)/current_price if current_price > 0 else 0
                confidence_score = 0
                if expected_return > 0 and strength > 0: confidence_score = 0.5 + 0.5 * min(1, abs(expected_return*5))
                elif expected_return < 0 and strength < 0: confidence_score = -0.5 - 0.5 * min(1, abs(expected_return*5))
                else: confidence_score = expected_return * 0.5

                # ---------- risk ----------
                df['returns'] = df['close'].pct_change().fillna(0)
                volatility = df['returns'].std() * np.sqrt(252)
                atr_risk = df['ATR14'].iloc[-1]/current_price if current_price != 0 else 0
                risk_category = categorize_risk(volatility, atr_risk)

                # ---------- decision summary ----------
                decision = decision_summary(expected_return, confidence_score, risk_category, best_pattern)
                
                # ---------- best buy/sell dates ----------
                if forecast_series is not None and not forecast_series.empty:
                    future_dates = forecast_series.index
                    future_prices = forecast_series.values
                    best_buy_idx = np.argmin(future_prices)
                    best_sell_idx = np.argmax(future_prices)
                    best_buy_date = future_dates[best_buy_idx].strftime("%Y-%m-%d")
                    best_sell_date = future_dates[best_sell_idx].strftime("%Y-%m-%d")
                else:
                    best_buy_date = None
                    best_sell_date = None

                # ---------- final output ----------
                out = {
                    "current_price": current_price,
                    "forecast_price": round(forecast_avg,2) if forecast_avg else None,
                    "expected_return_pct": round(expected_return*100,2),
                    "confidence_score": round(confidence_score,2),
                    "best_pattern": best_pattern,
                    "pattern_strength": strength,
                    "risk": {
                        "volatility": round(volatility,4) if volatility else None,
                        "atr_risk": round(atr_risk,4) if atr_risk else None,
                        "category": risk_category
                    },
                    "decision_summary": decision,
                    "best_buy_date": best_buy_date,
                    "best_sell_date": best_sell_date
                }

                results[symbol] = out

                # ---------- store in blob ----------
                date_str = datetime.utcnow().strftime('%Y%m%d')  # YYYYMMDD format
                blob_name = f"{symbol}/{date_str}.json"  # store in symbol folder, one file per day
                blob_client = blob_client_svc.get_blob_client(container=container_name, blob=blob_name)
                blob_client.upload_blob(json.dumps(out), overwrite=True)  # overwrite if file for same day exists
        # ---------- store in blob ----------
                date_str = datetime.utcnow().strftime('%Y%m%d')  # YYYYMMDD format
                blob_name = f"{symbol}/{date_str}.json"  # store in symbol folder, one file per day
                blob_client = blob_client_svc.get_blob_client(container=container_name, blob=blob_name)
                blob_client.upload_blob(json.dumps(out), overwrite=True)  # overwrite if file for same day exists

            except Exception as e:
                logging.error(f"Symbol {symbol} error: {str(e)}")
                results[symbol] = {"error": str(e)}

        # ---------- loop ends ----------
        
        # Final response: send back results AND per-symbol output
        response_payload = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "symbols_processed": list(results.keys()),
            "results": results
        }

        return func.HttpResponse(
            json.dumps(response_payload, indent=2),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

                
