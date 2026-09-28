"""Model wrapper (plan §3.4).

Trains on (features, label) pairs from a training window; predicts on a test
window. Logistic regression — deliberately simple.

This wrapper uses scikit-learn's LogisticRegression *if it is installed*, and
otherwise falls back to a small, self-contained NumPy implementation. Either way
the public interface is identical:

    m = LogisticRegressionModel()
    m.fit(X, y)            # X: 2D array-like, y: 0/1 labels
    p = m.predict_proba(X) # 1D array of P(label = 1)

Keeping a zero-dependency fallback means the harness runs before the heavy deps
are installed, and the leakage tests don't need sklearn in CI.
"""

from __future__ import annotations

import numpy as np

try:  # prefer sklearn when available (plan §8)
    from sklearn.linear_model import LogisticRegression as _SkLR
    _HAVE_SKLEARN = True
except Exception:  # pragma: no cover - environment dependent
    _HAVE_SKLEARN = False


class _NumpyLogReg:
    """Plain L2-regularized logistic regression via gradient descent.

    Standardizes inputs; handles the degenerate single-class case by predicting
    the (smoothed) base rate so the harness never crashes on a trivial window.
    """

    def __init__(self, lr: float = 0.1, n_iter: int = 2000, l2: float = 1e-3):
        self.lr, self.n_iter, self.l2 = lr, n_iter, l2
        self.w = None
        self.b = 0.0
        self.mu = None
        self.sigma = None
        self._const_prob = None

    @staticmethod
    def _sigmoid(z):
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float).ravel()
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        classes = np.unique(y)
        if len(classes) < 2:
            # Only one class present — predict smoothed base rate.
            self._const_prob = float((y.sum() + 0.5) / (len(y) + 1.0))
            return self

        self.mu = X.mean(axis=0)
        self.sigma = X.std(axis=0)
        self.sigma[self.sigma == 0] = 1.0
        Xs = (X - self.mu) / self.sigma

        n, d = Xs.shape
        self.w = np.zeros(d)
        self.b = 0.0
        for _ in range(self.n_iter):
            p = self._sigmoid(Xs @ self.w + self.b)
            err = p - y
            grad_w = Xs.T @ err / n + self.l2 * self.w
            grad_b = err.mean()
            self.w -= self.lr * grad_w
            self.b -= self.lr * grad_b
        return self

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if self._const_prob is not None:
            return np.full(X.shape[0], self._const_prob)
        Xs = (X - self.mu) / self.sigma
        return self._sigmoid(Xs @ self.w + self.b)


class LogisticRegressionModel:
    """Uniform interface over sklearn or the numpy fallback."""

    def __init__(self, **kwargs):
        if _HAVE_SKLEARN:
            self._impl = _SkLR(max_iter=1000, C=1.0)
            self._backend = "sklearn"
        else:
            self._impl = _NumpyLogReg(**kwargs)
            self._backend = "numpy"
        self._single_class_prob = None

    @property
    def backend(self) -> str:
        return self._backend

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y).ravel()
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if _HAVE_SKLEARN and len(np.unique(y)) < 2:
            # sklearn refuses single-class fits; mimic the numpy fallback.
            self._single_class_prob = float((y.sum() + 0.5) / (len(y) + 1.0))
            return self
        self._impl.fit(X, y)
        return self

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if self._single_class_prob is not None:
            return np.full(X.shape[0], self._single_class_prob)
        if _HAVE_SKLEARN:
            return self._impl.predict_proba(X)[:, 1]
        return self._impl.predict_proba(X)
