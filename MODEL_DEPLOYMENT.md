# Air Quality Monitor IoT - Deployment & Inference Specification

This documentation outlines the operational parameters and implementation specifications for deploying the trained XGBoost air quality classifier model. The model acts as the real-time inference engine for an ESP32 edge microcontroller station simulated within TinkerCad.

---

## 1. Core Model Metadata

- **Architecture:** XGBoost Classifier (`XGBClassifier`) serialized into native JSON format.
- **Accuracy:** **99% Legitimate Generalization Accuracy** across a 20,000-row unseen evaluation slice.
- **Behavior:** The model maps raw physical gas and particulate matter concentrations into standard environmental health classifications using non-linear decision thresholds.

---

## 2. Input Specifications (The Feature Vector)

The model expects an input matrix or DataFrame consisting of **exactly 4 features**.

> ⚠️ **CRITICAL DEVELOPMENT RULES:**
>
> 1. **Feature Sequence is Strict:** The features must be ordered exactly as shown in the table below. Rearranging columns will cause silent, catastrophic prediction failures.
> 2. **Prevent Hardware Warning Spam:** Wrap your input data structure in `np.ascontiguousarray(X)` directly inside the `.predict()` call to match device memory layout and maintain fast inference speeds.

### Feature Mapping Matrix

| Index | Feature Key | Description / Physical Source                                    |       Unit        | Target Range Bounds |
| :---: | :---------- | :--------------------------------------------------------------- | :---------------: | :-----------------: |
| **0** | `no2`       | Nitrogen Dioxide Concentration (from Gas Sensor 1 / MQ-135)      |        ppm        |  `0.00 -> 50.00+`   |
| **1** | `co`        | Carbon Monoxide Concentration (from Gas Sensor 2 / MQ-2)         |        ppm        |  `0.00 -> 100.00+`  |
| **2** | `pm25`      | Particulate Matter $\le 2.5\,\mu\text{m}$ (from Potentiometer 1) | $\mu\text{g/m}^3$ |   `0.0 -> 400.0+`   |
| **3** | `pm10`      | Particulate Matter $\le 10\,\mu\text{m}$ (from Potentiometer 2)  | $\mu\text{g/m}^3$ |   `0.0 -> 500.0+`   |

---

## 3. Inbound Telemetry Stream Protocol

The simulated ESP32 in TinkerCad transmits processed physical data over the serial interface every 2000ms. The string payload arrives over the COM/tty port matching this exact pattern:

```text
TELEMETRY:12.45,1.20,35.5,45.2
```
