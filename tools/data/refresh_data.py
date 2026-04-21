#!/usr/bin/env python3
"""
数据获取工具模块

职责: 从各种数据源获取加密货币K线数据

数据源支持:
1. Binance API (主要)
2. 本地缓存 (备用)
3. 其他交易所 (未来扩展)

主要功能:
- fetch_klines(): 获取K线数据
- fetch_current_price(): 获取当前价格
- fetch_latest(): 获取最新数据点
- fetch_historical(): 获取历史数据

依赖:
- requests: HTTP请求
- sqlite3: 本地缓存

注意事项:
1. 遵守API速率限制
2. 处理网络异常
3. 数据验证和清洗

版本: 1.0.0
作者: 量化团队
更新日期: 2026-04-19
"""

import requests
import sqlite3
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# 配置
BINANCE_API_URL = "https://api.binance.com"
BINANCE_KLINES_ENDPOINT = "/api/v3/klines"
BINANCE_TICKER_ENDPOINT = "/api/v3/ticker/price"

# 本地缓存配置
CACHE_DB_PATH = Path.home() / ".btc_quant" / "data_cache.db"
CACHE_TABLE = "price_cache"
CACHE_TTL = 300  # 缓存有效期(秒)

def fetch_klines(
    symbol: str = "BTCUSDT",
    timeframe: str = "4h",
    limit: int = 1000,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    """
    从Binance获取K线数据
    
    参数:
        symbol (str): 交易对，默认"BTCUSDT"
        timeframe (str): 时间框架，支持"1m","5m","15m","30m","1h","4h","1d","1w","1M"
        limit (int): 获取数量，默认1000，最大1500
        use_cache (bool): 是否使用本地缓存，默认True
    
    返回:
        List[Dict]: K线数据列表，每个元素包含:
            - timestamp (int): 时间戳(毫秒)
            - open (float): 开盘价
            - high (float): 最高价
            - low (float): 最低价
            - close (float): 收盘价
            - volume (float): 成交量
    
    异常:
        ConnectionError: 网络连接失败
        ValueError: 参数无效
        RuntimeError: API返回错误
    
    示例:
        >>> data = fetch_klines("BTCUSDT", "4h", 500)
        >>> len(data)
        500
        >>> data[0].keys()
        dict_keys(['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    性能:
        - 首次获取: ~2-3秒 (网络请求)
        - 缓存命中: ~0.01秒 (本地读取)
    
    注意事项:
        1. Binance API有每分钟1200次限制
        2. 数据时间戳是开盘时间
        3. 成交量单位是基础货币
    """
    # 参数验证
    if limit > 1500:
        limit = 1500  # Binance API限制
    
    valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
    if timeframe not in valid_timeframes:
        raise ValueError(f"无效的时间框架: {timeframe}，有效值: {valid_timeframes}")
    
    # 检查缓存
    cache_key = f"{symbol}_{timeframe}_{limit}"
    if use_cache:
        cached_data = _get_from_cache(cache_key)
        if cached_data:
            return cached_data
    
    try:
        # 构建API请求
        url = f"{BINANCE_API_URL}{BINANCE_KLINES_ENDPOINT}"
        params = {
            "symbol": symbol.upper(),
            "interval": timeframe,
            "limit": limit
        }
        
        # 发送请求
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # 解析响应
        raw_data = response.json()
        
        if not isinstance(raw_data, list):
            raise RuntimeError(f"API返回格式错误: {raw_data}")
        
        # 转换为标准格式
        klines = []
        for item in raw_data:
            kline = {
                "timestamp": int(item[0]),  # 开盘时间
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
                "close_time": int(item[6]),  # 收盘时间
                "quote_volume": float(item[7]),  # 报价货币成交量
                "trades": int(item[8]),  # 交易笔数
                "taker_buy_base": float(item[9]),  # 主动买入基础货币量
                "taker_buy_quote": float(item[10])  # 主动买入报价货币量
            }
            klines.append(kline)
        
        # 缓存数据
        if use_cache:
            _save_to_cache(cache_key, klines)
        
        return klines
        
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"网络请求失败: {e}")
    except (KeyError, IndexError, ValueError) as e:
        raise RuntimeError(f"数据解析失败: {e}")

def fetch_current_price(
    symbol: str = "BTCUSDT",
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    获取当前价格
    
    参数:
        symbol (str): 交易对，默认"BTCUSDT"
        use_cache (bool): 是否使用缓存，默认True
    
    返回:
        Dict: 包含价格信息:
            - symbol (str): 交易对
            - price (float): 当前价格
            - timestamp (str): ISO格式时间戳
    
    异常:
        ConnectionError: 网络连接失败
        RuntimeError: API返回错误
    
    示例:
        >>> price_data = fetch_current_price("BTCUSDT")
        >>> price_data['price']
        72106.85
        >>> price_data['symbol']
        'BTCUSDT'
    
    性能:
        - 网络请求: ~0.5-1秒
        - 缓存命中: ~0.001秒
    
    注意事项:
        1. 缓存有效期5分钟
        2. 失败时返回None
    """
    # 检查缓存
    cache_key = f"price_{symbol}"
    if use_cache:
        cached_price = _get_from_cache(cache_key, data_type="price")
        if cached_price:
            return cached_price
    
    try:
        # 构建API请求
        url = f"{BINANCE_API_URL}{BINANCE_TICKER_ENDPOINT}"
        params = {"symbol": symbol.upper()}
        
        # 发送请求
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        # 解析响应
        data = response.json()
        
        if "price" not in data:
            raise RuntimeError("API返回数据缺少价格字段")
        
        price_data = {
            "symbol": data.get("symbol", symbol),
            "price": float(data["price"]),
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
        # 缓存价格 (短期缓存)
        if use_cache:
            _save_to_cache(cache_key, price_data, ttl=60)  # 1分钟缓存
        
        return price_data
        
    except requests.exceptions.RequestException as e:
        # 网络失败时尝试返回缓存
        if use_cache:
            cached = _get_from_cache(cache_key, data_type="price")
            if cached:
                cached["cached"] = True
                cached["cache_age"] = _get_cache_age(cache_key)
                return cached
        
        raise ConnectionError(f"获取价格失败: {e}")
    except (KeyError, ValueError) as e:
        raise RuntimeError(f"价格数据解析失败: {e}")

def fetch_latest(
    symbol: str = "BTCUSDT",
    timeframe: str = "4h",
    count: int = 1
) -> List[Dict[str, Any]]:
    """
    获取最新数据点
    
    参数:
        symbol (str): 交易对
        timeframe (str): 时间框架
        count (int): 获取数量，默认1
    
    返回:
        List[Dict]: 最新的K线数据
    
    示例:
        >>> latest = fetch_latest("BTCUSDT", "4h", 5)
        >>> len(latest)
        5
        >>> latest[0]['close']  # 最新收盘价
        72106.85
    """
    # 获取稍多一些数据确保包含最新
    limit = min(count + 10, 100)
    data = fetch_klines(symbol, timeframe, limit, use_cache=True)
    
    # 返回最新的count条
    return data[-count:] if len(data) >= count else data

def fetch_historical(
    symbol: str = "BTCUSDT",
    timeframe: str = "1d",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    max_points: int = 1000
) -> List[Dict[str, Any]]:
    """
    获取历史数据 (分页获取)
    
    参数:
        symbol (str): 交易对
        timeframe (str): 时间框架
        start_time (str): 开始时间 (ISO格式)
        end_time (str): 结束时间 (ISO格式)
        max_points (int): 最大数据点数
    
    返回:
        List[Dict]: 历史K线数据
    
    注意:
        这个方法会进行多次API调用，请谨慎使用
    """
    # TODO: 实现分页获取历史数据
    # 这是一个占位实现
    return fetch_klines(symbol, timeframe, min(max_points, 1000))

def _get_from_cache(
    key: str,
    data_type: str = "klines"
) -> Optional[Any]:
    """从缓存获取数据"""
    try:
        # 确保缓存目录存在
        CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(CACHE_DB_PATH))
        cursor = conn.cursor()
        
        # 创建缓存表如果不存在
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {CACHE_TABLE} (
                key TEXT PRIMARY KEY,
                data_type TEXT,
                data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 查询缓存
        cursor.execute(
            f"SELECT data, timestamp FROM {CACHE_TABLE} WHERE key = ? AND data_type = ?",
            (key, data_type)
        )
        
        result = cursor.fetchone()
        
        if result:
            data_json, cache_time = result
            cache_time = datetime.fromisoformat(cache_time)
            
            # 检查缓存是否过期
            age_seconds = (datetime.now() - cache_time).total_seconds()
            ttl = 60 if data_type == "price" else CACHE_TTL
            
            if age_seconds < ttl:
                # 缓存有效，返回数据
                data = json.loads(data_json)
                return data
        
        conn.close()
        return None
        
    except Exception as e:
        # 缓存失败不影响主逻辑
        print(f"缓存读取失败: {e}")
        return None

def _save_to_cache(
    key: str,
    data: Any,
    data_type: str = "klines",
    ttl: Optional[int] = None
) -> bool:
    """保存数据到缓存"""
    try:
        conn = sqlite3.connect(str(CACHE_DB_PATH))
        cursor = conn.cursor()
        
        # 创建缓存表如果不存在
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {CACHE_TABLE} (
                key TEXT PRIMARY KEY,
                data_type TEXT,
                data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 保存数据
        data_json = json.dumps(data, default=str)
        
        cursor.execute(
            f"INSERT OR REPLACE INTO {CACHE_TABLE} (key, data_type, data, timestamp) VALUES (?, ?, ?, ?)",
            (key, data_type, data_json, datetime.now().isoformat())
        )
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"缓存保存失败: {e}")
        return False

def _get_cache_age(key: str) -> Optional[float]:
    """获取缓存年龄(秒)"""
    try:
        conn = sqlite3.connect(str(CACHE_DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute(
            f"SELECT timestamp FROM {CACHE_TABLE} WHERE key = ?",
            (key,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            cache_time = datetime.fromisoformat(result[0])
            age_seconds = (datetime.now() - cache_time).total_seconds()
            return age_seconds
        
        return None
        
    except Exception:
        return None

def clear_cache(
    older_than_hours: Optional[int] = None,
    data_type: Optional[str] = None
) -> int:
    """
    清理缓存
    
    参数:
        older_than_hours (int): 清理多少小时前的缓存
        data_type (str): 清理特定类型的数据
    
    返回:
        int: 清理的记录数
    """
    try:
        conn = sqlite3.connect(str(CACHE_DB_PATH))
        cursor = conn.cursor()
        
        # 构建清理条件
        conditions = []
        params = []
        
        if older_than_hours is not None:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            conditions.append("timestamp < ?")
            params.append(cutoff_time.isoformat())
        
        if data_type is not None:
            conditions.append("data_type = ?")
            params.append(data_type)
        
        # 执行清理
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        cursor.execute(f"DELETE FROM {CACHE_TABLE} WHERE {where_clause}", params)
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
        
    except Exception as e:
        print(f"缓存清理失败: {e}")
        return 0

# 测试代码
if __name__ == "__main__":
    # 测试数据获取
    print("测试数据获取功能...")
    
    try:
        # 测试当前价格
        price_data = fetch_current_price("BTCUSDT")
        print(f"当前价格: {price_data['price']} {price_data['symbol']}")
        
        # 测试K线数据
        klines = fetch_klines("BTCUSDT", "4h", 10)
        print(f"获取到 {len(klines)} 条K线数据")
        if klines:
            latest = klines[-1]
            print(f"最新K线: 时间={latest['timestamp']}, 收盘价={latest['close']}")
        
        # 测试缓存
        print("测试缓存功能...")
        cache_key = "test_cache"
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        _save_to_cache(cache_key, test_data, "test")
        
        cached = _get_from_cache(cache_key, "test")
        print(f"缓存读取: {'成功' if cached else '失败'}")
        
        # 清理测试缓存
        clear_cache(older_than_hours=0)
        
    except Exception as e:
        print(f"测试失败: {e}")