#!/usr/bin/env python3
"""
支撑阻力分析工具 - 第一阶段核心功能实现（修复版）

修复了数据类型问题（Decimal vs float）
"""

import mysql.connector
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
import json
from decimal import Decimal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    
    # ==================== 1. 基础支撑阻力识别 ====================
    
    def find_swing_points(self, prices: List[float], window: int = 5, min_amplitude: float = 0.01) -> Tuple[List[int], List[int]]:
        """
        优化版摆动点识别算法
        """
        n = len(prices)
        if n < window * 2 + 1:
            logger.warning(f"数据不足({n}条)，需要至少{window*2+1}条数据")
            return [], []
        
        swing_highs = []
        swing_lows = []
        
        for i in range(window, n - window):
            # 检查是否为摆动高点
            is_high = True
            for j in range(1, window + 1):
                if prices[i] <= prices[i - j] or prices[i] <= prices[i + j]:
                    is_high = False
                    break
            
            # 检查是否为摆动低点
            is_low = True
            for j in range(1, window + 1):
                if prices[i] >= prices[i - j] or prices[i] >= prices[i + j]:
                    is_low = False
                    break
            
            # 过滤微小波动
            if is_high:
                avg_surrounding = (sum(prices[i-window:i]) + sum(prices[i+1:i+window+1])) / (window * 2)
                amplitude = abs(prices[i] - avg_surrounding) / avg_surrounding
                if amplitude >= min_amplitude:
                    swing_highs.append(i)
            
            if is_low:
                avg_surrounding = (sum(prices[i-window:i]) + sum(prices[i+1:i+window+1])) / (window * 2)
                amplitude = abs(prices[i] - avg_surrounding) / avg_surrounding
                if amplitude >= min_amplitude:
                    swing_lows.append(i)
        
        logger.info(f"识别到 {len(swing_highs)} 个摆动高点和 {len(swing_lows)} 个摆动低点")
        return swing_highs, swing_lows
    
    def identify_technical_levels(self, timeframe: str, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """
        识别技术支撑阻力位（摆动高低点）
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            
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
            
            data.reverse()
            highs = [ensure_float(row['high']) for row in data]
            lows = [ensure_float(row['low']) for row in data]
            timestamps = [row['timestamp'] for row in data]
            
            swing_highs_idx, swing_lows_idx = self.find_swing_points(highs, window=3, min_amplitude=0.005)
            
            supports = []
            for idx in swing_lows_idx:
                supports.append({
                    'price': ensure_float(lows[idx]),
                    'timestamp': timestamps[idx],
                    'type': 'technical',
                    'subtype': 'swing_low',
                    'timeframe': timeframe,
                    'touch_count': 1,
                    'metadata': {
                        'index': idx,
                        'high': ensure_float(highs[idx]),
                        'low': ensure_float(lows[idx]),
                        'close': ensure_float(data[idx]['close']),
                        'volume': ensure_float(data[idx]['volume'])
                    }
                })
            
            resistances = []
            for idx in swing_highs_idx:
                resistances.append({
                    'price': ensure_float(highs[idx]),
                    'timestamp': timestamps[idx],
                    'type': 'technical',
                    'subtype': 'swing_high',
                    'timeframe': timeframe,
                    'touch_count': 1,
                    'metadata': {
                        'index': idx,
                        'high': ensure_float(highs[idx]),
                        'low': ensure_float(lows[idx]),
                        'close': ensure_float(data[idx]['close']),
                        'volume': ensure_float(data[idx]['volume'])
                    }
                })
            
            cursor.close()
            
            logger.info(f"{timeframe} 识别到 {len(supports)} 个技术支撑位和 {len(resistances)} 个技术阻力位")
            return {'supports': supports, 'resistances': resistances}
            
        except mysql.connector.Error as e:
            logger.error(f"识别技术位失败: {e}")
            return {'supports': [], 'resistances': []}
    
    def identify_dynamic_levels(self, timeframe: str, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """
        识别动态支撑阻力位（移动平均线、布林带）
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
                
                price_val = ensure_float(level['price'])
                
                if current_price > price_val:
                    level_type = 'support'
                else:
                    level_type = 'resistance'
                
                level_info = {
                    'price': price_val,
                    'timestamp': latest['timestamp'],
                    'type': 'dynamic',
                    'subtype': level['name'],
                    'timeframe': timeframe,
                    'base_strength': level['weight'],
                    'metadata': {
                        'current_price': current_price,
                        'relation': 'above' if current_price > price_val else 'below'
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
        """
        if symbol == 'BTCUSDT':
            major_levels = [1000, 5000, 10000]
        else:
            major_levels = [100, 500]
        
        lookback_percent = 0.2
        min_price = current_price * (1 - lookback_percent)
        max_price = current_price * (1 + lookback_percent)
        
        supports = []
        resistances = []
        
        for base in range(int(min_price // 1000) * 1000, int(max_price // 1000) * 1000 + 1000, 1000):
            if min_price <= base <= max_price:
                if current_price > base:
                    level_type = 'support'
                else:
                    level_type = 'resistance'
                
                strength = 2
                if base % 5000 == 0:
                    strength = 3
                if abs(current_price - base) / current_price < 0.01:
                    strength += 1
                
                level_info = {
                    'price': float(base),
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'type': 'psychological',
                    'subtype': 'major' if base % 5000 == 0 else 'standard',
                    'timeframe': 'all',
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
    
    # ==================== 2. 多时间框架融合系统 ====================
    
    def calculate_atr(self, timeframe: str, symbol: str = 'BTCUSDT', period: int = 14) -> float:
        """
        计算平均真实波幅(ATR)
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
            
            tr_values = []
            for i in range(1, len(data)):
                high = ensure_float(data[i]['high'])
                low = ensure_float(data[i]['low'])
                prev_close = ensure_float(data[i-1]['close'])
                
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                tr = max(tr1, tr2, tr3)
                tr_values.append(tr)
            
            atr = sum(tr_values[-period:]) / period if tr_values else 0.0
            
            cursor.close()
            return atr
            
        except mysql.connector.Error as e:
            logger.error(f"计算ATR失败: {e}")
            return 0.0
    
    def merge_nearby_levels(self, levels: List[Dict], atr: float, atr_multiplier: float = 1.0) -> List[Dict]:
        """
        合并相近的支撑阻力位
        """
        if not levels:
            return []
        
        sorted_levels = sorted(levels, key=lambda x: ensure_float(x['price']))
        
        merged = []
        current_group = [sorted_levels[0]]
        
        for i in range(1, len(sorted_levels)):
            current_price = ensure_float(sorted_levels[i]['price'])
            last_price_in_group = ensure_float(current_group[-1]['price'])
            atr_val = ensure_float(atr)
            
            if abs(current_price - last_price_in_group) <= atr_val * atr_multiplier:
                current_group.append(sorted_levels[i])
            else:
                merged.append(self._merge_group(current_group))
                current_group = [sorted_levels[i]]
        
        if current_group:
            merged.append(self._merge_group(current_group))
        
        logger.info(f"合并 {len(levels)} 个位点到 {len(merged)} 个区域")
        return merged
    
    def _merge_group(self, group: List[Dict]) -> Dict:
        """合并一个组内的位点"""
        if not group:
            return {}
        
        prices = [ensure_float(level['price']) for level in group]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        strengths = [self._extract_strength(level) for level in group]
        max_strength = max(strengths) if strengths else 0
        
        timeframes = set()
        for level in group:
            if 'timeframe' in level:
                timeframes.add(level['timeframe'])
        
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
        """
        logger.info(f"开始多时间框架支撑阻力分析: {symbol}")
        
        all_supports = []
        all_resistances = []
        
        current_price = self.get