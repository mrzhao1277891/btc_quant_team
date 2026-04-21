#!/usr/bin/env python3
"""
支撑阻力分析 - 参数调整版
调整过滤参数，避免过于严格
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入父类
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 由于导入问题，我们直接复制需要的父类代码
# 这里简化处理，直接创建一个新类
from typing import Dict, List, Any
import logging
import mysql.connector
from decimal import Decimal

logger = logging.getLogger(__name__)

def ensure_float(value):
    """确保值为float类型"""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except:
        return 0.0

class SupportResistanceAnalyzerAdjusted(SupportResistanceAnalyzerOptimized):
    """参数调整版分析器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 调整摆动点优化器参数（避免过滤太严格）
        self.swing_optimizer.config.update({
            'min_amplitude_multiplier': 1.0,  # 降低幅度要求
            'volume_threshold': 1.0,         # 允许正常成交量
            'max_lookback_days': 90,         # 延长回溯时间
        })
        
        # 调整斐波那契计算器参数
        self.fib_calculator.wave_config.update({
            'min_amplitude_pct': 3.0,        # 降低最小波段幅度
            'min_duration_bars': 5,          # 减少最小持续时间
        })
        
        # 调整成交量确认参数
        self.volume_system.config.update({
            'confirmation_window': 3,        # 减少确认窗口
            'volume_thresholds': {
                'strong_confirmation': 1.8,
                'confirmation': 1.3,
                'weak_confirmation': 1.1,
                'no_confirmation': 1.0,
            },
            'price_tolerance_pct': 0.01,     # 增加价格容差
            'min_test_count': 1,             # 减少最小测试次数
        })
    
    def calculate_final_score(self, level: Dict, level_type: str, current_price: float) -> Dict:
        """调整评分计算（降低门槛）"""
        score = 0.0
        score_factors = {}
        
        # 1. 时间框架权重（0-0.25）
        timeframe_weight = level.get('timeframe_weight', 1)
        timeframe_score = timeframe_weight / 4.0
        score += timeframe_score * 0.25
        score_factors['timeframe'] = timeframe_score
        
        # 2. 置信度/强度（0-0.25）
        if 'confidence' in level:
            confidence_score = level['confidence']
        elif 'base_strength' in level:
            confidence_score = level['base_strength'] / 5.0
        elif 'importance' in level:
            confidence_score = level['importance'] / 3.0
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
                # 即使未确认，也给基础分
                volume_score = 0.3
        else:
            volume_score = 0.5  # 默认分
        
        score += volume_score * 0.2
        score_factors['volume'] = volume_score
        
        # 4. 距离当前价格（0-0.3）
        price = level.get('price', 0)
        if current_price > 0:
            distance_pct = abs(current_price - price) / current_price
            
            # 更宽松的距离评分
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
        
        # 调整等级映射（降低门槛）
        strength_level = self._map_score_to_level_adjusted(final_score)
        
        # 更新level信息
        level['final_score'] = final_score
        level['score_factors'] = score_factors
        level['strength_level'] = strength_level['level']
        level['strength_symbol'] = strength_level['symbol']
        
        return level
    
    def _map_score_to_level_adjusted(self, score: float) -> Dict:
        """调整等级映射（降低门槛）"""
        if score >= 0.70:
            return {'level': '极强', 'symbol': '★★★★★'}
        elif score >= 0.60:
            return {'level': '强', 'symbol': '★★★★'}
        elif score >= 0.50:
            return {'level': '中等', 'symbol': '★★★'}
        elif score >= 0.40:
            return {'level': '弱', 'symbol': '★★'}
        else:
            return {'level': '极弱', 'symbol': '★'}
    
    def multi_timeframe_analysis(self, symbol: str = 'BTCUSDT') -> Dict[str, Any]:
        """调整分析逻辑"""
        result = super().multi_timeframe_analysis(symbol)
        
        # 手动添加一些关键动态位（确保不会全部被过滤）
        current_price = result.get('current_price', 0)
        if current_price > 0:
            # 获取关键EMA和布林带
            try:
                cursor = self.connection.cursor(dictionary=True)
                
                # 获取4H关键指标
                query = """
                    SELECT ema50, boll_up, boll_dn
                    FROM klines 
                    WHERE symbol = %s AND timeframe = '4h'
                    ORDER BY timestamp DESC LIMIT 1
                """
                cursor.execute(query, (symbol,))
                data = cursor.fetchone()
                cursor.close()
                
                if data:
                    ema50 = ensure_float(data['ema50'])
                    boll_up = ensure_float(data['boll_up'])
                    boll_dn = ensure_float(data['boll_dn'])
                    
                    # 添加关键动态位到结果
                    supports = result.get('supports', [])
                    resistances = result.get('resistances', [])
                    
                    # EMA50
                    if ema50 > 0:
                        if current_price > ema50:
                            supports.append({
                                'price': ema50,
                                'type': 'dynamic',
                                'subtype': 'EMA50',
                                'timeframe': '4h',
                                'timeframe_weight': 1,
                                'base_strength': 3,
                                'final_score': 0.65,
                                'strength_symbol': '★★★',
                                'strength_level': '中等'
                            })
                        else:
                            resistances.append({
                                'price': ema50,
                                'type': 'dynamic',
                                'subtype': 'EMA50',
                                'timeframe': '4h',
                                'timeframe_weight': 1,
                                'base_strength': 3,
                                'final_score': 0.65,
                                'strength_symbol': '★★★',
                                'strength_level': '中等'
                            })
                    
                    # 布林带
                    if boll_dn > 0 and current_price > boll_dn:
                        supports.append({
                            'price': boll_dn,
                            'type': 'dynamic',
                            'subtype': 'BOLL_DN',
                            'timeframe': '4h',
                            'timeframe_weight': 1,
                            'base_strength': 2,
                            'final_score': 0.60,
                            'strength_symbol': '★★★',
                            'strength_level': '中等'
                        })
                    
                    if boll_up > 0 and current_price < boll_up:
                        resistances.append({
                            'price': boll_up,
                            'type': 'dynamic',
                            'subtype': 'BOLL_UP',
                            'timeframe': '4h',
                            'timeframe_weight': 1,
                            'base_strength': 2,
                            'final_score': 0.60,
                            'strength_symbol': '★★★',
                            'strength_level': '中等'
                        })
                    
                    # 重新排序
                    supports.sort(key=lambda x: x.get('final_score', 0), reverse=True)
                    resistances.sort(key=lambda x: x.get('final_score', 0), reverse=True)
                    
                    result['supports'] = supports
                    result['resistances'] = resistances
                    
            except Exception as e:
                logger.error(f"添加关键动态位失败: {e}")
        
        return result


def ensure_float(value):
    """确保值为float类型"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except:
        return 0.0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='支撑阻力分析 - 参数调整版')
    parser.add_argument('--symbol', default='BTCUSDT', help='交易对')
    
    args = parser.parse_args()
    
    analyzer = SupportResistanceAnalyzerAdjusted()
    analyzer.run_analysis(symbol=args.symbol)


if __name__ == "__main__":
    main()