"""
性能指标计算模块

负责计算回测的各种性能指标，包括：
- 总收益率
- 胜率
- 最大回撤
- 夏普比率
- 盈亏比
- 连胜连亏统计
"""

from typing import List, Tuple
import pandas as pd
import numpy as np
from backend.backtest.models import TradeRecord, PerformanceMetrics


class MetricsCalculator:
    """性能指标计算器"""
    
    def __init__(self, trades: List[TradeRecord], initial_capital: float):
        """
        初始化指标计算器
        
        Args:
            trades: 交易记录列表
            initial_capital: 初始资金
        """
        self.trades = trades
        self.initial_capital = initial_capital
        
        # 计算最终资金
        total_pnl = sum(trade.profit_loss for trade in trades)
        self.final_capital = initial_capital + total_pnl
    
    def calculate_total_return(self) -> float:
        """
        计算总收益率
        
        Formula: total_return = (final_capital - initial_capital) / initial_capital
        
        Returns:
            总收益率（小数形式，如0.15表示15%）
        """
        if self.initial_capital == 0:
            return 0.0
        
        return (self.final_capital - self.initial_capital) / self.initial_capital
    
    def calculate_win_rate(self) -> float:
        """
        计算胜率
        
        Formula: win_rate = winning_trades / total_trades
        
        Returns:
            胜率（小数形式，如0.6表示60%）
        """
        if len(self.trades) == 0:
            return 0.0
        
        winning_trades = sum(1 for trade in self.trades if trade.profit_loss > 0)
        return winning_trades / len(self.trades)
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> Tuple[float, float]:
        """
        计算最大回撤
        
        最大回撤是指从峰值到谷底的最大跌幅。
        
        Formula: max_drawdown = max((peak_value - trough_value) / peak_value)
        
        Args:
            equity_curve: 权益曲线，pandas Series，索引为时间戳，值为资金余额
        
        Returns:
            Tuple[float, float]: (最大回撤金额, 最大回撤百分比)
        """
        if len(equity_curve) == 0:
            return 0.0, 0.0
        
        # 计算累计最大值（峰值）
        cumulative_max = equity_curve.expanding().max()
        
        # 计算回撤金额
        drawdown_amount = cumulative_max - equity_curve
        
        # 计算回撤百分比
        drawdown_pct = drawdown_amount / cumulative_max
        
        # 找到最大回撤
        max_drawdown_amount = drawdown_amount.max()
        max_drawdown_pct = drawdown_pct.max()
        
        return max_drawdown_amount, max_drawdown_pct
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        计算夏普比率
        
        夏普比率衡量每单位风险的超额收益。
        
        Formula: sharpe_ratio = (mean_return - risk_free_rate) / std_return
        
        Args:
            returns: 收益率序列（每个时间段的收益率）
            risk_free_rate: 无风险利率，默认为0
        
        Returns:
            夏普比率
        """
        if len(returns) == 0:
            return 0.0
        
        # 计算平均收益率
        mean_return = returns.mean()
        
        # 计算收益率标准差
        std_return = returns.std()
        
        # 如果标准差为0，返回0（避免除零错误）
        if std_return == 0 or np.isnan(std_return):
            return 0.0
        
        # 计算夏普比率
        sharpe_ratio = (mean_return - risk_free_rate) / std_return
        
        return sharpe_ratio
    
    def calculate_profit_factor(self) -> float:
        """
        计算盈亏比
        
        Formula: profit_factor = total_profit / abs(total_loss)
        
        Returns:
            盈亏比
        """
        if len(self.trades) == 0:
            return 0.0
        
        total_profit = sum(trade.profit_loss for trade in self.trades if trade.profit_loss > 0)
        total_loss = sum(abs(trade.profit_loss) for trade in self.trades if trade.profit_loss < 0)
        
        if total_loss == 0:
            # 如果没有亏损交易，返回无穷大（或一个很大的数）
            return float('inf') if total_profit > 0 else 0.0
        
        return total_profit / total_loss
    
    def calculate_trade_statistics(self) -> Tuple[int, int, int, float, float]:
        """
        计算交易统计信息
        
        注意：盈亏为0的交易既不计入盈利也不计入亏损
        
        Returns:
            Tuple[int, int, int, float, float]: 
            (总交易数, 盈利交易数, 亏损交易数, 平均盈利, 平均亏损)
        """
        if len(self.trades) == 0:
            return 0, 0, 0, 0.0, 0.0
        
        total_trades = len(self.trades)
        winning_trades = [trade for trade in self.trades if trade.profit_loss > 0]
        losing_trades = [trade for trade in self.trades if trade.profit_loss < 0]
        # 注意：profit_loss == 0 的交易不计入winning或losing
        
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        
        avg_profit = sum(trade.profit_loss for trade in winning_trades) / winning_count if winning_count > 0 else 0.0
        avg_loss = sum(trade.profit_loss for trade in losing_trades) / losing_count if losing_count > 0 else 0.0
        
        return total_trades, winning_count, losing_count, avg_profit, avg_loss
    
    def calculate_streaks(self) -> Tuple[int, int]:
        """
        计算最长连胜和最长连亏
        
        Returns:
            Tuple[int, int]: (最长连胜, 最长连亏)
        """
        if len(self.trades) == 0:
            return 0, 0
        
        longest_win_streak = 0
        longest_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for trade in self.trades:
            if trade.profit_loss > 0:
                current_win_streak += 1
                current_loss_streak = 0
                longest_win_streak = max(longest_win_streak, current_win_streak)
            elif trade.profit_loss < 0:
                current_loss_streak += 1
                current_win_streak = 0
                longest_loss_streak = max(longest_loss_streak, current_loss_streak)
            # 如果profit_loss == 0，不计入连胜或连亏
        
        return longest_win_streak, longest_loss_streak
    
    def calculate_all_metrics(self, equity_curve: pd.Series, returns: pd.Series) -> PerformanceMetrics:
        """
        计算所有性能指标
        
        Args:
            equity_curve: 权益曲线
            returns: 收益率序列
        
        Returns:
            PerformanceMetrics对象，包含所有性能指标
        """
        # 基础指标
        total_return = self.calculate_total_return()
        win_rate = self.calculate_win_rate()
        
        # 回撤指标
        max_drawdown_amount, max_drawdown_pct = self.calculate_max_drawdown(equity_curve)
        
        # 风险调整收益指标
        sharpe_ratio = self.calculate_sharpe_ratio(returns)
        
        # 盈亏指标
        profit_factor = self.calculate_profit_factor()
        
        # 交易统计
        total_trades, winning_count, losing_count, avg_profit, avg_loss = self.calculate_trade_statistics()
        
        # 连胜连亏
        longest_win_streak, longest_loss_streak = self.calculate_streaks()
        
        return PerformanceMetrics(
            initial_capital=self.initial_capital,
            final_capital=self.final_capital,
            total_return=self.final_capital - self.initial_capital,
            total_return_pct=total_return,
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown_amount,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            longest_win_streak=longest_win_streak,
            longest_loss_streak=longest_loss_streak,
            total_fees=0.0  # 暂不实现手续费
        )
