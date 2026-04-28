#!/usr/bin/env python3
"""
支撑阻力分析工具 - 第一阶段核心功能实现

第一阶段目标：
1. 基础支撑阻力识别（技术位、动态位、心理位）
2. 多时间框架融合系统
3. 智能评分计算器

基于：support_resistance.md 优化版说明文档
"""

import mysql.connector
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
import json
import sys
import os
import requests
from decimal import Decimal

# 添加当前目录到路径，确保能导入优化模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def ensure_float(value):
    """确保值为float类型"""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except:
        return 0.0

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupportResistanceAnalyzerPhase1:
    """
    支撑阻力分析器 - 第一阶段核心功能
    
    基于完整多时间框架数据实现：
    1. 基础支撑阻力识别
    2. 多时间框架融合
    3. 智能评分计算
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 3306,
        user: str = 'root',
        password: str = '',
        database: str = 'btc_assistant'
    ):
        """初始化分析器"""
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4'
        }
        self.connection = None
        # 回测用：限制所有查询只看此时间戳之前的数据（毫秒），None 表示不限制
        self.before_ts: Optional[int] = None
        
        # 时间框架配置（金字塔决策）
        self.timeframe_config = {
            '1M': {'weight': 4, 'lookback': 24, 'description': '月线-战略层'},
            '1w': {'weight': 3, 'lookback': 52, 'description': '周线-战役层'},
            '1d': {'weight': 2, 'lookback': 100, 'description': '日线-战术层'},
            '4h': {'weight': 1, 'lookback': 200, 'description': '4小时-执行层'}
        }
        
        # 交易参数（Francis交易档案）
        self.trading_params = {
            'account_balance': 2403,  # U
            'leverage': 5,
            'max_per_trade': 10000,  # U
            'hard_stop': 100,  # U
            'min_risk_reward': 2.0,
            'max_holding_hours': 48
        }
        
        # 初始化优化模块（延迟导入，避免循环依赖）
        self.swing_optimizer = None
        self.fib_calculator = None
        self.volume_system = None
        
        # ================================================================
        # 集中参数配置 —— 所有可调参数都在这里，修改后全局生效
        # ================================================================
        self.params = {
            
            # ── 摆动点识别 ──────────────────────────────────────────────
            # 各周期窗口大小：左右各看几根K线来判断极值点
            # 4h=3(±12h)  1d=5(±5天)  1w=4(±4周)  1M=3(±3个月)
            'swing_window_by_tf': {
                '4h': 3,
                '1d': 5,
                '1w': 4,
                '1M': 3,
            },
            # 兜底默认值（未匹配到周期时使用）
            'swing_window': 3,
            # 实盘模式：True=最近window根K线用纯左侧确认，False=严格左右两侧（回测用）
            # before_ts不为None时自动切换为False（回测模式）
            'realtime_mode': True,
            # 最小波动幅度：摆动点相对周围均值的最小涨跌幅，过滤噪音
            # 0.003 = 0.3%，BTC 7万刀时约 210 刀
            'swing_min_amplitude': 0.003,
            # 原始方法（无优化器时）的最小幅度，稍高一点过滤更多噪音
            'swing_min_amplitude_fallback': 0.005,
            
            # ── 斐波那契计算 ─────────────────────────────────────────────
            # 各周期用于寻找近期波段的回溯K线数
            'fib_lookback': {'1M': 24, '1w': 52, '1d': 120, '4h': 144},
            # 波段最小振幅（相对幅度），低于此不计算 fib
            'fib_min_wave_amplitude': 0.03,       # 3%
            # 回撤比例列表（只保留最重要的黄金分割位，减少噪音）
            'fib_retracement_ratios': [0.382, 0.5, 0.618],
            # 延伸比例列表
            'fib_extension_ratios': [1.272, 1.618],
            
            # ── 动态位（均线/布林带）────────────────────────────────────
            # 历史触碰验证容差：均线价格 ± 此比例内算"触碰"
            'dynamic_touch_tolerance': 0.01,      # 1%
            # 触碰次数上限加成（每次+1强度，最多加此值）
            'dynamic_touch_bonus_max': 2,
            
            # ── 心理位 ───────────────────────────────────────────────────
            # 心理位扫描范围：当前价格 ± 此比例
            'psych_range_pct': 0.20,              # ±20%
            # 心理位间隔（整千）
            'psych_interval': 1000,
            # 重要心理位间隔（整五千，强度+1）
            'psych_major_interval': 5000,
            
            # ── 位点合并 ─────────────────────────────────────────────────
            # 合并容差 = min(ATR/价格 × 此倍数, 1.5%)
            # 即：ATR 相对比例 和 固定上限 1.5% 取较小值，防止月线大 ATR 把所有位点合并成一个
            # 调大 → 合并更激进（位点更少），调小 → 保留更多独立位点
            'merge_atr_multiplier': 1.0,
            
            # ── 评分权重（总和 1.0）────────────────────────────────
            # 触碰/置信度：历史验证次数，最能预测位点有效性
            'score_weight_confidence': 0.50,
            # 多时间框架共振：改为报告层 ⚡ 标注，不再参与评分
            'score_weight_confluence': 0.0,
            # 时间框架权威性：大周期位点更可靠
            'score_weight_timeframe': 0.20,
            # 成交量确认：有量才有效
            'score_weight_volume': 0.15,
            # RSI 确认：超买超卖增强可靠性
            'score_weight_rsi': 0.15,
            # 距离当前价格：不参与评分
            'score_weight_distance': 0.0,
            # 无成交量数据时的默认分（0~1）
            'score_volume_default': 0.3,
            
            # ── 距离评分档位（distance_pct → score）────────────────────
            # 格式：[(距离上限, 得分), ...]，从近到远
            'score_distance_tiers': [
                (0.03, 1.0),   # 3% 以内
                (0.06, 0.8),   # 6% 以内
                (0.10, 0.6),   # 10% 以内
                (0.15, 0.4),   # 15% 以内
                (0.25, 0.2),   # 25% 以内
            ],
            # 超出所有档位时的兜底分
            'score_distance_fallback': 0.1,
            
            # ── 过滤门槛 ─────────────────────────────────────────────────
            # 综合分析中过滤弱位点的归一化评分下限（0~1）
            # 0.2 ≈ 原系统 3/15 分，调高则结果更精简，调低则结果更多
            'filter_min_score': 0.2,
        }
    
    def connect(self) -> bool:
        """连接到数据库"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info(f"✅ 成功连接到数据库: {self.config['database']}")
            return True
        except mysql.connector.Error as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("🔌 数据库连接已关闭")
    
    def _init_optimization_modules(self):
        """初始化优化模块（延迟加载）"""
        if self.swing_optimizer is None:
            try:
                from swing_point_optimizer import SwingPointOptimizer
                self.swing_optimizer = SwingPointOptimizer()
                # 调整参数避免过滤太严格
                self.swing_optimizer.config.update({
                    'min_amplitude_multiplier': 0.8,  # 降低幅度要求
                    'volume_threshold': 0.8,         # 允许正常成交量
                    'max_lookback_days': 60,         # 延长回溯时间
                })
                logger.info("✅ 摆动点优化器初始化完成")
            except ImportError as e:
                logger.warning(f"无法导入摆动点优化器: {e}")
                self.swing_optimizer = None
        
        if self.fib_calculator is None:
            try:
                from fibonacci_calculator import FibonacciCalculator
                self.fib_calculator = FibonacciCalculator()
                # 调整参数
                self.fib_calculator.wave_config.update({
                    'min_amplitude_pct': 3.0,        # 降低最小波段幅度
                    'min_duration_bars': 5,          # 减少最小持续时间
                })
                logger.info("✅ 斐波那契计算器初始化完成")
            except ImportError as e:
                logger.warning(f"无法导入斐波那契计算器: {e}")
                self.fib_calculator = None
        
        if self.volume_system is None:
            try:
                from volume_confirmation import VolumeConfirmationSystem
                self.volume_system = VolumeConfirmationSystem()
                # 调整参数
                self.volume_system.config.update({
                    'confirmation_window': 3,
                    'volume_thresholds': {
                        'strong_confirmation': 1.5,
                        'confirmation': 1.2,
                        'weak_confirmation': 1.0,
                        'no_confirmation': 0.8,
                    },
                    'price_tolerance_pct': 0.015,    # 增加价格容差
                    'min_test_count': 1,             # 减少最小测试次数
                })
                logger.info("✅ 成交量确认系统初始化完成")
            except ImportError as e:
                logger.warning(f"无法导入成交量确认系统: {e}")
                self.volume_system = None
    
    # ==================== 1. 基础支撑阻力识别 ====================

    def _count_touches(self, level_price: float,
                       highs: List[float], lows: List[float], closes: List[float],
                       tolerance_pct: float = 0.015) -> int:
        """
        统计历史K线中价格触及某个位点并反转的次数。
        触及条件：high >= level - tolerance 且 low <= level + tolerance
        反转条件：收盘价前后方向不同（局部高低点）
        """
        tolerance = level_price * tolerance_pct
        count = 0
        for i in range(1, len(closes) - 1):
            touched = (highs[i] >= level_price - tolerance and
                       lows[i]  <= level_price + tolerance)
            if touched:
                rev_up = closes[i - 1] < closes[i] and closes[i] > closes[i + 1]
                rev_dn = closes[i - 1] > closes[i] and closes[i] < closes[i + 1]
                if rev_up or rev_dn:
                    count += 1
        return count
    
    def find_swing_points(self, prices: List[float], window: int = None,
                          min_amplitude: float = None,
                          realtime_mode: bool = False) -> Tuple[List[int], List[int]]:
        """
        摆动点识别算法

        realtime_mode=True 时，最近 window 根 K 线改用纯左侧确认：
          - 高点：prices[i] 是左侧 window 根内的最高点，且比前一根高
          - 低点：prices[i] 是左侧 window 根内的最低点，且比前一根低
        这样实盘时不会因为缺少右侧数据而漏掉最新摆动点。
        """
        n = len(prices)
        if window is None:
            window = self.params['swing_window']
        if min_amplitude is None:
            min_amplitude = self.params['swing_min_amplitude']
        if n < window * 2 + 1:
            logger.warning(f"数据不足({n}条)，需要至少{window*2+1}条数据")
            return [], []

        swing_highs = []
        swing_lows = []

        # 标准区间：有完整左右两侧数据
        for i in range(window, n - window):
            is_high = all(prices[i] > prices[i - j] and prices[i] > prices[i + j]
                          for j in range(1, window + 1))
            is_low  = all(prices[i] < prices[i - j] and prices[i] < prices[i + j]
                          for j in range(1, window + 1))

            if is_high or is_low:
                avg_surrounding = (sum(prices[i - window:i]) + sum(prices[i + 1:i + window + 1])) / (window * 2)
                if avg_surrounding == 0:
                    continue
                amplitude = abs(prices[i] - avg_surrounding) / avg_surrounding
                if is_high and amplitude >= min_amplitude:
                    swing_highs.append(i)
                if is_low and amplitude >= min_amplitude:
                    swing_lows.append(i)

        # 实盘模式：对最近 window 根 K 线补充纯左侧确认
        if realtime_mode and n > window:
            for i in range(n - window, n):
                if i < window:
                    continue
                left = prices[max(0, i - window): i]
                if not left:
                    continue

                is_high = prices[i] == max(left + [prices[i]]) and prices[i] > prices[i - 1]
                is_low  = prices[i] == min(left + [prices[i]]) and prices[i] < prices[i - 1]

                if is_high or is_low:
                    avg_left = sum(left) / len(left)
                    if avg_left == 0:
                        continue
                    amplitude = abs(prices[i] - avg_left) / avg_left
                    if is_high and amplitude >= min_amplitude:
                        swing_highs.append(i)
                    if is_low and amplitude >= min_amplitude:
                        swing_lows.append(i)

        logger.info(f"识别到 {len(swing_highs)} 个摆动高点和 {len(swing_lows)} 个摆动低点"
                    f"{'（含实盘左侧确认）' if realtime_mode else ''}")
        return swing_highs, swing_lows
    
    def identify_technical_levels(self, timeframe: str, symbol: str = 'BTCUSDT', use_optimizer: bool = True) -> Dict[str, List[Dict]]:
        """
        识别技术支撑阻力位（摆动高低点）
        
        参数:
            timeframe: 时间框架（1M, 1w, 1d, 4h）
            symbol: 交易对
            use_optimizer: 是否使用优化器
        
        返回:
            技术位字典：{'supports': [], 'resistances': []}
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 获取价格数据
            lookback = self.timeframe_config[timeframe]['lookback'] * 3
            if self.before_ts:
                query = """
                    SELECT timestamp, high, low, close, volume
                    FROM klines
                    WHERE symbol = %s AND timeframe = %s AND timestamp < %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """
                cursor.execute(query, (symbol, timeframe, self.before_ts, lookback))
            else:
                query = """
                    SELECT timestamp, high, low, close, volume
                    FROM klines
                    WHERE symbol = %s AND timeframe = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """
                cursor.execute(query, (symbol, timeframe, lookback))
            data = cursor.fetchall()
            
            if not data:
                logger.warning(f"没有找到 {timeframe} 时间框架的数据")
                return {'supports': [], 'resistances': []}
            
            # 提取价格序列（按时间正序）
            data.reverse()
            highs = [ensure_float(row['high']) for row in data]
            lows = [ensure_float(row['low']) for row in data]
            closes = [ensure_float(row['close']) for row in data]
            volumes = [ensure_float(row['volume']) for row in data]
            timestamps = [row['timestamp'] for row in data]
            
            supports = []
            resistances = []
            
            # 获取当前价格用于方向校正
            current_price = closes[-1] if closes else 0

            # 按周期取对应 window；回测模式（before_ts不为None）强制关闭实盘左侧确认
            tf_window = self.params['swing_window_by_tf'].get(timeframe, self.params['swing_window'])
            realtime_mode = self.params['realtime_mode'] and (self.before_ts is None)
            
            if use_optimizer and self.swing_optimizer is not None:
                # 使用优化器识别摆动点
                self._init_optimization_modules()
                swing_highs, swing_lows = self.swing_optimizer.find_swing_points_optimized(
                    highs=highs,
                    lows=lows,
                    closes=closes,
                    volumes=volumes,
                    timestamps=timestamps,
                    timeframe=timeframe,
                    min_days=30
                )
                
                # 摆动低点：价格下方 → 支撑，价格上方 → 阻力
                for swing_low in swing_lows:
                    price = swing_low['price']
                    level = {
                        'price': price,
                        'timestamp': swing_low['timestamp'],
                        'type': 'technical',
                        'subtype': 'swing_low_optimized',
                        'timeframe': timeframe,
                        'confidence': swing_low.get('confidence', 0.5),
                        'metadata': {
                            'amplitude': swing_low.get('amplitude', 0),
                            'volume_ratio': swing_low.get('volume_ratio', 1),
                            'atr_ratio': swing_low.get('atr_ratio', 0)
                        }
                    }
                    if price < current_price:
                        supports.append(level)
                    else:
                        resistances.append(level)
                
                # 摆动高点：价格上方 → 阻力，价格下方 → 支撑
                for swing_high in swing_highs:
                    price = swing_high['price']
                    level = {
                        'price': price,
                        'timestamp': swing_high['timestamp'],
                        'type': 'technical',
                        'subtype': 'swing_high_optimized',
                        'timeframe': timeframe,
                        'confidence': swing_high.get('confidence', 0.5),
                        'metadata': {
                            'amplitude': swing_high.get('amplitude', 0),
                            'volume_ratio': swing_high.get('volume_ratio', 1),
                            'atr_ratio': swing_high.get('atr_ratio', 0)
                        }
                    }
                    if price > current_price:
                        resistances.append(level)
                    else:
                        supports.append(level)
                
                logger.info(f"{timeframe} 优化识别: {len(supports)}支撑, {len(resistances)}阻力")
            else:
                # 使用原始方法
                swing_highs_idx, swing_lows_idx = self.find_swing_points(
                    highs,
                    window=tf_window,
                    min_amplitude=self.params['swing_min_amplitude_fallback'],
                    realtime_mode=realtime_mode
                )
                
                for idx in swing_lows_idx:
                    price = lows[idx]
                    touch_count = self._count_touches(price, highs, lows, closes)
                    level = {
                        'price': price,
                        'timestamp': timestamps[idx],
                        'type': 'technical',
                        'subtype': 'swing_low',
                        'timeframe': timeframe,
                        'touch_count': max(1, touch_count),  # 至少1（自身就是摆动点）
                        'metadata': {
                            'index': idx,
                            'high': highs[idx],
                            'low': lows[idx],
                            'close': closes[idx],
                            'volume': volumes[idx]
                        }
                    }
                    if price < current_price:
                        supports.append(level)
                    else:
                        resistances.append(level)
                
                for idx in swing_highs_idx:
                    price = highs[idx]
                    touch_count = self._count_touches(price, highs, lows, closes)
                    level = {
                        'price': price,
                        'timestamp': timestamps[idx],
                        'type': 'technical',
                        'subtype': 'swing_high',
                        'timeframe': timeframe,
                        'touch_count': max(1, touch_count),  # 至少1
                        'metadata': {
                            'index': idx,
                            'high': highs[idx],
                            'low': lows[idx],
                            'close': closes[idx],
                            'volume': volumes[idx]
                        }
                    }
                    if price > current_price:
                        resistances.append(level)
                    else:
                        supports.append(level)
                
                logger.info(f"{timeframe} 原始识别: {len(supports)}支撑, {len(resistances)}阻力")
            
            cursor.close()
            return {'supports': supports, 'resistances': resistances}
            
        except mysql.connector.Error as e:
            logger.error(f"识别技术位失败: {e}")
            return {'supports': [], 'resistances': []}
    
    def identify_dynamic_levels(self, timeframe: str, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """
        识别动态支撑阻力位（均线 + 布林带），加入历史触碰验证
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if self.before_ts:
                query = """
                    SELECT timestamp, high, low, close,
                           ema7, ema12, ema25, ema50,
                           boll, boll_up, boll_md, boll_dn
                    FROM klines
                    WHERE symbol = %s AND timeframe = %s AND timestamp < %s
                    ORDER BY timestamp DESC
                    LIMIT 100
                """
                cursor.execute(query, (symbol, timeframe, self.before_ts))
            else:
                query = """
                    SELECT timestamp, high, low, close,
                           ema7, ema12, ema25, ema50,
                           boll, boll_up, boll_md, boll_dn
                    FROM klines
                    WHERE symbol = %s AND timeframe = %s
                    ORDER BY timestamp DESC
                    LIMIT 100
                """
                cursor.execute(query, (symbol, timeframe))
            data = cursor.fetchall()
            
            if not data:
                return {'supports': [], 'resistances': []}

            latest = data[0]
            current_price = ensure_float(latest['close'])

            # 实盘模式下，均线值用倒数第二根（已收盘），避免未收盘K线数据不稳定
            # 回测模式（before_ts不为None）数据已截止，直接用最新一根
            ma_bar = data[1] if (self.before_ts is None and len(data) >= 2) else data[0]
            
            # 动态位配置
            dynamic_level_defs = [
                {'key': 'ema50',   'name': 'EMA50',   'weight': 3},
                {'key': 'boll_md', 'name': 'BOLL_MD', 'weight': 3},
                {'key': 'ema25',   'name': 'EMA25',   'weight': 2},
                {'key': 'ema12',   'name': 'EMA12',   'weight': 2},
                {'key': 'ema7',    'name': 'EMA7',    'weight': 1},
                {'key': 'boll_up', 'name': 'BOLL_UP', 'weight': 2},
                {'key': 'boll_dn', 'name': 'BOLL_DN', 'weight': 2},
            ]
            
            # 提取历史价格序列（正序）用于触碰验证
            history = list(reversed(data))  # 从旧到新
            hist_highs  = [ensure_float(r['high'])  for r in history]
            hist_lows   = [ensure_float(r['low'])   for r in history]
            hist_closes = [ensure_float(r['close']) for r in history]

            supports = []
            resistances = []

            for defn in dynamic_level_defs:
                raw_price = ma_bar.get(defn['key'])
                if raw_price is None:
                    continue
                level_price = ensure_float(raw_price)
                if level_price <= 0:
                    continue

                # 提取每根K线对应的历史均线值（用各自那根K线的均线，而非当前固定值）
                hist_levels = [ensure_float(r.get(defn['key']) or 0) for r in history]

                # 历史触碰验证：用 high/low 判断是否触及当时的均线，用收盘价方向判断是否反转
                touch_count = 0
                for i in range(1, len(hist_closes) - 1):
                    hl = hist_levels[i]
                    if hl <= 0:
                        continue
                    tolerance = hl * self.params['dynamic_touch_tolerance']
                    # 触及判断：K线的high/low穿过当时的均线附近
                    touched = (hist_highs[i] >= hl - tolerance and
                               hist_lows[i]  <= hl + tolerance)
                    if touched:
                        # 反转判断：收盘价前后方向不同
                        reversed_up = hist_closes[i-1] < hist_closes[i] and hist_closes[i] > hist_closes[i+1]
                        reversed_dn = hist_closes[i-1] > hist_closes[i] and hist_closes[i] < hist_closes[i+1]
                        if reversed_up or reversed_dn:
                            touch_count += 1
                
                # 触碰次数加成强度（最多+2）
                touch_bonus = min(touch_count, self.params['dynamic_touch_bonus_max'])
                final_weight = defn['weight'] + touch_bonus
                
                level_info = {
                    'price': level_price,
                    'timestamp': ma_bar['timestamp'],
                    'type': 'dynamic',
                    'subtype': defn['name'],
                    'timeframe': timeframe,
                    'base_strength': final_weight,
                    'touch_count': touch_count,
                    'metadata': {
                        'current_price': current_price,
                        'touch_count': touch_count,
                        'relation': 'above' if current_price > level_price else 'below'
                    }
                }
                
                if current_price > level_price:
                    supports.append(level_info)
                else:
                    resistances.append(level_info)
            
            cursor.close()
            logger.info(f"{timeframe} 动态位: {len(supports)}支撑, {len(resistances)}阻力")
            return {'supports': supports, 'resistances': resistances}
            
        except mysql.connector.Error as e:
            logger.error(f"识别动态位失败: {e}")
            return {'supports': [], 'resistances': []}
    
    def identify_psychological_levels(self, current_price: float, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """
        识别心理支撑阻力位（整数关口）
        
        参数:
            current_price: 当前价格
            symbol: 交易对
        
        返回:
            心理位字典
        """
        # BTC的心理关口配置
        if symbol == 'BTCUSDT':
            major_levels = [1000, 5000, 10000]  # 主要心理位间隔
            minor_levels = [500, 100]  # 次要心理位间隔
        else:
            # 其他币种可以有不同的配置
            major_levels = [100, 500]
            minor_levels = [50, 10]
        
        # 计算当前价格±20%范围内的心理位
        lookback_percent = self.params['psych_range_pct']
        min_price = current_price * (1 - lookback_percent)
        max_price = current_price * (1 + lookback_percent)
        
        supports = []
        resistances = []
        
        # 生成主要心理位
        for base in range(int(min_price // self.params['psych_interval']) * self.params['psych_interval'],
                          int(max_price // self.params['psych_interval']) * self.params['psych_interval'] + self.params['psych_interval'],
                          self.params['psych_interval']):
            if min_price <= base <= max_price:
                if current_price > base:
                    level_type = 'support'
                else:
                    level_type = 'resistance'
                
                strength = 2
                is_major = (base % self.params['psych_major_interval'] == 0)
                if is_major:
                    strength = 3
                if abs(current_price - base) / current_price < 0.01:
                    strength += 1

                level_info = {
                    'price': float(base),
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'type': 'psychological',
                    'subtype': 'major' if is_major else 'standard',
                    'timeframe': 'all',
                    'base_strength': strength,
                    # 只有整5000及以上才参与多时间框架合并，整千太密会污染所有位点
                    'merge_eligible': is_major,
                    'metadata': {
                        'current_price': current_price,
                        'distance_pct': abs(current_price - base) / current_price * 100
                    }
                }
                
                if level_type == 'support':
                    supports.append(level_info)
                else:
                    resistances.append(level_info)
        
        logger.info(f"识别到 {len(supports)} 个心理支撑位和 {len(resistances)} 个心理阻力位")
        return {'supports': supports, 'resistances': resistances}
    
    def identify_fibonacci_levels(self, timeframe: str, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """
        识别斐波那契支撑阻力位
        
        参数:
            timeframe: 时间框架
            symbol: 交易对
        
        返回:
            斐波那契位字典
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 获取价格数据（同时取当前价格）
            if self.before_ts:
                query = """
                    SELECT timestamp, close, volume
                    FROM klines
                    WHERE symbol = %s AND timeframe = %s AND timestamp < %s
                    ORDER BY timestamp ASC
                    LIMIT 200
                """
                cursor.execute(query, (symbol, timeframe, self.before_ts))
            else:
                query = """
                    SELECT timestamp, close, volume
                    FROM klines
                    WHERE symbol = %s AND timeframe = %s
                    ORDER BY timestamp ASC
                    LIMIT 200
                """
                cursor.execute(query, (symbol, timeframe))
            data = cursor.fetchall()
            cursor.close()

            if not data or len(data) < 50:
                logger.warning(f"{timeframe} 数据不足计算斐波那契位")
                return {'supports': [], 'resistances': []}

            closes     = [ensure_float(row['close'])  for row in data]
            volumes    = [ensure_float(row['volume']) for row in data]
            timestamps = [row['timestamp']            for row in data]
            
            # 当前价格取最新收盘价
            current_price = closes[-1]
            
            # 使用斐波那契计算器
            self._init_optimization_modules()
            if self.fib_calculator is None:
                return self._calculate_simple_fibonacci(closes, timestamps, current_price, timeframe)
            
            # 识别波段
            waves = self.fib_calculator.identify_waves(closes, volumes)

            # 计算斐波那契位
            fib_levels = self.fib_calculator.calculate_all_fibonacci_levels(waves)

            # 时间格式按周期
            tf_fmt = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}.get(timeframe, '%m-%d')

            def _find_ts(price_val):
                """在closes里找最接近price_val的索引，返回对应时间戳"""
                if not closes:
                    return None
                idx = min(range(len(closes)), key=lambda i: abs(closes[i] - price_val))
                return timestamps[idx]

            def _ts_fmt(ts):
                if not ts:
                    return ''
                try:
                    return datetime.fromtimestamp(ts / 1000).strftime(tf_fmt)
                except Exception:
                    return ''

            # 根据当前价格修正支撑/阻力方向，并补充时间信息
            corrected_supports = []
            corrected_resistances = []

            for level in fib_levels.get('supports', []) + fib_levels.get('resistances', []):
                level['timeframe'] = timeframe
                price = level.get('price', 0)
                if price <= 0:
                    continue

                # 从 wave 字段提取波段时间信息
                wave = level.get('wave', {})
                wave_start_price = wave.get('start', 0)
                wave_end_price   = wave.get('end', 0)
                if wave_start_price and wave_end_price:
                    ts_start = _find_ts(wave_start_price)
                    ts_end   = _find_ts(wave_end_price)
                    wave_time = f"{_ts_fmt(ts_start)}~{_ts_fmt(ts_end)}" if ts_start and ts_end else ''
                    level['timestamp'] = ts_start
                    level['metadata'] = {
                        'ratio':      level.get('ratio'),
                        'direction':  wave.get('direction', ''),
                        'wave_high':  max(wave_start_price, wave_end_price),
                        'wave_low':   min(wave_start_price, wave_end_price),
                        'wave_time':  wave_time,
                    }

                if price < current_price:
                    corrected_supports.append(level)
                else:
                    corrected_resistances.append(level)
            
            logger.info(f"{timeframe} 斐波那契位: {len(corrected_supports)}支撑, {len(corrected_resistances)}阻力")
            return {'supports': corrected_supports, 'resistances': corrected_resistances}
            
        except Exception as e:
            logger.error(f"识别斐波那契位失败: {e}")
            return {'supports': [], 'resistances': []}
    
    def _calculate_simple_fibonacci(self, closes: List[float], timestamps: List[int],
                                    current_price: float, timeframe: str) -> Dict[str, List[Dict]]:
        """
        基于近期趋势波段的斐波那契计算
        识别最近一次明显的涨跌波段，分别计算回撤位和延伸位
        """
        if len(closes) < 20:
            return {'supports': [], 'resistances': []}

        # 根据时间框架决定用多少根K线来找近期波段
        lookback_map = self.params['fib_lookback']
        lookback = lookback_map.get(timeframe, 100)
        recent = closes[-lookback:] if len(closes) >= lookback else closes
        recent_ts = timestamps[-lookback:] if len(timestamps) >= lookback else timestamps

        # 时间格式按周期
        tf_fmt = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}.get(timeframe, '%m-%d')

        def _ts_str(ts):
            try:
                return datetime.fromtimestamp(ts / 1000).strftime(tf_fmt)
            except Exception:
                return ''

        # 找近期波段：用滑动窗口找局部高低点
        window = max(5, len(recent) // 20)
        local_highs = []
        local_lows = []
        for i in range(window, len(recent) - window):
            if all(recent[i] >= recent[i-j] and recent[i] >= recent[i+j] for j in range(1, window+1)):
                local_highs.append((i, recent[i], recent_ts[i]))
            if all(recent[i] <= recent[i-j] and recent[i] <= recent[i+j] for j in range(1, window+1)):
                local_lows.append((i, recent[i], recent_ts[i]))

        if not local_highs or not local_lows:
            swing_high = max(recent)
            swing_low  = min(recent)
            waves = [('down', swing_high, swing_low, None, None)]
        else:
            last_high_idx, last_high_val, last_high_ts = local_highs[-1]
            last_low_idx,  last_low_val,  last_low_ts  = local_lows[-1]

            min_amplitude = self.params['fib_min_wave_amplitude']
            waves = []

            if last_high_idx > last_low_idx:
                amp = (last_high_val - last_low_val) / last_low_val
                if amp >= min_amplitude:
                    waves.append(('up', last_low_val, last_high_val, last_low_ts, last_high_ts))
                prev_lows = [l for l in local_lows if l[0] < last_low_idx]
                if prev_lows:
                    prev_high_candidates = [h for h in local_highs if h[0] < last_low_idx]
                    if prev_high_candidates:
                        _, prev_high_val, prev_high_ts = prev_high_candidates[-1]
                        amp2 = (prev_high_val - last_low_val) / prev_high_val
                        if amp2 >= min_amplitude:
                            waves.append(('down', prev_high_val, last_low_val, prev_high_ts, last_low_ts))
            else:
                amp = (last_high_val - last_low_val) / last_high_val
                if amp >= min_amplitude:
                    waves.append(('down', last_high_val, last_low_val, last_high_ts, last_low_ts))
                prev_highs = [h for h in local_highs if h[0] < last_high_idx]
                if prev_highs:
                    prev_low_candidates = [l for l in local_lows if l[0] < last_high_idx]
                    if prev_low_candidates:
                        _, prev_low_val, prev_low_ts = prev_low_candidates[-1]
                        amp2 = (last_high_val - prev_low_val) / prev_low_val
                        if amp2 >= min_amplitude:
                            waves.append(('up', prev_low_val, last_high_val, prev_low_ts, last_high_ts))

            if not waves:
                swing_high = max(recent[-50:])
                swing_low  = min(recent[-50:])
                waves = [('down', swing_high, swing_low, None, None)]
                waves = [('down', swing_high, swing_low)]

        # 标准斐波那契比例
        retracement_ratios = self.params['fib_retracement_ratios']
        extension_ratios   = self.params['fib_extension_ratios']

        supports = []
        resistances = []

        for direction, wave_start, wave_end, ts_start, ts_end in waves:
            diff = abs(wave_end - wave_start)
            if diff <= 0:
                continue

            # 波段时间范围字符串
            wave_time = ''
            if ts_start and ts_end:
                wave_time = f"{_ts_str(ts_start)}~{_ts_str(ts_end)}"
            elif ts_start:
                wave_time = _ts_str(ts_start)

            # timestamp 用波段起点时间（方便在图表上定位）
            level_ts = ts_start or ts_end

            if direction == 'up':
                high, low = wave_end, wave_start
                for ratio in retracement_ratios:
                    price = high - diff * ratio
                    importance = 3 if ratio in (0.382, 0.618) else 2
                    level = {
                        'price': round(price, 2),
                        'type': 'fibonacci',
                        'subtype': f'retracement_{ratio}',
                        'timeframe': timeframe,
                        'base_strength': importance,
                        'timestamp': level_ts,
                        'metadata': {'ratio': ratio, 'direction': 'up',
                                     'wave_high': high, 'wave_low': low, 'wave_time': wave_time}
                    }
                    if price < current_price:
                        supports.append(level)
                    elif price > current_price:
                        resistances.append(level)
                for ratio in extension_ratios:
                    price = low + diff * ratio
                    level = {
                        'price': round(price, 2),
                        'type': 'fibonacci',
                        'subtype': f'extension_{ratio}',
                        'timeframe': timeframe,
                        'base_strength': 2,
                        'timestamp': level_ts,
                        'metadata': {'ratio': ratio, 'direction': 'up',
                                     'wave_high': high, 'wave_low': low, 'wave_time': wave_time}
                    }
                    if price > current_price:
                        resistances.append(level)

            else:
                high, low = wave_start, wave_end
                for ratio in retracement_ratios:
                    price = low + diff * ratio
                    importance = 3 if ratio in (0.382, 0.618) else 2
                    level = {
                        'price': round(price, 2),
                        'type': 'fibonacci',
                        'subtype': f'retracement_{ratio}',
                        'timeframe': timeframe,
                        'base_strength': importance,
                        'timestamp': level_ts,
                        'metadata': {'ratio': ratio, 'direction': 'down',
                                     'wave_high': high, 'wave_low': low, 'wave_time': wave_time}
                    }
                    if price > current_price:
                        resistances.append(level)
                    elif price < current_price:
                        supports.append(level)
                for ratio in extension_ratios:
                    price = high - diff * ratio
                    level = {
                        'price': round(price, 2),
                        'type': 'fibonacci',
                        'subtype': f'extension_{ratio}',
                        'timeframe': timeframe,
                        'base_strength': 2,
                        'timestamp': level_ts,
                        'metadata': {'ratio': ratio, 'direction': 'down',
                                     'wave_high': high, 'wave_low': low, 'wave_time': wave_time}
                    }
                    if price < current_price:
                        supports.append(level)

        logger.info(f"{timeframe} 斐波那契({len(waves)}个波段): {len(supports)}支撑, {len(resistances)}阻力")
        return {'supports': supports, 'resistances': resistances}
    
    # ==================== 2. 多时间框架融合系统 ====================
    
    def calculate_atr(self, timeframe: str, symbol: str = 'BTCUSDT', period: int = 14) -> float:
        """直接从 klines 表的 atr 字段读取最新 ATR(14)"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if self.before_ts:
                cursor.execute(
                    "SELECT atr FROM klines WHERE symbol = %s AND timeframe = %s "
                    "AND atr IS NOT NULL AND timestamp < %s ORDER BY timestamp DESC LIMIT 1",
                    (symbol, timeframe, self.before_ts)
                )
            else:
                cursor.execute(
                    "SELECT atr FROM klines WHERE symbol = %s AND timeframe = %s "
                    "AND atr IS NOT NULL ORDER BY timestamp DESC LIMIT 1",
                    (symbol, timeframe)
                )
            result = cursor.fetchone()
            cursor.close()
            return float(result['atr']) if result and result['atr'] else 0.0
        except mysql.connector.Error as e:
            logger.error(f"读取ATR失败: {e}")
            return 0.0
    
    def merge_nearby_levels(self, levels: List[Dict], atr: float, atr_multiplier: float = 1.0) -> List[Dict]:
        """
        合并相近的支撑阻力位
        
        用相对价格百分比作为合并容差（避免不同周期 ATR 差异过大导致链式合并）
        和组内第一个位点（锚点）比较，防止链式漂移
        """
        if not levels:
            return []
        
        sorted_levels = sorted(levels, key=lambda x: float(x['price']))
        
        # 合并容差：取 ATR 相对比例 和 固定1.5% 中较小的，避免月线 ATR 把所有位点合并
        anchor_price = float(sorted_levels[0]['price']) if sorted_levels else 1
        atr_pct = float(atr) / anchor_price if anchor_price > 0 else 0.015
        merge_pct = min(atr_pct * atr_multiplier, 0.015)  # 最大容差 1.5%
        
        merged = []
        current_group = [sorted_levels[0]]
        group_anchor = float(sorted_levels[0]['price'])  # 锚点：组内第一个价格
        
        for i in range(1, len(sorted_levels)):
            current_val = float(sorted_levels[i]['price'])
            
            # 和锚点比较，防止链式漂移
            if group_anchor > 0 and abs(current_val - group_anchor) / group_anchor <= merge_pct:
                current_group.append(sorted_levels[i])
            else:
                merged.append(self._merge_group(current_group))
                current_group = [sorted_levels[i]]
                group_anchor = current_val  # 新组的锚点
        
        if current_group:
            merged.append(self._merge_group(current_group))
        
        logger.info(f"合并 {len(levels)} 个位点到 {len(merged)} 个区域 (容差={merge_pct*100:.1f}%)")
        return merged
    
    def _merge_group(self, group: List[Dict]) -> Dict:
        """合并一个组内的位点"""
        if not group:
            return {}

        prices    = [float(level['price']) for level in group]
        strengths = [self._extract_strength(level) for level in group]
        max_strength = max(strengths) if strengths else 0

        # 代表价：取强度最高的位点价格（而非平均值，避免漂移到无意义的虚构价格）
        # 同强度时取时间框架权重最高的
        best_level = max(
            group,
            key=lambda l: (
                self._extract_strength(l),
                l.get('timeframe_weight', 1)
            )
        )
        representative_price = float(best_level['price'])

        # 收集时间框架，取平均权重
        timeframes = set()
        tf_weights = []
        for level in group:
            if 'timeframe' in level:
                timeframes.add(level['timeframe'])
            tf_weights.append(level.get('timeframe_weight', 1))
        avg_tf_weight = sum(tf_weights) / len(tf_weights) if tf_weights else 1

        types = set()
        for level in group:
            if 'type' in level:
                types.add(level['type'])

        total_touch = sum(level.get('touch_count', 0) for level in group)

        return {
            'price':        representative_price,
            'price_range':  [min(prices), max(prices)],
            'strength':     max_strength,
            'timeframes':   list(timeframes),
            'types':        list(types),
            'source_count': len(group),
            'sources':      group,
            'is_merged':    True,
            'timeframe_weight': avg_tf_weight,
            'base_strength':    max_strength,
            'touch_count':      total_touch,
        }
    
    def _extract_strength(self, level: Dict) -> int:
        """从位点信息中提取强度"""
        if 'base_strength' in level:
            return level['base_strength']
        elif 'strength' in level:
            return level['strength']
        else:
            # 根据类型分配基础强度
            type_strength = {
                'technical': 2,
                'dynamic': 2,
                'psychological': 2,
                'fibonacci': 2
            }
            return type_strength.get(level.get('type', ''), 1)
    
    def multi_timeframe_analysis(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """
        多时间框架支撑阻力分析
        
        参数:
            symbol: 交易对
        
        返回:
            多时间框架分析结果
        """
        logger.info(f"开始多时间框架支撑阻力分析: {symbol}")
        
        all_supports = []
        all_resistances = []
        
        # 每个时间框架的独立分析结果（用于分周期报告）
        timeframe_results = {}
        
        # 获取当前价格
        current_price = self.get_current_price(symbol)
        if current_price is None:
            logger.error("无法获取当前价格")
            return {'supports': [], 'resistances': []}
        
        # 1. 分析每个时间框架
        for timeframe, config in self.timeframe_config.items():
            logger.info(f"分析 {timeframe} 时间框架...")
            
            # 计算ATR
            atr = self.calculate_atr(timeframe, symbol)
            
            # 识别各种位点
            technical_levels = self.identify_technical_levels(timeframe, symbol, use_optimizer=True)
            dynamic_levels = self.identify_dynamic_levels(timeframe, symbol)
            fib_levels = self.identify_fibonacci_levels(timeframe, symbol)

            # 合并当前时间框架的位点
            timeframe_supports = (
                technical_levels['supports'] +
                dynamic_levels['supports'] +
                fib_levels['supports']
            )
            timeframe_resistances = (
                technical_levels['resistances'] +
                dynamic_levels['resistances'] +
                fib_levels['resistances']
            )

            # 成交量验证：用该时间框架自己的数据，在合并前做
            self._init_optimization_modules()
            if self.volume_system is not None and timeframe_supports + timeframe_resistances:
                ohlcv = self._fetch_ohlcv_for_volume(timeframe, symbol)
                if ohlcv and len(ohlcv.get('closes', [])) >= 20:
                    try:
                        confirmed_sup, confirmed_res = self.volume_system.integrate_with_support_resistance(
                            support_levels=timeframe_supports,
                            resistance_levels=timeframe_resistances,
                            prices=ohlcv['prices'],
                            highs=ohlcv['highs'],
                            lows=ohlcv['lows'],
                            closes=ohlcv['closes'],
                            volumes=ohlcv['volumes'],
                            timestamps=ohlcv['timestamps'],
                        )
                        # 成交量未确认的位点保留但降低置信度，不直接丢弃
                        confirmed_prices_sup = {l['price'] for l in confirmed_sup}
                        confirmed_prices_res = {l['price'] for l in confirmed_res}
                        for lv in timeframe_supports:
                            if lv['price'] not in confirmed_prices_sup:
                                lv.setdefault('volume_confirmation', {'confirmed': False, 'confidence': 0.1})
                        for lv in timeframe_resistances:
                            if lv['price'] not in confirmed_prices_res:
                                lv.setdefault('volume_confirmation', {'confirmed': False, 'confidence': 0.1})
                        # 把确认信息写回原列表
                        for lv in confirmed_sup:
                            for orig in timeframe_supports:
                                if orig['price'] == lv['price']:
                                    orig['volume_confirmation'] = lv.get('volume_confirmation', {})
                                    break
                        for lv in confirmed_res:
                            for orig in timeframe_resistances:
                                if orig['price'] == lv['price']:
                                    orig['volume_confirmation'] = lv.get('volume_confirmation', {})
                                    break
                        logger.debug(f"{timeframe} 成交量验证完成")
                    except Exception as e:
                        logger.warning(f"{timeframe} 成交量验证失败: {e}")

            # RSI 验证：用最新一根K线的RSI判断超买超卖
            rsi_list = ohlcv.get('rsi14', []) if ohlcv else []
            # 取倒数第二根（已收盘），实盘模式下避免未收盘数据
            rsi_idx = -2 if (self.before_ts is None and len(rsi_list) >= 2) else -1
            latest_rsi = rsi_list[rsi_idx] if rsi_list and rsi_list[rsi_idx] is not None else None

            if latest_rsi is not None:
                for lv in timeframe_supports:
                    lv['rsi14'] = latest_rsi
                    # 支撑位：RSI < 35 超卖，反弹概率高
                    if latest_rsi < 35:
                        lv['rsi_signal'] = 'oversold'
                    elif latest_rsi < 50:
                        lv['rsi_signal'] = 'neutral_low'
                    else:
                        lv['rsi_signal'] = 'neutral_high'
                for lv in timeframe_resistances:
                    lv['rsi14'] = latest_rsi
                    # 阻力位：RSI > 65 超买，回落概率高
                    if latest_rsi > 65:
                        lv['rsi_signal'] = 'overbought'
                    elif latest_rsi > 50:
                        lv['rsi_signal'] = 'neutral_high'
                    else:
                        lv['rsi_signal'] = 'neutral_low'
            
            # 添加时间框架权重
            for level in timeframe_supports + timeframe_resistances:
                level['timeframe_weight'] = config['weight']
                level['timeframe'] = timeframe
            
            # 对本周期位点按当前价格校正方向后评分并排序
            # 支撑必须在当前价格下方，阻力必须在上方
            tf_supports_corrected = [l for l in timeframe_supports if l.get('price', 0) < current_price]
            tf_resistances_corrected = [l for l in timeframe_resistances if l.get('price', 0) > current_price]
            # 方向错误的位点交换过去
            tf_supports_corrected += [l for l in timeframe_resistances if l.get('price', 0) < current_price]
            tf_resistances_corrected += [l for l in timeframe_supports if l.get('price', 0) > current_price]
            
            tf_scored_supports = [self.calculate_strength_score(level, 'support', current_price)
                                  for level in tf_supports_corrected]
            tf_scored_resistances = [self.calculate_strength_score(level, 'resistance', current_price)
                                     for level in tf_resistances_corrected]
            tf_scored_supports.sort(key=lambda x: (-x.get('final_score', 0), -(x.get('price', 0))))
            tf_scored_resistances.sort(key=lambda x: (-x.get('final_score', 0), x.get('price', 0)))
            
            timeframe_results[timeframe] = {
                'atr': atr,
                'weight': config['weight'],
                'description': config['description'],
                'supports': tf_scored_supports,
                'resistances': tf_scored_resistances,
            }
            
            all_supports.extend(tf_supports_corrected)
            all_resistances.extend(tf_resistances_corrected)
        
        # 2. 添加心理位（整5000以上加入汇总，整千只做标注）
        psychological_levels = self.identify_psychological_levels(current_price, symbol)
        for level in psychological_levels['supports'] + psychological_levels['resistances']:
            level['timeframe_weight'] = 1
            level['timeframe'] = 'all'

        for lv in psychological_levels['supports']:
            if lv.get('merge_eligible', False):
                lv_scored = self.calculate_strength_score(lv, 'support', current_price)
                all_supports.append(lv_scored)
        for lv in psychological_levels['resistances']:
            if lv.get('merge_eligible', False):
                lv_scored = self.calculate_strength_score(lv, 'resistance', current_price)
                all_resistances.append(lv_scored)

        # 3. 对所有位点评分（各周期位点已在循环里评分，这里补评未评分的）
        for lv in all_supports:
            if 'final_score' not in lv:
                self.calculate_strength_score(lv, 'support', current_price)
        for lv in all_resistances:
            if 'final_score' not in lv:
                self.calculate_strength_score(lv, 'resistance', current_price)

        # 4. 标注共振：相近位点（1.5%以内）互相标注来自哪些周期
        CONFLUENCE_TOL = 0.006  # 0.6%
        SUBTYPE_LABELS = {
            'EMA7': 'EMA7', 'EMA12': 'EMA12', 'EMA25': 'EMA25', 'EMA50': 'EMA50',
            'BOLL_MD': '布林中轨', 'BOLL_UP': '布林上轨', 'BOLL_DN': '布林下轨',
            'swing_low': '摆动低点', 'swing_high': '摆动高点',
            'swing_low_optimized': '摆动低点', 'swing_high_optimized': '摆动高点',
            'retracement_0.382': 'Fib38.2%', 'retracement_0.5': 'Fib50%',
            'retracement_0.618': 'Fib61.8%', 'extension_1.272': 'Fib127.2%',
            'extension_1.618': 'Fib161.8%', 'major': '整五千关口', 'standard': '整千关口',
        }
        TYPE_LABELS = {
            'technical': '技术位', 'dynamic': '动态位',
            'fibonacci': '斐波那契', 'psychological': '心理位',
        }

        def _mark_confluence(levels: List[Dict]):
            for i, lv in enumerate(levels):
                p = lv['price']
                resonant = []
                for j, other in enumerate(levels):
                    if i == j:
                        continue
                    other_p = other['price']
                    if abs(other_p - p) / p <= CONFLUENCE_TOL:
                        tf = other.get('timeframe', '')
                        sub = other.get('subtype', '')
                        type_ = other.get('type', '')
                        label = SUBTYPE_LABELS.get(sub, '') or TYPE_LABELS.get(type_, '')
                        tf_label = {'1M': '月', '1w': '周', '1d': '日', '4h': '4H', 'all': '通用'}.get(tf, tf)
                        diff_pts = other_p - p
                        diff_pct = diff_pts / p * 100
                        sign = '+' if diff_pts >= 0 else ''
                        dist_str = f"{sign}{diff_pts:,.0f}点/{sign}{diff_pct:.2f}%"
                        ts = other.get('timestamp')
                        if ts:
                            tf_fmt = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}.get(tf, '%m-%d')
                            time_str = datetime.fromtimestamp(ts / 1000).strftime(tf_fmt)
                        else:
                            time_str = ''
                        # 斐波那契附加波段时间范围，去掉单独的时间戳（波段时间已包含）
                        wave_str = ''
                        if type_ == 'fibonacci':
                            meta = other.get('metadata', {})
                            wave_time = meta.get('wave_time', '')
                            wave_high = meta.get('wave_high', 0)
                            wave_low  = meta.get('wave_low', 0)
                            if wave_high and wave_low:
                                wave_str = f" 波段${wave_low:,.0f}~${wave_high:,.0f}"
                                if wave_time:
                                    wave_str += f" {wave_time}"
                            time_str = ''  # 波段时间已包含，不再单独显示
                        time_part = f" {time_str}" if time_str else ''
                        note = f"{tf_label}:{label} | ${other_p:,.0f}({dist_str}{time_part}{wave_str})" if label else f"{tf_label} | ${other_p:,.0f}({dist_str}{time_part}{wave_str})"
                        resonant.append(note)
                lv['confluence_notes'] = list(dict.fromkeys(resonant))  # 去重保序

        _mark_confluence(all_supports)
        _mark_confluence(all_resistances)

        # 5. 相近位点合并（差距 < $500 合并为一个，保留评分最高的作代表）
        MERGE_THRESHOLD = 500  # 美元

        def _merge_close_levels(levels: List[Dict]) -> List[Dict]:
            if not levels:
                return []
            # 按价格排序
            sorted_lvs = sorted(levels, key=lambda x: x['price'])
            merged = []
            group = [sorted_lvs[0]]
            for lv in sorted_lvs[1:]:
                if abs(lv['price'] - group[-1]['price']) < MERGE_THRESHOLD:
                    group.append(lv)
                else:
                    merged.append(_pick_best(group))
                    group = [lv]
            merged.append(_pick_best(group))
            return merged

        def _pick_best(group: List[Dict]) -> Dict:
            """取评分最高的作代表，其余作为合并注释"""
            best = max(group, key=lambda x: x.get('final_score', 0))
            if len(group) > 1:
                others = [l for l in group if l is not best]
                extra_notes = []
                for o in others:
                    tf = o.get('timeframe', '')
                    sub = o.get('subtype', '')
                    type_ = o.get('type', '')
                    tf_label = {'1M': '月', '1w': '周', '1d': '日', '4h': '4H', 'all': '通用'}.get(tf, tf)
                    label = SUBTYPE_LABELS.get(sub, '') or TYPE_LABELS.get(type_, type_)
                    diff_pts = o['price'] - best['price']
                    diff_pct = diff_pts / best['price'] * 100
                    sign = '+' if diff_pts >= 0 else ''
                    dist_str = f"{sign}{diff_pts:,.0f}点/{sign}{diff_pct:.2f}%"
                    ts = o.get('timestamp')
                    if ts:
                        tf_fmt = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}.get(tf, '%m-%d')
                        time_str = datetime.fromtimestamp(ts / 1000).strftime(tf_fmt)
                    else:
                        time_str = ''
                    wave_str = ''
                    if type_ == 'fibonacci':
                        meta = o.get('metadata', {})
                        wave_time = meta.get('wave_time', '')
                        wave_high = meta.get('wave_high', 0)
                        wave_low  = meta.get('wave_low', 0)
                        if wave_high and wave_low:
                            wave_str = f" 波段${wave_low:,.0f}~${wave_high:,.0f}"
                            if wave_time:
                                wave_str += f" {wave_time}"
                        time_str = ''  # 波段时间已包含
                    time_part = f" {time_str}" if time_str else ''
                    note = f"{tf_label}:{label} | ${o['price']:,.0f}({dist_str}{time_part}{wave_str})" if label else f"{tf_label} | ${o['price']:,.0f}({dist_str}{time_part}{wave_str})"
                    extra_notes.append(note)
                existing = best.get('confluence_notes', [])
                best['confluence_notes'] = list(dict.fromkeys(existing + extra_notes))
            return best

        all_supports   = _merge_close_levels(all_supports)
        all_resistances = _merge_close_levels(all_resistances)

        # 6. 按距离当前价格排序，取最近各5个
        all_supports.sort(key=lambda x: current_price - x['price'])
        all_resistances.sort(key=lambda x: x['price'] - current_price)
        top_supports    = all_supports[:5]
        top_resistances = all_resistances[:5]

        base_atr = self.calculate_atr('4h', symbol)

        logger.info(f"✅ 分析完成: 上方{len(top_resistances)}阻力, 下方{len(top_supports)}支撑")

        return {
            'symbol':        symbol,
            'current_price': current_price,
            'base_atr':      base_atr,
            'supports':      top_supports,
            'resistances':   top_resistances,
            'timeframe_results': timeframe_results,
            'analysis_time': datetime.now().isoformat(),
            'timeframes_analyzed': list(self.timeframe_config.keys()),
            'optimizations': {
                'swing_point_filter':   self.swing_optimizer is not None,
                'fibonacci_calculation': self.fib_calculator is not None,
                'volume_confirmation':  self.volume_system is not None,
            }
        }
    
    def get_current_price(self, symbol: str = 'BTCUSDT') -> Optional[float]:
        """获取当前价格：优先从 Binance 实时 ticker 拉取，失败时降级用最近 4H 收盘价"""

        # 回测模式：直接用历史 4H 收盘价，不请求实时接口
        if not self.before_ts:
            try:
                url = f"https://api.binance.com/api/v3/ticker/price"
                resp = requests.get(url, params={'symbol': symbol}, timeout=5)
                resp.raise_for_status()
                price = float(resp.json()['price'])
                logger.debug(f"✅ 实时价格: {symbol} = {price}")
                return price
            except Exception as e:
                logger.warning(f"⚠️ 实时价格获取失败，降级用 4H 收盘价: {e}")

        # 降级 / 回测：从数据库取最近 4H 收盘价
        try:
            cursor = self.connection.cursor(dictionary=True)
            if self.before_ts:
                query = """
                    SELECT close FROM klines
                    WHERE symbol = %s AND timeframe = '4h' AND timestamp < %s
                    ORDER BY timestamp DESC LIMIT 1
                """
                cursor.execute(query, (symbol, self.before_ts))
            else:
                query = """
                    SELECT close FROM klines
                    WHERE symbol = %s AND timeframe = '4h'
                    ORDER BY timestamp DESC LIMIT 1
                """
                cursor.execute(query, (symbol,))
            result = cursor.fetchone()
            cursor.close()
            return ensure_float(result['close']) if result else None
        except Exception as e:
            logger.error(f"获取当前价格失败: {e}")
            return None
    
    def _fetch_ohlcv_for_volume(self, timeframe: str, symbol: str, limit: int = 300) -> Dict:
        """获取某时间框架的 OHLCV+RSI 序列，用于成交量和RSI验证（正序）"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if self.before_ts:
                cursor.execute(
                    "SELECT timestamp, high, low, close, volume, rsi14 FROM klines "
                    "WHERE symbol=%s AND timeframe=%s AND timestamp<%s "
                    "ORDER BY timestamp DESC LIMIT %s",
                    (symbol, timeframe, self.before_ts, limit)
                )
            else:
                cursor.execute(
                    "SELECT timestamp, high, low, close, volume, rsi14 FROM klines "
                    "WHERE symbol=%s AND timeframe=%s "
                    "ORDER BY timestamp DESC LIMIT %s",
                    (symbol, timeframe, limit)
                )
            rows = list(reversed(cursor.fetchall()))
            cursor.close()
            return {
                'prices':     [ensure_float(r['close'])  for r in rows],
                'highs':      [ensure_float(r['high'])   for r in rows],
                'lows':       [ensure_float(r['low'])    for r in rows],
                'closes':     [ensure_float(r['close'])  for r in rows],
                'volumes':    [ensure_float(r['volume']) for r in rows],
                'timestamps': [r['timestamp']            for r in rows],
                'rsi14':      [ensure_float(r['rsi14']) if r['rsi14'] is not None else None for r in rows],
            }
        except Exception as e:
            logger.warning(f"获取 {timeframe} OHLCV 失败: {e}")
            return {}
        """获取价格数据用于成交量分析"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM klines 
                WHERE symbol = %s AND timeframe = %s
                ORDER BY timestamp ASC
                LIMIT %s
            """
            
            cursor.execute(query, (symbol, timeframe, limit))
            data = cursor.fetchall()
            cursor.close()
            
            if not data:
                return None
            
            return {
                'timestamps': [row['timestamp'] for row in data],
                'opens': [ensure_float(row['open']) for row in data],
                'highs': [ensure_float(row['high']) for row in data],
                'lows': [ensure_float(row['low']) for row in data],
                'closes': [ensure_float(row['close']) for row in data],
                'volumes': [ensure_float(row['volume']) for row in data]
            }
            
        except Exception as e:
            logger.error(f"获取价格数据失败: {e}")
            return None
    
    # ==================== 3. 智能评分计算器 ====================
    
    def calculate_strength_score(self, level: Dict, level_type: str, current_price: float) -> Dict:
        """
        综合强度评分

        权重分配（总100%）：
        - 触碰/置信度         50%  （历史验证次数，最能预测位点有效性）
        - 多时间框架共振      30%  （跨越几个不同周期，越多越可靠）
        - 时间框架权威性      20%  （平均周期权重，区分纯月线 vs 多周期融合）
        """
        score = 0.0
        score_factors = {}

        # ── 1. 触碰/置信度（50%）────────────────────────────────
        # 优先用 touch_count（最直接的历史验证），
        # 优化器的 confidence 作为辅助参考而非覆盖
        tc = level.get('touch_count', 0)
        if tc > 0:
            # 1次=0.3, 2次=0.5, 3次=0.7, 4次=0.9, 5次以上=1.0
            confidence_score = min(0.2 * tc + 0.1, 1.0)
            # 优化器有 confidence 时，取两者均值（互相印证）
            if 'confidence' in level:
                confidence_score = (confidence_score + float(level['confidence'])) / 2
        elif 'confidence' in level:
            confidence_score = float(level['confidence'])
        elif 'base_strength' in level:
            confidence_score = min(level['base_strength'] / 5.0, 1.0)
        elif 'importance' in level:
            confidence_score = level['importance'] / 3.0
        else:
            confidence_score = 0.2  # 无任何历史验证，给低分

        score += confidence_score * self.params['score_weight_confidence']
        score_factors['confidence'] = round(confidence_score, 3)

        # ── 2. 时间框架权威性（25%）─────────────────────────────
        # 范围 1~4，归一化到 0~1：1→0, 2→0.33, 3→0.67, 4→1.0
        timeframe_weight = level.get('timeframe_weight', 1)
        timeframe_score  = (timeframe_weight - 1) / 3.0
        score += timeframe_score * self.params['score_weight_timeframe']
        score_factors['timeframe'] = round(timeframe_score, 3)

        # ── 3. 成交量确认（15%）──────────────────────────────────
        vol_conf = level.get('volume_confirmation', {})
        if vol_conf:
            if vol_conf.get('confirmed', False):
                volume_score = min(0.4 + vol_conf.get('confidence', 0.5) * 0.6, 1.0)
            else:
                volume_score = max(vol_conf.get('confidence', 0.1) * 0.4, 0.05)
        else:
            volume_score = self.params['score_volume_default']
        score += volume_score * self.params['score_weight_volume']
        score_factors['volume'] = round(volume_score, 3)

        # ── 4. RSI 确认（15%）────────────────────────────────────
        rsi_signal = level.get('rsi_signal', '')
        rsi_val    = level.get('rsi14')
        if level_type == 'support':
            if rsi_signal == 'oversold':       # RSI < 35，超卖，支撑有效性高
                rsi_score = 1.0
            elif rsi_signal == 'neutral_low':  # RSI 35-50，中性偏低
                rsi_score = 0.6
            elif rsi_signal == 'neutral_high': # RSI > 50，偏高，支撑效果打折
                rsi_score = 0.3
            else:
                rsi_score = 0.5                # 无数据，中性
        else:  # resistance
            if rsi_signal == 'overbought':     # RSI > 65，超买，阻力有效性高
                rsi_score = 1.0
            elif rsi_signal == 'neutral_high': # RSI 50-65，中性偏高
                rsi_score = 0.6
            elif rsi_signal == 'neutral_low':  # RSI < 50，偏低，阻力效果打折
                rsi_score = 0.3
            else:
                rsi_score = 0.5
        score += rsi_score * self.params['score_weight_rsi']
        score_factors['rsi'] = round(rsi_score, 3)
        if rsi_val:
            score_factors['rsi14'] = round(rsi_val, 1)

        # ── 转换为 1~15 分（用 round 避免 int 向下取整的分布不均）──
        final_score = max(0.0, min(score, 1.0))
        final_score_15 = max(1, min(15, round(final_score * 14) + 1))

        strength_level = self._map_score_to_level(final_score_15)

        level['final_score']            = final_score_15
        level['final_score_normalized'] = round(final_score, 4)
        level['score_factors']          = score_factors
        level['strength_level']         = strength_level['level']
        level['strength_symbol']        = strength_level['symbol']
        level['stop_buffer_multiplier'] = strength_level['buffer_multiplier']

        return level
    
    def _calculate_timeframe_score(self, level: Dict) -> int:
        """计算时间框架权威性分数"""
        timeframes = level.get('timeframes', [])
        if not timeframes:
            return 1
        
        # 取最高时间框架权重
        max_weight = 0
        for tf in timeframes:
            weight = self.timeframe_config.get(tf, {}).get('weight', 0)
            max_weight = max(max_weight, weight)
        
        return max_weight  # 1-4分
    
    def _calculate_confluence_score(self, level: Dict) -> int:
        """计算技术位重合度分数"""
        types = level.get('types', [])
        sources = level.get('sources', [])
        
        score = 0
        
        # 检查技术位重合
        if 'technical' in types:
            score += 1
        
        # 检查多个来源
        if len(sources) >= 2:
            score += 1
        if len(sources) >= 3:
            score += 1
        
        return min(score, 3)  # 0-3分
    
    def _calculate_dynamic_score(self, level: Dict) -> int:
        """计算动态位重合度分数"""
        types = level.get('types', [])
        sources = level.get('sources', [])
        
        score = 0
        
        # 检查动态位重合
        if 'dynamic' in types:
            score += 1
        
        # 检查多个动态指标
        dynamic_sources = [s for s in sources if s.get('type') == 'dynamic']
        if len(dynamic_sources) >= 2:
            score += 1
        
        # 检查布林带重合
        boll_sources = [s for s in sources if 'boll' in str(s.get('subtype', '')).lower()]
        if boll_sources:
            score += 1
        
        return min(score, 3)  # 0-3分
    
    def _calculate_psychological_score(self, level: Dict) -> int:
        """计算心理位重合分数"""
        types = level.get('types', [])
        
        score = 0
        
        # 检查心理位重合
        if 'psychological' in types:
            score += 1
        
        # 检查是否为重要心理位
        price = level.get('price', 0)
        if price % 5000 == 0:  # 五千关口
            score += 1
        
        return min(score, 2)  # 0-2分
    
    def _calculate_recent_score(self, level: Dict, current_price: float) -> int:
        """计算近期有效性分数"""
        if current_price == 0:
            return 0
        
        # 检查是否接近当前价格（±5%）
        price = level.get('price', 0)
        distance_pct = abs(current_price - price) / current_price
        
        if distance_pct <= 0.05:  # 5%以内
            return 1
        else:
            return 0
    
    def _map_score_to_level(self, score: int) -> Dict:
        """将分数映射到强度等级"""
        if score >= 13:
            return {'level': '极强', 'symbol': '★★★★★', 'buffer_multiplier': 0.3}
        elif score >= 10:
            return {'level': '强', 'symbol': '★★★★', 'buffer_multiplier': 0.5}
        elif score >= 7:
            return {'level': '中等', 'symbol': '★★★', 'buffer_multiplier': 0.7}
        elif score >= 4:
            return {'level': '弱', 'symbol': '★★', 'buffer_multiplier': 1.0}
        else:
            return {'level': '极弱', 'symbol': '★', 'buffer_multiplier': 1.2}
    
    # ==================== 报告生成 ====================
    
    def generate_report(self, analysis_result: Dict) -> str:
        """生成分析报告：先输出各周期，再输出综合"""
        symbol = analysis_result.get('symbol', 'BTCUSDT')
        current_price = analysis_result.get('current_price', 0)
        base_atr = analysis_result.get('base_atr', 0)
        timeframe_results = analysis_result.get('timeframe_results', {})

        SUBTYPE_LABELS = {
            'EMA7': 'EMA7', 'EMA12': 'EMA12', 'EMA25': 'EMA25', 'EMA50': 'EMA50',
            'BOLL_MD': '布林中轨', 'BOLL_UP': '布林上轨', 'BOLL_DN': '布林下轨',
            'swing_low': '摆动低点', 'swing_high': '摆动高点',
            'swing_low_optimized': '摆动低点', 'swing_high_optimized': '摆动高点',
            'retracement_0.382': 'Fib38.2%', 'retracement_0.5': 'Fib50%',
            'retracement_0.618': 'Fib61.8%', 'extension_1.272': 'Fib127.2%',
            'extension_1.618': 'Fib161.8%', 'major': '整五千关口', 'standard': '整千关口',
        }
        TYPE_LABELS = {
            'technical': '技术位', 'dynamic': '动态位',
            'fibonacci': '斐波那契', 'psychological': '心理位',
        }

        def _level_desc(level: Dict) -> str:
            """生成位点描述：周期 + 具体类型（斐波那契加波段时间范围）"""
            tf      = level.get('timeframe', '')
            subtype = level.get('subtype', '')
            type_   = level.get('type', '')
            tf_label = {'1M': '月线', '1w': '周线', '1d': '日线', '4h': '4H', 'all': '通用'}.get(tf, tf)
            detail   = SUBTYPE_LABELS.get(subtype, '') or TYPE_LABELS.get(type_, type_)

            # 斐波那契：附加波段时间范围和高低点
            if type_ == 'fibonacci':
                meta = level.get('metadata', {})
                wave_time = meta.get('wave_time', '')
                wave_high = meta.get('wave_high', 0)
                wave_low  = meta.get('wave_low', 0)
                wave_info = ''
                if wave_high and wave_low:
                    wave_info = f"[波段${wave_low:,.0f}~${wave_high:,.0f}"
                    if wave_time:
                        wave_info += f" {wave_time}"
                    wave_info += ']'
                return f"{tf_label} {detail} {wave_info}".strip()

            return f"{tf_label} {detail}" if detail else tf_label

        def _vol_tag(level: Dict) -> str:
            """成交量确认标签"""
            vc = level.get('volume_confirmation', {})
            vol_str = ''
            if vc:
                if vc.get('confirmed'):
                    vol_str = f" 📊量确认{vc.get('confidence', 0):.0%}"
                else:
                    vol_str = ' 📊量未确认'
            # RSI 标注
            rsi_signal = level.get('rsi_signal', '')
            rsi_val    = level.get('rsi14')
            rsi_str = ''
            if rsi_val:
                rsi_icon = {'oversold': '🔵超卖', 'overbought': '🔴超买',
                            'neutral_low': '', 'neutral_high': ''}.get(rsi_signal, '')
                rsi_str = f" RSI{rsi_val:.0f}{' ' + rsi_icon if rsi_icon else ''}"
            return vol_str + rsi_str

        def _psych_tag(price: float) -> str:
            return ''
        
        report = []
        report.append("=" * 60)
        report.append(f"📊 {symbol} 支撑阻力分析报告")
        report.append(f"时间: {analysis_result.get('analysis_time', 'N/A')[:19]}")
        report.append("=" * 60)

        tf_order = ['1M', '1w', '1d', '4h']
        tf_labels = {
            '1M': '月线 1M（战略层）',
            '1w': '周线 1w（战役层）',
            '1d': '日线 1d（战术层）',
            '4h': '4H（执行层）',
        }

        for tf in tf_order:
            if tf not in timeframe_results:
                continue
            tf_data = timeframe_results[tf]
            tf_supports    = tf_data.get('supports', [])
            tf_resistances = tf_data.get('resistances', [])
            atr_val = tf_data.get('atr', 0)

            report.append(f"\n【{tf_labels[tf]}】  ATR={atr_val:,.0f}")
            report.append(f"{'─'*60}")

            report.append("  📉 阻力:")
            for level in sorted(tf_resistances, key=lambda x: x.get('price', 0))[:5]:
                price = level.get('price', 0)
                score = level.get('final_score', 0)
                stars = level.get('strength_symbol', '★')
                desc  = _level_desc(level)
                vol   = _vol_tag(level)
                dist  = (price - current_price) / current_price * 100
                report.append(f"    {stars} ${price:,.2f}  +{dist:.1f}%  [{score}/15]  {desc}{vol}")

            report.append("  📈 支撑:")
            for level in sorted(tf_supports, key=lambda x: x.get('price', 0), reverse=True)[:5]:
                price = level.get('price', 0)
                score = level.get('final_score', 0)
                stars = level.get('strength_symbol', '★')
                desc  = _level_desc(level)
                vol   = _vol_tag(level)
                dist  = (current_price - price) / current_price * 100
                report.append(f"    {stars} ${price:,.2f}  -{dist:.1f}%  [{score}/15]  {desc}{vol}")
        
        # ── 综合分析 ──
        report.append(f"\n{'='*60}")
        report.append(f"🔥 综合分析  当前价格: ${current_price:,.2f}  ATR: ${base_atr:,.2f}")
        report.append(f"{'='*60}")

        supports   = analysis_result.get('supports', [])
        resistances = analysis_result.get('resistances', [])

        def _fmt_level(i, level, direction):
            price  = level.get('price', 0)
            score  = level.get('final_score', 0)
            stars  = level.get('strength_symbol', '★')
            desc   = _level_desc(level)
            vol    = _vol_tag(level)
            dist   = abs(price - current_price) / current_price * 100
            sign   = '+' if direction == 'res' else '-'
            lines  = [f"  {i}. {stars} ${price:,.2f}  {sign}{dist:.1f}%  [{score}/15]  {desc}{vol}"]
            notes  = level.get('confluence_notes', [])
            if notes:
                lines.append(f"     ⚡ " + '\n       '.join(notes[:3]))
            return lines

        report.append("\n  � 阻力位（由近到远）")
        report.append(f"  {'─'*56}")
        res_sorted = sorted(resistances, key=lambda x: x.get('price', 0))
        if res_sorted:
            for i, r in enumerate(res_sorted, 1):
                for line in _fmt_level(i, r, 'res'):
                    report.append(line)
        else:
            report.append("  未识别到阻力位")

        report.append(f"\n  📈 支撑位（由近到远）")
        report.append(f"  {'─'*56}")
        sup_sorted = sorted(supports, key=lambda x: x.get('price', 0), reverse=True)
        if sup_sorted:
            for i, s in enumerate(sup_sorted, 1):
                for line in _fmt_level(i, s, 'sup'):
                    report.append(line)
        else:
            report.append("  未识别到支撑位")

        # 交易建议
        report.append(f"\n{'─'*60}")
        nearest_res = res_sorted[0] if res_sorted else None
        nearest_sup = sup_sorted[0] if sup_sorted else None
        if nearest_res and nearest_sup:
            rr = (nearest_res['price'] - current_price) / (current_price - nearest_sup['price'])
            rr_str = f"盈亏比(做多): {rr:.2f}  {'✅ 可做多' if rr >= 2 else '⚠️ 盈亏比不足'}"
            report.append(f"💡 上方阻力: ${nearest_res['price']:,.2f} ({nearest_res.get('strength_symbol','★')})  "
                          f"下方支撑: ${nearest_sup['price']:,.2f} ({nearest_sup.get('strength_symbol','★')})  "
                          f"{rr_str}")
        report.append(f"{'='*60}")
        return "\n".join(report)
    
    def save_report(self, analysis_result: Dict, filepath: str = None):
        """保存分析结果到文件"""
        if filepath is None:
            import os
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"/tmp/support_resistance_{timestamp}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            logger.info(f"分析结果已保存到: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
            return None
    
    def print_volume_detail(self, symbol: str = 'BTCUSDT'):
        """
        打印每个位点的成交量确认详情，用于业务验证。
        输出每次触及的：时间、价格、成交量比率、价格行为、置信度。
        """
        self._init_optimization_modules()
        if self.volume_system is None:
            print("❌ 成交量确认模块未加载")
            return

        current_price = self.get_current_price(symbol)
        print(f"\n当前价格: ${current_price:,.2f}")

        tf_fmt_map = {'1M': '%Y-%m', '1w': '%Y-%m-%d', '1d': '%Y-%m-%d', '4h': '%m-%d %H:%M'}

        for tf in ['1M', '1w', '1d', '4h']:
            print(f"\n{'='*60}")
            print(f"【{tf}】成交量确认详情")
            print(f"{'='*60}")

            # 取该周期所有位点
            tech  = self.identify_technical_levels(tf, symbol, use_optimizer=False)
            dyn   = self.identify_dynamic_levels(tf, symbol)
            fib   = self.identify_fibonacci_levels(tf, symbol)
            all_levels = (tech['supports'] + tech['resistances'] +
                          dyn['supports']  + dyn['resistances'] +
                          fib['supports']  + fib['resistances'])

            if not all_levels:
                print("  无位点")
                continue

            # 取该周期 OHLCV
            ohlcv = self._fetch_ohlcv_for_volume(tf, symbol)
            if not ohlcv or len(ohlcv.get('closes', [])) < 20:
                print("  数据不足")
                continue

            prices     = ohlcv['prices']
            highs      = ohlcv['highs']
            lows       = ohlcv['lows']
            closes     = ohlcv['closes']
            volumes    = ohlcv['volumes']
            timestamps = ohlcv['timestamps']
            tf_fmt     = tf_fmt_map.get(tf, '%m-%d')

            for lv in all_levels[:8]:  # 每个周期最多显示8个位点
                price   = lv['price']
                subtype = lv.get('subtype', '')
                ltype   = lv.get('type', '')
                label   = f"{ltype}/{subtype}" if subtype else ltype
                direction = '支撑' if price < current_price else '阻力'

                print(f"\n  [{direction}] ${price:,.2f}  {label}")
                print(f"  {'─'*50}")

                # 找触及K线
                tol = price * self.volume_system.config['price_tolerance_pct']
                test_series = lows if direction == '支撑' else highs
                test_indices = [i for i, v in enumerate(test_series)
                                if abs(v - price) <= tol]

                if not test_indices:
                    print(f"    历史无触及记录（容差±{tol:,.0f}）")
                    continue

                print(f"    触及次数: {len(test_indices)}  容差: ±{tol:,.0f}")
                print(f"    {'时间':18} {'触及价':>10} {'量比':>6} {'价格行为':>8} {'置信度':>6}")
                print(f"    {'─'*18} {'─'*10} {'─'*6} {'─'*8} {'─'*6}")

                confidences = []
                for idx in test_indices:
                    ts_str = datetime.fromtimestamp(timestamps[idx]/1000).strftime(tf_fmt)
                    touch_price = test_series[idx]

                    # 成交量比率（用前20根均量）
                    lb = max(0, idx - 20)
                    avg_vol = sum(volumes[lb:idx]) / max(len(volumes[lb:idx]), 1)
                    vol_ratio = volumes[idx] / avg_vol if avg_vol > 0 else 1.0

                    # 价格行为
                    if idx == 0 or idx >= len(closes) - 1:
                        pa = 'unknown'
                    else:
                        cur_c  = closes[idx]
                        next_c = closes[idx+1] if idx+1 < len(closes) else cur_c
                        if direction == '支撑':
                            if cur_c > price and next_c > cur_c:
                                pa = 'bounce ✅'
                            elif cur_c < price and next_c < cur_c:
                                pa = 'break  ❌'
                            else:
                                pa = 'consol ~'
                        else:
                            if cur_c < price and next_c < cur_c:
                                pa = 'reject ✅'
                            elif cur_c > price and next_c > cur_c:
                                pa = 'break  ❌'
                            else:
                                pa = 'consol ~'

                    # 置信度（原算法）
                    test_result = self.volume_system._analyze_single_test(
                        idx, price, prices, highs, lows, closes, volumes,
                        'support' if direction == '支撑' else 'resistance'
                    )
                    conf = test_result.get('confidence', 0)
                    confidences.append(conf)

                    print(f"    {ts_str:18} ${touch_price:>9,.0f} {vol_ratio:>5.1f}x {pa:>10} {conf:>5.0%}")

                avg_conf = sum(confidences) / len(confidences) if confidences else 0
                confirmed = avg_conf >= 0.6
                print(f"    → 平均置信度: {avg_conf:.0%}  {'✅ 确认' if confirmed else '❌ 未确认'}")

    def run_analysis(self, symbol: str = 'BTCUSDT', output_file: str = None) -> Dict[str, Any]:
        """
        运行完整的支撑阻力分析
        
        参数:
            symbol: 交易对
            output_file: 输出文件路径（可选）
        
        返回:
            分析结果
        """
        logger.info(f"🚀 开始运行支撑阻力分析: {symbol}")
        
        # 连接数据库
        if not self.connect():
            return {'error': '数据库连接失败'}
        
        try:
            # 运行多时间框架分析
            analysis_result = self.multi_timeframe_analysis(symbol)
            
            # 生成报告
            report_text = self.generate_report(analysis_result)
            print(report_text)
            
            # 保存结果
            if output_file:
                saved_path = self.save_report(analysis_result, output_file)
                if saved_path:
                    print(f"\n📁 分析结果已保存到: {saved_path}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}
        
        finally:
            self.disconnect()


# ==================== 命令行接口 ====================

def main():
    """命令行主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='支撑阻力分析工具 - 第一阶段核心功能')
    parser.add_argument('--host', default='localhost', help='MySQL主机')
    parser.add_argument('--port', type=int, default=3306, help='MySQL端口')
    parser.add_argument('--user', default='root', help='MySQL用户')
    parser.add_argument('--password', default='', help='MySQL密码')
    parser.add_argument('--database', default='btc_assistant', help='数据库名')
    parser.add_argument('--symbol', default='BTCUSDT', help='交易对')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--test', action='store_true', help='测试模式')
    parser.add_argument('--volume-detail', action='store_true', help='打印成交量确认详情（用于业务验证）')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = SupportResistanceAnalyzerPhase1(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    if getattr(args, 'volume_detail', False):
        analyzer = SupportResistanceAnalyzerPhase1(
            host=args.host, port=args.port, user=args.user,
            password=args.password, database=args.database
        )
        if analyzer.connect():
            try:
                analyzer.print_volume_detail(args.symbol)
            finally:
                analyzer.disconnect()
        return

    if args.test:
        print("🧪 测试模式 - 验证核心功能")
        
        # 连接数据库
        if not analyzer.connect():
            print("❌ 数据库连接失败")
            return
        
        try:
            # 测试获取当前价格
            current_price = analyzer.get_current_price(args.symbol)
            print(f"✅ 当前价格: ${current_price:,.2f}")
            
            # 测试计算ATR
            atr = analyzer.calculate_atr('4h', args.symbol)
            print(f"✅ 4H ATR(14): ${atr:,.2f}")
            
            # 测试识别技术位
            technical_levels = analyzer.identify_technical_levels('4h', args.symbol)
            print(f"✅ 4H技术位: {len(technical_levels['supports'])}支撑, {len(technical_levels['resistances'])}阻力")
            
            # 测试识别动态位
            dynamic_levels = analyzer.identify_dynamic_levels('4h', args.symbol)
            print(f"✅ 4H动态位: {len(dynamic_levels['supports'])}支撑, {len(dynamic_levels['resistances'])}阻力")
            
            # 测试识别心理位
            if current_price:
                psychological_levels = analyzer.identify_psychological_levels(current_price, args.symbol)
                print(f"✅ 心理位: {len(psychological_levels['supports'])}支撑, {len(psychological_levels['resistances'])}阻力")
            
            print("\n✅ 所有核心功能测试通过!")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            analyzer.disconnect()
    
    else:
        # 运行完整分析
        analyzer.run_analysis(symbol=args.symbol, output_file=args.output)


if __name__ == "__main__":
    main()