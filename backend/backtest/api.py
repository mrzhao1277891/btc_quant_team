#!/usr/bin/env python3
"""
BTC 回测系统 API
FastAPI 后端服务，提供回测执行、策略管理等功能
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import asyncio
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.backtest.engine import BacktestEngine
from backend.backtest.models import StrategyConfig
from backend.backtest.metrics import MetricsCalculator
from backend.database import DatabaseConnector
from backend.indicators import IndicatorCalculator
from backend.backtest.logger import get_logger

logger = get_logger("backtest_api")

# 创建 FastAPI 应用
app = FastAPI(
    title="BTC 回测系统 API",
    description="提供策略回测、性能分析、策略管理等功能",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（Web UI）
web_dir = project_root / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# 全局状态存储
backtest_results = {}  # 存储回测结果
backtest_status = {}   # 存储回测状态
saved_strategies = {}  # 存储已保存的策略


# ============================================================================
# Pydantic 模型定义
# ============================================================================

class IndicatorConditionRequest(BaseModel):
    """指标条件请求模型"""
    indicator: str
    operator: str
    value: Any
    timeframe: Optional[str] = "1d"


class BacktestRequest(BaseModel):
    """回测请求模型 - 支持双向交易策略和向后兼容"""
    strategy_name: str
    timeframe: str = "1d"
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    
    # 持仓和风控参数
    position_size: float = 1000.0
    position_size_type: str = "fixed"
    leverage: float = 1.0  # 杠杆倍数，默认1倍（现货）
    
    # 旧版字段（向后兼容）
    entry_conditions: Optional[List[IndicatorConditionRequest]] = None
    entry_logic: str = "AND"
    exit_conditions: Optional[List[IndicatorConditionRequest]] = None
    exit_logic: str = "OR"
    position_side: Optional[str] = "long"
    take_profit_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_amount: Optional[float] = None
    stop_loss_amount: Optional[float] = None
    
    # 新版双向开仓条件字段
    long_entry_conditions: Optional[List[IndicatorConditionRequest]] = None
    short_entry_conditions: Optional[List[IndicatorConditionRequest]] = None
    long_exit_conditions: Optional[List[IndicatorConditionRequest]] = None
    short_exit_conditions: Optional[List[IndicatorConditionRequest]] = None
    
    # 新版双向逻辑运算符
    long_entry_logic: Optional[str] = "AND"
    short_entry_logic: Optional[str] = "AND"
    long_exit_logic: Optional[str] = "OR"
    short_exit_logic: Optional[str] = "OR"
    
    # 新版双向止盈止损
    long_take_profit_pct: Optional[float] = None
    long_stop_loss_pct: Optional[float] = None
    short_take_profit_pct: Optional[float] = None
    short_stop_loss_pct: Optional[float] = None


class StrategyResponse(BaseModel):
    """策略响应模型"""
    strategy_id: str
    strategy_name: str
    created_at: str
    config: Dict[str, Any]


# ============================================================================
# 辅助函数
# ============================================================================

def generate_backtest_id() -> str:
    """生成唯一的回测ID"""
    return f"bt_{uuid.uuid4().hex[:12]}"


def convert_request_to_strategy_config(request: BacktestRequest) -> Dict[str, Any]:
    """将请求转换为策略配置字典，支持双向策略和向后兼容"""
    logger.info(f"Converting request: position_size={request.position_size}, "
                f"position_size_type={request.position_size_type}, leverage={request.leverage}")
    
    config = {
        "name": request.strategy_name,
        "description": f"回测策略: {request.strategy_name}",
        "timeframe": request.timeframe,
        "position_size_type": "amount",  # 固定使用amount类型
        "position_size_value": request.position_size,  # 直接使用固定金额
        "initial_capital": request.initial_capital,
        "leverage": request.leverage,  # 使用用户设置的杠杆
    }
    
    # 处理双向条件（新版）
    if request.long_entry_conditions is not None:
        config["long_entry_conditions"] = {
            "conditions": [
                {
                    "indicator": cond.indicator,
                    "operator": cond.operator,
                    "value": cond.value,
                    "timeframe": cond.timeframe or request.timeframe
                }
                for cond in request.long_entry_conditions
            ],
            "logic_operator": request.long_entry_logic
        }
    
    if request.short_entry_conditions is not None:
        config["short_entry_conditions"] = {
            "conditions": [
                {
                    "indicator": cond.indicator,
                    "operator": cond.operator,
                    "value": cond.value,
                    "timeframe": cond.timeframe or request.timeframe
                }
                for cond in request.short_entry_conditions
            ],
            "logic_operator": request.short_entry_logic
        }
    
    # 处理做多平仓条件（支持仅止盈止损，无指标条件的情况）
    if request.long_exit_conditions is not None or request.long_take_profit_pct is not None or request.long_stop_loss_pct is not None:
        config["long_exit_conditions"] = {
            "indicator_conditions": [
                {
                    "indicator": cond.indicator,
                    "operator": cond.operator,
                    "value": cond.value,
                    "timeframe": cond.timeframe or request.timeframe
                }
                for cond in request.long_exit_conditions
            ] if request.long_exit_conditions else [],
            "take_profit_pct": request.long_take_profit_pct / 100 if request.long_take_profit_pct else None,
            "stop_loss_pct": request.long_stop_loss_pct / 100 if request.long_stop_loss_pct else None,
            "logic_operator": request.long_exit_logic
        }
    
    # 处理做空平仓条件（支持仅止盈止损，无指标条件的情况）
    if request.short_exit_conditions is not None or request.short_take_profit_pct is not None or request.short_stop_loss_pct is not None:
        config["short_exit_conditions"] = {
            "indicator_conditions": [
                {
                    "indicator": cond.indicator,
                    "operator": cond.operator,
                    "value": cond.value,
                    "timeframe": cond.timeframe or request.timeframe
                }
                for cond in request.short_exit_conditions
            ] if request.short_exit_conditions else [],
            "take_profit_pct": request.short_take_profit_pct / 100 if request.short_take_profit_pct else None,
            "stop_loss_pct": request.short_stop_loss_pct / 100 if request.short_stop_loss_pct else None,
            "logic_operator": request.short_exit_logic
        }
    
    # 向后兼容：处理旧版字段
    if request.entry_conditions is not None and request.long_entry_conditions is None and request.short_entry_conditions is None:
        logger.warning("Using legacy entry_conditions field, consider migrating to long/short_entry_conditions")
        config["position_direction"] = request.position_side
        config["entry_conditions"] = {
            "conditions": [
                {
                    "indicator": cond.indicator,
                    "operator": cond.operator,
                    "value": cond.value,
                    "timeframe": cond.timeframe or request.timeframe
                }
                for cond in request.entry_conditions
            ],
            "logic_operator": request.entry_logic
        }
    
    if request.exit_conditions is not None and request.long_exit_conditions is None and request.short_exit_conditions is None:
        config["exit_conditions"] = {
            "indicator_conditions": [
                {
                    "indicator": cond.indicator,
                    "operator": cond.operator,
                    "value": cond.value,
                    "timeframe": cond.timeframe or request.timeframe
                }
                for cond in request.exit_conditions
            ],
            "take_profit_pct": request.take_profit_pct / 100 if request.take_profit_pct else None,
            "stop_loss_pct": request.stop_loss_pct / 100 if request.stop_loss_pct else None,
            "take_profit_amount": request.take_profit_amount,
            "stop_loss_amount": request.stop_loss_amount,
            "logic_operator": request.exit_logic
        }
    
    logger.info(f"Converted config: position_size_value={config['position_size_value']}, "
                f"leverage={config['leverage']}")
    
    return config


async def run_backtest_task(backtest_id: str, request: BacktestRequest):
    """后台任务：运行回测"""
    try:
        logger.info(f"开始回测 {backtest_id}: {request.strategy_name}")
        backtest_status[backtest_id] = {"status": "running", "progress": 0}
        
        # 1. 连接数据库获取数据
        db = DatabaseConnector()
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        klines_df = db.fetch_klines(
            symbol="BTCUSDT",
            timeframe=request.timeframe,
            start_date=start_date,
            end_date=end_date
        )
        
        if klines_df.empty:
            backtest_status[backtest_id] = {"status": "failed", "error": "没有获取到数据"}
            return
        
        # 转换所有数值列为 float（避免 Decimal 类型问题）
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in klines_df.columns:
                klines_df[col] = klines_df[col].astype(float)
        
        backtest_status[backtest_id]["progress"] = 30
        
        # 2. 计算技术指标
        calculator = IndicatorCalculator()
        klines_with_indicators = calculator.calculate_all_indicators(klines_df)
        
        backtest_status[backtest_id]["progress"] = 50
        
        # 3. 创建策略配置
        strategy_dict = convert_request_to_strategy_config(request)
        strategy = StrategyConfig.from_dict(strategy_dict)
        
        # 4. 运行回测（直接使用 DataFrame）
        engine = BacktestEngine(strategy, klines_with_indicators)
        result = engine.run()
        
        backtest_status[backtest_id]["progress"] = 90
        
        # 6. 保存结果
        backtest_results[backtest_id] = {
            "backtest_id": backtest_id,
            "strategy_config": strategy_dict,
            "performance_metrics": result.metrics.to_dict(),
            "trades": [trade.to_dict() for trade in result.trades],
            "initial_capital": strategy_dict['initial_capital'],
            "final_capital": result.metrics.final_capital,
            "completed_at": datetime.now().isoformat()
        }
        
        backtest_status[backtest_id] = {"status": "completed", "progress": 100}
        logger.info(f"回测完成 {backtest_id}")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"回测失败 {backtest_id}: {e}\n{error_details}")
        backtest_status[backtest_id] = {"status": "failed", "error": str(e)}


# ============================================================================
# API 端点
# ============================================================================

@app.get("/")
async def root():
    """根路径"""
    return {"message": "BTC 回测系统 API", "version": "1.0.0"}


@app.get("/backtest.html")
async def serve_backtest_ui():
    """提供回测 UI 页面"""
    html_path = project_root / "web" / "backtest.html"
    if html_path.exists():
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="回测 UI 页面未找到")


@app.post("/api/backtest")
async def create_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    创建并运行回测
    
    - **strategy_name**: 策略名称
    - **timeframe**: 时间周期 (1m/1w/1d/4h)
    - **start_date**: 开始日期 (YYYY-MM-DD)
    - **end_date**: 结束日期 (YYYY-MM-DD)
    - **initial_capital**: 初始资金
    - **entry_conditions**: 开仓条件列表
    - **exit_conditions**: 平仓条件列表
    """
    backtest_id = generate_backtest_id()
    
    # 添加后台任务
    background_tasks.add_task(run_backtest_task, backtest_id, request)
    
    return {
        "backtest_id": backtest_id,
        "status": "queued",
        "message": "回测任务已提交"
    }


@app.get("/api/backtest/{backtest_id}/status")
async def get_backtest_status(backtest_id: str):
    """
    查询回测状态
    
    - **backtest_id**: 回测ID
    """
    if backtest_id not in backtest_status:
        raise HTTPException(status_code=404, detail="回测任务未找到")
    
    return {
        "backtest_id": backtest_id,
        **backtest_status[backtest_id]
    }


@app.get("/api/backtest/{backtest_id}/results")
async def get_backtest_results(backtest_id: str):
    """
    获取回测结果
    
    - **backtest_id**: 回测ID
    """
    if backtest_id not in backtest_results:
        # 检查状态
        if backtest_id in backtest_status:
            status = backtest_status[backtest_id]
            if status["status"] == "running":
                raise HTTPException(status_code=202, detail="回测正在运行中")
            elif status["status"] == "failed":
                raise HTTPException(status_code=500, detail=f"回测失败: {status.get('error', '未知错误')}")
        raise HTTPException(status_code=404, detail="回测结果未找到")
    
    return backtest_results[backtest_id]


@app.get("/api/indicators")
async def get_available_indicators():
    """获取可用的技术指标列表"""
    return {
        "indicators": [
            {"name": "ema7", "label": "EMA7", "type": "trend"},
            {"name": "ema12", "label": "EMA12", "type": "trend"},
            {"name": "ema25", "label": "EMA25", "type": "trend"},
            {"name": "ema50", "label": "EMA50", "type": "trend"},
            {"name": "rsi6", "label": "RSI6", "type": "momentum"},
            {"name": "rsi14", "label": "RSI14", "type": "momentum"},
            {"name": "dif", "label": "MACD DIF", "type": "momentum"},
            {"name": "dea", "label": "MACD DEA", "type": "momentum"},
            {"name": "macd", "label": "MACD", "type": "momentum"},
            {"name": "boll_up", "label": "布林上轨", "type": "volatility"},
            {"name": "boll_md", "label": "布林中轨", "type": "volatility"},
            {"name": "boll_dn", "label": "布林下轨", "type": "volatility"},
            {"name": "atr", "label": "ATR", "type": "volatility"},
            {"name": "close", "label": "收盘价", "type": "price"},
            {"name": "volume", "label": "成交量", "type": "volume"}
        ]
    }


@app.get("/api/timeframes")
async def get_available_timeframes():
    """获取可用的时间周期"""
    return {
        "timeframes": [
            {"value": "1m", "label": "月线"},
            {"value": "1w", "label": "周线"},
            {"value": "1d", "label": "日线"},
            {"value": "4h", "label": "4小时"}
        ]
    }


@app.get("/api/data-range")
async def get_data_range(timeframe: str = "1d"):
    """获取指定时间周期的数据范围"""
    try:
        db = DatabaseConnector()
        date_range = db.get_available_date_range("BTCUSDT", timeframe)
        
        if date_range:
            return {
                "timeframe": timeframe,
                "start_date": datetime.fromtimestamp(date_range[0] / 1000).date().isoformat(),
                "end_date": datetime.fromtimestamp(date_range[1] / 1000).date().isoformat()
            }
        else:
            return {
                "timeframe": timeframe,
                "start_date": None,
                "end_date": None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据范围失败: {str(e)}")


@app.get("/api/strategy-templates")
async def get_strategy_templates():
    """获取策略模板 - 包含单向和双向策略"""
    return {
        "templates": [
            # 单向策略模板（向后兼容）
            {
                "id": "ema_golden_cross",
                "name": "EMA金叉策略",
                "description": "EMA7上穿EMA25时做多，RSI过滤",
                "config": {
                    "timeframe": "1d",
                    "entry_conditions": [
                        {"indicator": "ema7", "operator": ">", "value": "ema25"},
                        {"indicator": "rsi14", "operator": "<", "value": 70}
                    ],
                    "entry_logic": "AND",
                    "exit_conditions": [
                        {"indicator": "ema7", "operator": "<", "value": "ema25"}
                    ],
                    "exit_logic": "OR",
                    "position_side": "long",
                    "take_profit_pct": 10,
                    "stop_loss_pct": 5
                }
            },
            {
                "id": "bollinger_breakout",
                "name": "布林带突破",
                "description": "价格突破布林上轨时做多",
                "config": {
                    "timeframe": "4h",
                    "entry_conditions": [
                        {"indicator": "close", "operator": ">", "value": "boll_up"}
                    ],
                    "entry_logic": "AND",
                    "exit_conditions": [
                        {"indicator": "close", "operator": "<", "value": "boll_md"}
                    ],
                    "exit_logic": "OR",
                    "position_side": "long",
                    "take_profit_pct": 8,
                    "stop_loss_pct": 4
                }
            },
            {
                "id": "rsi_oversold",
                "name": "RSI超卖反弹",
                "description": "RSI低于30时做多",
                "config": {
                    "timeframe": "1d",
                    "entry_conditions": [
                        {"indicator": "rsi14", "operator": "<", "value": 30},
                        {"indicator": "close", "operator": ">", "value": "ema50"}
                    ],
                    "entry_logic": "AND",
                    "exit_conditions": [
                        {"indicator": "rsi14", "operator": ">", "value": 70}
                    ],
                    "exit_logic": "OR",
                    "position_side": "long",
                    "take_profit_pct": 12,
                    "stop_loss_pct": 6
                }
            },
            # 双向策略模板
            {
                "id": "dual_rsi",
                "name": "双向RSI策略",
                "description": "RSI<30做多，RSI>70做空，配合EMA过滤",
                "config": {
                    "timeframe": "1d",
                    "long_entry_conditions": [
                        {"indicator": "rsi14", "operator": "<", "value": 30},
                        {"indicator": "close", "operator": ">", "value": "ema50"}
                    ],
                    "long_entry_logic": "AND",
                    "long_exit_conditions": [
                        {"indicator": "rsi14", "operator": ">", "value": 70}
                    ],
                    "long_exit_logic": "OR",
                    "long_take_profit_pct": 10,
                    "long_stop_loss_pct": 5,
                    "short_entry_conditions": [
                        {"indicator": "rsi14", "operator": ">", "value": 70},
                        {"indicator": "close", "operator": "<", "value": "ema50"}
                    ],
                    "short_entry_logic": "AND",
                    "short_exit_conditions": [
                        {"indicator": "rsi14", "operator": "<", "value": 30}
                    ],
                    "short_exit_logic": "OR",
                    "short_take_profit_pct": 10,
                    "short_stop_loss_pct": 5
                }
            },
            {
                "id": "dual_ma_crossover",
                "name": "双向均线策略",
                "description": "价格突破EMA25做多，跌破EMA25做空",
                "config": {
                    "timeframe": "4h",
                    "long_entry_conditions": [
                        {"indicator": "close", "operator": ">", "value": "ema25"},
                        {"indicator": "ema7", "operator": ">", "value": "ema25"}
                    ],
                    "long_entry_logic": "AND",
                    "long_exit_conditions": [
                        {"indicator": "close", "operator": "<", "value": "ema25"}
                    ],
                    "long_exit_logic": "OR",
                    "long_take_profit_pct": 8,
                    "long_stop_loss_pct": 4,
                    "short_entry_conditions": [
                        {"indicator": "close", "operator": "<", "value": "ema25"},
                        {"indicator": "ema7", "operator": "<", "value": "ema25"}
                    ],
                    "short_entry_logic": "AND",
                    "short_exit_conditions": [
                        {"indicator": "close", "operator": ">", "value": "ema25"}
                    ],
                    "short_exit_logic": "OR",
                    "short_take_profit_pct": 8,
                    "short_stop_loss_pct": 4
                }
            },
            {
                "id": "dual_bollinger",
                "name": "双向布林带策略",
                "description": "价格触及下轨做多，触及上轨做空",
                "config": {
                    "timeframe": "1d",
                    "long_entry_conditions": [
                        {"indicator": "close", "operator": "<", "value": "boll_dn"},
                        {"indicator": "rsi14", "operator": "<", "value": 40}
                    ],
                    "long_entry_logic": "AND",
                    "long_exit_conditions": [
                        {"indicator": "close", "operator": ">", "value": "boll_md"}
                    ],
                    "long_exit_logic": "OR",
                    "long_take_profit_pct": 12,
                    "long_stop_loss_pct": 6,
                    "short_entry_conditions": [
                        {"indicator": "close", "operator": ">", "value": "boll_up"},
                        {"indicator": "rsi14", "operator": ">", "value": 60}
                    ],
                    "short_entry_logic": "AND",
                    "short_exit_conditions": [
                        {"indicator": "close", "operator": "<", "value": "boll_md"}
                    ],
                    "short_exit_logic": "OR",
                    "short_take_profit_pct": 12,
                    "short_stop_loss_pct": 6
                }
            }
        ]
    }


@app.post("/api/strategies")
async def save_strategy(strategy: Dict[str, Any]):
    """保存策略"""
    strategy_id = f"strategy_{uuid.uuid4().hex[:8]}"
    saved_strategies[strategy_id] = {
        "strategy_id": strategy_id,
        "strategy_name": strategy.get("strategy_name", "未命名策略"),
        "created_at": datetime.now().isoformat(),
        "config": strategy
    }
    return saved_strategies[strategy_id]


@app.get("/api/strategies")
async def list_strategies():
    """获取所有已保存的策略"""
    return {"strategies": list(saved_strategies.values())}


@app.get("/api/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """获取特定策略"""
    if strategy_id not in saved_strategies:
        raise HTTPException(status_code=404, detail="策略未找到")
    return saved_strategies[strategy_id]


@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """删除策略"""
    if strategy_id not in saved_strategies:
        raise HTTPException(status_code=404, detail="策略未找到")
    del saved_strategies[strategy_id]
    return {"message": "策略已删除"}


# ============================================================================
# 异常处理
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器错误: {str(exc)}"}
    )


# ============================================================================
# 启动服务器
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 BTC 回测系统 API 服务器")
    print("=" * 60)
    print()
    print("📊 Web UI:      http://127.0.0.1:8001/backtest.html")
    print("📖 API 文档:    http://127.0.0.1:8001/docs")
    print("🛑 停止服务:    Ctrl+C")
    print()
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )
