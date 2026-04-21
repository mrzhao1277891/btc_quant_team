#!/usr/bin/env python3
"""
支撑阻力分析工具 - 优化集成版
集成了3个紧急优化：
1. 摆动点过滤优化
2. 斐波那契计算
3. 成交量确认
"""

import mysql.connector
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
import json
from decimal import Decimal

# 导入优化模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from swing_point_optimizer import SwingPointOptimizer
    from fibonacci_calculator import FibonacciCalculator
    from volume_confirmation import VolumeConfirmationSystem
except ImportError:
    # 如果直接运行，使用相对导入
    from .swing_point_optimizer import SwingPointOptimizer
    from .fibonacci_calculator import FibonacciCalculator
    from .volume_confirmation import VolumeConfirmationSystem

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

class SupportResistanceAnalyzerOptimized:
    """
    支撑阻力分析器 - 优化集成版
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
        
        # 初始化优化模块
        self.swing_optimizer = SwingPointOptimizer()
        self.fib_calculator = FibonacciCalculator()
        self.volume_system = VolumeConfirmationSystem()
        
        # 时间框架配置
        self.timeframe_config = {
            '1M': {'weight': 4, 'lookback': 24, 'description': '月线-战略层'},
            '1w': {'weight': 3, 'lookback': 52, 'description': '周线-战役层'},
            '1d': {'weight': 2, 'lookback': 100, 'description': '日线-战术层'},
            '4h': {'weight': 1, 'lookback': 200, 'description': '4小时-执行层'}
        }
        
        # 交易参数
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
    
    def get_price_data(self, timeframe: str, symbol: str = 'BTCUSDT', limit: int = 500) -> Dict[str, List]:
        """获取价格数据"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT timestamp, open, high, low, close, volume,
                       ema7, ema12, ema25, ema50,
                       boll, boll_up, boll_md, boll_dn
                FROM klines 
                WHERE symbol = %s AND timeframe = %s
                ORDER BY timestamp ASC
                LIMIT %s
            """
            
            cursor.execute(query, (symbol, timeframe, limit))
            data = cursor.fetchall()
            cursor.close()
            
            if not data:
                return {}
            
            # 提取数据
            result = {
                'timestamps': [row['timestamp'] for row in data],
                'opens': [ensure_float(row['open']) for row in data],
                'highs': [ensure_float(row['high']) for row in data],
                'lows': [ensure_float(row['low']) for row in data],
                'closes': [ensure_float(row['close']) for row in data],
                'volumes': [ensure_float(row['volume']) for row in data],
                'ema50': [ensure_float(row['ema50']) for row in data],
                'boll_md': [ensure_float(row['boll_md']) for row in data],
                'boll_up': [ensure_float(row['boll_up']) for row in data],
                'boll_dn': [ensure_float(row['boll_dn']) for row in data]
            }
            
            return result
            
        except mysql.connector.Error as e:
            logger.error(f"获取价格数据失败: {e}")
            return {}
    
    def identify_technical_levels_optimized(self, timeframe: str, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """
        优化版技术位识别（使用摆动点优化器）
        """
        # 获取价格数据
        price_data = self.get_price_data(timeframe, symbol, 300)
        if not price_data:
            return {'supports': [], 'resistances': []}
        
        # 使用优化器识别摆动点
        swing_highs, swing_lows = self.swing_optimizer.find_swing_points_optimized(
            highs=price_data['highs'],
            lows=price_data['lows'],
            closes=price_data['closes'],
            volumes=price_data['volumes'],
            timestamps=price_data['timestamps'],
            timeframe=timeframe,
            min_days=14
        )
        
        # 构建支撑位（摆动低点）
        supports = []
        for swing_low in swing_lows:
            supports.append({
                'price': swing_low['price'],
                'timestamp': swing_low['timestamp'],
                'type': 'technical',
                'subtype': 'swing_low_optimized',
                'timeframe': timeframe,
                'confidence': swing_low['confidence'],
                'metadata': {
                    'amplitude': swing_low['amplitude'],
                    'volume_ratio': swing_low['volume_ratio'],
                    'atr_ratio': swing_low['atr_ratio']
                }
            })
        
        # 构建阻力位（摆动高点）
        resistances = []
        for swing_high in swing_highs:
            resistances.append({
                'price': swing_high['price'],
                'timestamp': swing_high['timestamp'],
                'type': 'technical',
                'subtype': 'swing_high_optimized',
                'timeframe': timeframe,
                'confidence': swing_high['confidence'],
                'metadata': {
                    'amplitude': swing_high['amplitude'],
                    'volume_ratio': swing_high['volume_ratio'],
                    'atr_ratio': swing_high['atr_ratio']
                }
            })
        
        logger.info(f"{timeframe} 优化识别: {len(supports)}支撑, {len(resistances)}阻力")
        return {'supports': supports, 'resistances': resistances}
    
    def identify_dynamic_levels(self, timeframe: str, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """识别动态支撑阻力位"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT timestamp, close,
                       ema7, ema12, ema25, ema50,
                       boll_up, boll_md, boll_dn
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
            return {'supports': supports, 'resistances': resistances}
            
        except mysql.connector.Error as e:
            logger.error(f"识别动态位失败: {e}")
            return {'supports': [], 'resistances': []}
    
    def identify_fibonacci_levels(self, timeframe: str, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """识别斐波那契位"""
        # 获取价格数据
        price_data = self.get_price_data(timeframe, symbol, 200)
        if not price_data or len(price_data['closes']) < 50:
            return {'supports': [], 'resistances': []}
        
        # 识别波段
        waves = self.fib_calculator.identify_waves(
            prices=price_data['closes'],
            volumes=price_data['volumes']
        )
        
        # 计算斐波那契位
        fib_levels = self.fib_calculator.calculate_all_fibonacci_levels(waves)
        
        # 添加时间框架信息
        for level in fib_levels['supports'] + fib_levels['resistances']:
            level['timeframe'] = timeframe
        
        logger.info(f"{timeframe} 斐波那契位: {len(fib_levels['supports'])}支撑, {len(fib_levels['resistances'])}阻力")
        return fib_levels
    
    def identify_psychological_levels(self, current_price: float, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """识别心理支撑阻力位"""
        if symbol == 'BTCUSDT':
            major_levels = [1000, 5000, 10000]
        else:
            major_levels = [100, 500]
        
        lookback_percent = 0.15  # 当前价格±15%
        min_price = current_price * (1 - lookback_percent)
        max_price = current_price * (1 + lookback_percent)
        
        supports = []
        resistances = []
        
        # 只生成重要心理位
        for base in range(int(min_price // 1000) * 1000, int(max_price // 1000) * 1000 + 1000, 1000):
            if min_price <= base <= max_price:
                if current_price > base:
                    level_type = 'support'
                else:
                    level_type = 'resistance'
                
                # 只保留重要心理位（每5000或接近当前价格）
                importance = 0
                if base % 5000 == 0:
                    importance = 3  # 重要五千关口
                elif abs(current_price - base) / current_price < 0.02:  # 2%以内
                    importance = 2  # 接近当前价格
                elif base % 1000 == 0:
                    importance = 1  # 普通千位关口
                
                if importance == 0:
                    continue
                
                level_info = {
                    'price': float(base),
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'type': 'psychological',
                    'subtype': 'major' if base % 5000 == 0 else 'standard',
                    'timeframe': 'all',
                    'importance': importance,
                    'metadata': {
                        'current_price': current_price,
                        'distance_pct': abs(current_price - base) / current_price * 100
                    }
                }
                
                if level_type == 'support':
                    supports.append(level_info)
                else:
                    resistances.append(level_info)
        
        logger.info(f"心理位: {len(supports)}支撑, {len(resistances)}阻力 (过滤后)")
        return {'supports': supports, 'resistances': resistances}
    
    def merge_nearby_levels(self, levels: List[Dict], atr: float, atr_multiplier: float = 1.0) -> List[Dict]:
        """合并相近的支撑阻力位"""
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
        
        # 计算综合置信度
        confidences = []
        for level in group:
            if 'confidence' in level:
                confidences.append(level['confidence'])
            elif 'base_strength' in level:
                confidences.append(level['base_strength'] / 5.0)  # 转换为0-1范围
            elif 'importance' in level:
                confidences.append(level['importance'] / 3.0)  # 转换为0-1范围
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        # 收集信息
        timeframes = set()
        types = set()
        for level in group:
            if 'timeframe' in level:
                timeframes.add(level['timeframe'])
            if 'type' in level:
                types.add(level['type'])
        
        return {
            'price': avg_price,
            'price_range': [min_price, max_price],
            'confidence': avg_confidence,
            'timeframes': list(timeframes),
            'types': list(types),
            'source_count': len(group),
            'sources': group,
            'is_merged': True
        }
    
    def calculate_atr(self, timeframe: str, symbol: str = 'BTCUSDT', period: int = 14) -> float:
        """计算平均真实波幅(ATR)"""
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
    
    def get_current_price(self, symbol: str = 'BTCUSDT') -> Optional[float]:
        """获取当前价格"""
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
    
    def run_volume_confirmation(self, levels: Dict[str, List[Dict]], timeframe: str, symbol: str = 'BTCUSDT') -> Dict[str, List[Dict]]:
        """运行成交量确认"""
        # 获取价格数据
        price_data = self.get_price_data(timeframe, symbol, 300)
        if not price_data:
            return levels
        
        # 运行成交量确认
        confirmed_supports, confirmed_resistances = self.volume_system.integrate_with_support_resistance(
            support_levels=levels['supports'],
            resistance_levels=levels['resistances'],
            prices=price_data['closes'],
            highs=price_data['highs'],
            lows=price_data['lows'],
            closes=price_data['closes'],
            volumes=price_data['volumes'],
            timestamps=price_data['timestamps']
        )
        
        return {
            'supports': confirmed_supports,
            'resistances': confirmed_resistances
        }
    
    def multi_timeframe_analysis(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """
        多时间框架支撑阻力分析（优化版）
        """
        logger.info(f"🚀 开始优化版多时间框架分析: {symbol}")
        
        all_supports = []
        all_resistances = []
        
        # 获取当前价格
        current_price = self.get_current_price(symbol)
        if current_price is None:
            logger.error("无法获取当前价格")
            return {'supports': [], 'resistances': []}
        
        logger.info(f"当前价格: ${current_price:,.2f}")
        
        # 1. 分析每个时间框架
        for timeframe, config in self.timeframe_config.items():
            logger.info(f"📊 分析 {timeframe} 时间框架...")
            
            # 识别各种位点
            technical_levels = self.identify_technical_levels_optimized(timeframe, symbol)
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
        
        # 2. 添加心理位
        psychological_levels = self.identify_psychological_levels(current_price, symbol)
        for level in psychological_levels['supports'] + psychological_levels['resistances']:
            level['timeframe_weight'] = 1
            level['timeframe'] = 'all'
        
        all_supports.extend(psychological_levels['supports'])
        all_resistances.extend(psychological_levels['resistances'])
        
        # 3. 计算综合ATR
        base_atr = self.calculate_atr('4h', symbol)
        logger.info(f"基准ATR(14): ${base_atr:,.2f}")
        
        # 4. 合并相近位点
        merged_supports = self.merge_nearby_levels(all_supports, base_atr, atr_multiplier=1.0)
        merged_resistances = self.merge_nearby_levels(all_resistances, base_atr, atr_multiplier=1.0)
        
        # 5. 运行成交量确认（对4H时间框架）
        logger.info("🔍 运行成交量确认...")
        confirmed_levels = self.run_volume_confirmation(
            {'supports': merged_supports, 'resistances': merged_resistances},
            '4h',
            symbol
        )
        
        # 6. 计算综合评分
        scored_supports = [self.calculate_final_score(level, 'support', current_price) 
                          for level in confirmed_levels['supports']]
        scored_resistances = [self.calculate_final_score(level, 'resistance', current_price)
                             for level in confirmed_levels['resistances']]
        
        # 7. 按评分排序
        scored_supports.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        scored_resistances.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        # 8. 过滤弱位点
        strong_supports = [s for s in scored_supports if s.get('final_score', 0) >= 0.6]
        strong_resistances = [r for r in scored_resistances if r.get('final_score', 0) >= 0.6]
        
        logger.info(f"✅ 分析完成: {len(strong_supports)}强支撑, {len(strong_resistances)}强阻力")
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'base_atr': base_atr,
            'supports': strong_supports,
            'resistances': strong_resistances,
            'analysis_time': datetime.now().isoformat(),
            'timeframes_analyzed': list(self.timeframe_config.keys()),
            'optimizations_applied': ['swing_filter', 'fibonacci', 'volume_confirmation']
        }
    
    def calculate_final_score(self, level: Dict, level_type: str, current_price: float) -> Dict:
        """计算最终评分（0-1）"""
        score = 0.0
        score_factors = {}
        
        # 1. 时间框架权重（0-0.3）
        timeframe_weight = level.get('timeframe_weight', 1)
        timeframe_score = timeframe_weight / 4.0  # 转换为0-1
        score += timeframe_score * 0.3
        score_factors['timeframe'] = timeframe_score
        
        # 2. 置信度/强度（0-0.3）
        if 'confidence' in level:
            confidence_score = level['confidence']
        elif 'base_strength' in level:
            confidence_score = level['base_strength'] / 5.0
        elif 'importance' in level:
            confidence_score = level['importance'] / 3.0
        else:
            confidence_score = 0.5
        
        score += confidence_score * 0.3
        score_factors['confidence'] = confidence_score
        
        # 3. 成交量确认（0-0.2）
        volume_score = 0.0
        if 'volume_confirmation' in level:
            vol_conf = level['volume_confirmation']
            if vol_conf.get('confirmed', False):
                volume_score = vol_conf.get('confidence', 0)
        
        score += volume_score * 0.2
        score_factors['volume'] = volume_score
        
        # 4. 距离当前价格（0-0.2）
        price = level.get('price', 0)
        if current_price > 0:
            distance_pct = abs(current_price - price) / current_price
            # 距离越近，分数越高（但不要太近）
            if distance_pct <= 0.05:  # 5%以内
                distance_score = 0.8
            elif distance_pct <= 0.10:  # 10%以内
                distance_score = 0.6
            elif distance_pct <= 0.15:  # 15%以内
                distance_score = 0.4
            else:
                distance_score = 0.2
        else:
            distance_score = 0.5
        
        score += distance_score * 0.2
        score_factors['distance'] = distance_score
        
        # 确保分数在0-1范围内
        final_score = max(0, min(score, 1.0))
        
        # 添加等级
        strength_level = self._map_score_to_level(final_score)
        
        # 更新level信息
        level['final_score'] = final_score
        level['score_factors'] = score_factors
        level['strength_level'] = strength_level['level']
        level['strength_symbol'] = strength_level['symbol']
        
        return level
    
    def _map_score_to_level(self, score: float) -> Dict:
        """将分数映射到强度等级"""
        if score >= 0.85:
            return {'level': '极强', 'symbol': '★★★★★'}
        elif score >= 0.75:
            return {'level': '强', 'symbol': '★★★★'}
        elif score >= 0.65:
            return {'level': '中等', 'symbol': '★★★'}
        elif score >= 0.55:
            return {'level': '弱', 'symbol': '★★'}
        else:
            return {'level': '极弱', 'symbol': '★'}
    
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
        report.append(f"优化应用: {', '.join(analysis_result.get('optimizations_applied', []))}")
        report.append("=" * 80)
        
        # 支撑位报告
        report.append("\n📈 强支撑位 (按强度排序):")
        report.append("-" * 80)
        supports = analysis_result.get('supports', [])
        if supports:
            for i, support in enumerate(supports[:8], 1):  # 显示前8个
                price = support.get('price', 0)
                score = support.get('final_score', 0)
                level = support.get('strength_symbol', '★')
                timeframes = ', '.join(support.get('timeframes', []))
                types = ', '.join(support.get('types', []))
                
                distance_pct = ((current_price - price) / current_price * 100) if current_price > 0 else 0
                confirmed = "✅" if support.get('confirmed', False) else "⚠️"
                
                report.append(f"{i:2d}. {level} ${price:,.2f} "
                            f"(评分: {score:.2f}, 距离: {distance_pct:+.1f}%) {confirmed}")
                report.append(f"    时间框架: {timeframes} | 类型: {types}")
        else:
            report.append("未找到强支撑位")
        
        # 阻力位报告
        report.append("\n📉 强阻力位 (按强度排序):")
        report.append("-" * 80)
        resistances = analysis_result.get('resistances', [])
        if resistances:
            for i, resistance in enumerate(resistances[:8], 1):
                price = resistance.get('price', 0)
                score = resistance.get('final_score', 0)
                level = resistance.get('strength_symbol', '★')
                timeframes = ', '.join(resistance.get('timeframes', []))
                types = ', '.join(resistance.get('types', []))
                
                distance_pct = ((price - current_price) / current_price * 100) if current_price > 0 else 0
                confirmed = "✅" if resistance.get('confirmed', False) else "⚠️"
                
                report.append(f"{i:2d}. {level} ${price:,.2f} "
                            f"(评分: {score:.2f}, 距离: {distance_pct:+.1f}%) {confirmed}")
                report.append(f"    时间框架: {timeframes} | 类型: {types}")
        else:
            report.append("未找到强阻力位")
        
        # 交易建议
        report.append("\n💡 交易建议:")
        report.append("-" * 80)
        
        if supports and current_price > 0:
            nearest_support = supports[0] if supports else None
            if nearest_support:
                support_price = nearest_support.get('price', 0)
                support_distance = ((current_price - support_price) / current_price * 100)
                
                if support_distance <= 3:  # 3%以内
                    report.append(f"⚠️  价格接近强支撑位 ${support_price:,.2f} ({support_distance:.1f}%)")
                    report.append("   建议：等待看涨信号，准备做多")
                elif support_distance <= 8:  # 8%以内
                    report.append(f"📉  下方强支撑在 ${support_price:,.2f} ({support_distance:.1f}%)")
                    report.append("   建议：可等待回调至该区域")
                else:
                    report.append(f"📏  距离最近强支撑 {support_distance:.1f}%，空间较大")
        
        if resistances and current_price > 0:
            nearest_resistance = resistances[0] if resistances else None
            if nearest_resistance:
                resistance_price = nearest_resistance.get('price', 0)
                resistance_distance = ((resistance_price - current_price) / current_price * 100)
                
                if resistance_distance <= 3:  # 3%以内
                    report.append(f"⚠️  价格接近强阻力位 ${resistance_price:,.2f} ({resistance_distance:.1f}%)")
                    report.append("   建议：等待看跌信号，准备做空")
                elif resistance_distance <= 8:  # 8%以内
                    report.append(f"📈  上方强阻力在 ${resistance_price:,.2f} ({resistance_distance:.1f}%)")
                    report.append("   建议：接近该区域可考虑减仓")
        
        # 关键观察
        report.append("\n🔍 关键观察:")
        report.append("-" * 80)
        
        # 检查是否有成交量确认的位点
        confirmed_supports = [s for s in supports if s.get('confirmed', False)]
        confirmed_resistances = [r for r in resistances if r.get('confirmed', False)]
        
        report.append(f"✅ 成交量确认的支撑位: {len(confirmed_supports)}个")
        report.append(f"✅ 成交量确认的阻力位: {len(confirmed_resistances)}个")
        
        if base_atr > 0:
            report.append(f"📏 市场波动: ATR=${base_atr:,.2f} ({base_atr/current_price*100:.1f}%)")
        
        report.append("\n" + "=" * 80)
        report.append("优化版分析完成 🎯")
        
        return "\n".join(report)
    
    def run_analysis(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """
        运行完整的优化版支撑阻力分析
        """
        logger.info(f"🚀 开始运行优化版支撑阻力分析: {symbol}")
        
        # 连接数据库
        if not self.connect():
            return {'error': '数据库连接失败'}
        
        try:
            # 运行多时间框架分析
            analysis_result = self.multi_timeframe_analysis(symbol)
            
            # 生成报告
            report_text = self.generate_report(analysis_result)
            print(report_text)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}
        
        finally:
            self.disconnect()


# 命令行接口
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='支撑阻力分析工具 - 优化集成版')
    parser.add_argument('--symbol', default='BTCUSDT', help='交易对')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    analyzer = SupportResistanceAnalyzerOptimized()
    
    if args.test:
        print("🧪 测试优化版分析器...")
        # 简单测试连接
        if analyzer.connect():
            price = analyzer.get_current_price(args.symbol)
            print(f"✅ 连接成功，当前价格: ${price:,.2f}")
            analyzer.disconnect()
        else:
            print("❌ 连接失败")
    else:
        analyzer.run_analysis(symbol=args.symbol)


if __name__ == "__main__":
    main()
