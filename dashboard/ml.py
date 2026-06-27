import os
import numpy as np
import xgboost as xgb

_model = None
_classes = None


def load_model():
    global _model, _classes
    base = os.path.join(os.path.dirname(__file__), "..", "model")
    model_path = os.path.join(base, "xgboost_mq_only_model.json")

    _model = xgb.XGBClassifier()
    _model.load_model(model_path)

    classes_path = os.path.join(base, "mq_classes.npy")
    _classes = np.load(classes_path, allow_pickle=True).tolist()


def predict(no2: float, co: float, pm10: float, pm25: float) -> dict:
    if _model is None:
        load_model()

    X = np.array([[no2, co, pm10, pm25]], dtype=np.float32)
    X = np.ascontiguousarray(X)

    pred_idx = int(_model.predict(X)[0])
    proba = _model.predict_proba(X)[0].tolist()

    return {
        "class_name": _classes[pred_idx],
        "class_index": pred_idx,
        "confidence": max(proba),
        "probabilities": {name: round(p, 4) for name, p in zip(_classes, proba)},
    }
