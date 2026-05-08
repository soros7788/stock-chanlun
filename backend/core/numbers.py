"""Numeric helpers for API responses."""
from __future__ import annotations

import math


def finite_float(x, default: float = 0.0) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default
