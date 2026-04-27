#!/usr/bin/env python3
"""
成交量确认系统
验证支撑阻力位的有效性
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VolumeAnalysis:
    """成交量分析结果"""
    avg_volume: float
    std_volume: float
    median_volume: float
    q75_volume: float
    q90_volume: float
    volume_profile: Dict[str, float]  # 按价格区间的成交量分布

class VolumeConfirmationSystem:
    """成交量确认系统"""
    
    def __init__(self):
        self.config = {
            'confirmation_window': 5,  # 确认窗口（前后N根K线）
            'volume_thresholds': {
                'strong_confirmation': 2.0,  # 强确认：成交量>2倍平均
                'confirmation': 1.5,         # 确认：成交量>1.5倍平均
                'weak_confirmation': 1.2,    # 弱确认：成交量>1.2倍平均
                'no_confirmation': 1.0,      # 无确认：成交量<=平均
            },
            'price_tolerance_pct': 0.005,  # 价格容差0.5%
            'min_test_count': 2,           # 最小测试次数
        }
    
    def analyze_volume_profile(self, prices: List[float], volumes: List[float]) -> VolumeAnalysis:
        """
        分析成交量分布
        
        参数:
            prices: 价格序列
            volumes: 成交量序列
        
        返回:
            成交量分析结果
        """
        if len(prices) != len(volumes):
            logger.debug("价格和成交量序列长度不一致，自动截断到最短长度")
            min_len = min(len(prices), len(volumes))
            prices  = prices[:min_len]
            volumes = volumes[:min_len]
        
        if volumes is None or len(volumes) == 0:
            return VolumeAnalysis(0, 0, 0, 0, 0, {})
        
        volumes_array = np.array(volumes)
        
        # 计算基本统计量
        avg_volume = float(np.mean(volumes_array))
        std_volume = float(np.std(volumes_array))
        median_volume = float(np.median(volumes_array))
        q75_volume = float(np.percentile(volumes_array, 75))
        q90_volume = float(np.percentile(volumes_array, 90))
        
        # 分析成交量价格分布
        volume_profile = self._calculate_volume_profile(prices, volumes)
        
        return VolumeAnalysis(
            avg_volume=avg_volume,
            std_volume=std_volume,
            median_volume=median_volume,
            q75_volume=q75_volume,
            q90_volume=q90_volume,
            volume_profile=volume_profile
        )
    
    def _calculate_volume_profile(self, prices: List[float], volumes: List[float]) -> Dict[str, float]:
        """计算成交量价格分布"""
        if prices is None or len(prices) == 0 or volumes is None or len(volumes) == 0:
            return {}
        
        # 将价格分为10个区间
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        
        if price_range == 0:
            return {}
        
        num_bins = 10
        bin_size = price_range / num_bins
        
        volume_by_bin = [0] * num_bins
        count_by_bin = [0] * num_bins
        
        for price, volume in zip(prices, volumes):
            bin_idx = min(int((price - min_price) / bin_size), num_bins - 1)
            volume_by_bin[bin_idx] += volume
            count_by_bin[bin_idx] += 1
        
        # 计算每个区间的平均成交量
        profile = {}
        for i in range(num_bins):
            bin_start = min_price + i * bin_size
            bin_end = min_price + (i + 1) * bin_size
            avg_volume = volume_by_bin[i] / count_by_bin[i] if count_by_bin[i] > 0 else 0
            
            key = f"{bin_start:.0f}-{bin_end:.0f}"
            profile[key] = avg_volume
        
        return profile
    
    def check_support_confirmation(
        self,
        support_price: float,
        prices: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        timestamps: List[int]
    ) -> Dict[str, any]:
        """
        检查支撑位成交量确认
        
        参数:
            support_price: 支撑位价格
            prices: 价格序列（可以是close或典型价格）
            highs: 高价序列
            lows: 低价序列
            closes: 收盘价序列
            volumes: 成交量序列
            timestamps: 时间戳序列
        
        返回:
            确认结果
        """
        if len(prices) < 20:
            return {'confirmed': False, 'confidence': 0, 'reason': '数据不足'}
        
        # 1. 寻找测试该支撑位的K线
        test_indices = self._find_price_tests(support_price, lows, 'support')
        
        if len(test_indices) < self.config['min_test_count']:
            return {
                'confirmed': False,
                'confidence': 0,
                'reason': f'测试次数不足 ({len(test_indices)}次)',
                'test_count': len(test_indices)
            }
        
        # 2. 分析每次测试的成交量
        test_results = []
        total_confidence = 0
        
        for idx in test_indices:
            test_result = self._analyze_single_test(
                idx, support_price, prices, highs, lows, closes, volumes, 'support'
            )
            test_results.append(test_result)
            total_confidence += test_result['confidence']
        
        avg_confidence = total_confidence / len(test_results) if test_results else 0
        
        # 3. 分析反弹成交量（测试后的K线）
        rebound_analysis = self._analyze_rebound_volume(test_indices, volumes, closes, 'support')
        
        # 4. 综合判断
        confirmed = avg_confidence >= 0.6  # 平均置信度>=60%
        
        result = {
            'confirmed': confirmed,
            'confidence': avg_confidence,
            'test_count': len(test_indices),
            'test_results': test_results,
            'rebound_analysis': rebound_analysis,
            'volume_profile': self._get_volume_at_price(support_price, prices, volumes),
            'recommendation': self._generate_recommendation(confirmed, avg_confidence, len(test_indices))
        }
        
        return result
    
    def check_resistance_confirmation(
        self,
        resistance_price: float,
        prices: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        timestamps: List[int]
    ) -> Dict[str, any]:
        """
        检查阻力位成交量确认
        """
        if len(prices) < 20:
            return {'confirmed': False, 'confidence': 0, 'reason': '数据不足'}
        
        # 寻找测试该阻力位的K线
        test_indices = self._find_price_tests(resistance_price, highs, 'resistance')
        
        if len(test_indices) < self.config['min_test_count']:
            return {
                'confirmed': False,
                'confidence': 0,
                'reason': f'测试次数不足 ({len(test_indices)}次)',
                'test_count': len(test_indices)
            }
        
        # 分析每次测试
        test_results = []
        total_confidence = 0
        
        for idx in test_indices:
            test_result = self._analyze_single_test(
                idx, resistance_price, prices, highs, lows, closes, volumes, 'resistance'
            )
            test_results.append(test_result)
            total_confidence += test_result['confidence']
        
        avg_confidence = total_confidence / len(test_results) if test_results else 0
        
        # 分析回落成交量
        decline_analysis = self._analyze_decline_volume(test_indices, volumes, closes, 'resistance')
        
        confirmed = avg_confidence >= 0.6
        
        result = {
            'confirmed': confirmed,
            'confidence': avg_confidence,
            'test_count': len(test_indices),
            'test_results': test_results,
            'decline_analysis': decline_analysis,
            'volume_profile': self._get_volume_at_price(resistance_price, prices, volumes),
            'recommendation': self._generate_recommendation(confirmed, avg_confidence, len(test_indices))
        }
        
        return result
    
    def _find_price_tests(self, target_price: float, price_series: List[float], level_type: str) -> List[int]:
        """寻找测试特定价格的K线"""
        tolerance = target_price * self.config['price_tolerance_pct']
        test_indices = []
        
        for i in range(len(price_series)):
            if level_type == 'support':
                # 支撑位：低点接近目标价格
                if abs(price_series[i] - target_price) <= tolerance:
                    test_indices.append(i)
            else:  # resistance
                # 阻力位：高点接近目标价格
                if abs(price_series[i] - target_price) <= tolerance:
                    test_indices.append(i)
        
        return test_indices
    
    def _analyze_single_test(
        self,
        idx: int,
        target_price: float,
        prices: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        level_type: str
    ) -> Dict[str, any]:
        """分析单次测试"""
        if idx >= len(volumes) or idx >= len(closes):
            return {'confidence': 0, 'volume_ratio': 0, 'price_action': 'unknown'}
        
        current_volume = volumes[idx]
        current_close = closes[idx]
        
        # 计算成交量比率
        volume_analysis = self.analyze_volume_profile(prices[:idx+1], volumes[:idx+1])
        volume_ratio = current_volume / volume_analysis.avg_volume if volume_analysis.avg_volume > 0 else 1
        
        # 分析价格行为
        price_action = self._analyze_price_action(idx, target_price, highs, lows, closes, level_type)
        
        # 计算置信度
        confidence = self._calculate_test_confidence(volume_ratio, price_action, level_type)
        
        return {
            'index': idx,
            'volume': current_volume,
            'volume_ratio': volume_ratio,
            'close': current_close,
            'price_action': price_action,
            'confidence': confidence,
            'timestamp': idx  # 实际应用中应该是真实时间戳
        }
    
    def _analyze_price_action(
        self,
        idx: int,
        target_price: float,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        level_type: str
    ) -> str:
        """分析价格行为"""
        if idx == 0 or idx >= len(closes) - 1:
            return 'unknown'
        
        prev_close = closes[idx-1]
        current_close = closes[idx]
        next_close = closes[idx+1] if idx + 1 < len(closes) else current_close
        
        if level_type == 'support':
            # 支撑位：检查是否反弹
            if current_close > target_price and next_close > current_close:
                return 'bounce'  # 反弹
            elif current_close < target_price and next_close < current_close:
                return 'break'   # 跌破
            else:
                return 'consolidate'  # 震荡
        else:  # resistance
            # 阻力位：检查是否回落
            if current_close < target_price and next_close < current_close:
                return 'reject'  # 拒绝
            elif current_close > target_price and next_close > current_close:
                return 'break'   # 突破
            else:
                return 'consolidate'  # 震荡
    
    def _calculate_test_confidence(self, volume_ratio: float, price_action: str, level_type: str) -> float:
        """计算单次测试置信度"""
        confidence = 0.0
        
        # 成交量得分
        if volume_ratio >= self.config['volume_thresholds']['strong_confirmation']:
            confidence += 0.5
        elif volume_ratio >= self.config['volume_thresholds']['confirmation']:
            confidence += 0.4
        elif volume_ratio >= self.config['volume_thresholds']['weak_confirmation']:
            confidence += 0.3
        else:
            confidence += 0.1
        
        # 价格行为得分
        if level_type == 'support':
            if price_action == 'bounce':
                confidence += 0.5
            elif price_action == 'consolidate':
                confidence += 0.3
            else:  # break
                confidence += 0.0
        else:  # resistance
            if price_action == 'reject':
                confidence += 0.5
            elif price_action == 'consolidate':
                confidence += 0.3
            else:  # break
                confidence += 0.0
        
        return min(confidence, 1.0)
    
    def _analyze_rebound_volume(self, test_indices: List[int], volumes: List[float], closes: List[float], level_type: str) -> Dict[str, any]:
        """分析反弹成交量"""
        if not test_indices:
            return {'avg_rebound_ratio': 0, 'strong_rebound_count': 0}
        
        rebound_ratios = []
        strong_rebounds = 0
        
        volume_analysis = self.analyze_volume_profile([], volumes)
        
        for idx in test_indices:
            if idx + 3 < len(volumes) and idx + 3 < len(closes):
                # 检查后3根K线
                rebound_volumes = volumes[idx+1:idx+4]
                rebound_closes = closes[idx+1:idx+4]
                
                if len(rebound_volumes) > 0 and len(rebound_closes) > 0:
                    # 检查是否有放量反弹
                    max_rebound_volume = max(rebound_volumes)
                    rebound_ratio = max_rebound_volume / volume_analysis.avg_volume if volume_analysis.avg_volume > 0 else 0
                    rebound_ratios.append(rebound_ratio)
                    
                    # 检查价格是否反弹
                    if level_type == 'support':
                        price_rebound = any(c > closes[idx] for c in rebound_closes)
                        if price_rebound and rebound_ratio > 1.5:
                            strong_rebounds += 1
        
        avg_rebound_ratio = sum(rebound_ratios) / len(rebound_ratios) if rebound_ratios else 0
        
        return {
            'avg_rebound_ratio': avg_rebound_ratio,
            'strong_rebound_count': strong_rebounds,
            'total_tests': len(test_indices)
        }
    
    def _analyze_decline_volume(self, test_indices: List[int], volumes: List[float], closes: List[float], level_type: str) -> Dict[str, any]:
        """分析回落成交量"""
        if not test_indices:
            return {'avg_decline_ratio': 0, 'strong_decline_count': 0}
        
        decline_ratios = []
        strong_declines = 0
        
        volume_analysis = self.analyze_volume_profile([], volumes)
        
        for idx in test_indices:
            if idx + 3 < len(volumes) and idx + 3 < len(closes):
                decline_volumes = volumes[idx+1:idx+4]
                decline_closes = closes[idx+1:idx+4]
                
                if len(decline_volumes) > 0 and len(decline_closes) > 0:
                    max_decline_volume = max(decline_volumes)
                    decline_ratio = max_decline_volume / volume_analysis.avg_volume if volume_analysis.avg_volume > 0 else 0
                    decline_ratios.append(decline_ratio)
                    
                    if level_type == 'resistance':
                        price_decline = any(c < closes[idx] for c in decline_closes)
                        if price_decline and decline_ratio > 1.5:
                            strong_declines += 1
        
        avg_decline_ratio = sum(decline_ratios) / len(decline_ratios) if decline_ratios else 0
        
        return {
            'avg_decline_ratio': avg_decline_ratio,
            'strong_decline_count': strong_declines,
            'total_tests': len(test_indices)
        }
    
    def _get_volume_at_price(self, target_price: float, prices: List[float], volumes: List[float]) -> Dict[str, float]:
        """获取特定价格附近的成交量"""
        tolerance = target_price * 0.01  # 1%容差
        nearby_volumes = []
        nearby_prices = []
        
        for price, volume in zip(prices, volumes):
            if abs(price - target_price) <= tolerance:
                nearby_volumes.append(volume)
                nearby_prices.append(price)
        
        if not nearby_volumes:
            return {'avg_volume': 0, 'max_volume': 0, 'count': 0}
        
        return {
            'avg_volume': float(np.mean(nearby_volumes)),
            'max_volume': float(np.max(nearby_volumes)),
            'min_volume': float(np.min(nearby_volumes)),
            'count': len(nearby_volumes),
            'price_range': [min(nearby_prices), max(nearby_prices)] if nearby_prices else [0, 0]
        }
    
    def _generate_recommendation(self, confirmed: bool, confidence: float, test_count: int) -> str:
        """生成推荐"""
        if not confirmed:
            if test_count < self.config['min_test_count']:
                return "测试次数不足，需要更多数据确认"
            elif confidence < 0.4:
                return "成交量确认较弱，谨慎参考"
            else:
                return "未通过成交量确认，不建议依赖此位点"
        else:
            if confidence >= 0.8:
                return "强成交量确认，可靠性高"
            elif confidence >= 0.6:
                return "成交量确认良好，可参考"
            else:
                return "基本确认，但需结合其他指标"
    
    def integrate_with_support_resistance(
        self,
        support_levels: List[Dict],
        resistance_levels: List[Dict],
        prices: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        timestamps: List[int]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        将成交量确认集成到支撑阻力分析中

        返回:
            (confirmed_supports, confirmed_resistances): 经过成交量确认的位点
        """
        # 统一所有序列长度，取最短的
        min_len = min(len(prices), len(highs), len(lows), len(closes), len(volumes), len(timestamps))
        prices, highs, lows, closes, volumes, timestamps = (
            prices[:min_len], highs[:min_len], lows[:min_len],
            closes[:min_len], volumes[:min_len], timestamps[:min_len]
        )

        confirmed_supports = []
        confirmed_resistances = []
        
        # 分析支撑位
        for support in support_levels:
            support_price = support.get('price', 0)
            if support_price <= 0:
                continue
            
            confirmation = self.check_support_confirmation(
                support_price, prices, highs, lows, closes, volumes, timestamps
            )
            
            # 更新支撑位信息
            updated_support = support.copy()
            updated_support['volume_confirmation'] = confirmation
            updated_support['confirmed'] = confirmation['confirmed']
            updated_support['confidence'] = confirmation['confidence']
            
            # 如果确认，添加到结果列表
            if confirmation['confirmed']:
                confirmed_supports.append(updated_support)
        
        # 分析阻力位
        for resistance in resistance_levels:
            resistance_price = resistance.get('price', 0)
            if resistance_price <= 0:
                continue
            
            confirmation = self.check_resistance_confirmation(
                resistance_price, prices, highs, lows, closes, volumes, timestamps
            )
            
            updated_resistance = resistance.copy()
            updated_resistance['volume_confirmation'] = confirmation
            updated_resistance['confirmed'] = confirmation['confirmed']
            updated_resistance['confidence'] = confirmation['confidence']
            
            if confirmation['confirmed']:
                confirmed_resistances.append(updated_resistance)
        
        # 按置信度排序
        confirmed_supports.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        confirmed_resistances.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        logger.info(f"成交量确认: {len(confirmed_supports)}/{len(support_levels)}支撑位, "
                   f"{len(confirmed_resistances)}/{len(resistance_levels)}阻力位")
        
        return confirmed_supports, confirmed_resistances


# 测试函数
def test_volume_confirmation():
    """测试成交量确认系统"""
    print("🧪 测试成交量确认系统")
    print("=" * 60)
    
    # 创建测试数据
    np.random.seed(42)
    n = 100
    base_price = 75000
    
    # 生成价格序列
    trend = np.linspace(0, 0.05, n)
    noise = np.random.normal(0, 0.015, n)
    closes = base_price * (1 + trend + noise)
    
    # 生成高点和低点
    highs = closes * (1 + np.abs(np.random.normal(0, 0.008, n)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.008, n)))
    
    # 生成成交量（在特定价格区域放量）
    volumes = np.random.normal(1000, 200, n)
    
    # 模拟在75000附近放量（支撑位）
    support_price = 75000
    for i in range(n):
        if abs(closes[i] - support_price) < support_price * 0.01:  # 1%范围内
            volumes[i] *= 2.5  # 放量2.5倍
    
    # 模拟在76000附近放量（阻力位）
    resistance_price = 76000
    for i in range(n):
        if abs(closes[i] - resistance_price) < resistance_price * 0.01:
            volumes[i] *= 2.0  # 放量2倍
    
    prices = closes  # 使用收盘价作为价格序列
    
    # 创建系统
    system = VolumeConfirmationSystem()
    
    # 测试支撑位确认
    print("\n📊 测试支撑位确认 ($75,000):")
    support_result = system.check_support_confirmation(
        support_price, prices, highs, lows, closes, volumes, list(range(n))
    )
    
    print(f"  确认状态: {'✅ 通过' if support_result['confirmed'] else '❌ 未通过'}")
    print(f"  置信度: {support_result['confidence']:.2f}")
    print(f"  测试次数: {support_result['test_count']}")
    print(f"  推荐: {support_result['recommendation']}")
    
    # 测试阻力位确认
    print("\n📈 测试阻力位确认 ($76,000):")
    resistance_result = system.check_resistance_confirmation(
        resistance_price, prices, highs, lows, closes, volumes, list(range(n))
    )
    
    print(f"  确认状态: {'✅ 通过' if resistance_result['confirmed'] else '❌ 未通过'}")
    print(f"  置信度: {resistance_result['confidence']:.2f}")
    print(f"  测试次数: {resistance_result['test_count']}")
    print(f"  推荐: {resistance_result['recommendation']}")
    
    # 测试集成功能
    print("\n🔗 测试集成功能:")
    support_levels = [
        {'price': 75000, 'type': 'technical', 'strength': 3},
        {'price': 74800, 'type': 'psychological', 'strength': 2},
        {'price': 74500, 'type': 'dynamic', 'strength': 2}
    ]
    
    resistance_levels = [
        {'price': 76000, 'type': 'technical', 'strength': 3},
        {'price': 76200, 'type': 'psychological', 'strength': 2},
        {'price': 76500, 'type': 'dynamic', 'strength': 2}
    ]
    
    confirmed_supports, confirmed_resistances = system.integrate_with_support_resistance(
        support_levels, resistance_levels, prices, highs, lows, closes, volumes, list(range(n))
    )
    
    print(f"  原始支撑位: {len(support_levels)}个 → 确认后: {len(confirmed_supports)}个")
    print(f"  原始阻力位: {len(resistance_levels)}个 → 确认后: {len(confirmed_resistances)}个")
    
    if confirmed_supports:
        print("\n  ✅ 确认的支撑位:")
        for i, support in enumerate(confirmed_supports[:3], 1):
            print(f"    {i}. ${support['price']:,.0f} (置信度: {support['confidence']:.2f})")
    
    if confirmed_resistances:
        print("\n  ✅ 确认的阻力位:")
        for i, resistance in enumerate(confirmed_resistances[:3], 1):
            print(f"    {i}. ${resistance['price']:,.0f} (置信度: {resistance['confidence']:.2f})")
    
    return True


if __name__ == "__main__":
    test_volume_confirmation()