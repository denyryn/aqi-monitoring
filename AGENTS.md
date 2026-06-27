# AGENTS.md

This file is for AI coding agents (Claude Code, etc.).  
It describes the conventions, constraints, and context needed when working on this project.

## Project

AQI Monitor — Django web dashboard for XGBoost-based air quality inference.  
Reads gas sensor values (NO₂, CO, PM₁₀, PM₂.₅), predicts AQI class via trained model, stores results, displays dashboard with waffle chart + confidence trend + history table.

## Stack

- Python 3.14 / Django 5.2
- XGBoost + numpy (model inference)
- paho-mqtt (optional MQTT ingestion)
- SQLite (default)
- Chart.js (charts)
- Roboto font (Google Fonts)

## Layout

```
config/         — Django project settings
dashboard/      — single app
  ml.py         — model load + predict
  mqtt_client.py — MQTT listener daemon
  models.py     — PredictionRecord
  views.py      — index, predict, history
  templates/    — Red Broadcast design
  static/       — CSS
model/          — serialized XGBoost + class labels
```

## Key rules

- No auth — local/experimental tool
- No Bootstrap — custom Red Broadcast CSS only
- Color gradient follows danger: green → amber → orange → red → maroon → dark red
- Waffle chart colors use name-keyed map, not index
- MQTT listens on env-var topic, parses `TELEMETRY:no2,co,pm10,pm25`
- env vars: `MQTT_BROKER`, `MQTT_PORT`, `MQTT_TOPIC`
