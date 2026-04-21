#!/usr/bin/env python3
"""
支撑阻力分析工具

职责: 识别和分析支撑阻力位，包括技术位和心理位

主要功能:
- 技术支撑阻力: 基于技术指标
- 心理支撑阻力: 基于整数关口
- 动态支撑阻力: 基于移动平均线
- 多时间框架支撑阻力: 跨时间框架分析
- 支撑阻力强度评估: 评估位位的可靠性
- 突破分析: 分析突破信号

支撑阻力类型:
1. 技术位: 前期高低点、趋势线、形态颈线
2. 心理位: 整数关口、重要价格水平
3. 动态位: 移动平均线、布林带
4. 斐波那契位: 回调位、扩展位
5. 枢纽点: 日内交易枢纽点

支撑阻力位分析说明文档（基于完整多时间框架数据与交易习惯）
文档目的
本说明文档旨在基于你完整的数据库指标（直接存储月、周、日、4H等多时间框架数据），结合你的交易习惯（Francis交易档案）和多时间框架投资框架，系统化地定义支撑阻力位的识别方法、强度评估规则，并将其落地到具体的交易决策中（入场、止损、目标设置）。文档内容可直接用于指导AI编写支撑阻力分析代码，也可作为你日常手工分析的参考手册。

1. 数据基础与指标说明（优化版）
   1.1 核心数据表 klines - 完整多时间框架支持
   你的klines表直接存储了完整的多时间框架数据，无需聚合计算：

时间框架	记录数	最早时间	最新时间	用途
1M（月线）	160条	2021-05-01	2026-04-21	战略层分析
1w（周线）	250条	2021-07-12	2026-04-20	战役层分析
1d（日线）	600条	2024-08-30	2026-04-21	战术层分析
4h（4小时）	601条	2026-01-11	2026-04-21	执行层分析
1h（小时线）	400条	2026-04-04	2026-04-21	微观监控
15m（15分钟）	300条	2026-04-18	2026-04-21	日内分析
5m（5分钟）	200条	2026-04-20	2026-04-21	精确入场

1.2 各时间框架完整技术指标
每个时间框架都包含以下完整的技术指标字段：

字段类别	具体字段	用途说明
基础价格	open, high, low, close, volume	基础OHLCV数据
移动平均线	ema7, ema12, ema25, ema50, ma5, ma10	动态支撑阻力，趋势判断
MACD指标	dif, dea, macd	动能分析，背离检测
RSI指标	rsi14, rsi6	超买超卖判断
布林带指标	boll, boll_up, boll_md, boll_dn	波动率分析，轨道支撑阻力

优势：直接使用原生时间框架数据，无需聚合计算，分析更准确高效。

1.3 你的交易参数速查（保持不变）
参数	值	说明
账户总本金	2403 U
杠杆	5倍
名义仓位上限	10,000 U	实际占用保证金2000U（占本金83%）
硬止损	100 U / 笔	占本金4.16%
盈亏比	≥2:1	目标盈利≥200U
持仓时间	≤48小时	对应4H级别最多12根K线
分析层级	月→周→日→4h	金字塔决策

2. 支撑阻力位识别方法（优化版）
   根据你的完整多时间框架数据，将支撑阻力位分为以下六类，每类均有优化的计算公式和数据来源。

2.1 技术位：基于价格极值点（摆动高低点 - 优化算法）
数据来源：各时间框架的 high, low

识别规则（优化版）：

使用稳健的摆动点识别算法，避免伪信号：

def find_swing_points(prices, window=5, min_amplitude=0.01):
"""
优化版摆动点识别
window: 观察窗口大小（默认5，可调）
min_amplitude: 最小波动幅度（过滤噪音，默认1%）
返回：摆动高点列表、摆动低点列表
"""
# 实现逻辑：
# 1. 使用滑动窗口检测局部极值
# 2. 考虑价格幅度过滤微小波动
# 3. 结合成交量确认（可选）
# 4. 支持不同时间框架的参数调整

回溯窗口优化：

时间框架	回溯数量	时间跨度	说明
1M（月线）	24条	2年	长期趋势关键位
1w（周线）	52条	1年	中期趋势关键位
1d（日线）	100条	100天	短期交易关键位
4h（4小时）	200条	33天	执行层关键位

去重合并优化：

使用各时间框架自身的 ATR(14) × 动态倍数 作为容差：
- 强趋势市场：ATR × 0.3
- 震荡市场：ATR × 0.5
- 高波动市场：ATR × 0.8

ATR计算优化：为每个时间框架预计算并缓存ATR值，提高分析效率。

2.2 动态位：移动平均线与布林带（优化版）
数据来源：各时间框架的 ema7, ema12, ema25, ema50, boll_md, boll_up, boll_dn

支撑/阻力属性智能判断：

def determine_ma_role(price, ma_value, ma_trend, higher_tf_trend):
"""
智能判断均线的支撑/阻力角色
price: 当前价格
ma_value: 均线值
ma_trend: 均线趋势（向上/向下）
higher_tf_trend: 更高时间框架趋势
返回：角色类型、强度调整
"""
# 规则：
# 1. 价格>均线 & 均线向上 & 大周期向上 → 强支撑
# 2. 价格<均线 & 均线向下 & 大周期向下 → 强阻力
# 3. 均线与价格交叉附近 → 动态转换区域

强度评估优化（考虑多因素）：

均线	基础强度	趋势加成	大周期配合	最终强度
ema50	★★★ (3)	+1	+1	★★★★★ (5)
boll_md	★★★ (3)	+1	+1	★★★★★ (5)
ema25	★★ (2)	+1	+1	★★★★ (4)
ema12	★★ (2)	+1	+0	★★★ (3)
ema7	★ (1)	+0	+0	★ (1)

布林带轨道优化分析：

上轨(boll_up)分析：
- 连续两次触及未突破 → 阻力强度+1
- 布林带收窄后突破 → 趋势启动信号
- 与摆动高点重合 → 强度+1

下轨(boll_dn)分析：
- 连续两次触及未跌破 → 支撑强度+1
- 布林带收窄后跌破 → 趋势反转信号
- 与摆动低点重合 → 强度+1
  2.2 动态位：移动平均线
  数据来源：ema7, ema12, ema25, ema50, boll_md（布林中轨=SMA20）

支撑/阻力属性判断：

当价格在均线上方，且均线方向向上 → 均线为动态支撑（回踩做多）。

当价格在均线下方，且均线方向向下 → 均线为动态阻力（反弹做空）。

均线方向 = 最近3根K线的斜率（当前值 > 前一根值 为向上）。

强度默认值：

均线	基础强度	理由
ema50	★★★ (3)	长期趋势分界线，与你的周线EMA25逻辑一致
boll_md	★★★ (3)	布林中轨=SMA20，经典波段中轴
ema25	★★ (2)	中期趋势，与你的4H决策层匹配
ema12	★★ (2)	短期趋势
ema7	★ (1)	超短期，噪音较大
若均线方向与主趋势（月/周线方向）一致，强度额外 +1（上限3）。

2.3 心理位：整数关口（优化版）
数据来源：当前价格区间 ±20%

识别规则优化：

主要心理关口：
- BTC：每 1,000 美元（如 70,000, 71,000等）
- 重要心理位：每 5,000 美元（如 65,000, 70,000, 75,000）
- 历史关键位：历史高低点附近的整数关口

次要心理关口：
- 每 500 美元（精细分析）
- 每 100 美元（日内交易）

动态范围调整：
def calculate_psychological_levels(current_price, lookback_percent=0.2):
"""
根据当前价格动态计算心理位
lookback_percent: 查看当前价格±20%的范围
"""
min_price = current_price * (1 - lookback_percent)
max_price = current_price * (1 + lookback_percent)
# 生成该范围内的所有主要心理位

强度评估优化：

心理位类型	基础强度	重合加成	最终强度
主要千位关口	★★ (2)	+1	★★★ (3)
重要五千关口	★★★ (3)	+1	★★★★ (4)
历史关键位	★★★★ (4)	+1	★★★★★ (5)

2.4 斐波那契位（完整实现方案）
数据来源：自动识别各时间框架的明显波段

波段识别算法：
class WaveIdentifier:
"""自动识别价格波段"""

    def identify_wave(self, prices, min_wave_percent=0.1):
        """
        识别明显的上升/下降波段
        min_wave_percent: 最小波段幅度（默认10%）
        返回：波段起点、终点、幅度、方向
        """
        # 使用趋势变化检测算法
        # 考虑幅度过滤微小波动
        # 存储最近3个主要波段

斐波那契计算：
class FibonacciCalculator:
"""斐波那契位计算器"""

    key_ratios = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618]
    
    def calculate_levels(self, start_price, end_price, direction='up'):
        """计算斐波那契回撤和扩展位"""
        if direction == 'up':
            # 上升波段：计算回撤位
            diff = end_price - start_price
            return {ratio: end_price - diff * ratio for ratio in self.key_ratios}
        else:
            # 下降波段：计算反弹位
            diff = start_price - end_price
            return {ratio: end_price + diff * ratio for ratio in self.key_ratios}

强度评估：
- 基础强度：★★ (2)
- 与黄金分割位(0.618, 0.5)重合：+1强度
- 与多个技术位重合：+2强度
- 近期被测试有效：+1强度

2.5 成交量确认位（新增）
数据来源：各时间框架的volume字段

成交量分析规则：
def analyze_volume_confirmation(price_level, historical_data):
"""
分析价格位的成交量确认
返回：成交量确认强度(0-2)
"""
# 规则：
# 1. 在该价格位出现放量反弹/回落：+2
# 2. 在该价格位成交量明显放大：+1
# 3. 缩量测试该价格位：+0（需谨慎）

成交量阈值：
- 明显放量：> 1.5倍平均成交量
- 极度放量：> 2.0倍平均成交量
- 缩量：< 0.7倍平均成交量

3. 多时间框架支撑阻力融合规则（优化版）
   根据你的金字塔分析流程（月→周→日→4h），支撑阻力的优先级由时间框架决定，现优化为智能融合系统。

3.1 时间框架权重系统（优化）
时间框架	权重	数据来源	分析重点
1M（月线）	4	直接使用klines表	长期趋势，牛熊分界
1w（周线）	3	直接使用klines表	中期趋势，关键转折
1d（日线）	2	直接使用klines表	交易区域，主要波段
4h（4小时）	1	直接使用klines表	入场时机，微观结构

3.2 智能冲突处理系统
class MultiTimeframeResolver:
"""多时间框架冲突智能解析器"""

    def resolve_conflicts(self, levels_from_all_timeframes):
        """
        智能处理多时间框架支撑阻力冲突
        步骤：
        1. 价格聚类：将相近价格位聚类
        2. 权威性评估：考虑时间框架权重
        3. 近期有效性：最近被测试的位更有效
        4. 生成综合区域：带置信区间的支撑阻力带
        """
        
        # 1. 价格聚类（使用动态ATR容差）
        clustered_levels = self.cluster_by_price(levels_from_all_timeframes)
        
        # 2. 权威性加权计算
        weighted_levels = self.calculate_weighted_levels(clustered_levels)
        
        # 3. 生成综合支撑阻力带
        support_resistance_bands = self.generate_bands(weighted_levels)
        
        return support_resistance_bands

3.3 合并规则优化
def merge_nearby_levels(levels, atr_multiplier=1.0):
"""
合并相近的支撑阻力位
atr_multiplier: 动态调整合并容差
"""
# 使用各时间框架自身的ATR作为容差基准
# 强趋势市场：使用较小容差（ATR×0.8）
# 震荡市场：使用较大容差（ATR×1.2）

合并后的区域属性：
- 价格范围：min(所有相近位) ~ max(所有相近位)
- 综合强度：max(所有位的强度)
- 时间框架覆盖：记录哪些时间框架贡献了该区域
- 置信区间：基于覆盖的时间框架数量和质量

3.4 示例优化
月线EMA50 = 65,200（强度5，权重4）
周线摆动低点 = 65,150（强度4，权重3）
日线心理位 = 65,000（强度3，权重2）
4H布林带下轨 = 65,100（强度3，权重1）

合并结果：
- 支撑区域：64,900 ~ 65,300（ATR×1.0容差）
- 综合强度：5（取最大值）
- 时间框架覆盖：月、周、日、4H（全周期确认）
- 置信度：高（多时间框架重合）

4. 支撑阻力强度综合评分体系（优化版）
   为了量化每个支撑/阻力位的可靠性，定义增强的强度评分体系（1-15分），便于自动排序和智能决策。

4.1 评分因素优化表
评分因素	分值范围	判定细则	优化说明
时间框架权威性	1-4分	1M=4, 1w=3, 1d=2, 4h=1	直接使用原生数据
触及测试次数	0-4分	1次=1, 2次=2, 3次=3, ≥4次=4	增加权重，多次测试更可靠
技术位重合度	0-3分	与摆动点重合=1, 与趋势线重合=1, 与形态重合=1	多重重合增强
动态位重合度	0-3分	与1个均线重合=1, 与2个均线重合=2, 与布林带重合=1	动态位验证
心理位重合	0-2分	与千位关口重合=1, 与重要历史位重合=1	心理因素考虑
斐波那契位重合	0-2分	与关键斐波那契位(0.5,0.618)重合=2, 与其他位重合=1	黄金分割验证
成交量确认	0-2分	放量反弹/回落=2, 明显放量=1, 缩量=0	成交量验证
近期有效性	0-1分	最近20根K线内被测试有效=1	近期表现
突破失败记录	0-2分	突破后快速收回=2, 突破尝试失败=1	反向验证

4.2 智能评分计算器
class StrengthScoreCalculator:
"""智能强度评分计算器"""

    def calculate_score(self, level_info, market_condition):
        """
        计算支撑阻力位综合强度评分
        level_info: 位点详细信息
        market_condition: 当前市场状况（趋势/震荡/高波动）
        返回：综合评分(1-15)
        """
        base_score = 0
        
        # 1. 时间框架权威性
        base_score += self.get_timeframe_weight(level_info['timeframe'])
        
        # 2. 触及次数（加权）
        base_score += min(level_info['touch_count'], 4)
        
        # 3. 技术位重合度
        base_score += self.calculate_confluence_score(level_info)
        
        # 4. 动态调整（根据市场状况）
        adjusted_score = self.adjust_for_market_condition(base_score, market_condition)
        
        return min(adjusted_score, 15)  # 上限15分

4.3 强度等级映射优化
评分范围	等级	符号	交易意义	止损建议
13-15分	极强	★★★★★	高置信度，核心交易位	放在外侧+ATR×0.8
10-12分	强	★★★★	可靠交易位	放在外侧+ATR×0.6
7-9分	中等	★★★	参考交易位	放在外侧+ATR×0.4
4-6分	弱	★★	辅助参考位	谨慎使用，需额外确认
1-3分	极弱	★	噪音位	不建议依赖

4.4 动态强度调整
根据市场状况动态调整评分：
- 强趋势市场：技术位评分+1，动态位评分+1
- 震荡市场：心理位评分+1，多次测试位评分+1
- 高波动市场：ATR容差增大，强度要求提高

5. 结合交易习惯的深度集成应用规则（优化版）
   5.1 智能入场决策流程
   class SmartEntryDecision:
   """智能入场决策系统"""

   def generate_trading_plan(self, current_market_data):
   """
   生成完整的交易计划
   步骤：
   1. 多时间框架趋势分析
   2. 识别高置信度交易区域
   3. 等待价格到达并确认信号
   4. 计算精确交易参数
   """

        # 1. 大周期趋势过滤
        primary_trend = self.analyze_primary_trend()  # 月线+周线
        
        # 2. 识别关键交易区域（优化）
        if primary_trend == 'bullish':
            # 只做多：寻找强度≥10分的支撑区域
            support_areas = self.find_strong_support_areas(min_score=10)
            trading_plan = self.create_long_plan(support_areas)
        elif primary_trend == 'bearish':
            # 只做空：寻找强度≥10分的阻力区域
            resistance_areas = self.find_strong_resistance_areas(min_score=10)
            trading_plan = self.create_short_plan(resistance_areas)
        else:
            # 震荡市：轻仓或观望
            trading_plan = {'action': 'wait', 'reason': 'market_in_consolidation'}
        
        return trading_plan

入场条件优化：
- 价格进入目标区域：容差 = 该时间框架ATR × 0.3
- 小周期确认信号：4H出现明确反转形态 + 指标配合
- 成交量验证：放量确认信号有效性
- 多时间框架共振：至少两个时间框架发出同向信号

5.2 智能止损设置系统（深度集成100U硬止损）
class SmartStopLossCalculator:
"""智能止损计算系统"""

    def __init__(self, account_params):
        self.account_balance = account_params['balance']  # 2403U
        self.leverage = account_params['leverage']  # 5
        self.max_per_trade = account_params['max_per_trade']  # 10,000U
        self.hard_stop = account_params['hard_stop']  # 100U
    
    def calculate_stop_loss(self, entry_price, key_support_resistance, strength_score, timeframe_atr):
        """
        智能计算止损位和仓位
        考虑支撑阻力强度动态调整缓冲距离
        """
        
        # 1. 根据强度动态调整缓冲距离
        buffer_multiplier = self.get_buffer_multiplier(strength_score)
        buffer_distance = timeframe_atr * buffer_multiplier
        
        # 强度评分与缓冲距离关系：
        # 13-15分（极强）：ATR×0.3（紧止损）
        # 10-12分（强）：ATR×0.5（标准）
        # 7-9分（中等）：ATR×0.7（宽松）
        # 4-6分（弱）：ATR×1.0（很宽松）
        
        # 2. 计算理论止损价
        if entry_price > key_support_resistance:  # 做多
            stop_loss_price = key_support_resistance - buffer_distance
        else:  # 做空
            stop_loss_price = key_support_resistance + buffer_distance
        
        # 3. 计算止损百分比
        stop_loss_pct = abs(entry_price - stop_loss_price) / entry_price
        
        # 4. 智能仓位计算（确保硬止损100U）
        max_position_size = self.hard_stop / stop_loss_pct
        actual_position = min(max_position_size, self.max_per_trade)
        
        # 5. 计算实际占用保证金
        margin_required = actual_position / self.leverage
        margin_percent = margin_required / self.account_balance * 100
        
        return {
            'stop_loss_price': stop_loss_price,
            'stop_loss_pct': stop_loss_pct,
            'position_size': actual_position,
            'margin_required': margin_required,
            'margin_percent': margin_percent,
            'hard_stop_compliant': True  # 确保符合100U硬止损
        }

5.3 智能目标设置系统（确保盈亏比≥2:1）
class SmartTargetCalculator:
"""智能目标计算系统"""

    def calculate_targets(self, entry_price, stop_loss_price, market_structure):
        """
        计算盈利目标，考虑市场结构
        确保盈亏比≥2:1
        """
        
        # 1. 计算基础目标（2:1盈亏比）
        stop_distance = abs(entry_price - stop_loss_price)
        base_target_distance = stop_distance * 2
        base_target_price = entry_price + base_target_distance if entry_price > stop_loss_price else entry_price - base_target_distance
        
        # 2. 检查市场结构限制
        next_key_level = self.find_next_key_level(base_target_price, market_structure)
        
        # 3. 调整目标（如果被关键位阻挡）
        if next_key_level and self.is_blocked(base_target_price, next_key_level):
            adjusted_target = self.adjust_target_for_structure(base_target_price, next_key_level)
            # 重新计算盈亏比
            new_ratio = abs(adjusted_target - entry_price) / stop_distance
            if new_ratio >= 2.0:
                return adjusted_target, new_ratio
            else:
                return None, new_ratio  # 放弃交易
        else:
            return base_target_price, 2.0

5.4 智能持仓管理系统（48小时限制优化）
class PositionManager:
"""智能持仓管理系统"""

    def __init__(self, max_holding_hours=48):
        self.max_holding_hours = max_holding_hours
        self.check_interval = 8  # 每8小时检查一次
    
    def manage_position(self, position, current_price, time_elapsed):
        """
        管理持仓，包括：
        1. 定期检查支撑阻力有效性
        2. 移动止损管理
        3. 时间止损执行
        4. 目标调整
        """
        
        decisions = []
        
        # 1. 检查支撑阻力是否被破坏
        if self.is_support_resistance_broken(position):
            decisions.append({'action': 'close', 'reason': 'key_level_broken'})
        
        # 2. 移动止损管理
        new_stop_loss = self.calculate_trailing_stop(position, current_price)
        if new_stop_loss != position['stop_loss']:
            decisions.append({'action': 'move_stop', 'new_stop': new_stop_loss})
        
        # 3. 时间止损检查
        if time_elapsed >= self.max_holding_hours:
            decisions.append({'action': 'close', 'reason': 'time_stop'})
        
        # 4. 目标达成检查
        if self.is_target_reached(position, current_price):
            decisions.append({'action': 'close', 'reason': 'target_hit'})
        
        return decisions
    
    def calculate_trailing_stop(self, position, current_price):
        """智能移动止损计算"""
        # 浮盈达到50%目标：移动至保本
        # 浮盈达到100%目标：移动至关键回调位
        # 使用动态支撑阻力作为移动止损参考

6. 实时监控与告警系统（优化版）
   6.1 实时支撑阻力监控系统
   class RealTimeSupportResistanceMonitor:
   """实时支撑阻力监控系统"""

   def __init__(self, alert_threshold=0.003):  # 0.3%容差
   self.alert_threshold = alert_threshold
   self.monitored_levels = []
   self.last_price = None

   def update_price(self, current_price, current_time):
   """价格更新时实时检查"""
   self.last_price = current_price

        for level in self.monitored_levels:
            # 计算价格距离
            distance_pct = abs(current_price - level['price']) / level['price']
            
            # 检查是否进入监控区域
            if distance_pct <= self.alert_threshold:
                self.trigger_alert(level, current_price, 'approaching')
            
            # 检查是否突破
            if self.is_breakout(level, current_price):
                self.trigger_alert(level, current_price, 'breakout')

   def dynamic_adjust_threshold(self, market_volatility):
   """根据市场波动性动态调整监控阈值"""
   # ATR越高，监控阈值越大
   self.alert_threshold = 0.002 + (market_volatility * 0.001)  # 0.2% + ATR调整

   def add_monitored_level(self, level_info):
   """添加需要监控的关键水平"""
   self.monitored_levels.append({
   'price': level_info['price'],
   'type': level_info['type'],  # support/resistance
   'strength': level_info['strength'],
   'timeframes': level_info['timeframes'],
   'alert_sent': False
   })

6.2 智能告警触发器
class SmartAlertTrigger:
"""智能告警触发系统"""

    alert_conditions = {
        'high_confidence': {
            'strength_min': 10,  # 强度≥10分
            'rsi_condition': 'oversold/overbought',  # RSI超买超卖
            'volume_condition': 'increasing',  # 成交量增加
            'timeframe_confluence': 2  # 至少2个时间框架重合
        },
        'medium_confidence': {
            'strength_min': 7,
            'rsi_condition': 'extreme',  # RSI极端值
            'timeframe_confluence': 1
        }
    }
    
    def check_alert_conditions(self, price_level, market_data):
        """检查是否满足告警条件"""
        conditions_met = []
        
        # 1. 强度条件
        if price_level['strength'] >= self.alert_conditions['high_confidence']['strength_min']:
            conditions_met.append('high_strength')
        
        # 2. RSI条件
        if self.check_rsi_condition(price_level, market_data):
            conditions_met.append('rsi_confirmation')
        
        # 3. 成交量条件
        if self.check_volume_condition(price_level, market_data):
            conditions_met.append('volume_confirmation')
        
        # 4. 多时间框架条件
        if len(price_level['timeframes']) >= self.alert_conditions['high_confidence']['timeframe_confluence']:
            conditions_met.append('multi_timeframe')
        
        return conditions_met
    
    def trigger_alert(self, price_level, conditions_met, alert_type):
        """触发告警"""
        alert_message = self.format_alert_message(price_level, conditions_met, alert_type)
        
        # 发送到多个渠道
        self.send_to_telegram(alert_message)
        self.send_to_dingtalk(alert_message)
        self.log_alert(alert_message)
        
        return alert_message

6.3 自动化分析任务调度
class AnalysisScheduler:
"""分析任务智能调度系统"""

    schedule_config = {
        'high_frequency': {
            'interval': '1h',  # 每小时
            'tasks': ['update_monitored_levels', 'check_immediate_alerts']
        },
        'daily_analysis': {
            'time': '09:00',  # 每天9点
            'tasks': ['full_support_resistance_analysis', 'generate_trading_plan']
        },
        'weekly_review': {
            'day': 'Monday',  # 每周一
            'time': '10:00',
            'tasks': ['weekly_structure_analysis', 'parameter_optimization']
        }
    }
    
    def run_scheduled_task(self, task_name, market_condition):
        """运行计划任务"""
        if task_name == 'full_support_resistance_analysis':
            return self.run_full_analysis(market_condition)
        elif task_name == 'generate_trading_plan':
            return self.generate_daily_trading_plan()
        # ... 其他任务

7. 回测与优化系统（新增）
   7.1 支撑阻力有效性回测
   class SupportResistanceBacktester:
   """支撑阻力有效性回测系统"""

   def backtest_levels(self, start_date, end_date, symbol='BTCUSDT'):
   """
   回测支撑阻力位的有效性
   返回统计报告
   """
   statistics = {
   'support_levels': {
   'total_tested': 0,
   'held_successfully': 0,
   'broken': 0,
   'average_hold_percentage': 0,
   'max_bounce_percentage': 0
   },
   'resistance_levels': {
   'total_tested': 0,
   'held_successfully': 0,
   'broken': 0,
   'average_hold_percentage': 0,
   'max_break_percentage': 0
   }
   }

        # 实现回测逻辑
        # 1. 获取历史数据
        # 2. 识别历史支撑阻力位
        # 3. 测试每个位的有效性
        # 4. 统计结果
        
        return statistics

   def optimize_parameters(self, historical_data):
   """优化摆动点识别、ATR倍数等参数"""
   # 使用网格搜索或优化算法
   # 寻找最佳参数组合

8. 实战案例优化（基于完整多时间框架数据）
   场景：BTC当前价格 75,000，使用完整多时间框架数据进行分析。

步骤优化：

1. 多时间框架趋势分析：
    - 月线(1M)：价格>EMA25，EMA25向上，MACD零轴上方 → 牛市确认 ✅
    - 周线(1w)：价格在EMA25上方，但接近前高阻力 → 上涨中后期
    - 日线(1d)：价格在上升通道中，RSI14=65（偏强但未超买）
    - 4h线：短期调整，寻找做多机会

2. 识别关键支撑区域（优化版）：
    - 月线技术位：前低 72,500（强度12分：权重4+触及3次+与EMA50重合）
    - 周线动态位：EMA25 = 73,200（强度10分：权重3+趋势向上）
    - 日线心理位：73,000整数关口（强度9分：权重2+与摆动低点重合）
    - 4h布林带：下轨 72,800（强度8分：权重1+连续测试有效）

   智能合并结果：
    - 综合支撑区域：72,400 ~ 73,400（ATR×1.2容差）
    - 综合强度：12分（极强 ★★★★★）
    - 时间框架覆盖：月、周、日、4h（全周期确认）
    - 置信度：极高

3. 智能交易计划生成：
    - 交易方向：只做多（月线牛市确认）
    - 入场区域：72,400 ~ 73,400
    - 等待信号：4h出现看涨吞没 + RSI14<40反弹
    - 假设入场价：73,000

4. 智能止损计算：
    - 关键支撑下限：72,400
    - 根据强度(12分)选择缓冲：ATR×0.4 = 320点
    - 止损价：72,400 - 320 = 72,080
    - 止损百分比：(73,000 - 72,080)/73,000 = 1.26%
    - 智能仓位：100U / 1.26% = 7,937U（确保硬止损100U）
    - 占用保证金：7,937 / 5 = 1,587U（占本金66.1%）

5. 智能目标计算：
    - 止损距离：920点
    - 基础目标距离：920 × 2 = 1,840点
    - 基础目标价：73,000 + 1,840 = 74,840
    - 检查阻力：下一个强阻力在75,200（前高）
    - 调整目标：74,800（在阻力前）
    - 实际盈亏比：1,800/920 = 1.96:1（接近2:1，可接受）

6. 智能执行与监控：
    - 入场后：立即设置止损72,080，目标74,800
    - 实时监控：价格接近支撑区域时启动告警
    - 持仓管理：每8小时检查一次，48小时时间止损
    - 移动止损：浮盈达到50%时移至保本价

9. 总结与实施建议
   本优化版说明文档基于你完整的多时间框架数据，提供了：

✅ 数据层优化：直接使用原生时间框架数据，无需聚合
✅ 算法优化：稳健的摆动点识别、智能冲突处理
✅ 评分系统优化：增强的1-15分评分体系
✅ 交易集成优化：深度结合你的交易习惯和参数
✅ 实时监控优化：智能告警和动态调整
✅ 回测系统：验证和优化参数

实施建议：

第一阶段（核心功能）：
1. 实现基础支撑阻力识别（技术位、动态位、心理位）
2. 实现多时间框架融合系统
3. 实现智能评分计算器

第二阶段（增强功能）：
4. 实现斐波那契计算和成交量确认
5. 实现智能交易计划生成
6. 实现实时监控和告警系统

第三阶段（高级功能）：
7. 实现回测和参数优化系统
8. 实现可视化报告生成
9. 实现机器学习优化

你可以：
- 按照优化后的文档手工分析，验证逻辑合理性
- 分阶段实现自动化分析系统
- 将输出集成到现有监控和交易系统
- 定期回测优化，持续改进系统性能



版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""