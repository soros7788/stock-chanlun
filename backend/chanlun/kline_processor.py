"""
缠论 K线预处理模块
处理包含关系、顶底分型识别
"""
import pandas as pd
import numpy as np
from typing import Literal
from .elements import KLine


class KLineProcessor:
    """
    K线预处理:
    1. 确保数据按时间排序
    2. 处理包含关系（合并包含的K线）
    3. 识别顶分型和底分型
    """

    def __init__(self, klines: pd.DataFrame):
        """
        klines: DataFrame with columns [date, open, high, low, close, volume]
        """
        self.df = klines.copy()
        self._ensure_sorted()
        self._ensure_columns()

    def _ensure_sorted(self):
        if 'date' in self.df.columns:
            self.df = self.df.sort_values('date').reset_index(drop=True)

    def _ensure_columns(self):
        col_map = {
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume',
            '时间': 'date'
        }
        self.df.rename(columns=col_map, inplace=True)
        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'])

    def process_inclusion(self) -> pd.DataFrame:
        """
        处理包含关系：从左到右扫描，合并包含的K线
        返回处理后的 DataFrame
        """
        df = self.df.copy()
        result = []
        i = 0

        while i < len(df):
            if i < 4:  # 前面4根直接保留
                result.append(df.iloc[i].to_dict())
                i += 1
                continue

            # 取前4根判断分型
            seg = df.iloc[max(0, i-4):i+1].copy()
            fx_type = self._detect_fenxing(seg)

            if fx_type is None:
                # 无分型，继续
                result.append(df.iloc[i].to_dict())
                i += 1
            else:
                # 有分型，记录并跳到分型位置
                result.append(df.iloc[i].to_dict())
                i += 1

        out = pd.DataFrame(result)
        out = out.drop_duplicates(subset=['date']).reset_index(drop=True)
        return out

    def _detect_fenxing(self, seg: pd.DataFrame) -> Literal["top", "bottom", None]:
        """
        识别分型：顶分型=中间K线高点最高、低点也最高
                  底分型=中间K线高点最低、低点也最低
        返回: "top" / "bottom" / None
        """
        if len(seg) < 5:
            return None

        # 中间3根（排除两边各1根）
        middle = seg.iloc[-3]
        left = seg.iloc[-4]
        right = seg.iloc[-1]

        mid_h, mid_l = middle['high'], middle['low']
        # 顶分型
        if mid_h > left['high'] and mid_h > right['high'] and \
           mid_l > left['low'] and mid_l > right['low']:
            return "top"
        # 底分型
        if mid_h < left['high'] and mid_h < right['high'] and \
           mid_l < left['low'] and mid_l < right['low']:
            return "bottom"
        return None

    def detect_all_fenxing(self) -> list[dict]:
        """
        识别所有分型点（用于笔的起点/终点判断）
        返回分型列表: [{'date', 'type': 'top'|'bottom', 'high', 'low', 'index'}]
        """
        df = self.process_inclusion().reset_index(drop=True)
        fenxings = []
        i = 4

        while i < len(df):
            seg = df.iloc[i-4:i+1].copy()
            fx_type = self._detect_fenxing(seg)

            if fx_type:
                middle = df.iloc[i-2]
                fenxings.append({
                    'date': middle['date'],
                    'type': fx_type,
                    'high': float(middle['high']),
                    'low': float(middle['low']),
                    'index': i - 2,
                    'kline': middle.to_dict()
                })
                i += 4  # 跳过分型区间
            else:
                i += 1

        return fenxings

    def to_kline_list(self) -> list[KLine]:
        """转换为 KLine 对象列表"""
        rows = []
        for _, row in self.df.iterrows():
            rows.append(KLine(
                date=row['date'].to_pydatetime() if hasattr(row['date'], 'to_pydatetime') else row['date'],
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['volume']) if pd.notna(row.get('volume')) else 0.0,
                amount=float(row.get('amount', 0)) if pd.notna(row.get('amount', 0)) else 0.0
            ))
        return rows
