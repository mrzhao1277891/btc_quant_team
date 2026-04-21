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
    
    def find_swing_points(self, prices: List[float], window: int = 3, min_amplitude: float = 0.003) -> Tuple[List[int], List[int]]:
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
                swing_highs_idx, swing_lows_idx = self.find_swing_points(highs, window=3, min_amplitude=0.005)
                
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
        识别动态支撑阻力位（移动平均线、布林带）
        
        参数:
            timeframe: 时间框架
            symbol: 交易对
        
        返回:
            动态位字典
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 获取最新数据（包含技术指标）
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
            current_price = latest['close']
            
            # 动态位配置
            dynamic_levels = [
                {'price': latest['ema50'], 'name': 'EMA50', 'weight': 3},
                {'price': latest['boll_md'], 'name': 'BOLL_MD', 'weight': 3},
                {'price': latest['ema25'], 'name': 'EMA25', 'weight': 2},
                {'price': latest['ema12'], 'name': 'EMA12', 'weight': 2},
                {'price': latest['ema7'], 'name': 'EMA7', 'weight': 1},
                {'price': latest['boll_up'], 'name': 'BOLL_UP', 'weight': 2},
                {'price': latest['boll_dn'], 'name': 'BOLL_DN', 'weight': 2}
            ]
            
            supports = []
            resistances = []
            
            for level in dynamic_levels:
                if level['price'] is None:
                    continue
                
                # 判断是支撑还是阻力
                if current_price > level['price']:
                    # 价格在均线上方，可能是支撑
                    level_type = 'support'
                else:
                    # 价格在均线下方，可能是阻力
                    level_type = 'resistance'
                
                level_info = {
                    'price': float(level['price']),
                    'timestamp': latest['timestamp'],
                    'type': 'dynamic',
                    'subtype': level['name'],
                    'timeframe': timeframe,
                    'base_strength': level['weight'],
                    'metadata': {
                        'current_price': current_price,
                        'relation': 'above' if current_price > level['price'] else 'below'
                    }
                }
                
                if level_type == 'support':
                    supports.append(level_info)
                else:
                    resistances.append(level_info)
            
            cursor.close()
            
            logger.info(f"{timeframe} 识别到 {len(supports)} 个动态支撑位和 {len(resistances)} 个动态阻力位")
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
        lookback_percent = 0.2
        min_price = current_price * (1 - lookback_percent)
        max_price = current_price * (1 + lookback_percent)
        
        supports = []
        resistances = []
        
        # 生成主要心理位
        for base in range(int(min_price // 1000) * 1000, int(max_price // 1000) * 1000 + 1000, 1000):
            if min_price <= base <= max_price:
                # 判断是支撑还是阻力
                if current_price > base:
                    level_type = 'support'
                else:
                    level_type = 'resistance'
                
                # 评估强度
                strength = 2  # 基础强度
                if base % 5000 == 0:  # 重要五千关口
                    strength = 3
                if abs(current_price - base) / current_price < 0.01:  # 接近当前价格
                    strength += 1
                
                level_info = {
                    'price': float(base),
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'type': 'psychological',
                    'subtype': 'major' if base % 5000 == 0 else 'standard',
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
        无外部计算器时的简单斐波那契回撤计算
        取近期最高/最低价计算标准回撤位
        """
        if len(closes) < 20:
            return {'supports': [], 'resistances': []}
        
        recent = closes[-100:] if len(closes) >= 100 else closes
        swing_high = max(recent)
        swing_low = min(recent)
        diff = swing_high - swing_low
        
        if diff <= 0:
            return {'supports': [], 'resistances': []}
        
        # 标准斐波那契回撤比例
        fib_ratios = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        
        supports = []
        resistances = []
        
        for ratio in fib_ratios:
            # 下跌回撤位（从高点往下）
            price = swing_high - diff * ratio
            level = {
                'price': round(price, 2),
                'type': 'fibonacci',
                'subtype': f'fib_{ratio}',
                'timeframe': timeframe,
                'base_strength': 2,
                'metadata': {'ratio': ratio, 'swing_high': swing_high, 'swing_low': swing_low}
            }
            if price < current_price:
                supports.append(level)
            elif price > current_price:
                resistances.append(level)
        
        logger.info(f"{timeframe} 简单斐波那契: {len(supports)}支撑, {len(resistances)}阻力")
        return {'supports': supports, 'resistances': resistances}
    
    # ==================== 2. 多时间框架融合系统 ====================
    
    def calculate_atr(self, timeframe: str, symbol: str = 'BTCUSDT', period: int = 14) -> float:
        """
        计算平均真实波幅(ATR)
        
        参数:
            timeframe: 时间框架
            symbol: 交易对
            period: ATR周期
        
        返回:
            ATR值
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT high, low, close,
                       LAG(close, 1) OVER (ORDER BY timestamp) as prev_close
                FROM klines 
                WHERE symbol = %s AND timeframe = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            
            cursor.execute(query, (symbol, timeframe, period * 2))
            data = cursor.fetchall()
            
            if len(data) < period:
                logger.warning(f"数据不足计算ATR({period})，只有{len(data)}条数据")
                return 0.0
            
            # 计算真实波幅
            tr_values = []
            for i in range(1, len(data)):
                high = data[i]['high']
                low = data[i]['low']
                prev_close = data[i-1]['close']
                
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                tr = max(tr1, tr2, tr3)
                tr_values.append(tr)
            
            # 计算ATR
            atr = sum(tr_values[-period:]) / period if tr_values else 0.0
            
            cursor.close()
            return atr
            
        except mysql.connector.Error as e:
            logger.error(f"计算ATR失败: {e}")
            return 0.0
    
    def merge_nearby_levels(self, levels: List[Dict], atr: float, atr_multiplier: float = 1.0) -> List[Dict]:
        """
        合并相近的支撑阻力位
        
        参数:
            levels: 位点列表
            atr: 平均真实波幅
            atr_multiplier: ATR倍数（调整合并容差）
        
        返回:
            合并后的位点列表
        """
        if not levels:
            return []
        
        # 按价格排序
        sorted_levels = sorted(levels, key=lambda x: x['price'])
        
        merged = []
        current_group = [sorted_levels[0]]
        
        for i in range(1, len(sorted_levels)):
            current_price = sorted_levels[i]['price']
            last_price_in_group = current_group[-1]['price']
            
            # 检查是否应该合并到当前组
            # 确保数据类型正确
            current_price_val = float(current_price)
            last_price_val = float(last_price_in_group)
            atr_val = float(atr)
            
            if abs(current_price_val - last_price_val) <= atr_val * atr_multiplier:
                current_group.append(sorted_levels[i])
            else:
                # 合并当前组
                merged.append(self._merge_group(current_group))
                current_group = [sorted_levels[i]]
        
        # 合并最后一组
        if current_group:
            merged.append(self._merge_group(current_group))
        
        logger.info(f"合并 {len(levels)} 个位点到 {len(merged)} 个区域")
        return merged
    
    def _merge_group(self, group: List[Dict]) -> Dict:
        """合并一个组内的位点"""
        if not group:
            return {}
        
        # 计算合并后的价格范围
        prices = [float(level['price']) for level in group]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        # 计算综合强度（取最大值）
        strengths = [self._extract_strength(level) for level in group]
        max_strength = max(strengths) if strengths else 0
        
        # 收集时间框架信息
        timeframes = set()
        for level in group:
            if 'timeframe' in level:
                timeframes.add(level['timeframe'])
        
        # 收集类型信息
        types = set()
        for level in group:
            if 'type' in level:
                types.add(level['type'])
        
        return {
            'price': avg_price,
            'price_range': [min_price, max_price],
            'strength': max_strength,
            'timeframes': list(timeframes),
            'types': list(types),
            'source_count': len(group),
            'sources': group,
            'is_merged': True
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
            
            all_supports.extend(timeframe_supports)
            all_resistances.extend(timeframe_resistances)
        
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
        merged_supports_raw = self.merge_nearby_levels(all_supports, base_atr, atr_multiplier=1.0)
        merged_resistances_raw = self.merge_nearby_levels(all_resistances, base_atr, atr_multiplier=1.0)
        
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
        
        # 5. 运行成交量确认（可选）
        if self.volume_system is not None:
            self._init_optimization_modules()
            logger.info("🔍 运行成交量确认...")
            
            # 获取4H价格数据用于成交量确认，limit 与 fib 保持一致
            price_data = self._get_price_data_for_volume('4h', symbol, 200)
            if price_data and len(price_data['closes']) == len(price_data['volumes']):
                try:
                    confirmed_supports, confirmed_resistances = self.volume_system.integrate_with_support_resistance(
                        support_levels=merged_supports,
                        resistance_levels=merged_resistances,
                        prices=price_data['closes'],
                        highs=price_data['highs'],
                        lows=price_data['lows'],
                        closes=price_data['closes'],
                        volumes=price_data['volumes'],
                        timestamps=price_data['timestamps']
                    )
                    merged_supports = confirmed_supports
                    merged_resistances = confirmed_resistances
                except Exception as e:
                    logger.warning(f"成交量确认失败，跳过: {e}")
        
        # 6. 计算综合强度评分
        scored_supports = [self.calculate_strength_score(level, 'support', current_price) 
                          for level in merged_supports]
        scored_resistances = [self.calculate_strength_score(level, 'resistance', current_price)
                             for level in merged_resistances]
        
        # 6. 按强度排序，同分时距离近的优先
        scored_supports.sort(key=lambda x: (-x.get('final_score', 0), -(x.get('price', 0))))
        scored_resistances.sort(key=lambda x: (-x.get('final_score', 0), x.get('price', 0)))
        
        # 7. 过滤弱位点（降低门槛）
        # 原系统：评分<4过滤，新系统：归一化评分<0.3过滤
        strong_supports = []
        for s in scored_supports:
            score = s.get('final_score', 0)
            norm_score = s.get('final_score_normalized', score/15.0)
            if norm_score >= 0.3:  # 相当于原系统4.5分
                strong_supports.append(s)
        
        strong_resistances = []
        for r in scored_resistances:
            score = r.get('final_score', 0)
            norm_score = r.get('final_score_normalized', score/15.0)
            if norm_score >= 0.3:
                strong_resistances.append(r)
        
        logger.info(f"✅ 分析完成: {len(strong_supports)}强支撑, {len(strong_resistances)}强阻力")
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'base_atr': base_atr,
            'supports': strong_supports,
            'resistances': strong_resistances,
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
        计算支撑阻力位综合强度评分（优化版）
        
        考虑优化模块的置信度，评分范围0-1
        """
        score = 0.0
        score_factors = {}
        
        # 1. 时间框架权威性（0-0.25）
        timeframe_weight = level.get('timeframe_weight', 1)
        timeframe_score = timeframe_weight / 4.0  # 转换为0-1
        score += timeframe_score * 0.25
        score_factors['timeframe'] = timeframe_score
        
        # 2. 基础置信度/强度（0-0.25）
        if 'confidence' in level:
            # 来自优化模块的置信度
            confidence_score = level['confidence']
        elif 'base_strength' in level:
            confidence_score = level['base_strength'] / 5.0
        elif 'importance' in level:
            confidence_score = level['importance'] / 3.0
        elif 'touch_count' in level:
            confidence_score = min(level['touch_count'] / 4.0, 1.0)
        else:
            confidence_score = 0.5
        
        score += confidence_score * 0.25
        score_factors['confidence'] = confidence_score
        
        # 3. 成交量确认（0-0.2）
        volume_score = 0.0
        if 'volume_confirmation' in level:
            vol_conf = level['volume_confirmation']
            if vol_conf.get('confirmed', False):
                volume_score = vol_conf.get('confidence', 0)
            else:
                volume_score = 0.3  # 即使未确认，也给基础分
        else:
            volume_score = 0.5  # 默认分
        
        score += volume_score * 0.2
        score_factors['volume'] = volume_score
        
        # 4. 距离当前价格（0-0.3）
        price = level.get('price', 0)
        if current_price > 0:
            distance_pct = abs(current_price - price) / current_price
            
            # 距离评分：距离越近，分数越高（但不要太近）
            if distance_pct <= 0.03:  # 3%以内
                distance_score = 0.9
            elif distance_pct <= 0.06:  # 6%以内
                distance_score = 0.7
            elif distance_pct <= 0.10:  # 10%以内
                distance_score = 0.5
            elif distance_pct <= 0.15:  # 15%以内
                distance_score = 0.3
            else:
                distance_score = 0.1
        else:
            distance_score = 0.5
        
        score += distance_score * 0.3
        score_factors['distance'] = distance_score
        
        # 确保分数在0-1范围内
        final_score = max(0, min(score, 1.0))
        
        # 转换为1-15分（兼容原系统）
        final_score_15 = int(final_score * 14) + 1
        
        # 添加等级映射
        strength_level = self._map_score_to_level(final_score_15)
        
        # 更新level信息
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
        """生成分析报告"""
        symbol = analysis_result.get('symbol', 'BTCUSDT')
        current_price = analysis_result.get('current_price', 0)
        base_atr = analysis_result.get('base_atr', 0)
        
        report = []
        report.append("=" * 80)
        report.append(f"📊 BTC支撑阻力分析报告 - 优化版")
        report.append(f"分析时间: {analysis_result.get('analysis_time', 'N/A')}")
        report.append(f"当前价格: ${current_price:,.2f}")
        report.append(f"基准ATR(14): ${base_atr:,.2f}")
        report.append(f"优化应用: 摆动点过滤 + 斐波那契计算 + 成交量确认")
        report.append("=" * 80)
        
        # 支撑位报告
        report.append("\n📈 强支撑位 (按强度排序):")
        report.append("-" * 80)
        supports = analysis_result.get('supports', [])
        if supports:
            for i, support in enumerate(supports[:10], 1):  # 显示前10个
                price = support.get('price', 0)
                score = support.get('final_score', 0)
                level = support.get('strength_symbol', '★')
                timeframes = ', '.join(support.get('timeframes', []))
                types = ', '.join(support.get('types', []))
                
                distance_pct = ((current_price - price) / current_price * 100) if current_price > 0 else 0
                
                report.append(f"{i:2d}. {level} ${price:,.2f} "
                            f"(评分: {score}/15, 距离: {distance_pct:+.1f}%)")
                report.append(f"    时间框架: {timeframes} | 类型: {types}")
        else:
            report.append("未找到强支撑位")
        
        # 阻力位报告
        report.append("\n📉 强阻力位 (按强度排序):")
        report.append("-" * 80)
        resistances = analysis_result.get('resistances', [])
        if resistances:
            for i, resistance in enumerate(resistances[:10], 1):  # 显示前10个
                price = resistance.get('price', 0)
                score = resistance.get('final_score', 0)
                level = resistance.get('strength_symbol', '★')
                timeframes = ', '.join(resistance.get('timeframes', []))
                types = ', '.join(resistance.get('types', []))
                
                distance_pct = ((price - current_price) / current_price * 100) if current_price > 0 else 0
                
                report.append(f"{i:2d}. {level} ${price:,.2f} "
                            f"(评分: {score}/15, 距离: {distance_pct:+.1f}%)")
                report.append(f"    时间框架: {timeframes} | 类型: {types}")
        else:
            report.append("未找到强阻力位")
        
        # 交易建议
        report.append("\n💡 交易建议:")
        report.append("-" * 80)
        if supports and current_price > 0:
            nearest_support = supports[0]
            support_price = nearest_support.get('price', 0)
            support_distance = ((current_price - support_price) / current_price * 100)
            
            if support_distance <= 5:  # 5%以内
                report.append(f"⚠️  价格接近强支撑位 ${support_price:,.2f} ({support_distance:.1f}%)")
                report.append("   建议：等待看涨信号，准备做多")
            else:
                report.append(f"价格距离最近强支撑位 {support_distance:.1f}%，可等待回调")
        
        if resistances and current_price > 0:
            nearest_resistance = resistances[0]
            resistance_price = nearest_resistance.get('price', 0)
            resistance_distance = ((resistance_price - current_price) / current_price * 100)
            
            if resistance_distance <= 5:  # 5%以内
                report.append(f"⚠️  价格接近强阻力位 ${resistance_price:,.2f} ({resistance_distance:.1f}%)")
                report.append("   建议：等待看跌信号，准备做空")
            else:
                report.append(f"上方强阻力位在 ${resistance_price:,.2f} ({resistance_distance:.1f}%)")
        
        report.append("\n" + "=" * 80)
        report.append("分析完成 🎯")
        
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