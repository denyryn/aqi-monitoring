import os
import json
import logging
import threading
import django
import paho.mqtt.client as mqtt

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from .ml import predict
from .models import PredictionRecord

logger = logging.getLogger(__name__)


def _parse(payload: str):
    """Return (no2, co, pm10, pm25) from CSV or JSON payload."""
    payload = payload.strip()
    # strip optional "TELEMETRY:" prefix (legacy CSV)
    if payload.startswith("TELEMETRY:"):
        payload = payload.split(":", 1)[1].strip()

    if payload.startswith("{"):
        data = json.loads(payload)
        return (
            float(data["no2"]),
            float(data["co"]),
            float(data["pm10"]),
            float(data["pm25"]),
        )
    # fallback: CSV
    parts = [float(x.strip()) for x in payload.split(",")]
    if len(parts) < 4:
        raise ValueError("need at least 4 values")
    return parts[:4]


def on_message(client, userdata, msg):
    """Parse CSV or JSON payload → run inference → save."""
    try:
        payload = msg.payload.decode().strip()
        no2, co, pm10, pm25 = _parse(payload)
    except (ValueError, IndexError, KeyError):
        logger.warning("Failed to parse payload: %s", payload[:80])
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
        logger.exception("Failed to process MQTT message")


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
        logger.error("MQTT connection failed: %s", e)
        _client = None

    return _client
