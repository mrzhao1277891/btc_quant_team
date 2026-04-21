#!/usr/bin/env python3
"""
摆动点识别优化器
增加成交量过滤、时间过滤、幅度过滤，减少噪音
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SwingPointOptimizer:
    """优化版摆动点识别器"""
    
    def __init__(self):
        self.config = {
            'min_amplitude_multiplier': 1.5,  # 最小幅度 = ATR × 倍数
            'volume_threshold': 1.2,  # 成交量阈值（>平均成交量×倍数）
            'max_lookback_days': 30,  # 最大回溯天数
            'window_sizes': {
                '1M': 3,   # 月线窗口
                '1w': 5,   # 周线窗口
                '1d': 7,   # 日线窗口
                '4h': 9,   # 4小时窗口
                '1h': 11,  # 小时线窗口
            }
        }
    
    def calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """计算平均真实波幅(ATR)"""
        if len(highs) < period + 1:
            return 0.0
        
        tr_values = []
        for i in range(1, len(highs)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            tr = max(tr1, tr2, tr3)
            tr_values.append(tr)
        
        return sum(tr_values[-period:]) / period if tr_values else 0.0
    
    def calculate_volume_profile(self, volumes: List[float]) -> Dict[str, float]:
        """计算成交量分布"""
        if not volumes:
            return {'avg': 0, 'std': 0, 'median': 0}
        
        volumes_array = np.array(volumes)
        return {
            'avg': float(np.mean(volumes_array)),
            'std': float(np.std(volumes_array)),
            'median': float(np.median(volumes_array)),
            'q75': float(np.percentile(volumes_array, 75)),
            'q90': float(np.percentile(volumes_array, 90))
        }
    
    def find_swing_points_optimized(
        self,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        timestamps: List[int],
        timeframe: str = '4h',
        min_days: int = 7
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        优化版摆动点识别
        
        参数:
            highs: 高价序列
            lows: 低价序列
            closes: 收盘价序列
            volumes: 成交量序列
            timestamps: 时间戳序列
            timeframe: 时间框架
            min_days: 最小保留天数
        
        返回:
            (swing_highs, swing_lows): 优化后的摆动点列表
        """
        if len(highs) < 20:
            logger.warning("数据不足，至少需要20个数据点")
            return [], []
        
        # 1. 计算技术指标
        atr = self.calculate_atr(highs, lows, closes)
        volume_profile = self.calculate_volume_profile(volumes)
        
        # 2. 获取窗口大小
        window = self.config['window_sizes'].get(timeframe, 5)
        
        # 3. 识别原始摆动点
        raw_highs, raw_lows = self._find_raw_swing_points(highs, lows, window)
        
        # 4. 过滤摆动高点
        filtered_highs = []
        for idx in raw_highs:
            swing_high = self._filter_swing_high(
                idx, highs, lows, closes, volumes, timestamps,
                atr, volume_profile, timeframe, min_days
            )
            if swing_high:
                filtered_highs.append(swing_high)
        
        # 5. 过滤摆动低点
        filtered_lows = []
        for idx in raw_lows:
            swing_low = self._filter_swing_low(
                idx, highs, lows, closes, volumes, timestamps,
                atr, volume_profile, timeframe, min_days
            )
            if swing_low:
                filtered_lows.append(swing_low)
        
        logger.info(f"优化过滤: {len(raw_highs)}→{len(filtered_highs)}高点, {len(raw_lows)}→{len(filtered_lows)}低点")
        return filtered_highs, filtered_lows
    
    def _find_raw_swing_points(self, highs: List[float], lows: List[float], window: int) -> Tuple[List[int], List[int]]:
        """识别原始摆动点（无过滤）"""
        n = len(highs)
        if n < window * 2 + 1:
            return [], []
        
        swing_highs = []
        swing_lows = []
        
        for i in range(window, n - window):
            # 检查摆动高点
            is_high = True
            for j in range(1, window + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_high = False
                    break
            
            # 检查摆动低点
            is_low = True
            for j in range(1, window + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_low = False
                    break
            
            if is_high:
                swing_highs.append(i)
            if is_low:
                swing_lows.append(i)
        
        return swing_highs, swing_lows
    
    def _filter_swing_high(
        self,
        idx: int,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        timestamps: List[int],
        atr: float,
        volume_profile: Dict[str, float],
        timeframe: str,
        min_days: int
    ) -> Optional[Dict]:
        """过滤摆动高点"""
        # 1. 幅度过滤
        amplitude = self._calculate_amplitude(idx, highs, lows, 3)  # 3根K线窗口
        min_amplitude = atr * self.config['min_amplitude_multiplier']
        
        if amplitude < min_amplitude:
            return None
        
        # 2. 成交量过滤
        volume = volumes[idx] if idx < len(volumes) else 0
        if volume < volume_profile['avg'] * self.config['volume_threshold']:
            return None
        
        # 3. 时间过滤（只保留最近N天）
        if self._is_too_old(idx, timestamps, timeframe, min_days):
            return None
        
        # 4. 形态过滤（检查是否为有效顶部）
        if not self._is_valid_top(idx, highs, lows, closes, 5):
            return None
        
        # 构建摆动高点信息
        return {
            'index': idx,
            'price': highs[idx],
            'timestamp': timestamps[idx],
            'amplitude': amplitude,
            'volume': volume,
            'volume_ratio': volume / volume_profile['avg'] if volume_profile['avg'] > 0 else 0,
            'atr_ratio': amplitude / atr if atr > 0 else 0,
            'confidence': self._calculate_confidence(idx, highs, lows, closes, volumes, volume_profile)
        }
    
    def _filter_swing_low(
        self,
        idx: int,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        timestamps: List[int],
        atr: float,
        volume_profile: Dict[str, float],
        timeframe: str,
        min_days: int
    ) -> Optional[Dict]:
        """过滤摆动低点"""
        # 1. 幅度过滤
        amplitude = self._calculate_amplitude(idx, highs, lows, 3)
        min_amplitude = atr * self.config['min_amplitude_multiplier']
        
        if amplitude < min_amplitude:
            return None
        
        # 2. 成交量过滤（底部可以缩量）
        volume = volumes[idx] if idx < len(volumes) else 0
        # 底部允许缩量，但反弹时需要放量
        
        # 3. 时间过滤
        if self._is_too_old(idx, timestamps, timeframe, min_days):
            return None
        
        # 4. 形态过滤（检查是否为有效底部）
        if not self._is_valid_bottom(idx, highs, lows, closes, 5):
            return None
        
        # 检查反弹成交量（后3根K线）
        rebound_volume_ok = True
        if idx + 3 < len(volumes):
            rebound_volumes = volumes[idx+1:idx+4]
            if rebound_volumes and max(rebound_volumes) < volume_profile['avg'] * 1.5:
                rebound_volume_ok = False
        
        if not rebound_volume_ok:
            return None
        
        return {
            'index': idx,
            'price': lows[idx],
            'timestamp': timestamps[idx],
            'amplitude': amplitude,
            'volume': volume,
            'volume_ratio': volume / volume_profile['avg'] if volume_profile['avg'] > 0 else 0,
            'atr_ratio': amplitude / atr if atr > 0 else 0,
            'confidence': self._calculate_confidence(idx, highs, lows, closes, volumes, volume_profile)
        }
    
    def _calculate_amplitude(self, idx: int, highs: List[float], lows: List[float], window: int) -> float:
        """计算摆动点幅度"""
        start = max(0, idx - window)
        end = min(len(highs), idx + window + 1)
        
        if idx < len(highs):
            # 对于高点，计算从周围平均低点到高点的幅度
            surrounding_lows = lows[start:end]
            if surrounding_lows:
                avg_low = sum(surrounding_lows) / len(surrounding_lows)
                return highs[idx] - avg_low
        else:
            # 对于低点，计算从低点到周围平均高点的幅度
            surrounding_highs = highs[start:end]
            if surrounding_highs:
                avg_high = sum(surrounding_highs) / len(surrounding_highs)
                return avg_high - lows[idx]
        
        return 0.0
    
    def _is_too_old(self, idx: int, timestamps: List[int], timeframe: str, min_days: int) -> bool:
        """检查是否太旧"""
        if not timestamps or idx >= len(timestamps):
            return True
        
        # 计算时间差（毫秒转天）
        current_time = timestamps[-1] if timestamps else 0
        swing_time = timestamps[idx]
        time_diff_days = (current_time - swing_time) / (1000 * 60 * 60 * 24)
        
        return time_diff_days > min_days
    
    def _is_valid_top(self, idx: int, highs: List[float], lows: List[float], closes: List[float], window: int) -> bool:
        """检查是否为有效顶部"""
        if idx < window or idx >= len(highs) - window:
            return False
        
        # 检查前后价格走势
        prev_prices = closes[idx-window:idx]
        next_prices = closes[idx+1:idx+window+1]
        
        if not prev_prices or not next_prices:
            return False
        
        # 前window根K线应该上涨
        prev_trend = (closes[idx] - closes[idx-window]) / closes[idx-window]
        
        # 后window根K线应该下跌
        next_trend = (closes[idx+window] - closes[idx]) / closes[idx]
        
        return prev_trend > 0.01 and next_trend < -0.01  # 至少1%的涨跌
    
    def _is_valid_bottom(self, idx: int, highs: List[float], lows: List[float], closes: List[float], window: int) -> bool:
        """检查是否为有效底部"""
        if idx < window or idx >= len(lows) - window:
            return False
        
        # 检查前后价格走势
        prev_prices = closes[idx-window:idx]
        next_prices = closes[idx+1:idx+window+1]
        
        if not prev_prices or not next_prices:
            return False
        
        # 前window根K线应该下跌
        prev_trend = (closes[idx] - closes[idx-window]) / closes[idx-window]
        
        # 后window根K线应该上涨
        next_trend = (closes[idx+window] - closes[idx]) / closes[idx]
        
        return prev_trend < -0.01 and next_trend > 0.01  # 至少1%的涨跌
    
    def _calculate_confidence(
        self,
        idx: int,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        volume_profile: Dict[str, float]
    ) -> float:
        """计算置信度分数（0-1）"""
        confidence = 0.0
        
        # 1. 幅度得分（0-0.3）
        amplitude = self._calculate_amplitude(idx, highs, lows, 3)
        amplitude_score = min(amplitude / (volume_profile.get('std', 1) * 3), 0.3)
        confidence += amplitude_score
        
        # 2. 成交量得分（0-0.3）
        if idx < len(volumes):
            volume_ratio = volumes[idx] / volume_profile['avg'] if volume_profile['avg'] > 0 else 1
            volume_score = min((volume_ratio - 1) * 0.1, 0.3)
            confidence += volume_score
        
        # 3. 形态得分（0-0.2）
        # 检查是否为双顶/双底或头肩形态
        pattern_score = self._check_patterns(idx, highs, lows, closes, 5)
        confidence += pattern_score * 0.2
        
        # 4. 时间得分（0-0.2）
        # 近期摆动点得分更高
        time_score = 0.2 if idx > len(highs) * 0.7 else 0.1
        confidence += time_score
        
        return min(confidence, 1.0)
    
    def _check_patterns(self, idx: int, highs: List[float], lows: List[float], closes: List[float], window: int) -> float:
        """检查形态模式"""
        # 简化版形态检查
        if idx < window * 2 or idx >= len(highs) - window * 2:
            return 0.0
        
        # 检查双顶/双底
        left_window = highs[idx-window:idx] if idx < len(highs) else []
        right_window = highs[idx+1:idx+window+1] if idx + window < len(highs) else []
        
        if left_window and right_window:
            # 检查是否有相似的高点/低点
            left_extreme = max(left_window) if highs[idx] == max(left_window + [highs[idx]]) else min(left_window)
            right_extreme = max(right_window) if highs[idx] == max(right_window + [highs[idx]]) else min(right_window)
            
            similarity = 1 - abs(left_extreme - right_extreme) / highs[idx]
            if similarity > 0.95:  # 95%相似
                return 0.8  # 可能是双顶/双底
        
        return 0.0


# 测试函数
def test_swing_point_optimizer():
    """测试摆动点优化器"""
    print("🧪 测试摆动点优化器")
    print("=" * 60)
    
    # 创建测试数据
    np.random.seed(42)
    n = 100
    base_price = 75000
    
    # 生成价格序列（有趋势和波动）
    trend = np.linspace(0, 0.1, n)  # 10%上涨趋势
    noise = np.random.normal(0, 0.02, n)  # 2%噪声
    prices = base_price * (1 + trend + noise)
    
    # 生成高点和低点（价格±1%）
    highs = prices * (1 + np.abs(np.random.normal(0, 0.01, n)))
    lows = prices * (1 - np.abs(np.random.normal(0, 0.01, n)))
    closes = prices
    
    # 生成成交量（与波动相关）
    volatility = np.abs(np.random.normal(0, 0.015, n))
    volumes = 1000 + volatility * 50000
    
    # 生成时间戳
    timestamps = [1704067200000 + i * 3600000 * 4 for i in range(n)]  # 4小时间隔
    
    # 创建优化器
    optimizer = SwingPointOptimizer()
    
    # 运行优化识别
    swing_highs, swing_lows = optimizer.find_swing_points_optimized(
        highs=list(highs),
        lows=list(lows),
        closes=list(closes),
        volumes=list(volumes),
        timestamps=timestamps,
        timeframe='4h',
        min_days=14
    )
    
    print(f"✅ 识别到 {len(swing_highs)} 个优化后的摆动高点")
    print(f"✅ 识别到 {len(swing_lows)} 个优化后的摆动低点")
    
    if swing_highs:
        print("\n📈 摆动高点示例:")
        for i, high in enumerate(swing_highs[:3], 1):
            print(f"  {i}. 价格: ${high['price']:,.2f}, 置信度: {high['confidence']:.2f}, "
                  f"成交量比: {high['volume_ratio']:.2f}x")
    
    if swing_lows:
        print("\n📉 摆动低点示例:")
        for i, low in enumerate(swing_lows[:3], 1):
            print(f"  {i}. 价格: ${low['price']:,.2f}, 置信度: {low['confidence']:.2f}, "
                  f"成交量比: {low['volume_ratio']:.2f}x")
    
    # 计算过滤效果
    raw_highs, raw_lows = optimizer._find_raw_swing_points(list(highs), list(lows), 5)
    print(f"\n📊 过滤效果: 原始{len(raw_highs)}高点→优化{len(swing_highs)}高点 "
          f"({len(swing_highs)/len(raw_highs)*100:.1f}%保留)")
    print(f"           原始{len(raw_lows)}低点→优化{len(swing_lows)}低点 "
          f"({len(swing_lows)/len(raw_lows)*100:.1f}%保留)")
    
    return True


if __name__ == "__main__":
    test_swing_point_optimizer()
