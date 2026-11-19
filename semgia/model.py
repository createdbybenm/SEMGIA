"""Classifiers. All models take NORMALIZED features (see processing.Calibration).

    predict(features: np.ndarray) -> int   # one window, returns config.REST / CONTRACT
"""

from collections import deque
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from semgia import config


def log_ratio(X: np.ndarray) -> np.ndarray:
    """Features are 'x times rest'. log makes 'twice as strong' the same step at any electrode gain."""
    return np.log(np.maximum(X, 1e-3))


class ThresholdModel:
    """Model A: hysteresis threshold on RMS relative to rest. Needs no training. Demo fallback."""

    def __init__(self, on: float = config.THRESHOLD_ON, off: float = config.THRESHOLD_OFF):
        self.on, self.off = on, off
        self.state = config.REST

    def predict(self, f: np.ndarray) -> int:
        rms = f[0]
        if self.state == config.REST and rms > self.on:
            self.state = config.CONTRACT
        elif self.state == config.CONTRACT and rms < self.off:
            self.state = config.REST
        return self.state

    def predict_many(self, X: np.ndarray) -> np.ndarray:
        self.state = config.REST
        return np.array([self.predict(f) for f in X])


class MLModel:
    """Model B: logistic regression (default) or random forest on all normalized features."""

    def __init__(self, kind: str = "logreg"):
        self.kind = kind
        if kind == "logreg":
            clf = LogisticRegression(class_weight="balanced")
        elif kind == "forest":
            clf = RandomForestClassifier(n_estimators=100, max_depth=6, class_weight="balanced",
                                         random_state=0)
        else:
            raise ValueError(f"unknown model kind {kind}")
        self.clf = make_pipeline(FunctionTransformer(log_ratio), StandardScaler(), clf)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MLModel":
        self.clf.fit(X, y)
        return self

    def predict(self, f: np.ndarray) -> int:
        return int(self.clf.predict(f.reshape(1, -1))[0])

    def predict_many(self, X: np.ndarray) -> np.ndarray:
        return self.clf.predict(X)

    def save(self, path: Path = config.MODELS / "model.joblib") -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: Path = config.MODELS / "model.joblib") -> "MLModel":
        return joblib.load(path)


class Smoother:
    """Majority vote over the last n predictions, so the output does not flicker."""

    def __init__(self, n: int = config.SMOOTH_N):
        self.hist = deque(maxlen=n)

    def __call__(self, pred: int) -> int:
        self.hist.append(pred)
        return int(sum(self.hist) * 2 > len(self.hist))
