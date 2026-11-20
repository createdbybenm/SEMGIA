"""Classifiers. All models take NORMALIZED features (see processing.Calibration).

    predict(features: np.ndarray) -> int   # one window, returns config.REST / CONTRACT
"""

from collections import deque
from pathlib import Path

import joblib
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
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


# The options we compare (docs/report/model_research.md, section 2). train.py and evaluation.py use this list.
ML_KINDS = ["logreg", "lda", "forest"]


class MLModel:
    """Model B: logistic regression (default), LDA or random forest on all normalized features.

    Class imbalance (rest 2/3, contraction 1/3) is handled with class weights, no resampling
    (resampling miscalibrates logistic regression: van den Goorbergh 2022, see model_research.md 3b).
    """

    def __init__(self, kind: str = "logreg"):
        self.kind = kind
        if kind == "logreg":
            # default: linear, one weight per feature (explainable); linear models drifted least
            # across days in Kaufmann 2010 (model_research.md 2)
            clf = LogisticRegression(class_weight="balanced")
        elif kind == "lda":
            # cross-check: most robust model without retraining in Kaufmann 2010, generalised better than
            # an MLP under electrode shift in Young 2011. LDA has no class_weight; equal priors are its
            # equivalent of "balanced" (the decision ignores that rest windows are twice as frequent).
            clf = LinearDiscriminantAnalysis(priors=[0.5, 0.5])
        elif kind == "forest":
            # non-linear comparison only: shows whether non-linearity helps; flexible models lost most
            # on unseen sessions in Kaufmann 2010 (model_research.md 2)
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
