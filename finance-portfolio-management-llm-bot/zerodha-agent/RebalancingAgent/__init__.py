import logging
import azure.functions as func
import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from azure.storage.blob import BlobServiceClient
from groq import Groq
import markdown2  # <-- NEW: for proper Markdown -> HTML rendering

# -------------------------------
# Groq client (use env variable)
# -------------------------------
GROQ_API_KEY = ''
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Minimum final allocation floor in percent
MIN_ALLOCATION_FLOOR_PCT = 3.0  # <-- NEW: ensure non-zero allocations

# -------------------------------
# Small utilities
# -------------------------------
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
        return 0.0
    return max(0.0, expected_return / variance)

def categorize_risk(volatility, atr_risk):
    v = float(volatility or 0)
    a = float(atr_risk or 0)
    score = v + a
    if score < 0.2:
        return "Low"
    elif score < 0.5:
        return "Medium"
    else:
        return "High"

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
    try:
        df["date"] = df["date"].dt.tz_localize(None)
    except Exception:
        pass
    df.set_index("date", inplace=True)
    df = df.sort_index()
    df["close"] = df["close"].astype(float)
    return df

def weighted_forecast(models_dict, errors_dict):
    inv_rmse = {k: (1 / v if (v and v > 0) else 0) for k, v in errors_dict.items()}
    total = sum(inv_rmse.values())
    weights = {k: inv_rmse[k] / total for k in inv_rmse} if total > 0 else {k: 1 / len(models_dict) for k in models_dict}
    forecast_combined = sum(models_dict[k] * weights.get(k, 0) for k in models_dict)
    return forecast_combined, weights

def compute_best_dates(forecast_series):
    try:
        buy_date = forecast_series.idxmin().strftime("%Y-%m-%d")
        sell_date = forecast_series.idxmax().strftime("%Y-%m-%d")
        return buy_date, sell_date
    except Exception:
        return None, None

# -------------------------------
# Predictive-output blobs
# -------------------------------
def read_latest_predictive_blob(symbol: str) -> dict:
    try:
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not conn_str:
            return {}
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        container_name = "predictive-output"
        container_client = blob_service_client.get_container_client(container_name)

        blob_names = [
            b.name for b in container_client.list_blobs(name_starts_with=f"{symbol}/")
            if b.name.endswith(".json")
        ]
        if not blob_names:
            return {}

        latest_blob = sorted(blob_names)[-1]
        blob_client = container_client.get_blob_client(latest_blob)
        data = blob_client.download_blob().readall()
        return json.loads(data)
    except Exception as e:
        logging.warning(f"[Blob] Failed to read latest predictive blob for {symbol}: {e}")
        return {}

def read_all_latest_predictive_blobs(symbols) -> dict:
    out = {}
    for sym in symbols:
        out[sym] = read_latest_predictive_blob(sym)
    return out

# -------------------------------
# Allocation logic
# -------------------------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def scale_confidence(x):
    return (clamp(x, -1.0, 1.0) + 1.0) / 2.0

def pattern_to_unit(strength):
    try:
        s = float(strength)
    except Exception:
        s = 0.0
    return clamp((s + 2.0) / 4.0, 0.0, 1.0)

def risk_to_unit(risk_category: str):
    m = {
        "Low": 1.0,
        "Medium": 0.6,
        "High": 0.3
    }
    return m.get(str(risk_category), 0.6)

def compute_allocation(expected_return: float,
                       volatility: float,
                       confidence: float,
                       pattern_strength: float,
                       risk_category: str) -> float:
    pos_er = max(float(expected_return or 0.0), 0.0)
    vol = float(volatility or 0.0)
    vol_factor = 1.0 / (1.0 + 10.0 * max(vol, 0.0))
    conf_unit = scale_confidence(float(confidence or 0.0))
    conf_factor = 0.5 + 0.5 * conf_unit
    patt_unit = pattern_to_unit(pattern_strength)
    patt_factor = 0.5 + 0.5 * patt_unit
    risk_factor = risk_to_unit(risk_category)
    base = 100.0 * pos_er
    raw = base * vol_factor * conf_factor * patt_factor * risk_factor
    return float(clamp(raw, 0.0, 100.0))

# -------------------------------
# Groq LLM
# -------------------------------
def query_groq(user_prompt: str, context: dict) -> str:
    if not groq_client:
        return "Groq API key not configured. Please set GROQ_API_KEY."
    try:
        content = (
            "You are a helpful trading assistant. "
            "Use the provided JSON data to justify specific, concise answers. "
            "Prefer INR figures. If data is missing, state assumptions clearly.\n\n"
            f"CONTEXT JSON:\n{json.dumps(context, indent=2)}\n\n"
            f"USER QUESTION: {user_prompt}"
        )
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a precise, no-hype trading copilot focused on clarity and risk."},
                {"role": "user", "content": content}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Groq error: {e}")
        return f"(Groq error: {e})"

# -------------------------------
# Core rebalancing
# -------------------------------
def compute_rebalance(symbol, df, forecast_models, pattern_strength_map,
                      volatility_lookback=30, final_allocation_pct=None):
    current_price = float(df["close"].iloc[-1])
    last_actuals = df["close"].tail(volatility_lookback)
    n = len(last_actuals)

    errors = {}
    for name, series in forecast_models.items():
        try:
            if series is None or len(series) < n:
                continue
            pred_vals = np.array(series.iloc[:n].astype(float))
            act_vals = np.array(last_actuals.values.astype(float))
            err = rmse_from_arrays(act_vals, pred_vals)
            if err is not None:
                errors[name] = err
        except Exception:
            continue

    forecast_series, model_weights = weighted_forecast(forecast_models, errors)
    forecast_avg = safe_mean(forecast_series)

    dir_acc = {}
    for name, series in forecast_models.items():
        try:
            dir_acc[name] = directional_accuracy(last_actuals.values, series.iloc[:n].values)
        except Exception:
            dir_acc[name] = None

    df["returns"] = df["close"].pct_change().fillna(0)
    volatility = float(df["returns"].std() * np.sqrt(252))
    atr_risk = float(df["close"].diff().abs().rolling(14, min_periods=1).mean().iloc[-1] / current_price) if current_price > 0 else 0.0
    risk_category = categorize_risk(volatility, atr_risk)

    buy_date, sell_date = compute_best_dates(forecast_series)
    expected_return = (forecast_avg - current_price) / current_price if current_price > 0 else 0.0
    confidence_score = float(expected_return or 0.0)

    best_pattern = None
    strength = 0.0
    try:
        if isinstance(pattern_strength_map, dict) and pattern_strength_map:
            best_pattern = max(pattern_strength_map.keys(), key=lambda p: abs(pattern_strength_map.get(p, 0)))
            strength = float(pattern_strength_map.get(best_pattern, 0))
    except Exception:
        pass

    result = {
        "current_price": current_price,
        "forecast_price": round(forecast_avg, 2) if forecast_avg is not None else None,
        "expected_return_pct": round((expected_return or 0.0) * 100.0, 2),
        "weighted_confidence": round(confidence_score, 4),
        "best_buy_date": buy_date,
        "best_sell_date": sell_date,
        "risk_category": risk_category,
        "pattern_detected": best_pattern,
        "pattern_strength": strength,
        "directional_accuracy": dir_acc,
        "rmse_accuracy": errors,
        "model_weights": model_weights,
    }

    if final_allocation_pct is not None:
        result["final_allocation_pct"] = round(final_allocation_pct, 2)

    return result

# -------------------------------
# Azure Function: main
# -------------------------------
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("RebalancingAgent + PredictiveAnalytics + Groq triggered")
    try:
        body = req.get_json()
    except Exception:
        body = {}

    user_prompt = body.get("prompt", "")
    symbol_filter = body.get("symbol", None)

    try:
        api_key = os.getenv("ZERODHA_API_KEY")
        access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
        price_agent_url = os.getenv("PRICE_AGENT_URL")
        if not api_key or not access_token:
            return func.HttpResponse("Missing Zerodha credentials", status_code=400)
        if not price_agent_url:
            return func.HttpResponse("PRICE_AGENT_URL not set", status_code=400)

        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        portfolio = fetch_portfolio(price_agent_url)
        if symbol_filter:
            one = portfolio.get(symbol_filter)
            portfolio = {symbol_filter: one} if one is not None else {}
        if not portfolio:
            return func.HttpResponse(json.dumps({"error": "Empty portfolio or symbol not found"}), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(f"Init error: {e}")
        return func.HttpResponse(f"Init error: {e}", status_code=500)

    symbols = list(portfolio.keys())

    paa_http_all = {}
    try:
        paa_res = requests.get("http://localhost:7071/api/PredictiveAnalyticsAgent", timeout=10)
        if paa_res.status_code == 200:
            paa_http_all = paa_res.json()
    except Exception as e:
        logging.warning(f"PAA HTTP fetch failed: {e}")

    paa_blob_latest_by_symbol = read_all_latest_predictive_blobs(symbols)
    pattern_strength_map = {}

    results = {}
    raw_allocations = {}

    for symbol in symbols:
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=365)
            df = fetch_historical(kite, symbol, start_date, end_date)

            forecast_models = {
                "ARIMA": df["close"],
                "Prophet": df["close"],
                "RF": df["close"]
            }

            agent_data = compute_rebalance(symbol, df, forecast_models, pattern_strength_map)

            vol = float(df["close"].pct_change().std())
            expected_return = float(agent_data.get("expected_return_pct", 0.0)) / 100.0
            confidence = float(agent_data.get("weighted_confidence", 0.0))
            patt_strength = float(agent_data.get("pattern_strength", 0.0))
            risk_category = agent_data.get("risk_category", "Medium")

            raw_alloc = compute_allocation(
                expected_return=expected_return,
                volatility=vol,
                confidence=confidence,
                pattern_strength=patt_strength,
                risk_category=risk_category
            )
            raw_allocations[symbol] = max(0.0, raw_alloc)

            results[symbol] = agent_data

        except Exception as e:
            logging.error(f"Symbol {symbol} error: {e}")
            results[symbol] = {"error": str(e)}

    # -------------------------------
    # Normalize with a minimum floor (>= 3% each) and sum ~ 100%
    # -------------------------------
    valid_symbols = [s for s in results.keys() if "error" not in results[s]]
    n = len(valid_symbols)

    if n > 0:
        total_raw = sum(raw_allocations.get(s, 0.0) for s in valid_symbols)

        # Baseline allocations
        if total_raw > 0:
            baseline = {s: (raw_allocations.get(s, 0.0) / total_raw) * 100.0 for s in valid_symbols}
        else:
            # If no signal at all, split equally
            baseline = {s: 100.0 / n for s in valid_symbols}

        # Floor handling (3% each, or fallback to 100/n if 3%*n > 100)
        floor_pct = MIN_ALLOCATION_FLOOR_PCT
        if floor_pct * n > 100.0:
            floor_pct = 100.0 / n

        # Apply floor
        allocations = {s: max(baseline[s], floor_pct) for s in valid_symbols}
        sum_alloc = sum(allocations.values())

        # If sum > 100, cut proportionally from those above the floor
        if sum_alloc > 100.0:
            excess = sum_alloc - 100.0
            above_floor = {s: allocations[s] - floor_pct for s in valid_symbols if allocations[s] > floor_pct}
            total_above = sum(above_floor.values())
            if total_above > 1e-9:
                for s in above_floor:
                    cut = excess * (above_floor[s] / total_above)
                    allocations[s] = max(floor_pct, allocations[s] - cut)
            else:
                # All are at floor (should only happen if floor == 100/n)
                allocations = {s: 100.0 / n for s in valid_symbols}

        # If sum < 100, scale up proportionally (keeps all >= floor)
        sum_alloc = sum(allocations.values())
        if sum_alloc < 100.0 and sum_alloc > 0:
            scale = 100.0 / sum_alloc
            allocations = {s: allocations[s] * scale for s in valid_symbols}

        # Round and set on results
        for s in valid_symbols:
            results[s]["final_allocation_pct"] = round(allocations[s], 2)

        # Any error symbols get 0 allocation (kept as-is)
        for s in results.keys():
            if s not in valid_symbols:
                results[s]["final_allocation_pct"] = 0.0
    else:
        # No valid symbols; keep zeros (should be rare)
        for s in results.keys():
            results[s]["final_allocation_pct"] = 0.0

    # -------------------------------
    # Prepare context AFTER allocation is ready and query Groq
    # Also convert GPT reply to HTML using markdown2
    # -------------------------------
    for symbol in results.keys():
        # Skip GPT query for error entries
        if "error" in results[symbol]:
            continue

        paa_http_symbol = paa_http_all.get(symbol, {})
        paa_blob_symbol = paa_blob_latest_by_symbol.get(symbol, {})
        context = {
            "symbol": symbol,
            "rebalancing_data": results[symbol],
            "predictive_data": {
                "http_all_symbols": paa_http_all,
                "http_this_symbol": paa_http_symbol,
                "blob_latest": paa_blob_symbol
            }
        }

        gpt_reply = query_groq(user_prompt, context)
        results[symbol]["gpt_reply"] = gpt_reply

        # NEW: HTML-rendered Markdown for UI consumption
        try:
            results[symbol]["gpt_reply_html"] = markdown2.markdown(
                gpt_reply or "",
                extras=[
                    "fenced-code-blocks",
                    "tables",
                    "strike",
                    "code-friendly",
                    "smarty-pants"
                ]
            )
        except Exception as e:
            logging.warning(f"Markdown2 conversion failed for {symbol}: {e}")
            results[symbol]["gpt_reply_html"] = gpt_reply or ""

    return func.HttpResponse(json.dumps(results), status_code=200, mimetype="application/json")
