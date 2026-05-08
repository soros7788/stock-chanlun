"""背驰检测边界：MACD 面积为 0 时不应抛异常。"""
import os
import sys
import unittest
from datetime import datetime, timedelta

import pandas as pd

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from chanlun.elements import Bi  # noqa: E402
from ai.divergence import DivergenceDetector  # noqa: E402


def _make_bi(d0: datetime, direction: str, high: float, low: float) -> Bi:
    return Bi(
        id="1",
        start=d0,
        end=d0 + timedelta(days=1),
        direction=direction,  # type: ignore[arg-type]
        high=high,
        low=low,
        start_price=low,
        end_price=high,
    )


class DivergenceZeroMacdTests(unittest.TestCase):
    def test_check_divergence_no_raise_when_macd_sum_zero(self):
        # 常数 close -> MACD 柱可全为 0
        t0 = datetime(2020, 1, 1)
        rows = []
        for i in range(30):
            d = t0 + timedelta(days=i)
            rows.append(
                {
                    "date": d,
                    "open": 10.0,
                    "high": 10.0,
                    "low": 10.0,
                    "close": 10.0,
                    "volume": 1.0,
                }
            )
        df = pd.DataFrame(rows)
        up1 = _make_bi(t0, "up", 10.0, 9.0)
        up2 = _make_bi(t0 + timedelta(days=5), "up", 10.1, 9.1)
        up3 = _make_bi(t0 + timedelta(days=10), "up", 10.2, 9.2)
        up4 = _make_bi(t0 + timedelta(days=15), "up", 10.3, 9.1)
        bis = [up1, up2, up3, up4]
        det = DivergenceDetector(df)
        # 之前 macd1==0 会 ZeroDivisionError；现应安全返回 None
        out = det.check_divergence(bis)
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()
