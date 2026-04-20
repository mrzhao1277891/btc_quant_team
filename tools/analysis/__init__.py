"""
分析工具包

导出以下分析工具:

技术分析 (technical/):
- TechnicalAnalyzer: 技术分析器
- TechnicalAnalysisReport: 技术分析报告
- TrendAnalysis: 趋势分析结果
- MomentumAnalysis: 动量分析结果
- VolatilityAnalysis: 波动率分析结果
- VolumeAnalysis: 成交量分析结果
- TechnicalSignal: 技术信号
- TrendDirection: 趋势方向枚举
- MarketPhase: 市场阶段枚举
- SignalType: 信号类型枚举

支撑阻力分析 (support_resistance/):
- SupportResistanceAnalyzer: 支撑阻力分析器
- SupportResistanceReport: 支撑阻力分析报告
- SupportResistanceLevel: 支撑阻力位
- BreakoutAnalysis: 突破分析
- LevelType: 位位类型枚举
- StrengthLevel: 强度等级枚举
- BreakoutType: 突破类型枚举

模式识别 (patterns/):
- PatternRecognizer: 模式识别器
- PatternAnalysisReport: 模式分析报告
- Pattern: 技术模式
- CandlestickPattern: 蜡烛图模式
- PatternType: 模式类型枚举
- PatternDirection: 模式方向枚举
- PatternStatus: 模式状态枚举

多时间框架分析 (multi_timeframe/):
- MultiTimeframeAnalyzer: 多时间框架分析器
- MultiTimeframeReport: 多时间框架分析报告
- TimeframeAnalysis: 时间框架分析
- TrendAlignment: 趋势对齐分析
- SignalConfirmation: 信号确认分析
- SupportResistanceConfluence: 支撑阻力重合分析
- TimeframeHierarchy: 时间框架层级枚举
- AlignmentStatus: 对齐状态枚举

使用示例:
    from tools.analysis.technical import TechnicalAnalyzer
    from tools.analysis.support_resistance import SupportResistanceAnalyzer
    from tools.analysis.patterns import PatternRecognizer
    from tools.analysis.multi_timeframe import MultiTimeframeAnalyzer
    
    # 技术分析
    technical_analyzer = TechnicalAnalyzer()
    technical_report = technical_analyzer.analyze(df, "BTCUSDT", "4h")
    
    # 支撑阻力分析
    sr_analyzer = SupportResistanceAnalyzer()
    sr_report = sr_analyzer.analyze(df, "BTCUSDT", "4h")
    
    # 模式识别
    pattern_recognizer = PatternRecognizer()
    pattern_report = pattern_recognizer.analyze(df, "BTCUSDT", "4h")
    
    # 多时间框架分析
    mtf_data = {"1d": df_daily, "4h": df_4h, "1h": df_1h}
    mtf_analyzer = MultiTimeframeAnalyzer()
    mtf_report = mtf_analyzer.analyze(mtf_data, "BTCUSDT")
"""

# 技术分析工具
from .technical import (
    TechnicalAnalyzer,
    TechnicalAnalysisReport,
    TrendAnalysis,
    MomentumAnalysis,
    VolatilityAnalysis,
    VolumeAnalysis,
    TechnicalSignal,
    TrendDirection,
    MarketPhase,
    SignalType
)

# 支撑阻力分析工具
from .support_resistance import (
    SupportResistanceAnalyzer,
    SupportResistanceReport,
    SupportResistanceLevel,
    BreakoutAnalysis,
    LevelType,
    StrengthLevel,
    BreakoutType
)

# 模式识别工具
from .patterns import (
    PatternRecognizer,
    PatternAnalysisReport,
    Pattern,
    CandlestickPattern,
    PatternType,
    PatternDirection,
    PatternStatus
)

# 多时间框架分析工具
from .multi_timeframe import (
    MultiTimeframeAnalyzer,
    MultiTimeframeReport,
    TimeframeAnalysis,
    TrendAlignment,
    SignalConfirmation,
    SupportResistanceConfluence,
    TimeframeHierarchy,
    AlignmentStatus
)

__all__ = [
    # 技术分析
    'TechnicalAnalyzer',
    'TechnicalAnalysisReport',
    'TrendAnalysis',
    'MomentumAnalysis',
    'VolatilityAnalysis',
    'VolumeAnalysis',
    'TechnicalSignal',
    'TrendDirection',
    'MarketPhase',
    'SignalType',
    
    # 支撑阻力分析
    'SupportResistanceAnalyzer',
    'SupportResistanceReport',
    'SupportResistanceLevel',
    'BreakoutAnalysis',
    'LevelType',
    'StrengthLevel',
    'BreakoutType',
    
    # 模式识别
    'PatternRecognizer',
    'PatternAnalysisReport',
    'Pattern',
    'CandlestickPattern',
    'PatternType',
    'PatternDirection',
    'PatternStatus',
    
    # 多时间框架分析
    'MultiTimeframeAnalyzer',
    'MultiTimeframeReport',
    'TimeframeAnalysis',
    'TrendAlignment',
    'SignalConfirmation',
    'SupportResistanceConfluence',
    'TimeframeHierarchy',
    'AlignmentStatus'
]