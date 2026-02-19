import os
import time
import json
from kafka import KafkaProducer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")

# Create producer
producer = None
while True:
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode("utf-8")  # <-- serialize dict to JSON bytes
        )
        print("Connected to Kafka!")
        break
    except Exception as e:
        print("Waiting for Kafka to be ready...", e)
        time.sleep(3)

def send_message(topic, message: dict):
    if producer is None:
        raise Exception("Kafka producer not initialized")
    producer.send(topic, message)
    producer.flush()
