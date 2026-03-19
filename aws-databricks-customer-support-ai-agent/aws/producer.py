import boto3, json, uuid, random, time, threading
from datetime import datetime

# AWS Client
client = boto3.client("events", region_name="us-east-1")

# Order lifecycle
ORDER_FLOW = ["CREATED", "CONFIRMED", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"]

# Shared state
orders_db = {}
lock = threading.Lock()

# -----------------------------
# COMMON EVENT SENDER
# -----------------------------
def send_event(source, detail_type, detail):
    try:
        client.put_events(
            Entries=[{
                "Source": source,
                "DetailType": detail_type,
                "Detail": json.dumps(detail),
                "EventBusName": "orders-pipeline-event-bus"
            }]
        )
        print(f"{source} → {detail_type} | {detail.get('order_id', '')}")
    except Exception as e:
        print("Error:", e)


# -----------------------------
# ORDER SERVICE
# -----------------------------
def order_service():
    while True:
        with lock:
            # Create or update order
            if not orders_db or random.random() < 0.4:
                order_id = str(uuid.uuid4())
                orders_db[order_id] = {
                    "order_id": order_id,
                    "customer_id": f"C{random.randint(1000,9999)}",
                    "product_id": f"P{random.randint(100,999)}",
                    "amount": round(random.uniform(100, 2000), 2),
                    "payment_method": random.choice(["CARD", "UPI"]),
                    "status_index": 0,
                    "created_at": str(datetime.utcnow())
                }
            else:
                order = random.choice(list(orders_db.values()))
                if order["status_index"] < len(ORDER_FLOW) - 1:
                    order["status_index"] += 1

            order = random.choice(list(orders_db.values()))

        status = ORDER_FLOW[order["status_index"]]

        event = {
            "order_id": order["order_id"],
            "customer_id": order["customer_id"],
            "product_id": order["product_id"],
            "order_status": status,
            "order_amount": order["amount"],
            "currency": "INR",
            "payment_method": order["payment_method"],
            "payment_status": order.get("payment_status", "PENDING"),
            "shipping_address": "Bangalore",
            "billing_address": "Bangalore",
            "order_date": order["created_at"],
            "delivery_date": str(datetime.utcnow()),
            "discount": round(random.uniform(0, 200), 2),
            "tax": round(random.uniform(10, 200), 2),
            "shipping_cost": round(random.uniform(20, 100), 2),
            "quantity": random.randint(1, 5),
            "seller_id": f"S{random.randint(100,999)}",
            "warehouse_id": f"W{random.randint(1,10)}",
            "region": "IN",
            "city": "Bangalore",
            "pincode": "560001",
            "device_type": random.choice(["mobile", "web"]),
            "browser": "Chrome",
            "ip_address": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
            "is_gift": random.choice([True, False]),
            "gift_message": "Happy Birthday",
            "coupon_code": random.choice(["SALE20", "NEWUSER", None]),
            "loyalty_points_used": random.randint(0, 200),
            "order_channel": random.choice(["APP", "WEB"]),
            "fulfillment_type": random.choice(["STANDARD", "EXPRESS"]),
            "delivery_partner": "Delhivery",
            "status_timestamp": str(datetime.utcnow()),
            "created_at": order["created_at"],
            "updated_at": str(datetime.utcnow())
        }

        send_event("orders.service", "OrderStatusChanged", event)
        time.sleep(random.uniform(0,0.1))


# -----------------------------
# PAYMENT SERVICE
# -----------------------------
def payment_service():
    while True:
        with lock:
            if not orders_db:
                continue
            order = random.choice(list(orders_db.values()))

        if order["status_index"] > 1:
            time.sleep(2)
            continue

        status = random.choice(["SUCCESS", "FAILED"])

        event = {
            "payment_id": str(uuid.uuid4()),
            "order_id": order["order_id"],
            "customer_id": order["customer_id"],
            "payment_status": status,
            "payment_method": order["payment_method"],
            "amount": order["amount"],
            "currency": "INR",
            "transaction_time": str(datetime.utcnow()),
            "gateway": "Razorpay",
            "bank_name": "HDFC",
            "card_type": random.choice(["VISA", "MASTERCARD"]),
            "card_last4": str(random.randint(1000,9999)),
            "upi_id": "user@upi",
            "failure_reason": "Insufficient funds" if status == "FAILED" else None,
            "retry_count": random.randint(0, 3),
            "is_refund": False,
            "refund_amount": 0,
            "refund_status": None,
            "fraud_score": round(random.uniform(0, 1), 2),
            "risk_level": random.choice(["LOW", "MEDIUM", "HIGH"]),
            "ip_address": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
            "device_id": str(uuid.uuid4()),
            "location": "India",
            "lat": 12.97,
            "lon": 77.59,
            "network_type": random.choice(["4G", "5G", "WiFi"]),
            "app_version": "1.0.0",
            "os": random.choice(["Android", "iOS"]),
            "browser": "Chrome",
            "created_at": str(datetime.utcnow()),
            "updated_at": str(datetime.utcnow())
        }

        send_event("payments.service", "PaymentProcessed", event)
        time.sleep(random.uniform(2, 4))


# -----------------------------
# SHIPMENT SERVICE
# -----------------------------
def shipment_service():
    while True:
        with lock:
            if not orders_db:
                continue
            order = random.choice(list(orders_db.values()))

        if order["status_index"] < 2:
            time.sleep(2)
            continue

        event = {
            "shipment_id": str(uuid.uuid4()),
            "order_id": order["order_id"],
            "carrier": "Delhivery",
            "tracking_number": f"TRK{random.randint(100000,999999)}",
            "status": ORDER_FLOW[order["status_index"]],
            "origin": "Mumbai",
            "destination": "Bangalore",
            "dispatch_time": str(datetime.utcnow()),
            "delivery_time": str(datetime.utcnow()),
            "estimated_delivery": str(datetime.utcnow()),
            "delay_reason": random.choice([None, "Weather", "Traffic"]),
            "warehouse_id": f"W{random.randint(1,10)}",
            "hub_id": f"H{random.randint(1,5)}",
            "route": "Mumbai-BLR",
            "distance_km": random.randint(100, 2000),
            "weight": round(random.uniform(0.5, 5), 2),
            "volume": round(random.uniform(0.1, 1), 2),
            "shipping_cost": round(random.uniform(50, 200), 2),
            "driver_id": f"D{random.randint(100,999)}",
            "vehicle_id": f"V{random.randint(100,999)}",
            "fuel_cost": round(random.uniform(10, 50), 2),
            "temperature": round(random.uniform(20, 40), 2),
            "humidity": round(random.uniform(30, 80), 2),
            "gps_lat": 12.97,
            "gps_lon": 77.59,
            "current_location": "Bangalore",
            "attempts": random.randint(1, 3),
            "delivery_status": random.choice(["SUCCESS", "FAILED"]),
            "signature_required": random.choice([True, False]),
            "priority": random.choice(["NORMAL", "HIGH"]),
            "created_at": str(datetime.utcnow()),
            "updated_at": str(datetime.utcnow())
        }

        send_event("logistics.service", "ShipmentUpdate", event)
        time.sleep(random.uniform(2, 5))


# -----------------------------
# TICKET SERVICE
# -----------------------------
def ticket_service():
    while True:
        with lock:
            if not orders_db:
                continue
            order = random.choice(list(orders_db.values()))

        if random.random() > 0.2:
            time.sleep(3)
            continue

        event = {
            "ticket_id": str(uuid.uuid4()),
            "order_id": order["order_id"],
            "customer_id": order["customer_id"],
            "issue_type": random.choice(["DELAY", "PAYMENT", "DAMAGED"]),
            "description": "Customer reported issue",
            "priority": random.choice(["LOW", "MEDIUM", "HIGH"]),
            "status": "OPEN",
            "channel": random.choice(["CHAT", "EMAIL", "CALL"]),
            "created_at": str(datetime.utcnow()),
            "updated_at": str(datetime.utcnow()),
            "resolved_at": None,
            "agent_id": f"A{random.randint(100,999)}",
            "resolution": None,
            "sla_hours": random.randint(24, 72),
            "response_time": random.randint(1, 10),
            "customer_satisfaction": None,
            "category": "Logistics",
            "sub_category": "Delay",
            "region": "IN",
            "city": "Bangalore",
            "pincode": "560001",
            "device_type": random.choice(["mobile", "web"]),
            "browser": "Chrome",
            "app_version": "2.0",
            "tags": ["delay"],
            "is_escalated": random.choice([True, False]),
            "escalation_level": random.randint(0, 3),
            "first_response_time": random.randint(1, 5),
            "closure_code": None,
            "language": "EN",
            "created_by": "customer"
        }

        send_event("support.service", "TicketCreated", event)
        time.sleep(random.uniform(3, 6))


# -----------------------------
# USER ACTIVITY SERVICE
# -----------------------------
def user_activity_service():
    while True:
        event = {
            "event_id": str(uuid.uuid4()),
            "user_id": f"U{random.randint(1000,9999)}",
            "session_id": str(uuid.uuid4()),
            "event_type": random.choice(["CLICK", "VIEW", "PURCHASE"]),
            "page_url": random.choice(["/home", "/product", "/checkout"]),
            "referrer": "google.com",
            "device_type": random.choice(["mobile", "web"]),
            "os": random.choice(["Android", "iOS"]),
            "browser": "Chrome",
            "ip_address": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
            "location": "India",
            "lat": 12.97,
            "lon": 77.59,
            "screen_resolution": "1080x1920",
            "app_version": "2.1",
            "network": random.choice(["WiFi", "4G"]),
            "load_time": round(random.uniform(0.1, 3), 2),
            "click_x": random.randint(0, 1080),
            "click_y": random.randint(0, 1920),
            "scroll_depth": round(random.uniform(0, 100), 2),
            "time_on_page": random.randint(1, 300),
            "conversion": random.choice([True, False]),
            "campaign_id": "CMP123",
            "ad_id": "AD456",
            "experiment_id": "EXP1",
            "feature_flag": "new_ui",
            "error_code": None,
            "error_message": None,
            "device_id": str(uuid.uuid4()),
            "created_at": str(datetime.utcnow())
        }

        send_event("analytics.service", "UserActivity", event)
        time.sleep(random.uniform(0.5, 2))


# -----------------------------
# START THREADS
# -----------------------------
threads = [
    threading.Thread(target=order_service),
    threading.Thread(target=payment_service),
    threading.Thread(target=shipment_service),
    threading.Thread(target=ticket_service),
    threading.Thread(target=user_activity_service),
]

for t in threads:
    t.start()

for t in threads:
    t.join()    