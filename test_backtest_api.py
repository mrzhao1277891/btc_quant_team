#!/usr/bin/env python3
"""
测试回测API
"""
import requests
import json
import time
from datetime import datetime, timedelta

API_BASE = "http://127.0.0.1:8001"

def test_strategy(strategy_name, config):
    """测试一个策略"""
    print(f"\n{'='*60}")
    print(f"测试策略: {strategy_name}")
    print(f"{'='*60}")
    
    # 准备回测请求
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 90天数据
    
    request_data = {
        "strategy_name": strategy_name,
        "timeframe": config["timeframe"],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "initial_capital": 10000,
        "position_side": config["position_side"],
        "position_size": config["position_size"],
        "position_size_type": config["position_size_type"],
        "entry_conditions": config["entry_conditions"],
        "entry_logic": config["entry_logic"],
        "exit_conditions": config["exit_conditions"],
        "exit_logic": config["exit_logic"],
        "take_profit_pct": config.get("take_profit_pct"),
        "stop_loss_pct": config.get("stop_loss_pct")
    }
    
    print(f"回测时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    print(f"初始资金: ${request_data['initial_capital']}")
    
    # 提交回测
    response = requests.post(f"{API_BASE}/api/backtest", json=request_data)
    if response.status_code != 200:
        print(f"❌ 提交失败: {response.text}")
        return None
    
    result = response.json()
    backtest_id = result["backtest_id"]
    print(f"✅ 回测已提交: {backtest_id}")
    
    # 轮询状态
    max_attempts = 30
    for i in range(max_attempts):
        time.sleep(1)
        status_response = requests.get(f"{API_BASE}/api/backtest/{backtest_id}/status")
        if status_response.status_code != 200:
            print(f"❌ 查询状态失败: {status_response.text}")
            return None
        
        status_data = status_response.json()
        status = status_data.get("status")
        progress = status_data.get("progress", 0)
        
        if status == "completed":
            print(f"✅ 回测完成 (100%)")
            break
        elif status == "failed":
            error = status_data.get("error", "未知错误")
            print(f"❌ 回测失败: {error}")
            return None
        else:
            print(f"⏳ 回测进行中... ({progress}%)")
    
    # 获取结果
    results_response = requests.get(f"{API_BASE}/api/backtest/{backtest_id}/results")
    if results_response.status_code != 200:
        print(f"❌ 获取结果失败: {results_response.text}")
        return None
    
    results = results_response.json()
    
    # 显示结果
    print(f"\n📊 回测结果:")
    print(f"{'─'*60}")
    metrics = results["performance_metrics"]
    print(f"初始资金: ${metrics['initial_capital']:.2f}")
    print(f"最终资金: ${metrics['final_capital']:.2f}")
    print(f"总收益: ${metrics['total_return']:.2f} ({metrics['total_return_pct']:.2f}%)")
    print(f"总交易次数: {metrics['total_trades']}")
    print(f"胜率: {metrics['win_rate']:.2f}%")
    print(f"盈亏比: {metrics['profit_factor']:.2f}")
    print(f"最大回撤: {metrics['max_drawdown_pct']:.2f}%")
    print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"最长连胜: {metrics['longest_win_streak']}")
    print(f"最长连亏: {metrics['longest_loss_streak']}")
    
    # 显示交易记录
    trades = results["trades"]
    if trades:
        print(f"\n📝 交易记录 (前5笔):")
        print(f"{'─'*60}")
        for trade in trades[:5]:
            entry_time = trade['entry_time'][:10]
            exit_time = trade['exit_time'][:10]
            pnl = trade['profit_loss']
            pnl_pct = trade['profit_loss_pct']
            reason = trade['exit_reason']
            print(f"  {entry_time} → {exit_time}: ${pnl:+.2f} ({pnl_pct:+.2f}%) [{reason}]")
    
    return results


def main():
    """主函数"""
    print("🚀 开始测试回测系统")
    
    # 获取策略模板
    response = requests.get(f"{API_BASE}/api/strategy-templates")
    if response.status_code != 200:
        print(f"❌ 获取策略模板失败: {response.text}")
        return
    
    templates = response.json()["templates"]
    print(f"找到 {len(templates)} 个策略模板")
    
    # 测试每个策略
    for template in templates:
        test_strategy(template["name"], template["config"])
        time.sleep(2)  # 间隔2秒
    
    print(f"\n{'='*60}")
    print("✅ 所有测试完成")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
