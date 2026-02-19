import json
from kafka import KafkaConsumer
import time

KAFKA_BROKER = "kafka:9092"
TOPIC = "notifications"

while True:
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            auto_offset_reset='earliest',
            group_id="notifier-group",
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        print("Connected to Kafka, waiting for messages...")
        break
    except Exception as e:
        print(f"Kafka not ready yet ({e}), retrying in 3 seconds...")
        time.sleep(3)

def send_email(to_email, subject, body):
    print(f"[EMAIL] To: {to_email}, Subject: {subject}, Body: {body}")

for message in consumer:
    event = message.value
    if event["type"] == "password_change":
        send_email(event["user_email"], "Password Changed", "Your password was changed.")
    elif event["type"] == "offer_created":
        send_email(event["offeror_email"], "Offer Created", "You created a new offer.")
        send_email(event["offeree_email"], "New Offer Received", "You have a new trade offer.")
    elif event["type"] in ["offer_accepted", "offer_rejected"]:
        action = event["type"].split("_")[1]
        send_email(event["offeror_email"], f"Offer {action.title()}", f"Your offer was {action}.")
        send_email(event["offeree_email"], f"Offer {action.title()}", f"The offer was {action}.")
