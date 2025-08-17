import logging
import os
import azure.functions as func
from kiteconnect import KiteConnect
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("PriceAgent triggered")

    try:
        api_key = os.getenv("ZERODHA_API_KEY")
        access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
        if not api_key or not access_token:
            return func.HttpResponse(
                "Missing API credentials or access token",
                status_code=400
            )

        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)

        # Get holdings
        holdings = kite.holdings()
        portfolio = {}

        for item in holdings:
            symbol = item["tradingsymbol"]
            exchange = item.get("exchange", "NSE")
            quote_key = f"{exchange}:{symbol}"

            # Get live price
            quote_data = kite.quote(quote_key)
            ltp = quote_data.get(quote_key, {}).get("last_price", None)

            portfolio[symbol] = {
                "qty": item["quantity"],
                "average_price": item["average_price"],
                "last_price": ltp
            }

        return func.HttpResponse(
            body=json.dumps(portfolio),   # ✅ proper JSON
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse(
            json.dumps({"error": f"Error fetching prices: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
