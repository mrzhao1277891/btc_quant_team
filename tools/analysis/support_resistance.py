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
            # 窗口大小：左右各看几根K线来判断极值点，越大越严格，识别的点越少
            'swing_window': 3,
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
            # 回撤比例列表（黄金分割 0.382/0.618 强度+1）
            'fib_retracement_ratios': [0.236, 0.382, 0.5, 0.618, 0.786],
            # 延伸比例列表
            'fib_extension_ratios': [1.272, 1.618, 2.0],
            
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
            
            # ── 评分权重（四项之和应为 1.0）────────────────────────────
            # 时间框架权威性：大周期位点更可靠
            'score_weight_timeframe': 0.35,
            # 触碰/置信度：历史验证次数越多越可靠
            'score_weight_confidence': 0.35,
            # 成交量确认：有量才有效
            'score_weight_volume': 0.15,
            # 距离当前价格：近的参考价值高，但不主导评分
            'score_weight_distance': 0.15,
            # 无成交量数据时的默认分（0~1）
            'score_volume_default': 0.4,
            
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
    
    def find_swing_points(self, prices: List[float], window: int = None, min_amplitude: float = None) -> Tuple[List[int], List[int]]:
        """
        优化版摆动点识别算法
        
        参数:
            prices: 价格序列
            window: 观察窗口大小（默认3，降低以识别更多摆动点）
            min_amplitude: 最小波动幅度（默认0.3%，BTC大价格适配）
        
        返回:
            (swing_highs, swing_lows): 摆动高点索引列表，摆动低点索引列表
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
        
        for i in range(window, n - window):
            # 检查是否为摆动高点
            is_high = all(prices[i] > prices[i - j] and prices[i] > prices[i + j]
                          for j in range(1, window + 1))
            
            # 检查是否为摆动低点
            is_low = all(prices[i] < prices[i - j] and prices[i] < prices[i + j]
                         for j in range(1, window + 1))
            
            # 过滤微小波动（用周围均值计算相对幅度）
            if is_high or is_low:
                avg_surrounding = (sum(prices[i - window:i]) + sum(prices[i + 1:i + window + 1])) / (window * 2)
                if avg_surrounding == 0:
                    continue
                amplitude = abs(prices[i] - avg_surrounding) / avg_surrounding
                if is_high and amplitude >= min_amplitude:
                    swing_highs.append(i)
                if is_low and amplitude >= min_amplitude:
                    swing_lows.append(i)
        
        logger.info(f"识别到 {len(swing_highs)} 个摆动高点和 {len(swing_lows)} 个摆动低点")
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
            query = """
                SELECT timestamp, high, low, close, volume
                FROM klines 
                WHERE symbol = %s AND timeframe = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            
            lookback = self.timeframe_config[timeframe]['lookback'] * 3
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
                    window=self.params['swing_window'],
                    min_amplitude=self.params['swing_min_amplitude_fallback']
                )
                
                for idx in swing_lows_idx:
                    price = lows[idx]
                    level = {
                        'price': price,
                        'timestamp': timestamps[idx],
                        'type': 'technical',
                        'subtype': 'swing_low',
                        'timeframe': timeframe,
                        'touch_count': 1,
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
                    level = {
                        'price': price,
                        'timestamp': timestamps[idx],
                        'type': 'technical',
                        'subtype': 'swing_high',
                        'timeframe': timeframe,
                        'touch_count': 1,
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
            
            query = """
                SELECT timestamp, close,
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
            
            # 提取历史收盘价序列（正序）用于触碰验证
            history = list(reversed(data))  # 从旧到新
            hist_closes = [ensure_float(r['close']) for r in history]
            
            supports = []
            resistances = []
            
            for defn in dynamic_level_defs:
                raw_price = latest.get(defn['key'])
                if raw_price is None:
                    continue
                level_price = ensure_float(raw_price)
                if level_price <= 0:
                    continue
                
                # 历史触碰验证：统计过去N根K线中价格在该均线附近反转的次数
                tolerance = level_price * self.params['dynamic_touch_tolerance']
                touch_count = 0
                for i in range(1, len(hist_closes) - 1):
                    if abs(hist_closes[i] - level_price) <= tolerance:
                        # 判断是否发生反转（前后方向不同）
                        if (hist_closes[i-1] < hist_closes[i] and hist_closes[i] > hist_closes[i+1]) or \
                           (hist_closes[i-1] > hist_closes[i] and hist_closes[i] < hist_closes[i+1]):
                            touch_count += 1
                
                # 触碰次数加成强度（最多+2）
                touch_bonus = min(touch_count, self.params['dynamic_touch_bonus_max'])
                final_weight = defn['weight'] + touch_bonus
                
                level_info = {
                    'price': level_price,
                    'timestamp': latest['timestamp'],
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
                if base % self.params['psych_major_interval'] == 0:
                    strength = 3
                if abs(current_price - base) / current_price < 0.01:  # 接近当前价格
                    strength += 1
                
                level_info = {
                    'price': float(base),
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'type': 'psychological',
                    'subtype': 'major' if base % self.params['psych_major_interval'] == 0 else 'standard',
                    'timeframe': 'all',  # 心理位适用于所有时间框架
                    'base_strength': strength,
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
            
            # 提取数据
            closes = [ensure_float(row['close']) for row in data]
            volumes = [ensure_float(row['volume']) for row in data]
            
            # 当前价格取最新收盘价
            current_price = closes[-1]
            
            # 使用斐波那契计算器
            self._init_optimization_modules()
            if self.fib_calculator is None:
                # 无计算器时用简单方法：取近期高低点计算 fib 回撤
                return self._calculate_simple_fibonacci(closes, current_price, timeframe)
            
            # 识别波段
            waves = self.fib_calculator.identify_waves(closes, volumes)
            
            # 计算斐波那契位
            fib_levels = self.fib_calculator.calculate_all_fibonacci_levels(waves)
            
            # 根据当前价格修正支撑/阻力方向
            corrected_supports = []
            corrected_resistances = []
            
            for level in fib_levels.get('supports', []) + fib_levels.get('resistances', []):
                level['timeframe'] = timeframe
                price = level.get('price', 0)
                if price <= 0:
                    continue
                if price < current_price:
                    corrected_supports.append(level)
                else:
                    corrected_resistances.append(level)
            
            logger.info(f"{timeframe} 斐波那契位: {len(corrected_supports)}支撑, {len(corrected_resistances)}阻力")
            return {'supports': corrected_supports, 'resistances': corrected_resistances}
            
        except Exception as e:
            logger.error(f"识别斐波那契位失败: {e}")
            return {'supports': [], 'resistances': []}
    
    def _calculate_simple_fibonacci(self, closes: List[float], current_price: float, timeframe: str) -> Dict[str, List[Dict]]:
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

        # 找近期波段：用滑动窗口找局部高低点
        window = max(5, len(recent) // 20)
        local_highs = []
        local_lows = []
        for i in range(window, len(recent) - window):
            if all(recent[i] >= recent[i-j] and recent[i] >= recent[i+j] for j in range(1, window+1)):
                local_highs.append((i, recent[i]))
            if all(recent[i] <= recent[i-j] and recent[i] <= recent[i+j] for j in range(1, window+1)):
                local_lows.append((i, recent[i]))

        if not local_highs or not local_lows:
            # 兜底：直接用全段高低点
            swing_high = max(recent)
            swing_low = min(recent)
            waves = [('down', swing_high, swing_low)]
        else:
            # 取最近的高点和低点，判断当前趋势方向
            last_high_idx, last_high_val = local_highs[-1]
            last_low_idx, last_low_val = local_lows[-1]

            # 振幅过滤：波段幅度低于阈值不计算
            min_amplitude = self.params['fib_min_wave_amplitude']
            waves = []

            if last_high_idx > last_low_idx:
                # 最近是上涨波段：从低点涨到高点
                amp = (last_high_val - last_low_val) / last_low_val
                if amp >= min_amplitude:
                    waves.append(('up', last_low_val, last_high_val))
                # 同时找上一个低点，构造更大的下跌波段
                prev_lows = [l for l in local_lows if l[0] < last_low_idx]
                if prev_lows:
                    prev_high_candidates = [h for h in local_highs if h[0] < last_low_idx]
                    if prev_high_candidates:
                        prev_high_val = prev_high_candidates[-1][1]
                        amp2 = (prev_high_val - last_low_val) / prev_high_val
                        if amp2 >= min_amplitude:
                            waves.append(('down', prev_high_val, last_low_val))
            else:
                # 最近是下跌波段：从高点跌到低点
                amp = (last_high_val - last_low_val) / last_high_val
                if amp >= min_amplitude:
                    waves.append(('down', last_high_val, last_low_val))
                # 同时找上一个高点，构造更大的上涨波段
                prev_highs = [h for h in local_highs if h[0] < last_high_idx]
                if prev_highs:
                    prev_low_candidates = [l for l in local_lows if l[0] < last_high_idx]
                    if prev_low_candidates:
                        prev_low_val = prev_low_candidates[-1][1]
                        amp2 = (last_high_val - prev_low_val) / prev_low_val
                        if amp2 >= min_amplitude:
                            waves.append(('up', prev_low_val, last_high_val))

            if not waves:
                swing_high = max(recent[-50:])
                swing_low = min(recent[-50:])
                waves = [('down', swing_high, swing_low)]

        # 标准斐波那契比例
        retracement_ratios = self.params['fib_retracement_ratios']
        extension_ratios   = self.params['fib_extension_ratios']

        supports = []
        resistances = []

        for direction, wave_start, wave_end in waves:
            diff = abs(wave_end - wave_start)
            if diff <= 0:
                continue

            if direction == 'up':
                # 上涨波段：回撤位在下方（支撑），延伸位在上方（阻力）
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
                        'metadata': {'ratio': ratio, 'direction': 'up', 'wave_high': high, 'wave_low': low}
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
                        'metadata': {'ratio': ratio, 'direction': 'up', 'wave_high': high, 'wave_low': low}
                    }
                    if price > current_price:
                        resistances.append(level)

            else:
                # 下跌波段：回撤位在上方（阻力），延伸位在下方（支撑）
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
                        'metadata': {'ratio': ratio, 'direction': 'down', 'wave_high': high, 'wave_low': low}
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
                        'metadata': {'ratio': ratio, 'direction': 'down', 'wave_high': high, 'wave_low': low}
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
        
        prices = [float(level['price']) for level in group]
        avg_price = sum(prices) / len(prices)
        
        strengths = [self._extract_strength(level) for level in group]
        max_strength = max(strengths) if strengths else 0
        
        # 收集时间框架，取最高权重
        timeframes = set()
        max_tf_weight = 1
        for level in group:
            if 'timeframe' in level:
                timeframes.add(level['timeframe'])
            tw = level.get('timeframe_weight', 1)
            if tw > max_tf_weight:
                max_tf_weight = tw
        
        types = set()
        for level in group:
            if 'type' in level:
                types.add(level['type'])
        
        # 触碰次数累加（多个来源叠加）
        total_touch = sum(level.get('touch_count', 0) for level in group)
        
        return {
            'price': avg_price,
            'price_range': [min(prices), max(prices)],
            'strength': max_strength,
            'timeframes': list(timeframes),
            'types': list(types),
            'source_count': len(group),
            'sources': group,
            'is_merged': True,
            # 关键：保留权重和触碰信息供评分使用
            'timeframe_weight': max_tf_weight,
            'base_strength': max_strength,
            'touch_count': total_touch,
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
        
        # 2. 添加心理位（适用于所有时间框架）
        psychological_levels = self.identify_psychological_levels(current_price, symbol)
        for level in psychological_levels['supports'] + psychological_levels['resistances']:
            level['timeframe_weight'] = 1  # 心理位基础权重
            level['timeframe'] = 'all'
        
        all_supports.extend(psychological_levels['supports'])
        all_resistances.extend(psychological_levels['resistances'])
        
        # 3. 计算综合ATR（使用4H ATR作为基准）
        base_atr = self.calculate_atr('4h', symbol)
        
        # 4. 合并相近位点，合并后按当前价格重新校正方向
        merged_supports_raw = self.merge_nearby_levels(all_supports, base_atr, atr_multiplier=self.params['merge_atr_multiplier'])
        merged_resistances_raw = self.merge_nearby_levels(all_resistances, base_atr, atr_multiplier=self.params['merge_atr_multiplier'])
        
        # 合并后重新校正：支撑必须在当前价格下方，阻力必须在上方
        merged_supports = []
        merged_resistances = []
        for level in merged_supports_raw:
            if level.get('price', 0) < current_price:
                merged_supports.append(level)
            else:
                merged_resistances.append(level)  # 合并后跑到上方，归为阻力
        for level in merged_resistances_raw:
            if level.get('price', 0) > current_price:
                merged_resistances.append(level)
            else:
                merged_supports.append(level)  # 合并后跑到下方，归为支撑
        
        # 5. 成交量确认（当前跳过，volume_confirmation 模块会清空所有位点）
        # TODO: 修复 volume_confirmation 的序列长度问题后再启用
        
        # 6. 计算综合强度评分
        scored_supports = [self.calculate_strength_score(level, 'support', current_price) 
                          for level in merged_supports]
        scored_resistances = [self.calculate_strength_score(level, 'resistance', current_price)
                             for level in merged_resistances]
        
        # 6. 按强度排序，同分时距离近的优先
        scored_supports.sort(key=lambda x: (-x.get('final_score', 0), -(x.get('price', 0))))
        scored_resistances.sort(key=lambda x: (-x.get('final_score', 0), x.get('price', 0)))
        
        # 7. 过滤弱位点
        strong_supports = [s for s in scored_supports
                           if s.get('final_score_normalized', 0) >= self.params['filter_min_score']]
        strong_resistances = [r for r in scored_resistances
                              if r.get('final_score_normalized', 0) >= self.params['filter_min_score']]
        
        logger.info(f"✅ 分析完成: {len(strong_supports)}强支撑, {len(strong_resistances)}强阻力")
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'base_atr': base_atr,
            'supports': strong_supports,
            'resistances': strong_resistances,
            'timeframe_results': timeframe_results,
            'analysis_time': datetime.now().isoformat(),
            'timeframes_analyzed': list(self.timeframe_config.keys()),
            'optimizations': {
                'swing_point_filter': self.swing_optimizer is not None,
                'fibonacci_calculation': self.fib_calculator is not None,
                'volume_confirmation': self.volume_system is not None
            }
        }
    
    def get_current_price(self, symbol: str = 'BTCUSDT') -> Optional[float]:
        """获取当前价格（使用最新4H数据）"""
        try:
            cursor = self.connection.cursor(dictionary=True)
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
    
    def _get_price_data_for_volume(self, timeframe: str, symbol: str = 'BTCUSDT', limit: int = 300) -> Optional[Dict]:
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
        - 时间框架权威性  35%  （大周期更可靠）
        - 触碰/置信度     35%  （历史验证次数）
        - 成交量确认      15%  （有量才有效）
        - 距离当前价格    15%  （参考价值，不主导评分）
        """
        score = 0.0
        score_factors = {}
        
        # 1. 时间框架权威性（35%）
        timeframe_weight = level.get('timeframe_weight', 1)
        timeframe_score = timeframe_weight / 4.0
        score += timeframe_score * self.params['score_weight_timeframe']
        score_factors['timeframe'] = timeframe_score
        
        # 2. 触碰次数 / 置信度（35%）
        if 'confidence' in level:
            confidence_score = float(level['confidence'])
        elif 'touch_count' in level:
            # 触碰1次=0.3，2次=0.6，3次=0.8，4次以上=1.0
            tc = level['touch_count']
            confidence_score = min(0.25 * tc + 0.05, 1.0)
        elif 'base_strength' in level:
            confidence_score = min(level['base_strength'] / 5.0, 1.0)
        elif 'importance' in level:
            confidence_score = level['importance'] / 3.0
        else:
            confidence_score = 0.4
        
        score += confidence_score * self.params['score_weight_confidence']
        score_factors['confidence'] = confidence_score
        
        # 3. 成交量确认（15%）
        if 'volume_confirmation' in level:
            vol_conf = level['volume_confirmation']
            volume_score = vol_conf.get('confidence', 0.3) if vol_conf.get('confirmed', False) else 0.2
        else:
            volume_score = self.params['score_volume_default']
        
        score += volume_score * self.params['score_weight_volume']
        score_factors['volume'] = volume_score
        
        # 4. 距离当前价格（15%）—— 仅作参考，不主导
        price = level.get('price', 0)
        if current_price > 0 and price > 0:
            distance_pct = abs(current_price - price) / current_price
            distance_score = self.params['score_distance_fallback']
            for threshold, dscore in self.params['score_distance_tiers']:
                if distance_pct <= threshold:
                    distance_score = dscore
                    break
        else:
            distance_score = 0.4
        
        score += distance_score * self.params['score_weight_distance']
        score_factors['distance'] = distance_score
        
        # 归一化到 0-1，转换为 1-15 分
        final_score = max(0.0, min(score, 1.0))
        final_score_15 = int(final_score * 14) + 1
        
        strength_level = self._map_score_to_level(final_score_15)
        
        level['final_score'] = final_score_15
        level['final_score_normalized'] = final_score
        level['score_factors'] = score_factors
        level['strength_level'] = strength_level['level']
        level['strength_symbol'] = strength_level['symbol']
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
        
        report = []
        report.append("=" * 80)
        report.append(f"📊 {symbol} 支撑阻力分析报告")
        report.append(f"分析时间: {analysis_result.get('analysis_time', 'N/A')}")
        report.append(f"当前价格: ${current_price:,.2f}  |  基准ATR(14): ${base_atr:,.2f}")
        report.append("=" * 80)
        
        # ── 各周期独立分析 ──
        tf_order = ['1M', '1w', '1d', '4h']
        tf_labels = {
            '1M': '月线 1M（战略层，权重×4）',
            '1w': '周线 1w（战役层，权重×3）',
            '1d': '日线 1d（战术层，权重×2）',
            '4h': '4小时 4h（执行层，权重×1）',
        }
        
        for tf in tf_order:
            if tf not in timeframe_results:
                continue
            tf_data = timeframe_results[tf]
            tf_supports = tf_data.get('supports', [])
            tf_resistances = tf_data.get('resistances', [])
            atr_val = tf_data.get('atr', 0)
            
            report.append(f"\n{'─'*80}")
            report.append(f"【{tf_labels[tf]}】  ATR={atr_val:,.2f}")
            report.append(f"{'─'*80}")
            
            # 阻力位（从低到高，最近的在前）
            report.append("  📉 阻力位（由近到远）:")
            tf_res_sorted = sorted(tf_resistances, key=lambda x: x.get('price', 0))
            if tf_res_sorted:
                for level in tf_res_sorted[:5]:
                    price = level.get('price', 0)
                    score = level.get('final_score', 0)
                    stars = level.get('strength_symbol', '★')
                    types = ', '.join(level.get('types', [level.get('type', '')]))
                    dist = (price - current_price) / current_price * 100
                    report.append(f"    {stars} ${price:,.2f}  距离+{dist:.1f}%  评分{score}/15  [{types}]")
            else:
                report.append("    暂无识别到阻力位")
            
            # 支撑位（从高到低，最近的在前）
            report.append("  📈 支撑位（由近到远）:")
            tf_sup_sorted = sorted(tf_supports, key=lambda x: x.get('price', 0), reverse=True)
            if tf_sup_sorted:
                for level in tf_sup_sorted[:5]:
                    price = level.get('price', 0)
                    score = level.get('final_score', 0)
                    stars = level.get('strength_symbol', '★')
                    types = ', '.join(level.get('types', [level.get('type', '')]))
                    dist = (current_price - price) / current_price * 100
                    report.append(f"    {stars} ${price:,.2f}  距离-{dist:.1f}%  评分{score}/15  [{types}]")
            else:
                report.append("    暂无识别到支撑位")
        
        # ── 综合分析（多时间框架加权融合）──
        report.append(f"\n{'='*80}")
        report.append("🔥 综合分析（多时间框架加权融合）")
        report.append(f"{'='*80}")
        
        supports = analysis_result.get('supports', [])
        resistances = analysis_result.get('resistances', [])
        
        # 综合阻力位
        report.append("\n  📉 关键阻力位（由近到远）:")
        res_sorted = sorted(resistances, key=lambda x: x.get('price', 0))
        if res_sorted:
            for i, r in enumerate(res_sorted[:8], 1):
                price = r.get('price', 0)
                score = r.get('final_score', 0)
                stars = r.get('strength_symbol', '★')
                tfs = ', '.join(r.get('timeframes', [r.get('timeframe', '')]))
                types = ', '.join(r.get('types', [r.get('type', '')]))
                dist = (price - current_price) / current_price * 100
                report.append(f"  {i:2d}. {stars} ${price:,.2f}  距离+{dist:.1f}%  评分{score}/15")
                report.append(f"      时间框架: {tfs}  |  类型: {types}")
        else:
            report.append("  未识别到综合阻力位")
        
        # 综合支撑位
        report.append("\n  � 关键支撑位（由近到远）:")
        sup_sorted = sorted(supports, key=lambda x: x.get('price', 0), reverse=True)
        if sup_sorted:
            for i, s in enumerate(sup_sorted[:8], 1):
                price = s.get('price', 0)
                score = s.get('final_score', 0)
                stars = s.get('strength_symbol', '★')
                tfs = ', '.join(s.get('timeframes', [s.get('timeframe', '')]))
                types = ', '.join(s.get('types', [s.get('type', '')]))
                dist = (current_price - price) / current_price * 100
                report.append(f"  {i:2d}. {stars} ${price:,.2f}  距离-{dist:.1f}%  评分{score}/15")
                report.append(f"      时间框架: {tfs}  |  类型: {types}")
        else:
            report.append("  未识别到综合支撑位")
        
        # 交易建议
        report.append(f"\n{'─'*80}")
        report.append("💡 交易建议:")
        nearest_res = res_sorted[0] if res_sorted else None
        nearest_sup = sup_sorted[0] if sup_sorted else None
        
        if nearest_res:
            dist = (nearest_res['price'] - current_price) / current_price * 100
            report.append(f"  上方最近阻力: ${nearest_res['price']:,.2f}  (+{dist:.1f}%)  {nearest_res.get('strength_symbol','★')}")
        if nearest_sup:
            dist = (current_price - nearest_sup['price']) / current_price * 100
            report.append(f"  下方最近支撑: ${nearest_sup['price']:,.2f}  (-{dist:.1f}%)  {nearest_sup.get('strength_symbol','★')}")
        
        if nearest_res and nearest_sup:
            rr = (nearest_res['price'] - current_price) / (current_price - nearest_sup['price'])
            report.append(f"  当前位置盈亏比（做多）: {rr:.2f}  {'✅ 可考虑做多' if rr >= 2 else '⚠️ 盈亏比不足2，谨慎'}")
        
        report.append("=" * 80)
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
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = SupportResistanceAnalyzerPhase1(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    if args.test:
        # 测试模式
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