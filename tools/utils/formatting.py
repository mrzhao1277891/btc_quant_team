#!/usr/bin/env python3
"""
格式化工具模块

职责: 提供数据格式化相关的工具函数，包括价格、数字、文本等格式化。

主要功能:
- 价格格式化 (添加货币符号、千位分隔符)
- 数字格式化 (精度控制、百分比)
- 文本格式化 (截断、对齐、颜色)
- 数据结构格式化 (JSON、表格)

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import json
from typing import Any, Dict, List, Union, Optional
from decimal import Decimal, ROUND_HALF_UP

def format_price(
    price: Union[float, int, str],
    currency: str = "USD",
    precision: int = 2,
    use_symbol: bool = True
) -> str:
    """
    格式化价格
    
    参数:
        price: 价格数值
        currency (str): 货币代码，默认"USD"
        precision (int): 小数精度，默认2
        use_symbol (bool): 是否使用货币符号，默认True
    
    返回:
        str: 格式化后的价格字符串
    
    示例:
        >>> format_price(12345.6789)
        '$12,345.68'
        >>> format_price(12345.6789, precision=0)
        '$12,346'
        >>> format_price(12345.6789, currency="CNY", use_symbol=False)
        '12,345.68 CNY'
    """
    # 转换为Decimal确保精度
    try:
        if isinstance(price, str):
            price = Decimal(price)
        else:
            price = Decimal(str(price))
    except:
        return f"无效价格: {price}"
    
    # 四舍五入
    rounding_format = f"0.{'0' * precision}" if precision > 0 else "0"
    price_rounded = price.quantize(Decimal(rounding_format), rounding=ROUND_HALF_UP)
    
    # 添加千位分隔符
    price_str = f"{price_rounded:,}"
    
    # 添加货币符号
    currency_symbols = {
        "USD": "$",
        "CNY": "¥",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥"
    }
    
    if use_symbol:
        symbol = currency_symbols.get(currency.upper(), f"{currency} ")
        return f"{symbol}{price_str}"
    else:
        return f"{price_str} {currency.upper()}"

def format_percentage(
    value: Union[float, int, str],
    precision: int = 2,
    include_sign: bool = True
) -> str:
    """
    格式化百分比
    
    参数:
        value: 百分比数值 (如0.15表示15%)
        precision (int): 小数精度，默认2
        include_sign (bool): 是否包含百分号，默认True
    
    返回:
        str: 格式化后的百分比字符串
    
    示例:
        >>> format_percentage(0.15678)
        '15.68%'
        >>> format_percentage(-0.05, precision=1)
        '-5.0%'
        >>> format_percentage(0.5, include_sign=False)
        '50.00'
    """
    try:
        if isinstance(value, str):
            value = Decimal(value)
        else:
            value = Decimal(str(value))
    except:
        return f"无效百分比: {value}"
    
    # 转换为百分比 (乘以100)
    percentage = value * Decimal("100")
    
    # 四舍五入
    rounding_format = f"0.{'0' * precision}" if precision > 0 else "0"
    percentage_rounded = percentage.quantize(Decimal(rounding_format), rounding=ROUND_HALF_UP)
    
    # 格式化
    percentage_str = f"{percentage_rounded}"
    
    if include_sign:
        return f"{percentage_str}%"
    else:
        return percentage_str

def format_number(
    number: Union[float, int, str],
    precision: Optional[int] = None,
    use_commas: bool = True,
    scientific: bool = False
) -> str:
    """
    通用数字格式化
    
    参数:
        number: 数字
        precision (int): 小数精度，None表示自动
        use_commas (bool): 是否使用千位分隔符，默认True
        scientific (bool): 是否使用科学计数法，默认False
    
    返回:
        str: 格式化后的数字字符串
    
    示例:
        >>> format_number(1234567.89123)
        '1,234,567.89'
        >>> format_number(0.00012345, precision=6)
        '0.000123'
        >>> format_number(1234567.89123, scientific=True)
        '1.23e+06'
    """
    try:
        if isinstance(number, str):
            num = Decimal(number)
        else:
            num = Decimal(str(number))
    except:
        return f"无效数字: {number}"
    
    # 科学计数法
    if scientific:
        if precision is None:
            precision = 2
        
        format_str = f".{precision}e"
        return format(float(num), format_str)
    
    # 确定精度
    if precision is None:
        # 自动确定精度：小数字多保留，大数字少保留
        abs_num = abs(num)
        if abs_num == 0:
            precision = 2
        elif abs_num < 0.0001:
            precision = 8
        elif abs_num < 0.01:
            precision = 6
        elif abs_num < 1:
            precision = 4
        elif abs_num < 1000:
            precision = 2
        else:
            precision = 0
    
    # 四舍五入
    rounding_format = f"0.{'0' * precision}" if precision > 0 else "0"
    rounded = num.quantize(Decimal(rounding_format), rounding=ROUND_HALF_UP)
    
    # 格式化
    if use_commas:
        # 添加千位分隔符
        parts = str(rounded).split('.')
        int_part = parts[0]
        
        # 处理负数
        if int_part.startswith('-'):
            sign = '-'
            int_part = int_part[1:]
        else:
            sign = ''
        
        # 添加千位分隔符
        formatted_int = ''
        for i, digit in enumerate(reversed(int_part)):
            if i > 0 and i % 3 == 0:
                formatted_int = ',' + formatted_int
            formatted_int = digit + formatted_int
        
        formatted_int = sign + formatted_int
        
        if len(parts) > 1:
            return f"{formatted_int}.{parts[1]}"
        else:
            return formatted_int
    else:
        return str(rounded)

def format_change(
    old_value: Union[float, int, str],
    new_value: Union[float, int, str],
    format_type: str = "both"
) -> Dict[str, Any]:
    """
    格式化变化值
    
    参数:
        old_value: 旧值
        new_value: 新值
        format_type (str): 格式化类型，"absolute"绝对值，"percentage"百分比，"both"两者
    
    返回:
        Dict: 包含变化信息的字典
    
    示例:
        >>> format_change(100, 120)
        {'absolute': 20.0, 'percentage': 20.0, 'direction': 'up'}
        >>> format_change(100, 80)
        {'absolute': -20.0, 'percentage': -20.0, 'direction': 'down'}
    """
    try:
        old = Decimal(str(old_value))
        new = Decimal(str(new_value))
    except:
        return {"error": "无效的数值"}
    
    # 计算变化
    absolute_change = float(new - old)
    if old != 0:
        percentage_change = float((new - old) / old * 100)
    else:
        percentage_change = 0.0 if new == 0 else (100.0 if new > 0 else -100.0)
    
    # 确定方向
    if absolute_change > 0:
        direction = "up"
    elif absolute_change < 0:
        direction = "down"
    else:
        direction = "unchanged"
    
    result = {
        "old_value": float(old),
        "new_value": float(new),
        "absolute": absolute_change,
        "percentage": percentage_change,
        "direction": direction
    }
    
    # 根据类型格式化输出
    if format_type == "absolute":
        result["formatted"] = format_number(absolute_change, precision=2)
    elif format_type == "percentage":
        result["formatted"] = format_percentage(percentage_change / 100, precision=2)
    elif format_type == "both":
        abs_str = format_number(absolute_change, precision=2)
        pct_str = format_percentage(percentage_change / 100, precision=2)
        result["formatted"] = f"{abs_str} ({pct_str})"
    
    return result

def format_table(
    data: List[Dict[str, Any]],
    headers: Optional[List[str]] = None,
    max_width: int = 80
) -> str:
    """
    格式化数据为表格
    
    参数:
        data: 数据列表
        headers: 表头列表，None表示使用数据键
        max_width: 最大宽度
    
    返回:
        str: 格式化后的表格字符串
    
    示例:
        >>> data = [{"name": "BTC", "price": 72000}, {"name": "ETH", "price": 3500}]
        >>> print(format_table(data))
        +------+--------+
        | name | price  |
        +------+--------+
        | BTC  | 72,000 |
        | ETH  | 3,500  |
        +------+--------+
    """
    if not data:
        return "无数据"
    
    # 确定表头
    if headers is None:
        headers = list(data[0].keys())
    
    # 计算每列最大宽度
    col_widths = []
    for header in headers:
        # 表头宽度
        max_len = len(str(header))
        
        # 数据宽度
        for row in data:
            value = row.get(header, "")
            max_len = max(max_len, len(str(value)))
        
        # 限制最大宽度
        max_len = min(max_len, max_width // len(headers))
        col_widths.append(max_len)
    
    # 构建表格
    table_lines = []
    
    # 上边框
    border = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    table_lines.append(border)
    
    # 表头
    header_cells = []
    for i, header in enumerate(headers):
        cell = f" {str(header).ljust(col_widths[i])} "
        header_cells.append(cell)
    table_lines.append("|" + "|".join(header_cells) + "|")
    table_lines.append(border)
    
    # 数据行
    for row in data:
        row_cells = []
        for i, header in enumerate(headers):
            value = row.get(header, "")
            cell = f" {str(value).ljust(col_widths[i])} "
            row_cells.append(cell)
        table_lines.append("|" + "|".join(row_cells) + "|")
    
    # 下边框
    table_lines.append(border)
    
    return "\n".join(table_lines)

def format_json(
    data: Any,
    indent: int = 2,
    sort_keys: bool = True,
    ensure_ascii: bool = False
) -> str:
    """
    格式化JSON数据
    
    参数:
        data: 要格式化的数据
        indent (int): 缩进空格数
        sort_keys (bool): 是否按键排序
        ensure_ascii (bool): 是否确保ASCII
    
    返回:
        str: 格式化后的JSON字符串
    
    示例:
        >>> data = {"name": "BTC", "price": 72000}
        >>> print(format_json(data))
        {
          "name": "BTC",
          "price": 72000
        }
    """
    try:
        return json.dumps(
            data,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
            default=str  # 处理非JSON序列化对象
        )
    except Exception as e:
        return f"JSON格式化失败: {e}"

def truncate_text(
    text: str,
    max_length: int,
    ellipsis: str = "..."
) -> str:
    """
    截断文本
    
    参数:
        text (str): 原始文本
        max_length (int): 最大长度
        ellipsis (str): 省略号字符串
    
    返回:
        str: 截断后的文本
    
    示例:
        >>> truncate_text("这是一个很长的文本需要截断", 10)
        '这是一个很...'
    """
    if len(text) <= max_length:
        return text
    
    if max_length <= len(ellipsis):
        return ellipsis[:max_length]
    
    return text[:max_length - len(ellipsis)] + ellipsis

def format_bytes(
    bytes_count: int,
    precision: int = 2
) -> str:
    """
    格式化字节大小
    
    参数:
        bytes_count (int): 字节数
        precision (int): 小数精度
    
    返回:
        str: 格式化后的字节大小
    
    示例:
        >>> format_bytes(1024)
        '1.00 KB'
        >>> format_bytes(1500000)
        '1.43 MB'
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    
    if bytes_count == 0:
        return "0 B"
    
    size = float(bytes_count)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.{precision}f} {units[unit_index]}"

def format_duration(
    seconds: float,
    precision: int = 0
) -> str:
    """
    格式化持续时间 (从时间模块导入的兼容函数)
    
    参数:
        seconds (float): 秒数
        precision (int): 小数精度
    
    返回:
        str: 格式化的持续时间
    """
    # 导入时间模块的函数
    from .time import format_duration as time_format_duration
    return time_format_duration(seconds)

def colorize_text(
    text: str,
    color: str = "green",
    style: str = "normal"
) -> str:
    """
    为文本添加颜色 (终端ANSI颜色)
    
    参数:
        text (str): 文本
        color (str): 颜色，可选: black, red, green, yellow, blue, magenta, cyan, white
        style (str): 样式，可选: normal, bold, dim, italic, underline
    
    返回:
        str: 带颜色的文本 (仅终端有效)
    """
    colors = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37"
    }
    
    styles = {
        "normal": "0",
        "bold": "1",
        "dim": "2",
        "italic": "3",
        "underline": "4"
    }
    
    color_code = colors.get(color.lower(), "37")  # 默认白色
    style_code = styles.get(style.lower(), "0")   # 默认正常
    
    return f"\033[{style_code};{color_code}m{text}\033[0m"

# 测试代码
if __name__ == "__main__":
    print("测试格式化工具...")
    
    # 测试价格格式化
    print("价格格式化:")
    print(f"  {format_price(12345.6789)}")
    print(f"  {format_price(12345.6789, precision=0)}")
    print(f"  {format_price(12345.6789, currency='CNY')}")
    
    # 测试百分比格式化
    print("\n百分比格式化:")
    print(f"  {format_percentage(0.15678)}")
    print(f"  {format_percentage(-0.05, precision=1)}")
    
    # 测试数字格式化
    print("\n数字格式化:")
    print(f"  {format_number(1234567.89123)}")
    print(f"  {format_number(0.00012345, precision=6)}")
    
    # 测试变化格式化
    print("\n变化格式化:")
    change = format_change(100, 120)
    print(f"  100 → 120: {change['formatted']}")
    
    # 测试表格格式化
    print("\n表格格式化:")
    data = [
        {"资产": "BTC", "价格": 72000, "变化": 0.05},
        {"资产": "ETH", "价格": 3500, "变化": -0.02},
        {"资产": "BNB", "价格": 580, "变化": 0.12}
    ]
    print(format_table(data))
    
    # 测试JSON格式化
    print("\nJSON格式化:")
    json_data = {"name": "BTC", "price": 72000, "change": 0.05}
    print(format_json(json_data))
    
    print("\n格式化工具测试完成!")