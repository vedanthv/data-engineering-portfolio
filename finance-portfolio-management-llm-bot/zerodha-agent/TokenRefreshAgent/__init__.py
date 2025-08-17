import logging
import os
import azure.functions as func
from kiteconnect import KiteConnect

def main(mytimer: func.TimerRequest) -> None:
    logging.info("TokenRefreshAgent triggered.")

    try:
        api_key = os.getenv("ZERODHA_API_KEY")
        api_secret = os.getenv("ZERODHA_API_SECRET")
        request_token = os.getenv("ZERODHA_REQUEST_TOKEN")

        if not api_key or not api_secret or not request_token:
            logging.error("Missing API credentials")
            return

        # Initialize KiteConnect
        kite = KiteConnect(api_key=api_key)

        # Generate access token
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data.get("access_token")

        if access_token:
            logging.info(f"Access token refreshed: {access_token}")

            # Store in environment variable for local testing
            os.environ["ZERODHA_ACCESS_TOKEN"] = access_token

        else:
            logging.error(f"Failed to refresh token: {data}")

    except Exception as e:
        logging.error(str(e))
