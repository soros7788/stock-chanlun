"""
分型检测器 — 顶分型 & 底分型识别
"""
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Fenxing:
    """分型"""
    date: datetime
    type: Literal["top", "bottom"]
    high: float
    low: float
    index: int


class FenxingDetector:
    """
    顶分型: 中间K线高点最高、低点也最高 → 顶
    底分型: 中间K线高点最低、低点也最低 → 底
    """

    def __init__(self, klines: pd.DataFrame):
        """
        klines: DataFrame, sorted by date, columns: date/open/high/low/close/volume
        """
        self.klines = klines.reset_index(drop=True)
        self._process_inclusion()

    def _process_inclusion(self):
        """
        处理包含关系（单次遍历，缠论规则）：
        - 上升趋势中：取高高（合并K线取最高高点和最低高点）
        - 下降趋势中：取低低（合并K线取最高高点和最低低点）

        包含判断：
        - prev 包含 cur: prev.low <= cur.low AND prev.high >= cur.high
        - cur  包含 prev: cur.low  <= prev.low AND cur.high  >= prev.high
        """
        rows = self.klines.to_dict("records")
        result = [rows[0]]

        for i in range(1, len(rows)):
            cur = rows[i]
            prev = result[-1]

            # prev 包含 cur
            if prev["low"] <= cur["low"] and prev["high"] >= cur["high"]:
                direction = "up" if prev["close"] >= prev["open"] else "down"
                result[-1] = {
                    "date": prev["date"],
                    "open": prev["open"],
                    "high": max(prev["high"], cur["high"]),
                    "low": prev["low"] if direction == "up" else min(prev["low"], cur["low"]),
                    "close": cur["close"],
                    "volume": prev.get("volume", 0) + cur.get("volume", 0),
                }
            # cur 包含 prev
            elif cur["low"] <= prev["low"] and cur["high"] >= prev["high"]:
                direction = "up" if prev["close"] >= prev["open"] else "down"
                result[-1] = {
                    "date": cur["date"],
                    "open": prev["open"],
                    "high": max(prev["high"], cur["high"]),
                    "low": cur["low"] if direction == "up" else min(prev["low"], cur["low"]),
                    "close": cur["close"],
                    "volume": prev.get("volume", 0) + cur.get("volume", 0),
                }
            else:
                result.append(cur)

        self.klines = pd.DataFrame(result).reset_index(drop=True)

    def detect(self) -> list[Fenxing]:
        """识别所有分型"""
        df = self.klines
        fenxings = []

        for i in range(2, len(df)):
            seg = df.iloc[i-2:i+3]  # 取前后各2根，共5根
            if len(seg) < 5:
                continue

            # 中间是 seg.iloc[2]（第3根）
            middle = seg.iloc[2]
            left1, right1 = seg.iloc[1], seg.iloc[3]

            mid_h, mid_l = middle['high'], middle['low']

            # 顶分型
            if (mid_h > left1['high'] and mid_h > right1['high'] and
                    mid_l > left1['low'] and mid_l > right1['low']):
                fenxings.append(Fenxing(
                    date=middle['date'],
                    type="top",
                    high=float(mid_h),
                    low=float(mid_l),
                    index=i-2
                ))
            # 底分型
            elif (mid_h < left1['high'] and mid_h < right1['high'] and
                  mid_l < left1['low'] and mid_l < right1['low']):
                fenxings.append(Fenxing(
                    date=middle['date'],
                    type="bottom",
                    high=float(mid_h),
                    low=float(mid_l),
                    index=i-2
                ))

        return fenxings
