import os
import time
import json
from kafka import KafkaConsumer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPIC = "notifications"

# Retry until Kafka is ready
while True:
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset="earliest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            group_id="email_service"
        )
        print("Connected to Kafka!")
        break
    except Exception as e:
        print("Waiting for Kafka to be ready...", e)
        time.sleep(3)

print("Email service running. Waiting for messages...")

for message in consumer:
    msg = message.value
    # Here we simulate sending email
    if msg["type"] == "password_change":
        print(f"[EMAIL] Notify {msg['user_email']} that their password was changed")
    elif msg["type"] == "offer_created":
        print(f"[EMAIL] Notify {msg['offeror_email']} and {msg['offeree_email']} about new offer")
    elif msg["type"].startswith("offer_"):
        status = msg["type"].split("_")[1]
        print(f"[EMAIL] Notify {msg['offeror_email']} and {msg['offeree_email']} that offer was {status}")
    else:
        print("[EMAIL] Unknown message type:", msg)
