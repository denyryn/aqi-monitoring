import os
import threading
import django
import paho.mqtt.client as mqtt

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from .ml import predict
from .models import PredictionRecord


def on_message(client, userdata, msg):
    """Parse TELEMETRY:no2,co,pm10,pm25 → run inference → save."""
    try:
        payload = msg.payload.decode().strip()
        # strip optional "TELEMETRY:" prefix
        if ":" in payload:
            payload = payload.split(":", 1)[1]
        parts = [float(x.strip()) for x in payload.split(",")]
        if len(parts) < 4:
            return
        no2, co, pm10, pm25 = parts[:4]
    except (ValueError, IndexError):
        return

    try:
        pred = predict(no2, co, pm10, pm25)
        PredictionRecord.objects.create(
            no2=no2, co=co, pm10=pm10, pm25=pm25,
            predicted_class=pred["class_name"],
            confidence=pred["confidence"],
            probabilities=pred["probabilities"],
        )
    except Exception:
        pass


_client = None


def get_client() -> mqtt.Client:
    global _client
    if _client is not None:
        return _client

    _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    _client.on_message = on_message

    broker = settings.MQTT_BROKER
    port = settings.MQTT_PORT
    topic = settings.MQTT_TOPIC

    try:
        _client.connect(broker, port, keepalive=60)
        _client.subscribe(topic)
        thread = threading.Thread(target=_client.loop_forever, daemon=True)
        thread.start()
    except Exception as e:
        print(f"[MQTT] connection failed: {e}")
        _client = None

    return _client
