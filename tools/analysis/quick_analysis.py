#!/usr/bin/env python3
"""
快速支撑阻力分析 - 简化版
立即运行，显示关键支撑阻力位
"""

import mysql.connector
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_float(value):
    """确保值为float类型"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except:
        return 0.0

def get_current_price():
    """获取当前价格"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='btc_assistant',
            charset='utf8mb4'
        )
        cursor = conn.cursor(dictionary=True)
        
        # 获取最新价格
        query = "SELECT close FROM klines WHERE symbol='BTCUSDT' AND timeframe='4h' ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return ensure_float(result['close'])
        return None
        
    except Exception as e:
        logger.error(f"获取价格失败: {e}")
        return None

def analyze_support_resistance():
    """分析支撑阻力位"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='',
            database='btc_assistant',
            charset='utf8mb4'
        )
        cursor = conn.cursor(dictionary=True)
        
        # 获取当前价格
        current_price = get_current_price()
        if not current_price:
            print("❌ 无法获取当前价格")
            return
        
        print("=" * 80)
        print(f"📊 BTC支撑阻力分析报告")
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"当前价格: ${current_price:,.2f}")
        print("=" * 80)
        
        # 1. 分析关键动态位（EMA、布林带）
        print("\n📈 关键动态支撑阻力位:")
        print("-" * 80)
        
        timeframes = ['1M', '1w', '1d', '4h']
        for tf in timeframes:
            query = """
                SELECT timestamp, close,
                       ema7, ema12, ema25, ema50,
                       boll_up, boll_md, boll_dn
                FROM klines 
                WHERE symbol='BTCUSDT' AND timeframe=%s
                ORDER BY timestamp DESC LIMIT 1
            """
            cursor.execute(query, (tf,))
            data = cursor.fetchone()
            
            if data:
                close_price = ensure_float(data['close'])
                ema50 = ensure_float(data['ema50'])
                boll_md = ensure_float(data['boll_md'])
                boll_up = ensure_float(data['boll_up'])
                boll_dn = ensure_float(data['boll_dn'])
                
                print(f"\n{tf}时间框架:")
                
                # EMA50
                if ema50 > 0:
                    relation = "支撑" if close_price > ema50 else "阻力"
                    distance_pct = abs(close_price - ema50) / close_price * 100
                    print(f"  EMA50: ${ema50:,.2f} ({relation}, 距离: {distance_pct:.1f}%)")
                
                # 布林带
                if boll_md > 0:
                    relation = "支撑" if close_price > boll_md else "阻力"
                    distance_pct = abs(close_price - boll_md) / close_price * 100
                    print(f"  布林中轨: ${boll_md:,.2f} ({relation}, 距离: {distance_pct:.1f}%)")
                
                if boll_up > 0:
                    distance_pct = (boll_up - close_price) / close_price * 100
                    print(f"  布林上轨: ${boll_up:,.2f} (阻力, 上方: {distance_pct:.1f}%)")
                
                if boll_dn > 0:
                    distance_pct = (close_price - boll_dn) / close_price * 100
                    print(f"  布林下轨: ${boll_dn:,.2f} (支撑, 下方: {distance_pct:.1f}%)")
        
        # 2. 分析近期摆动高低点
        print("\n📉 近期关键摆动点 (4H):")
        print("-" * 80)
        
        query = """
            SELECT timestamp, high, low, close
            FROM klines 
            WHERE symbol='BTCUSDT' AND timeframe='4h'
            ORDER BY timestamp DESC
            LIMIT 100
        """
        cursor.execute(query)
        data = cursor.fetchall()
        
        if data:
            # 寻找近期摆动高点
            recent_highs = []
            for i in range(5, len(data)-5):
                high = ensure_float(data[i]['high'])
                is_swing_high = True
                
                # 检查前后5根K线
                for j in range(1, 6):
                    if high <= ensure_float(data[i-j]['high']) or high <= ensure_float(data[i+j]['high']):
                        is_swing_high = False
                        break
                
                if is_swing_high:
                    recent_highs.append({
                        'price': high,
                        'timestamp': data[i]['timestamp']
                    })
            
            # 寻找近期摆动低点
            recent_lows = []
            for i in range(5, len(data)-5):
                low = ensure_float(data[i]['low'])
                is_swing_low = True
                
                for j in range(1, 6):
                    if low >= ensure_float(data[i-j]['low']) or low >= ensure_float(data[i+j]['low']):
                        is_swing_low = False
                        break
                
                if is_swing_low:
                    recent_lows.append({
                        'price': low,
                        'timestamp': data[i]['timestamp']
                    })
            
            # 显示最近的3个摆动点
            if recent_highs:
                recent_highs.sort(key=lambda x: x['timestamp'], reverse=True)
                print("  最近摆动高点:")
                for i, high in enumerate(recent_highs[:3], 1):
                    distance_pct = (high['price'] - current_price) / current_price * 100
                    print(f"    {i}. ${high['price']:,.2f} (上方: {distance_pct:+.1f}%)")
            
            if recent_lows:
                recent_lows.sort(key=lambda x: x['timestamp'], reverse=True)
                print("  最近摆动低点:")
                for i, low in enumerate(recent_lows[:3], 1):
                    distance_pct = (current_price - low['price']) / current_price * 100
                    print(f"    {i}. ${low['price']:,.2f} (下方: {distance_pct:.1f}%)")
        
        # 3. 心理位分析
        print("\n🧠 关键心理位:")
        print("-" * 80)
        
        lookback_percent = 0.1  # 查看当前价格±10%
        min_price = current_price * (1 - lookback_percent)
        max_price = current_price * (1 + lookback_percent)
        
        # 生成心理位
        psychological_levels = []
        for base in range(int(min_price // 1000) * 1000, int(max_price // 1000) * 1000 + 1000, 1000):
            if min_price <= base <= max_price:
                psychological_levels.append(base)
        
        print("  附近整数关口:")
        for level in psychological_levels:
            if level % 5000 == 0:
                importance = "★★★"
            elif level % 1000 == 0:
                importance = "★★"
            else:
                continue
                
            if current_price > level:
                relation = "支撑"
                distance_pct = (current_price - level) / current_price * 100
            else:
                relation = "阻力"
                distance_pct = (level - current_price) / current_price * 100
            
            print(f"    {importance} ${level:,.0f} ({relation}, 距离: {distance_pct:.1f}%)")
        
        # 4. 交易建议
        print("\n💡 交易建议:")
        print("-" * 80)
        
        # 获取最近的EMA50和布林带
        query = """
            SELECT ema50, boll_dn, boll_up
            FROM klines 
            WHERE symbol='BTCUSDT' AND timeframe='4h'
            ORDER BY timestamp DESC LIMIT 1
        """
        cursor.execute(query)
        latest = cursor.fetchone()
        
        if latest:
            ema50 = ensure_float(latest['ema50'])
            boll_dn = ensure_float(latest['boll_dn'])
            boll_up = ensure_float(latest['boll_up'])
            
            # 判断当前趋势
            if current_price > ema50:
                trend = "上涨趋势"
                key_support = max(ema50, boll_dn)
                key_resistance = boll_up
            else:
                trend = "下跌趋势"
                key_support = boll_dn
                key_resistance = min(ema50, boll_up)
            
            print(f"  当前趋势: {trend}")
            
            if current_price > key_support:
                support_distance = (current_price - key_support) / current_price * 100
                print(f"  关键支撑: ${key_support:,.2f} (下方: {support_distance:.1f}%)")
                print(f"  建议: 等待回调至支撑区域再考虑做多")
            else:
                print(f"  价格已跌破关键支撑 ${key_support:,.2f}")
                print(f"  建议: 观望或考虑做空")
            
            resistance_distance = (key_resistance - current_price) / current_price * 100
            print(f"  关键阻力: ${key_resistance:,.2f} (上方: {resistance_distance:.1f}%)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("分析完成 🎯")
        
    except Exception as e:
        logger.error(f"分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_support_resistance()