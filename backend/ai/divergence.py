"""
背驰自动判断 — MACD面积 + RSI/KDJ背离检测
"""
import pandas as pd
import numpy as np
from typing import Optional
from chanlun.elements import MACDData, PowerMetrics, Bi


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    """
    计算 MACD 指标
    返回 DataFrame 追加 dif/dea/bar 列
    """
    df = df.copy()
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    df['dif'] = ema_fast - ema_slow
    df['dea'] = df['dif'].ewm(span=signal, adjust=False).mean()
    df['bar'] = (df['dif'] - df['dea']) * 2
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算 RSI"""
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def calculate_kdj(
    df: pd.DataFrame,
    n: int = 9,
    m1: int = 3,
    m2: int = 3
) -> pd.DataFrame:
    """计算 KDJ 指标"""
    df = df.copy()
    low_n = df['low'].rolling(n, min_periods=1).min()
    high_n = df['high'].rolling(n, min_periods=1).max()
    rsv = (df['close'] - low_n) / (high_n - low_n + 1e-9) * 100
    df['K'] = rsv.ewm(com=m1 - 1, adjust=False).mean()
    df['D'] = df['K'].ewm(com=m2 - 1, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    return df


def macd_area(bars: pd.Series) -> float:
    """计算MACD柱面积（近似积分）"""
    return float(bars.abs().sum())


class DivergenceDetector:
    """
    背驰检测:
    1. MACD面积对比（同向两段力度比较）
    2. RSI/KDJ 顶底背离
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df = calculate_macd(self.df)
        self.df['rsi'] = calculate_rsi(self.df)
        self.df = calculate_kdj(self.df)
        self.df.reset_index(drop=True, inplace=True)

    def check_divergence(self, bis: list[Bi]) -> Optional[dict]:
        """
        检测背驰: 比较最近两个同向段的力度
        返回: {'type': 'top'|'bottom', 'probability': 0-1}
        """
        if len(bis) < 4:
            return None

        # 取最近两个向上段
        up_segments = [b for b in bis if b.direction == "up"]
        down_segments = [b for b in bis if b.direction == "down"]

        if len(up_segments) >= 2:
            result = self._check_segment_divergence(
                up_segments[-2], up_segments[-1], "top"
            )
            if result:
                return result

        if len(down_segments) >= 2:
            result = self._check_segment_divergence(
                down_segments[-2], down_segments[-1], "bottom"
            )
            if result:
                return result

        return None

    def _check_segment_divergence(
        self, seg1: Bi, seg2: Bi, seg_type: str
    ) -> Optional[dict]:
        """比较两段的力度差异"""
        # 获取K线在这两段区间
        s1_df = self._get_segment_df(seg1.start, seg1.end)
        s2_df = self._get_segment_df(seg2.start, seg2.end)

        if s1_df.empty or s2_df.empty:
            return None

        macd1 = float(macd_area(s1_df["bar"]))
        macd2 = float(macd_area(s2_df["bar"]))
        # 避免 macd1==0 时除零（部分新股/极短区间柱和为 0）
        if macd1 <= 1e-15:
            return None

        if seg_type == "bottom":
            # 底背驰: 价格新低，但MACD面积（力度）减小
            price1 = float(seg1.low)
            price2 = float(seg2.low)
            if price1 <= 1e-12:
                return None
            if price2 < price1 and macd2 < macd1 * 0.85:
                ratio = macd2 / macd1
                prob = min(1.0, (1 - ratio) + 0.5)
                return {
                    "type": "bottom",
                    "probability": round(prob, 2),
                    "price_drop": round(abs(price2 - price1) / price1, 3),
                    "macd_ratio": round(ratio, 2),
                    "description": f"价格新低{money(price2-price1):.2f}但力度减弱至{ratio:.0%}"
                }
        else:
            # 顶背驰: 价格新高，但MACD面积（力度）减小
            price1 = float(seg1.high)
            price2 = float(seg2.high)
            if price1 <= 1e-12:
                return None
            if price2 > price1 and macd2 < macd1 * 0.85:
                ratio = macd2 / macd1
                prob = min(1.0, (1 - ratio) + 0.5)
                return {
                    "type": "top",
                    "probability": round(prob, 2),
                    "price_rise": round(abs(price2 - price1) / price1, 3),
                    "macd_ratio": round(ratio, 2),
                    "description": f"价格新高{money(price2-price1):.2f}但力度减弱至{ratio:.0%}"
                }
        return None

    def _get_segment_df(self, start, end) -> pd.DataFrame:
        mask = (self.df['date'] >= start) & (self.df['date'] <= end)
        return self.df[mask]


def money(v: float) -> float:
    """格式化金额显示"""
    return round(v, 2)
