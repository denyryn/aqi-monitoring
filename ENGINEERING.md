# ENGINEERING.md

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

Open http://localhost:8000

## Model

- 6-class XGBoost classifier, 4 features: no2, co, pm10, pm25
- Classes: Good, Moderate, Unhealthy for Sensitive Groups, Unhealthy, Very Unhealthy, Hazardous
- Feature order is strict (no2, co, pm10, pm25)
- Input wrapped in `np.ascontiguousarray` before predict

## MQTT

Optional. Start Mosquitto + app:

```bash
docker compose up
# or standalone:
mosquitto -d
python3 manage.py runserver
```

Publish test data:

```bash
mosquitto_pub -t aqi/sensor -m "TELEMETRY:12.45,1.20,35.5,45.2"
```

## Docker

```bash
docker compose up --build
```

Exposes port 8000 internally. Add `ports: ["8000:8000"]` to `docker-compose.yaml` for host access.

## Design

Red Broadcast design system:

- Roboto font, white backgrounds, red accent (#FF0000) reserved for confidence bars
- AQI tags color-coded by severity (green → dark red)
- Waffle chart (20×5) for class distribution
- Stat cards, tables, paginated history

## Env vars

| Var | Default | Description |
|---|---|---|
| `MQTT_BROKER` | localhost | MQTT broker host |
| `MQTT_PORT` | 1883 | MQTT broker port |
| `MQTT_TOPIC` | aqi/sensor | MQTT subscribe topic |
