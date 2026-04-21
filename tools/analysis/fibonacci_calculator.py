#!/usr/bin/env python3
"""
斐波那契位计算器
自动识别价格波段，计算关键斐波那契位
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PriceWave:
    """价格波段"""
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    direction: str  # 'up' or 'down'
    amplitude_pct: float
    duration_bars: int
    confidence: float

class FibonacciCalculator:
    """斐波那契位计算器"""
    
    def __init__(self):
        # 关键斐波那契比率
        self.key_ratios = {
            'extreme': [0.0, 1.0, 1.272, 1.618, 2.0, 2.618],
            'major': [0.236, 0.382, 0.5, 0.618, 0.786],
            'minor': [0.146, 0.236, 0.382, 0.5, 0.618, 0.786, 0.886]
        }
        
        # 波段识别参数
        self.wave_config = {
            'min_amplitude_pct': 5.0,  # 最小波段幅度5%
            'min_duration_bars': 10,   # 最小持续时间（K线数）
            'smoothing_window': 3,     # 平滑窗口
            'trend_confirmation': 5,   # 趋势确认K线数
        }
    
    def identify_waves(self, prices: List[float], volumes: Optional[List[float]] = None) -> List[PriceWave]:
        """
        识别价格波段
        
        参数:
            prices: 价格序列
            volumes: 成交量序列（可选）
        
        返回:
            识别的波段列表
        """
        if len(prices) < 20:
            logger.warning("价格数据不足，至少需要20个数据点")
            return []
        
        # 平滑价格序列
        smoothed_prices = self._smooth_prices(prices)
        
        # 寻找转折点
        turning_points = self._find_turning_points(smoothed_prices)
        
        # 构建波段
        waves = self._build_waves(turning_points, prices, volumes)
        
        # 过滤无效波段
        filtered_waves = self._filter_waves(waves)
        
        logger.info(f"识别到 {len(filtered_waves)} 个有效价格波段")
        return filtered_waves
    
    def _smooth_prices(self, prices: List[float]) -> List[float]:
        """平滑价格序列"""
        window = self.wave_config['smoothing_window']
        if len(prices) < window:
            return prices
        
        smoothed = []
        for i in range(len(prices)):
            start = max(0, i - window)
            end = min(len(prices), i + window + 1)
            smoothed.append(np.mean(prices[start:end]))
        
        return smoothed
    
    def _find_turning_points(self, prices: List[float]) -> List[int]:
        """寻找转折点"""
        n = len(prices)
        turning_points = []
        
        for i in range(2, n - 2):
            # 检查是否为局部高点
            if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
                prices[i] > prices[i+1] and prices[i] > prices[i+2]):
                turning_points.append(i)
            
            # 检查是否为局部低点
            elif (prices[i] < prices[i-1] and prices[i] < prices[i-2] and
                  prices[i] < prices[i+1] and prices[i] < prices[i+2]):
                turning_points.append(i)
        
        # 去重相近的转折点
        deduplicated = []
        last_point = -10  # 确保第一个点被加入
        for point in turning_points:
            if point - last_point > 3:  # 至少间隔3根K线
                deduplicated.append(point)
                last_point = point
        
        return deduplicated
    
    def _build_waves(self, turning_points: List[int], prices: List[float], volumes: Optional[List[float]]) -> List[PriceWave]:
        """构建波段"""
        if len(turning_points) < 2:
            return []
        
        waves = []
        
        for i in range(len(turning_points) - 1):
            start_idx = turning_points[i]
            end_idx = turning_points[i + 1]
            
            start_price = prices[start_idx]
            end_price = prices[end_idx]
            
            # 确定方向
            if end_price > start_price:
                direction = 'up'
                amplitude_pct = (end_price - start_price) / start_price * 100
            else:
                direction = 'down'
                amplitude_pct = (start_price - end_price) / start_price * 100
            
            duration_bars = end_idx - start_idx
            
            # 计算置信度
            confidence = self._calculate_wave_confidence(
                start_idx, end_idx, prices, volumes, direction
            )
            
            wave = PriceWave(
                start_idx=start_idx,
                end_idx=end_idx,
                start_price=start_price,
                end_price=end_price,
                direction=direction,
                amplitude_pct=amplitude_pct,
                duration_bars=duration_bars,
                confidence=confidence
            )
            
            waves.append(wave)
        
        return waves
    
    def _calculate_wave_confidence(
        self,
        start_idx: int,
        end_idx: int,
        prices: List[float],
        volumes: Optional[List[float]],
        direction: str
    ) -> float:
        """计算波段置信度"""
        confidence = 0.0
        
        # 1. 幅度得分（0-0.4）
        wave_prices = prices[start_idx:end_idx+1]
        if direction == 'up':
            wave_amplitude = max(wave_prices) - min(wave_prices)
        else:
            wave_amplitude = max(wave_prices) - min(wave_prices)
        
        avg_price = np.mean(wave_prices)
        amplitude_pct = wave_amplitude / avg_price * 100 if avg_price > 0 else 0
        
        if amplitude_pct >= 10:
            confidence += 0.4
        elif amplitude_pct >= 5:
            confidence += 0.3
        elif amplitude_pct >= 3:
            confidence += 0.2
        else:
            confidence += 0.1
        
        # 2. 趋势一致性得分（0-0.3）
        trend_consistency = self._check_trend_consistency(start_idx, end_idx, prices, direction)
        confidence += trend_consistency * 0.3
        
        # 3. 成交量确认得分（0-0.3）
        if volumes:
            volume_confirmation = self._check_volume_confirmation(start_idx, end_idx, volumes, direction)
            confidence += volume_confirmation * 0.3
        
        return min(confidence, 1.0)
    
    def _check_trend_consistency(self, start_idx: int, end_idx: int, prices: List[float], direction: str) -> float:
        """检查趋势一致性"""
        wave_prices = prices[start_idx:end_idx+1]
        
        if direction == 'up':
            # 上涨波段应该基本单调递增
            increasing_count = sum(1 for i in range(1, len(wave_prices)) if wave_prices[i] > wave_prices[i-1])
            consistency = increasing_count / (len(wave_prices) - 1)
        else:
            # 下跌波段应该基本单调递减
            decreasing_count = sum(1 for i in range(1, len(wave_prices)) if wave_prices[i] < wave_prices[i-1])
            consistency = decreasing_count / (len(wave_prices) - 1)
        
        return consistency
    
    def _check_volume_confirmation(self, start_idx: int, end_idx: int, volumes: List[float], direction: str) -> float:
        """检查成交量确认"""
        wave_volumes = volumes[start_idx:end_idx+1]
        if not wave_volumes:
            return 0.0
        
        avg_volume = np.mean(wave_volumes)
        
        if direction == 'up':
            # 上涨波段应该放量
            above_avg_count = sum(1 for v in wave_volumes if v > avg_volume * 1.2)
        else:
            # 下跌波段可以放量或缩量
            above_avg_count = sum(1 for v in wave_volumes if v > avg_volume * 1.1)
        
        return above_avg_count / len(wave_volumes)
    
    def _filter_waves(self, waves: List[PriceWave]) -> List[PriceWave]:
        """过滤无效波段"""
        filtered = []
        
        for wave in waves:
            # 幅度过滤
            if wave.amplitude_pct < self.wave_config['min_amplitude_pct']:
                continue
            
            # 持续时间过滤
            if wave.duration_bars < self.wave_config['min_duration_bars']:
                continue
            
            # 置信度过滤
            if wave.confidence < 0.5:
                continue
            
            filtered.append(wave)
        
        return filtered
    
    def calculate_fibonacci_levels(self, wave: PriceWave, level_type: str = 'major') -> Dict[str, float]:
        """
        计算斐波那契位
        
        参数:
            wave: 价格波段
            level_type: 'extreme', 'major', 'minor'
        
        返回:
            斐波那契位字典 {比率: 价格}
        """
        ratios = self.key_ratios.get(level_type, self.key_ratios['major'])
        levels = {}
        
        if wave.direction == 'up':
            # 上涨波段：计算回撤位
            price_range = wave.end_price - wave.start_price
            for ratio in ratios:
                level_price = wave.end_price - price_range * ratio
                levels[f'F{ratio}'] = level_price
        else:
            # 下跌波段：计算反弹位
            price_range = wave.start_price - wave.end_price
            for ratio in ratios:
                level_price = wave.end_price + price_range * ratio
                levels[f'F{ratio}'] = level_price
        
        return levels
    
    def calculate_all_fibonacci_levels(self, waves: List[PriceWave]) -> Dict[str, List[Dict]]:
        """
        计算所有波段的斐波那契位
        
        返回:
            {
                'supports': [{'price': ..., 'wave': ..., 'ratio': ..., 'confidence': ...}],
                'resistances': [...]
            }
        """
        supports = []
        resistances = []
        
        for wave in waves:
            # 计算主要斐波那契位
            fib_levels = self.calculate_fibonacci_levels(wave, 'major')
            
            for ratio_str, price in fib_levels.items():
                ratio = float(ratio_str[1:])  # 去掉'F'前缀
                
                # 根据波段方向判断是支撑还是阻力
                if wave.direction == 'up':
                    # 上涨波段的回撤位是支撑
                    level_info = {
                        'price': price,
                        'wave': {
                            'start': wave.start_price,
                            'end': wave.end_price,
                            'direction': wave.direction,
                            'amplitude_pct': wave.amplitude_pct
                        },
                        'ratio': ratio,
                        'confidence': wave.confidence * self._ratio_weight(ratio),
                        'type': 'fibonacci',
                        'subtype': f'retracement_{ratio}'
                    }
                    supports.append(level_info)
                else:
                    # 下跌波段的反弹位是阻力
                    level_info = {
                        'price': price,
                        'wave': {
                            'start': wave.start_price,
                            'end': wave.end_price,
                            'direction': wave.direction,
                            'amplitude_pct': wave.amplitude_pct
                        },
                        'ratio': ratio,
                        'confidence': wave.confidence * self._ratio_weight(ratio),
                        'type': 'fibonacci',
                        'subtype': f'extension_{ratio}'
                    }
                    resistances.append(level_info)
        
        # 按置信度排序
        supports.sort(key=lambda x: x['confidence'], reverse=True)
        resistances.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'supports': supports,
            'resistances': resistances
        }
    
    def _ratio_weight(self, ratio: float) -> float:
        """计算比率权重"""
        # 黄金分割位0.618权重最高
        if abs(ratio - 0.618) < 0.001:
            return 1.0
        elif abs(ratio - 0.5) < 0.001:
            return 0.9
        elif abs(ratio - 0.382) < 0.001:
            return 0.8
        elif abs(ratio - 0.786) < 0.001:
            return 0.7
        elif abs(ratio - 0.236) < 0.001:
            return 0.6
        else:
            return 0.5
    
    def merge_with_existing_levels(self, fib_levels: Dict, existing_levels: Dict) -> Dict:
        """
        将斐波那契位与现有支撑阻力位合并
        
        参数:
            fib_levels: 斐波那契位
            existing_levels: 现有支撑阻力位
        
        返回:
            合并后的支撑阻力位
        """
        merged_supports = existing_levels.get('supports', []) + fib_levels['supports']
        merged_resistances = existing_levels.get('resistances', []) + fib_levels['resistances']
        
        # 按价格排序（后续需要合并相近位点）
        merged_supports.sort(key=lambda x: x['price'])
        merged_resistances.sort(key=lambda x: x['price'])
        
        return {
            'supports': merged_supports,
            'resistances': merged_resistances
        }


# 测试函数
def test_fibonacci_calculator():
    """测试斐波那契计算器"""
    print("🧪 测试斐波那契计算器")
    print("=" * 60)
    
    # 创建测试数据（明显的上涨和下跌波段）
    np.random.seed(42)
    n = 200
    base_price = 70000
    
    # 创建有明显波段的价格序列
    prices = []
    
    # 波段1：上涨 70,000 → 80,000
    wave1 = np.linspace(70000, 80000, 50)
    
    # 波段2：回调 80,000 → 75,000
    wave2 = np.linspace(80000, 75000, 30)
    
    # 波段3：上涨 75,000 → 85,000
    wave3 = np.linspace(75000, 85000, 60)
    
    # 波段4：回调 85,000 → 80,000
    wave4 = np.linspace(85000, 80000, 40)
    
    # 添加一些噪声
    wave1_noise = wave1 * (1 + np.random.normal(0, 0.005, len(wave1)))
    wave2_noise = wave2 * (1 + np.random.normal(0, 0.005, len(wave2)))
    wave3_noise = wave3 * (1 + np.random.normal(0, 0.005, len(wave3)))
    wave4_noise = wave4 * (1 + np.random.normal(0, 0.005, len(wave4)))
    
    prices = list(wave1_noise) + list(wave2_noise) + list(wave3_noise) + list(wave4_noise)
    
    # 创建计算器
    calculator = FibonacciCalculator()
    
    # 识别波段
    waves = calculator.identify_waves(prices)
    
    print(f"✅ 识别到 {len(waves)} 个价格波段")
    
    for i, wave in enumerate(waves, 1):
        print(f"\n波段 {i}:")
        print(f"  方向: {'上涨' if wave.direction == 'up' else '下跌'}")
        print(f"  起点: ${wave.start_price:,.2f}")
        print(f"  终点: ${wave.end_price:,.2f}")
        print(f"  幅度: {wave.amplitude_pct:.1f}%")
        print(f"  持续时间: {wave.duration_bars}根K线")
        print(f"  置信度: {wave.confidence:.2f}")
    
    # 计算斐波那契位
    if waves:
        fib_levels = calculator.calculate_all_fibonacci_levels(waves)
        
        print(f"\n📊 斐波那契支撑位 ({len(fib_levels['supports'])}个):")
        for i, support in enumerate(fib_levels['supports'][:5], 1):
            print(f"  {i}. ${support['price']:,.2f} (比率: {support['ratio']}, 置信度: {support['confidence']:.2f})")
        
        print(f"\n📈 斐波那契阻力位 ({len(fib_levels['resistances'])}个):")
        for i, resistance in enumerate(fib_levels['resistances'][:5], 1):
            print(f"  {i}. ${resistance['price']:,.2f} (比率: {resistance['ratio']}, 置信度: {resistance['confidence']:.2f})")
        
        # 测试合并功能
        existing_levels = {
            'supports': [
                {'price': 75000, 'type': 'technical', 'confidence': 0.7},
                {'price': 76000, 'type': 'psychological', 'confidence': 0.6}
            ],
            'resistances': [
                {'price': 82000, 'type': 'technical', 'confidence': 0.8},
                {'price': 83000, 'type': 'psychological', 'confidence': 0.5}
            ]
        }
        
        merged = calculator.merge_with_existing_levels(fib_levels, existing_levels)
        
        print(f"\n🔗 合并后支撑位: {len(merged['supports'])}个")
        print(f"🔗 合并后阻力位: {len(merged['resistances'])}个")
    
    return True


if __name__ == "__main__":
    test_fibonacci_calculator()