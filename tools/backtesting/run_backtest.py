#!/usr/bin/env python3
"""
回测入口

用法：
  python tools/backtesting/run_backtest.py --password 你的密码
  python tools/backtesting/run_backtest.py --password 你的密码 --min-score 9
  python tools/backtesting/run_backtest.py --password 你的密码 --output result.json
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
import logging
from backtesting.sr_backtest import SRBacktester, BACKTEST_CONFIG
from backtesting.report import print_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    parser = argparse.ArgumentParser(description='支撑阻力位回测工具')
    parser.add_argument('--host',      default='localhost')
    parser.add_argument('--port',      type=int, default=3306)
    parser.add_argument('--user',      default='root')
    parser.add_argument('--password',  default='')
    parser.add_argument('--database',  default='btc_assistant')
    parser.add_argument('--symbol',    default='BTCUSDT')
    parser.add_argument('--min-score', type=int, default=7,
                        help='位点最低评分（1-15），默认 7')
    parser.add_argument('--min-rr',    type=float, default=2.0,
                        help='最小盈亏比，默认 2.0')
    parser.add_argument('--max-bars',  type=int, default=12,
                        help='最大持仓根数（4H），默认 12（=48小时）')
    parser.add_argument('--touch-mult', type=float, default=0.5,
                        help='触及判定 ATR 倍数，默认 0.5')
    parser.add_argument('--output',    default=None,
                        help='结果保存路径（JSON），不指定则只打印')
    args = parser.parse_args()

    # 覆盖配置
    BACKTEST_CONFIG['min_score']       = args.min_score
    BACKTEST_CONFIG['min_rr']          = args.min_rr
    BACKTEST_CONFIG['max_bars']        = args.max_bars
    BACKTEST_CONFIG['touch_atr_mult']  = args.touch_mult

    print(f"🔧 回测参数:")
    print(f"   最低评分: {args.min_score}  |  最小盈亏比: {args.min_rr}"
          f"  |  最大持仓: {args.max_bars} 根4H  |  触及倍数: {args.touch_mult}×ATR")
    print()

    backtester = SRBacktester(
        host=args.host, port=args.port,
        user=args.user, password=args.password,
        database=args.database
    )

    try:
        backtester.connect()
        report = backtester.run(symbol=args.symbol)
        print_report(report)

        if args.output:
            # 序列化时去掉不可 JSON 化的字段
            save_data = {
                'stats':        report['stats'],
                'by_direction': report['by_direction'],
                'by_score':     report['by_score'],
                'trades':       [
                    {k: v for k, v in t.items()} for t in report['trades']
                ]
            }
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"\n📁 结果已保存到: {args.output}")

    except Exception as e:
        print(f"\n❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        backtester.disconnect()


if __name__ == '__main__':
    main()
