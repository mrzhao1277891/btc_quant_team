#!/usr/bin/env python3
"""
时间处理工具模块

职责: 提供时间相关的工具函数，包括时间转换、格式化、计算等。

主要功能:
- 时间戳转换 (毫秒 ↔ 日期时间)
- 时间格式化 (各种格式输出)
- 时间计算 (加减、间隔)
- 时区处理

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Union, Optional, Tuple
import pytz

# 默认时区 (Asia/Shanghai)
DEFAULT_TIMEZONE = pytz.timezone("Asia/Shanghai")

def get_current_time(
    timezone_str: Optional[str] = None,
    as_string: bool = True
) -> Union[str, datetime]:
    """
    获取当前时间
    
    参数:
        timezone_str (str): 时区字符串，如"Asia/Shanghai"，默认使用配置时区
        as_string (bool): 是否返回字符串格式，默认True
    
    返回:
        Union[str, datetime]: 当前时间
    
    示例:
        >>> get_current_time()
        '2026-04-19T09:00:00+08:00'
        >>> get_current_time(as_string=False)
        datetime.datetime(2026, 4, 19, 9, 0, 0, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    """
    tz = pytz.timezone(timezone_str) if timezone_str else DEFAULT_TIMEZONE
    now = datetime.now(tz)
    
    if as_string:
        return now.isoformat()
    return now

def timestamp_to_datetime(
    timestamp_ms: int,
    timezone_str: Optional[str] = None
) -> datetime:
    """
    将毫秒时间戳转换为datetime对象
    
    参数:
        timestamp_ms (int): 毫秒时间戳
        timezone_str (str): 时区字符串
    
    返回:
        datetime: 转换后的datetime对象
    
    示例:
        >>> timestamp_to_datetime(1713499200000)
        datetime.datetime(2024, 4, 19, 12, 0, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    """
    tz = pytz.timezone(timezone_str) if timezone_str else DEFAULT_TIMEZONE
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz)
    return dt

def datetime_to_timestamp(
    dt: datetime,
    as_ms: bool = True
) -> int:
    """
    将datetime对象转换为时间戳
    
    参数:
        dt (datetime): datetime对象
        as_ms (bool): 是否返回毫秒时间戳，默认True
    
    返回:
        int: 时间戳 (秒或毫秒)
    
    示例:
        >>> dt = datetime(2024, 4, 19, 12, 0, tzinfo=timezone.utc)
        >>> datetime_to_timestamp(dt)
        1713499200000
        >>> datetime_to_timestamp(dt, as_ms=False)
        1713499200
    """
    # 确保datetime有时区信息
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=DEFAULT_TIMEZONE)
    
    timestamp = int(dt.timestamp())
    return timestamp * 1000 if as_ms else timestamp

def format_timestamp(
    timestamp_ms: int,
    format_str: str = "%Y-%m-%d %H:%M:%S",
    timezone_str: Optional[str] = None
) -> str:
    """
    格式化时间戳为字符串
    
    参数:
        timestamp_ms (int): 毫秒时间戳
        format_str (str): 格式化字符串
        timezone_str (str): 时区字符串
    
    返回:
        str: 格式化后的时间字符串
    
    示例:
        >>> format_timestamp(1713499200000)
        '2024-04-19 12:00:00'
        >>> format_timestamp(1713499200000, "%Y/%m/%d")
        '2024/04/19'
    """
    dt = timestamp_to_datetime(timestamp_ms, timezone_str)
    return dt.strftime(format_str)

def parse_time_string(
    time_str: str,
    format_str: str = "%Y-%m-%d %H:%M:%S",
    timezone_str: Optional[str] = None
) -> datetime:
    """
    解析时间字符串为datetime对象
    
    参数:
        time_str (str): 时间字符串
        format_str (str): 时间格式
        timezone_str (str): 时区字符串
    
    返回:
        datetime: 解析后的datetime对象
    
    示例:
        >>> parse_time_string("2024-04-19 12:00:00")
        datetime.datetime(2024, 4, 19, 12, 0, tzinfo=<DstTzInfo 'Asia/Shanghai' CST+8:00:00 STD>)
    """
    tz = pytz.timezone(timezone_str) if timezone_str else DEFAULT_TIMEZONE
    dt = datetime.strptime(time_str, format_str)
    return tz.localize(dt)

def calculate_time_difference(
    start_time: Union[int, datetime, str],
    end_time: Union[int, datetime, str],
    unit: str = "seconds"
) -> float:
    """
    计算时间差
    
    参数:
        start_time: 开始时间 (时间戳、datetime或字符串)
        end_time: 结束时间 (时间戳、datetime或字符串)
        unit (str): 返回单位，可选: seconds, minutes, hours, days
    
    返回:
        float: 时间差
    
    示例:
        >>> start = datetime(2024, 4, 19, 12, 0)
        >>> end = datetime(2024, 4, 19, 13, 30)
        >>> calculate_time_difference(start, end, "hours")
        1.5
    """
    # 统一转换为datetime
    def to_datetime(t):
        if isinstance(t, int):
            return timestamp_to_datetime(t)
        elif isinstance(t, str):
            return parse_time_string(t)
        elif isinstance(t, datetime):
            if t.tzinfo is None:
                t = DEFAULT_TIMEZONE.localize(t)
            return t
        else:
            raise TypeError(f"不支持的时间类型: {type(t)}")
    
    start_dt = to_datetime(start_time)
    end_dt = to_datetime(end_time)
    
    # 计算时间差
    diff_seconds = (end_dt - start_dt).total_seconds()
    
    # 转换为指定单位
    units = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600,
        "days": 86400
    }
    
    if unit not in units:
        raise ValueError(f"无效的单位: {unit}，有效值: {list(units.keys())}")
    
    return diff_seconds / units[unit]

def add_time(
    base_time: Union[int, datetime, str],
    amount: float,
    unit: str = "hours"
) -> datetime:
    """
    在基础时间上增加时间
    
    参数:
        base_time: 基础时间
        amount (float): 增加的数量
        unit (str): 时间单位
    
    返回:
        datetime: 增加后的时间
    
    示例:
        >>> base = datetime(2024, 4, 19, 12, 0)
        >>> add_time(base, 2.5, "hours")
        datetime.datetime(2024, 4, 19, 14, 30)
    """
    # 统一转换为datetime
    if isinstance(base_time, int):
        base_dt = timestamp_to_datetime(base_time)
    elif isinstance(base_time, str):
        base_dt = parse_time_string(base_time)
    else:
        base_dt = base_time
    
    # 计算增加的时间
    units = {
        "seconds": timedelta(seconds=amount),
        "minutes": timedelta(minutes=amount),
        "hours": timedelta(hours=amount),
        "days": timedelta(days=amount),
        "weeks": timedelta(weeks=amount)
    }
    
    if unit not in units:
        raise ValueError(f"无效的单位: {unit}，有效值: {list(units.keys())}")
    
    return base_dt + units[unit]

def is_within_time_range(
    check_time: Union[int, datetime, str],
    start_time: Union[int, datetime, str],
    end_time: Union[int, datetime, str],
    inclusive: bool = True
) -> bool:
    """
    检查时间是否在指定范围内
    
    参数:
        check_time: 要检查的时间
        start_time: 范围开始时间
        end_time: 范围结束时间
        inclusive (bool): 是否包含边界
    
    返回:
        bool: 是否在范围内
    
    示例:
        >>> check = datetime(2024, 4, 19, 12, 30)
        >>> start = datetime(2024, 4, 19, 12, 0)
        >>> end = datetime(2024, 4, 19, 13, 0)
        >>> is_within_time_range(check, start, end)
        True
    """
    # 统一转换为datetime
    def to_datetime(t):
        if isinstance(t, int):
            return timestamp_to_datetime(t)
        elif isinstance(t, str):
            return parse_time_string(t)
        else:
            return t
    
    check_dt = to_datetime(check_time)
    start_dt = to_datetime(start_time)
    end_dt = to_datetime(end_time)
    
    if inclusive:
        return start_dt <= check_dt <= end_dt
    else:
        return start_dt < check_dt < end_dt

def get_timeframe_seconds(timeframe: str) -> int:
    """
    获取时间框架对应的秒数
    
    参数:
        timeframe (str): 时间框架字符串，如"1m", "5m", "1h", "4h", "1d", "1w", "1M"
    
    返回:
        int: 对应的秒数
    
    示例:
        >>> get_timeframe_seconds("1h")
        3600
        >>> get_timeframe_seconds("4h")
        14400
    """
    timeframe_map = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "4h": 14400,
        "1d": 86400,
        "1w": 604800,
        "1M": 2592000,  # 近似30天
    }
    
    if timeframe not in timeframe_map:
        raise ValueError(f"无效的时间框架: {timeframe}，有效值: {list(timeframe_map.keys())}")
    
    return timeframe_map[timeframe]

def get_next_candle_time(
    current_time: Union[int, datetime, str],
    timeframe: str
) -> datetime:
    """
    获取下一个K线开始时间
    
    参数:
        current_time: 当前时间
        timeframe (str): 时间框架
    
    返回:
        datetime: 下一个K线开始时间
    
    示例:
        >>> current = datetime(2024, 4, 19, 12, 15)
        >>> get_next_candle_time(current, "1h")
        datetime.datetime(2024, 4, 19, 13, 0)
    """
    if isinstance(current_time, int):
        current_dt = timestamp_to_datetime(current_time)
    elif isinstance(current_time, str):
        current_dt = parse_time_string(current_time)
    else:
        current_dt = current_time
    
    timeframe_seconds = get_timeframe_seconds(timeframe)
    
    # 计算当前K线开始时间
    if timeframe == "1M":
        # 月度特殊处理
        next_month = current_dt.replace(day=1) + timedelta(days=32)
        next_candle = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif timeframe == "1w":
        # 周度特殊处理 (周一00:00)
        days_ahead = 7 - current_dt.weekday()  # 0=周一, 6=周日
        if days_ahead == 0:  # 已经是周一
            days_ahead = 7
        next_candle = (current_dt + timedelta(days=days_ahead)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    else:
        # 其他时间框架
        timestamp = datetime_to_timestamp(current_dt, as_ms=False)
        current_candle_start = timestamp - (timestamp % timeframe_seconds)
        next_candle_start = current_candle_start + timeframe_seconds
        next_candle = timestamp_to_datetime(next_candle_start * 1000)
    
    return next_candle

def format_duration(seconds: float) -> str:
    """
    格式化持续时间
    
    参数:
        seconds (float): 秒数
    
    返回:
        str: 格式化的持续时间，如"2天3小时15分钟"
    
    示例:
        >>> format_duration(123456)
        '1天10小时17分钟'
    """
    if seconds < 0:
        return "0秒"
    
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if secs > 0 or not parts:  # 如果没有其他部分，至少显示秒
        parts.append(f"{secs}秒")
    
    return "".join(parts)

# 测试代码
if __name__ == "__main__":
    print("测试时间工具...")
    
    # 测试当前时间
    current = get_current_time()
    print(f"当前时间: {current}")
    
    # 测试时间戳转换
    timestamp = 1713499200000
    dt = timestamp_to_datetime(timestamp)
    print(f"时间戳转换: {timestamp} -> {dt}")
    
    # 测试时间格式化
    formatted = format_timestamp(timestamp, "%Y年%m月%d日 %H:%M")
    print(f"时间格式化: {formatted}")
    
    # 测试时间差计算
    start = datetime(2024, 4, 19, 12, 0)
    end = datetime(2024, 4, 19, 14, 30)
    diff_hours = calculate_time_difference(start, end, "hours")
    print(f"时间差: {diff_hours}小时")
    
    # 测试时间框架
    for tf in ["1m", "1h", "4h", "1d", "1w"]:
        seconds = get_timeframe_seconds(tf)
        print(f"{tf} = {seconds}秒 ({format_duration(seconds)})")
    
    print("时间工具测试完成!")