/*
 * ESP32 AQI Sensor Node
 *
 * Pins:
 *   GPIO34  — MQ-135 analog (NO₂ proxy)
 *   GPIO35  — MQ-2  analog (CO  proxy)
 *   GPIO32  — Potentiometer 1 → PM2.5 (simulated PMS5003)
 *   GPIO33  — Potentiometer 2 → PM10  (simulated PMS5003)
 *
 * Publishes JSON to MQTT topic aqi/sensor:
 *   {"no2":0.12,"co":3.4,"pm25":45,"pm10":80}
 */

#include <WiFi.h>
#include <PubSubClient.h>

// ── WiFi / MQTT ──────────────────────────────────────────────────────
const char* WIFI_SSID     = "YOUR_SSID";
const char* WIFI_PASS     = "YOUR_PASS";
const char* MQTT_BROKER   = "192.168.1.100";      // your Django server IP
const int   MQTT_PORT     = 1883;
const char* MQTT_TOPIC    = "aqi/sensor";
const char* MQTT_CLIENT_ID = "esp32-aqi-node";

// ── Pins ─────────────────────────────────────────────────────────────
const int PIN_MQ135    = 34;
const int PIN_MQ2      = 35;
const int PIN_PM25_POT = 32;
const int PIN_PM10_POT = 33;

// ── ADC config ───────────────────────────────────────────────────────
const float VREF        = 3.3;        // ESP32 ADC reference
const int   ADC_RES     = 4095;
const int   SAMPLES     = 16;         // moving-average window

// ── Sensor mapping constants (demo-calibrated) ───────────────────────
// MQ-135 output ↑ as NO₂ ↑     voltage range ≈ 0.5 – 2.8 V → 0.0 – 1.0 ppm
const float NO2_V_MIN   = 0.5;
const float NO2_V_MAX   = 2.8;
const float NO2_PPM_MAX = 1.0;

// MQ-2   output ↑ as CO  ↑     voltage range ≈ 0.3 – 2.5 V → 0 – 25 ppm
const float CO_V_MIN    = 0.3;
const float CO_V_MAX    = 2.5;
const float CO_PPM_MAX  = 25.0;

// Potentiometers: 0 – 3.3 V → 0 – 500 µg/m³ (PM2.5), 0 – 600 µg/m³ (PM10)
const float PM25_MAX    = 500.0;
const float PM10_MAX    = 600.0;

// ── Globals ──────────────────────────────────────────────────────────
WiFiClient   wifiClient;
PubSubClient mqtt(wifiClient);

unsigned long lastPub  = 0;
const unsigned long PUB_INTERVAL = 10000;   // 10 s

// circular-sample buffers
float buf_no2  [SAMPLES];
float buf_co   [SAMPLES];
float buf_pm25 [SAMPLES];
float buf_pm10 [SAMPLES];
uint8_t buf_idx = 0;
uint8_t buf_fill = 0;   // how many samples collected (< SAMPLES while warming)

// ── WiFi ─────────────────────────────────────────────────────────────
void wifi_connect() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\nWiFi OK  IP: %s\n", WiFi.localIP().toString().c_str());
}

// ── MQTT ─────────────────────────────────────────────────────────────
void mqtt_reconnect() {
  while (!mqtt.connected()) {
    Serial.print("MQTT connecting …");
    if (mqtt.connect(MQTT_CLIENT_ID)) {
      Serial.println(" OK");
    } else {
      Serial.printf(" fail (rc=%d) retry 3s\n", mqtt.state());
      delay(3000);
    }
  }
}

// ── ADC read with noise filter ───────────────────────────────────────
float read_adc(int pin, float vmin, float vmax, float out_max) {
  uint32_t sum = 0;
  for (int i = 0; i < 8; i++) sum += analogRead(pin);
  float v = (sum / 8.0) / ADC_RES * VREF;
  float clamped = constrain(v, vmin, vmax);
  float norm = (clamped - vmin) / (vmax - vmin);   // 0.0 – 1.0
  return norm * out_max;
}

// ── Sample all sensors ───────────────────────────────────────────────
void sample() {
  // ponytail: MQ curves are non-linear; linear interpolation is
  // sufficient for demo.  Replace with true sensitivity curves
  // (Rs/Ro vs ppm from datasheet) when calibrating with known gases.
  buf_no2 [buf_idx] = read_adc(PIN_MQ135,   NO2_V_MIN,  NO2_V_MAX,  NO2_PPM_MAX);
  buf_co  [buf_idx] = read_adc(PIN_MQ2,     CO_V_MIN,   CO_V_MAX,   CO_PPM_MAX);
  buf_pm25[buf_idx] = read_adc(PIN_PM25_POT, 0, VREF, PM25_MAX);
  buf_pm10[buf_idx] = read_adc(PIN_PM10_POT, 0, VREF, PM10_MAX);

  buf_idx = (buf_idx + 1) % SAMPLES;
  if (buf_fill < SAMPLES) buf_fill++;
}

// ── Moving-average helper ────────────────────────────────────────────
float avg(float* buf) {
  if (buf_fill == 0) return 0;
  float s = 0;
  for (uint8_t i = 0; i < buf_fill; i++) s += buf[i];
  return s / buf_fill;
}

// ── Setup ────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);

  // ADC attenuation for 0 – 3.3 V input range
  analogReadResolution(12);   // 0-4095
  pinMode(PIN_MQ135,    INPUT);
  pinMode(PIN_MQ2,      INPUT);
  pinMode(PIN_PM25_POT, INPUT);
  pinMode(PIN_PM10_POT, INPUT);

  wifi_connect();
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);

  Serial.println("ESP32 AQI node ready");
}

// ── Loop ─────────────────────────────────────────────────────────────
void loop() {
  if (!mqtt.connected()) mqtt_reconnect();
  mqtt.loop();

  unsigned long now = millis();
  if (now - lastPub < PUB_INTERVAL) {
    delay(100);          // prevent tight-loop watchdog
    return;
  }
  lastPub = now;

  sample();

  // Build JSON payload
  char buf[128];
  snprintf(buf, sizeof(buf),
    R"({"no2":%.2f,"co":%.1f,"pm25":%.0f,"pm10":%.0f})",
    avg(buf_no2), avg(buf_co), avg(buf_pm25), avg(buf_pm10));

  Serial.printf("Publish: %s\n", buf);
  mqtt.publish(MQTT_TOPIC, buf);
}
