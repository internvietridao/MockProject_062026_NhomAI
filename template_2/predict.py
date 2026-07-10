import joblib
import pandas as pd

from config import MODEL_PATH


def predict(sample: dict):
    model = joblib.load(MODEL_PATH)
    data = pd.DataFrame([sample])

    result = {
        "prediction": model.predict(data)[0],
    }

    if hasattr(model, "predict_proba"):
        result["probabilities"] = dict(
            zip(model.classes_, model.predict_proba(data)[0])
        )

    return result
