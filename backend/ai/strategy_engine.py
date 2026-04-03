"""
策略推荐引擎
"""
from typing import Optional
from chanlun.elements import BuySellPoint, XiangSegment, Zhongshu, ASignal


class StrategyEngine:
    """
    策略推荐:
    1. 结合缠论信号 + 走势分类 + 背驰判断
    2. 输出带置信度的操作建议
    3. 止损/止盈计算
    """

    def __init__(self, signals: list[BuySellPoint],
                 trend: str,
                 current_price: float,
                 current_level: str,
                 zhongshus: list[Zhongshu],
                 divergence: Optional[dict] = None):
        self.signals = signals
        self.trend = trend
        self.current_price = current_price
        self.current_level = current_level
        self.zhongshus = zhongshus
        self.divergence = divergence

    def generate_signal(self) -> ASignal:
        """生成AI策略信号"""
        buy_signals = [s for s in self.signals if '买' in s.type]
        sell_signals = [s for s in self.signals if '卖' in s.type]

        # 最近信号
        recent_buy = buy_signals[-1] if buy_signals else None
        recent_sell = sell_signals[-1] if sell_signals else None

        if recent_buy and recent_sell:
            if recent_buy.datetime > recent_sell.datetime:
                active_signal = recent_buy
                direction = "买入"
            else:
                active_signal = recent_sell
                direction = "卖出"
        elif recent_buy:
            active_signal = recent_buy
            direction = "买入"
        elif recent_sell:
            active_signal = recent_sell
            direction = "卖出"
        else:
            active_signal = None
            direction = "观望"

        # 计算置信度
        confidence = self._calc_confidence(active_signal)

        # 风险评级
        risk = self._calc_risk(active_signal, direction)

        # 止损止盈
        entry, stop_loss, take_profit = self._calc_levels(active_signal, direction)

        # 操作窗口
        period = self._calc_holding_period()

        # 自然语言描述
        desc = self._make_description(active_signal, direction, confidence)

        return ASignal(
            stock_code="",
            level=self.current_level,
            direction=direction,
            confidence=confidence,
            risk_level=risk,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            holding_period=period,
            description=desc,
            signals=self.signals[-5:] if self.signals else []
        )

    def _calc_confidence(self, signal: Optional[BuySellPoint]) -> float:
        """计算置信度"""
        if not signal:
            return 0.0

        base = signal.confidence

        # 背驰加持 +15%
        if self.divergence and self.divergence.get('probability', 0) > 0.7:
            base = min(1.0, base + 0.15)

        # 多中枢震荡降低置信度
        if len(self.zhongshus) > 2:
            base *= 0.85

        # 趋势同向加持
        if self.trend == "上涨" and "买" in signal.type:
            base = min(1.0, base + 0.1)
        elif self.trend == "下跌" and "卖" in signal.type:
            base = min(1.0, base + 0.1)

        return round(base, 2)

    def _calc_risk(self, signal: Optional[BuySellPoint],
                    direction: str) -> str:
        """风险评级"""
        if not signal:
            return "中"

        risk = signal.confidence

        # 在中枢内风险高
        if self.zhongshus:
            last_zs = self.zhongshus[-1]
            if last_zs.range_low <= self.current_price <= last_zs.range_high:
                risk *= 0.8

        # 背驰信号降低风险
        if self.divergence and self.divergence.get('probability', 0) > 0.7:
            risk = min(1.0, risk + 0.1)

        if risk >= 0.75:
            return "低"
        elif risk >= 0.5:
            return "中"
        return "高"

    def _calc_levels(self, signal: Optional[BuySellPoint],
                     direction: str) -> tuple:
        """计算入场价、止损价、止盈价"""
        entry = self.current_price

        if not signal:
            return entry, None, None

        if direction == "买入":
            stop_loss = signal.stop_loss or round(self.current_price * 0.97, 2)
            take_profit = signal.take_profit or round(
                self.current_price * 1.05, 2)
            # 做多：须 止损 < 入场 < 止盈（纠正信号里 SL/TP 填反或混用旧字段）
            if stop_loss is not None and take_profit is not None:
                if stop_loss > take_profit:
                    stop_loss, take_profit = take_profit, stop_loss
                if stop_loss >= entry:
                    stop_loss = round(entry * 0.97, 2)
                if take_profit <= entry:
                    take_profit = round(entry * 1.05, 2)
        else:
            stop_loss = signal.stop_loss or round(self.current_price * 1.03, 2)
            take_profit = signal.take_profit or round(
                self.current_price * 0.95, 2)
            # 做空：须 止盈 < 入场 < 止损
            if stop_loss is not None and take_profit is not None:
                if take_profit > stop_loss:
                    stop_loss, take_profit = take_profit, stop_loss
                if stop_loss <= entry:
                    stop_loss = round(entry * 1.03, 2)
                if take_profit >= entry:
                    take_profit = round(entry * 0.95, 2)

        return entry, stop_loss, take_profit

    def _calc_holding_period(self) -> str:
        """操作窗口"""
        level_periods = {
            "1min": "30分钟内",
            "5min": "2-4小时",
            "15min": "半天-1天",
            "30min": "1-3天",
            "60min": "3-7天",
            "daily": "1-4周",
            "weekly": "1-3个月",
            "monthly": "3-12个月"
        }
        return level_periods.get(self.current_level, "1-3天")

    def _make_description(self, signal: Optional[BuySellPoint],
                        direction: str, confidence: float) -> str:
        """生成自然语言描述"""
        parts = [f"当前: {self.trend}趋势"]

        if signal:
            parts.append(f"信号: {signal.type}(置信{confidence:.0%})")
            parts.append(signal.description)
        else:
            parts.append("暂无明确信号")

        if self.divergence:
            parts.append(f"背驰概率: {self.divergence.get('probability', 0):.0%}")

        if self.zhongshus:
            last_zs = self.zhongshus[-1]
            parts.append(f"中枢: [{last_zs.range_low:.2f},{last_zs.range_high:.2f}]")

        return " | ".join(parts)
