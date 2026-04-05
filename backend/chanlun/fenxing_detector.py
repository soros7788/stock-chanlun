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
        - 两K线包含：prev 和 cur 任一完全包含另一根
        - 合并方向由两根K线的相对位置决定（不是由单根自身阴阳决定）：
            如果 prev 的最高点 ≤ cur 的最低点 → 向上关系 → 取高高（保留最高高点，合并高低点取高）
            否则（prev 的最低点 ≥ cur 的最高点）→ 向下关系 → 取低低（保留最低低点，合并高低点取低）

        包含判断：
        - prev 包含 cur: prev.low <= cur.low AND prev.high >= cur.high
        - cur  包含 prev: cur.low  <= prev.low AND cur.high  >= prev.high
        """
        rows = self.klines.to_dict("records")
        result = [rows[0]]

        for i in range(1, len(rows)):
            cur  = rows[i]
            prev = result[-1]

            # prev 包含 cur
            if prev["low"] <= cur["low"] and prev["high"] >= cur["high"]:
                if prev["high"] <= cur["low"]:
                    # 向上关系：prev 在 cur 下方 → 取高高
                    result[-1] = {
                        "date": prev["date"],
                        "open":  prev["open"],
                        "high":  max(prev["high"], cur["high"]),
                        "low":   max(prev["low"],  cur["low"]),
                        "close": cur["close"],
                        "volume": prev.get("volume", 0) + cur.get("volume", 0),
                    }
                else:
                    # 向下关系：prev 在 cur 上方 → 取低低
                    result[-1] = {
                        "date": prev["date"],
                        "open":  prev["open"],
                        "high":  max(prev["high"], cur["high"]),
                        "low":   min(prev["low"],  cur["low"]),
                        "close": cur["close"],
                        "volume": prev.get("volume", 0) + cur.get("volume", 0),
                    }
            # cur 包含 prev
            elif cur["low"] <= prev["low"] and cur["high"] >= prev["high"]:
                if prev["high"] <= cur["low"]:
                    # 向上关系
                    result[-1] = {
                        "date": cur["date"],
                        "open":  prev["open"],
                        "high":  max(prev["high"], cur["high"]),
                        "low":   max(prev["low"],  cur["low"]),
                        "close": cur["close"],
                        "volume": prev.get("volume", 0) + cur.get("volume", 0),
                    }
                else:
                    # 向下关系
                    result[-1] = {
                        "date": cur["date"],
                        "open":  prev["open"],
                        "high":  max(prev["high"], cur["high"]),
                        "low":   min(prev["low"],  cur["low"]),
                        "close": cur["close"],
                        "volume": prev.get("volume", 0) + cur.get("volume", 0),
                    }
            else:
                result.append(cur)

        self.klines = pd.DataFrame(result).reset_index(drop=True)

    def detect(self) -> list[Fenxing]:
        """
        识别所有分型（标准五笔窗口）：
        顶分型 = 中间K线高点 > 左1 且 > 右1，且低点 > 左1 且 > 右1
        底分型 = 中间K线高点 < 左1 且 < 右1，且低点 < 左1 且 < 右1
        窗口取前后各1根（共3根），严格对应缠论标准定义。
        """
        df = self.klines
        fenxings = []

        for i in range(1, len(df) - 1):
            prev = df.iloc[i - 1]
            middle = df.iloc[i]
            next_ = df.iloc[i + 1]

            mid_h, mid_l = middle['high'], middle['low']

            # 顶分型：中间K线"高"最高、"低"也最高（∧形）
            if (mid_h > prev['high'] and mid_h > next_['high'] and
                    mid_l > prev['low'] and mid_l > next_['low']):
                fenxings.append(Fenxing(
                    date=middle['date'],
                    type="top",
                    high=float(mid_h),
                    low=float(mid_l),
                    index=i
                ))
            # 底分型：中间K线"高"最低、"低"也最低（∨形）
            elif (mid_h < prev['high'] and mid_h < next_['high'] and
                  mid_l < prev['low'] and mid_l < next_['low']):
                fenxings.append(Fenxing(
                    date=middle['date'],
                    type="bottom",
                    high=float(mid_h),
                    low=float(mid_l),
                    index=i
                ))

        return fenxings
