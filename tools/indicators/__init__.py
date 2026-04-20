"""
指标工具包

导出以下指标计算函数:

趋势指标 (trend/):
- calculate_sma: 简单移动平均线
- calculate_ema: 指数移动平均线
- calculate_wma: 加权移动平均线
- calculate_macd: 移动平均收敛发散
- calculate_bollinger_bands: 布林带
- calculate_parabolic_sar: 抛物线转向指标
- identify_trend_direction: 识别趋势方向

动量指标 (momentum/):
- calculate_rsi: 相对强弱指数
- calculate_stochastic: 随机震荡指标
- calculate_cci: 商品通道指数
- calculate_momentum: 动量指标
- calculate_roc: 变动率指标
- calculate_williams_r: 威廉指标
- identify_momentum_signals: 识别动量信号

波动率指标 (volatility/):
- calculate_atr: 平均真实波幅
- calculate_standard_deviation: 标准差
- calculate_keltner_channels: 肯特纳通道
- calculate_donchian_channels: 唐奇安通道
- calculate_historical_volatility: 历史波动率
- calculate_volatility_ratio: 波动率比率
- identify_volatility_regime: 识别波动率状态

成交量指标 (volume/):
- calculate_volume_ma: 成交量移动平均线
- calculate_vwap: 成交量加权平均价格
- calculate_obv: 能量潮指标
- calculate_mfi: 资金流量指数
- calculate_volume_ratio: 成交量比率
- calculate_volume_oscillator: 成交量震荡指标
- identify_volume_signals: 识别成交量信号

使用示例:
    from tools.indicators.trend import calculate_ema, calculate_macd
    from tools.indicators.momentum import calculate_rsi
    from tools.indicators.volatility import calculate_atr
    from tools.indicators.volume import calculate_obv
    
    # 计算EMA
    ema = calculate_ema(prices, 12)
    
    # 计算MACD
    macd_data = calculate_macd(prices)
    
    # 计算RSI
    rsi = calculate_rsi(prices, 14)
    
    # 计算ATR
    atr = calculate_atr(highs, lows, closes, 14)
    
    # 计算OBV
    obv = calculate_obv(closes, volumes)
"""

# 趋势指标
from .trend_complete import (
    calculate_sma,
    calculate_ema,
    calculate_wma,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_parabolic_sar,
    identify_trend_direction
)

# 动量指标
from .momentum import (
    calculate_rsi,
    calculate_stochastic,
    calculate_cci,
    calculate_momentum,
    calculate_roc,
    calculate_williams_r,
    identify_momentum_signals
)

# 波动率指标
from .volatility import (
    calculate_atr,
    calculate_standard_deviation,
    calculate_keltner_channels,
    calculate_donchian_channels,
    calculate_historical_volatility,
    calculate_volatility_ratio,
    identify_volatility_regime
)

# 成交量指标
from .volume import (
    calculate_volume_ma,
    calculate_vwap,
    calculate_obv,
    calculate_mfi,
    calculate_volume_ratio,
    calculate_volume_oscillator,
    identify_volume_signals
)

__all__ = [
    # 趋势指标
    'calculate_sma',
    'calculate_ema',
    'calculate_wma',
    'calculate_macd',
    'calculate_bollinger_bands',
    'calculate_parabolic_sar',
    'identify_trend_direction',
    
    # 动量指标
    'calculate_rsi',
    'calculate_stochastic',
    'calculate_cci',
    'calculate_momentum',
    'calculate_roc',
    'calculate_williams_r',
    'identify_momentum_signals',
    
    # 波动率指标
    'calculate_atr',
    'calculate_standard_deviation',
    'calculate_keltner_channels',
    'calculate_donchian_channels',
    'calculate_historical_volatility',
    'calculate_volatility_ratio',
    'identify_volatility_regime',
    
    # 成交量指标
    'calculate_volume_ma',
    'calculate_vwap',
    'calculate_obv',
    'calculate_mfi',
    'calculate_volume_ratio',
    'calculate_volume_oscillator',
    'identify_volume_signals'
]