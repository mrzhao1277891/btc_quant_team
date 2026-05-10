// ============================================================================
// BTC 回测系统 - 前端逻辑
// ============================================================================

const API_BASE = 'http://127.0.0.1:8001/api';

let indicators = [];
let templates = [];
let currentBacktestId = null;
let currentResults = null;

// ============================================================================
// 初始化
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 初始化回测系统...');
    
    // 加载指标列表
    await loadIndicators();
    
    // 加载策略模板
    await loadTemplates();
    
    // 设置默认日期
    setDefaultDates();
    
    // 添加初始条件（双向策略）
    addLongEntryCondition();
    addShortEntryCondition();
    addLongExitCondition();
    addShortExitCondition();
    
    console.log('✅ 初始化完成');
});

// ============================================================================
// 数据加载
// ============================================================================

async function loadIndicators() {
    try {
        const response = await fetch(`${API_BASE}/indicators`);
        const data = await response.json();
        indicators = data.indicators;
        console.log(`✅ 加载了 ${indicators.length} 个指标`);
    } catch (error) {
        console.error('❌ 加载指标失败:', error);
        showError('加载指标失败');
    }
}

async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE}/strategy-templates`);
        const data = await response.json();
        templates = data.templates;
        
        // 填充模板下拉菜单
        const select = document.getElementById('templateSelect');
        templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = `${template.name} - ${template.description}`;
            select.appendChild(option);
        });
        
        // 监听模板选择
        select.addEventListener('change', (e) => {
            if (e.target.value) {
                loadTemplate(e.target.value);
            }
        });
        
        console.log(`✅ 加载了 ${templates.length} 个模板`);
    } catch (error) {
        console.error('❌ 加载模板失败:', error);
    }
}

function setDefaultDates() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 3); // 默认3个月
    
    document.getElementById('startDate').valueAsDate = startDate;
    document.getElementById('endDate').valueAsDate = endDate;
}

// ============================================================================
// 条件管理
// ============================================================================

function addLongEntryCondition() {
    const container = document.getElementById('longEntryConditions');
    const conditionHtml = createConditionHtml('longEntry');
    container.insertAdjacentHTML('beforeend', conditionHtml);
}

function addShortEntryCondition() {
    const container = document.getElementById('shortEntryConditions');
    const conditionHtml = createConditionHtml('shortEntry');
    container.insertAdjacentHTML('beforeend', conditionHtml);
}

function addLongExitCondition() {
    const container = document.getElementById('longExitConditions');
    const conditionHtml = createConditionHtml('longExit');
    container.insertAdjacentHTML('beforeend', conditionHtml);
}

function addShortExitCondition() {
    const container = document.getElementById('shortExitConditions');
    const conditionHtml = createConditionHtml('shortExit');
    container.insertAdjacentHTML('beforeend', conditionHtml);
}

function createConditionHtml(type) {
    const id = `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const indicatorOptions = indicators.map(ind => 
        `<option value="${ind.name}">${ind.label}</option>`
    ).join('');
    
    return `
        <div class="condition-item" id="${id}">
            <select class="indicator-select">
                ${indicatorOptions}
            </select>
            <select class="operator-select">
                <option value=">">></option>
                <option value="<"><</option>
                <option value=">=">>=</option>
                <option value="<="><=</option>
                <option value="==">==</option>
                <option value="!=">!=</option>
            </select>
            <input type="text" class="value-input" placeholder="值或指标名">
            <button type="button" class="btn-remove" onclick="removeCondition('${id}')">×</button>
        </div>
    `;
}

function removeCondition(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// ============================================================================
// 模板加载
// ============================================================================

function loadTemplate(templateId) {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    
    const config = template.config;
    
    // 基本设置
    document.getElementById('strategyName').value = template.name;
    document.getElementById('timeframe').value = config.timeframe;
    // 只在模板有 position_size 时才设置（否则保持用户输入的值）
    if (config.position_size !== undefined) {
        document.getElementById('positionSize').value = config.position_size;
    }
    
    // 检测是否为双向策略模板
    const isDualDirection = config.long_entry_conditions || config.short_entry_conditions;
    
    if (isDualDirection) {
        // 双向策略模板
        
        // 清空所有条件容器
        const longEntryContainer = document.getElementById('longEntryConditions');
        const shortEntryContainer = document.getElementById('shortEntryConditions');
        const longExitContainer = document.getElementById('longExitConditions');
        const shortExitContainer = document.getElementById('shortExitConditions');
        
        if (longEntryContainer) longEntryContainer.innerHTML = '';
        if (shortEntryContainer) shortEntryContainer.innerHTML = '';
        if (longExitContainer) longExitContainer.innerHTML = '';
        if (shortExitContainer) shortExitContainer.innerHTML = '';
        
        // 加载做多开仓条件
        if (config.long_entry_conditions && config.long_entry_conditions.length > 0) {
            config.long_entry_conditions.forEach(cond => {
                addLongEntryCondition();
                const container = document.getElementById('longEntryConditions');
                const lastCondition = container.lastElementChild;
                lastCondition.querySelector('.indicator-select').value = cond.indicator;
                lastCondition.querySelector('.operator-select').value = cond.operator;
                lastCondition.querySelector('.value-input').value = cond.value;
            });
            
            // 设置做多开仓逻辑运算符
            if (config.long_entry_logic) {
                const longEntryLogic = document.getElementById('longEntryLogic');
                if (longEntryLogic) {
                    longEntryLogic.value = config.long_entry_logic;
                }
            }
        }
        
        // 加载做空开仓条件
        if (config.short_entry_conditions && config.short_entry_conditions.length > 0) {
            config.short_entry_conditions.forEach(cond => {
                addShortEntryCondition();
                const container = document.getElementById('shortEntryConditions');
                const lastCondition = container.lastElementChild;
                lastCondition.querySelector('.indicator-select').value = cond.indicator;
                lastCondition.querySelector('.operator-select').value = cond.operator;
                lastCondition.querySelector('.value-input').value = cond.value;
            });
            
            // 设置做空开仓逻辑运算符
            if (config.short_entry_logic) {
                const shortEntryLogic = document.getElementById('shortEntryLogic');
                if (shortEntryLogic) {
                    shortEntryLogic.value = config.short_entry_logic;
                }
            }
        }
        
        // 加载做多平仓条件
        if (config.long_exit_conditions && config.long_exit_conditions.length > 0) {
            config.long_exit_conditions.forEach(cond => {
                addLongExitCondition();
                const container = document.getElementById('longExitConditions');
                const lastCondition = container.lastElementChild;
                lastCondition.querySelector('.indicator-select').value = cond.indicator;
                lastCondition.querySelector('.operator-select').value = cond.operator;
                lastCondition.querySelector('.value-input').value = cond.value;
            });
            
            // 设置做多平仓逻辑运算符
            if (config.long_exit_logic) {
                const longExitLogic = document.getElementById('longExitLogic');
                if (longExitLogic) {
                    longExitLogic.value = config.long_exit_logic;
                }
            }
        }
        
        // 加载做空平仓条件
        if (config.short_exit_conditions && config.short_exit_conditions.length > 0) {
            config.short_exit_conditions.forEach(cond => {
                addShortExitCondition();
                const container = document.getElementById('shortExitConditions');
                const lastCondition = container.lastElementChild;
                lastCondition.querySelector('.indicator-select').value = cond.indicator;
                lastCondition.querySelector('.operator-select').value = cond.operator;
                lastCondition.querySelector('.value-input').value = cond.value;
            });
            
            // 设置做空平仓逻辑运算符
            if (config.short_exit_logic) {
                const shortExitLogic = document.getElementById('shortExitLogic');
                if (shortExitLogic) {
                    shortExitLogic.value = config.short_exit_logic;
                }
            }
        }
        
        // 加载做多止盈止损百分比
        if (config.long_take_profit_pct !== undefined) {
            const longTakeProfitPct = document.getElementById('longTakeProfitPct');
            if (longTakeProfitPct) {
                longTakeProfitPct.value = config.long_take_profit_pct;
            }
        }
        if (config.long_stop_loss_pct !== undefined) {
            const longStopLossPct = document.getElementById('longStopLossPct');
            if (longStopLossPct) {
                longStopLossPct.value = config.long_stop_loss_pct;
            }
        }
        
        // 加载做空止盈止损百分比
        if (config.short_take_profit_pct !== undefined) {
            const shortTakeProfitPct = document.getElementById('shortTakeProfitPct');
            if (shortTakeProfitPct) {
                shortTakeProfitPct.value = config.short_take_profit_pct;
            }
        }
        if (config.short_stop_loss_pct !== undefined) {
            const shortStopLossPct = document.getElementById('shortStopLossPct');
            if (shortStopLossPct) {
                shortStopLossPct.value = config.short_stop_loss_pct;
            }
        }
        
    } else {
        // 单向策略模板（向后兼容）
        
        // 设置持仓方向（如果存在单选框）
        if (config.position_side) {
            const positionSideRadio = document.querySelector(`input[name="positionSide"][value="${config.position_side}"]`);
            if (positionSideRadio) {
                positionSideRadio.checked = true;
            }
        }
    }
    
    showSuccess(`已加载模板: ${template.name}`);
}

// ============================================================================
// 回测执行
// ============================================================================

async function runBacktest() {
    try {
        // 验证表单
        if (!validateForm()) {
            return;
        }
        
        // 收集表单数据
        const request = collectFormData();
        
        // 显示加载状态
        showLoading();
        
        // 提交回测请求
        const response = await fetch(`${API_BASE}/backtest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(request)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        currentBacktestId = data.backtest_id;
        
        console.log(`✅ 回测已提交: ${currentBacktestId}`);
        
        // 轮询回测状态
        await pollBacktestStatus(currentBacktestId);
        
    } catch (error) {
        console.error('❌ 回测失败:', error);
        showError(`回测失败: ${error.message}`);
        hideLoading();
    }
}

function validateForm() {
    const strategyName = document.getElementById('strategyName').value.trim();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (!strategyName) {
        showError('请输入策略名称');
        return false;
    }
    
    if (!startDate || !endDate) {
        showError('请选择回测日期范围');
        return false;
    }
    
    if (new Date(startDate) >= new Date(endDate)) {
        showError('开始日期必须早于结束日期');
        return false;
    }
    
    // 收集双向策略的开仓条件
    const longEntryConditions = collectConditions('longEntryConditions');
    const shortEntryConditions = collectConditions('shortEntryConditions');
    
    // 验证至少配置了一个方向的开仓条件
    if (longEntryConditions.length === 0 && shortEntryConditions.length === 0) {
        showError('请至少配置一个方向的开仓条件（做多或做空）');
        return false;
    }
    
    // 验证做多开仓条件的完整性
    if (!validateConditions(longEntryConditions, '做多开仓条件')) {
        return false;
    }
    
    // 验证做空开仓条件的完整性
    if (!validateConditions(shortEntryConditions, '做空开仓条件')) {
        return false;
    }
    
    // 验证做多平仓条件的完整性
    const longExitConditions = collectConditions('longExitConditions');
    if (!validateConditions(longExitConditions, '做多平仓条件')) {
        return false;
    }
    
    // 验证做空平仓条件的完整性
    const shortExitConditions = collectConditions('shortExitConditions');
    if (!validateConditions(shortExitConditions, '做空平仓条件')) {
        return false;
    }
    
    // 验证做多止盈止损百分比
    const longTakeProfitPct = parseFloatOrNull(safeGetElementValue('longTakeProfitPct'));
    const longStopLossPct = parseFloatOrNull(safeGetElementValue('longStopLossPct'));
    
    if (longTakeProfitPct !== null && longTakeProfitPct <= 0) {
        showError('做多止盈百分比必须为正数');
        return false;
    }
    
    if (longStopLossPct !== null && longStopLossPct <= 0) {
        showError('做多止损百分比必须为正数');
        return false;
    }
    
    // 验证做空止盈止损百分比
    const shortTakeProfitPct = parseFloatOrNull(safeGetElementValue('shortTakeProfitPct'));
    const shortStopLossPct = parseFloatOrNull(safeGetElementValue('shortStopLossPct'));
    
    if (shortTakeProfitPct !== null && shortTakeProfitPct <= 0) {
        showError('做空止盈百分比必须为正数');
        return false;
    }
    
    if (shortStopLossPct !== null && shortStopLossPct <= 0) {
        showError('做空止损百分比必须为正数');
        return false;
    }
    
    return true;
}

/**
 * 验证条件列表的完整性
 * @param {Array} conditions - 条件数组
 * @param {string} conditionType - 条件类型名称（用于错误提示）
 * @returns {boolean} - 验证是否通过
 */
function validateConditions(conditions, conditionType) {
    for (let i = 0; i < conditions.length; i++) {
        const condition = conditions[i];
        
        // 验证指标不能为空
        if (!condition.indicator || condition.indicator.trim() === '') {
            showError(`${conditionType}的第 ${i + 1} 个条件：指标不能为空`);
            return false;
        }
        
        // 验证运算符不能为空
        if (!condition.operator || condition.operator.trim() === '') {
            showError(`${conditionType}的第 ${i + 1} 个条件：运算符不能为空`);
            return false;
        }
        
        // 验证值不能为空
        if (condition.value === null || condition.value === undefined || condition.value === '') {
            showError(`${conditionType}的第 ${i + 1} 个条件：值不能为空`);
            return false;
        }
    }
    
    return true;
}

function collectFormData() {
    const data = {
        strategy_name: document.getElementById('strategyName').value.trim(),
        timeframe: document.getElementById('timeframe').value,
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value,
        initial_capital: parseFloat(document.getElementById('initialCapital').value),
        position_size: parseFloat(document.getElementById('positionSize').value),
        position_size_type: document.getElementById('positionSizeType').value,
        leverage: parseFloat(document.getElementById('leverage').value) || 5.0  // 读取杠杆值，默认5倍
    };
    
    // 收集双向策略的新字段
    const longEntryConditions = collectConditions('longEntryConditions');
    const shortEntryConditions = collectConditions('shortEntryConditions');
    const longExitConditions = collectConditions('longExitConditions');
    const shortExitConditions = collectConditions('shortExitConditions');
    
    // 如果配置了做多开仓条件
    if (longEntryConditions.length > 0) {
        data.long_entry_conditions = longEntryConditions;
        data.long_entry_logic = document.getElementById('longEntryLogic').value;
    }
    
    // 如果配置了做空开仓条件
    if (shortEntryConditions.length > 0) {
        data.short_entry_conditions = shortEntryConditions;
        data.short_entry_logic = document.getElementById('shortEntryLogic').value;
    }
    
    // 如果配置了做多平仓条件
    if (longExitConditions.length > 0) {
        data.long_exit_conditions = longExitConditions;
        data.long_exit_logic = document.getElementById('longExitLogic').value;
    }
    
    // 做多止盈止损
    const longTakeProfitPct = parseFloatOrNull(safeGetElementValue('longTakeProfitPct'));
    const longStopLossPct = parseFloatOrNull(safeGetElementValue('longStopLossPct'));
    if (longTakeProfitPct !== null) {
        data.long_take_profit_pct = longTakeProfitPct;
    }
    if (longStopLossPct !== null) {
        data.long_stop_loss_pct = longStopLossPct;
    }
    
    // 如果配置了做空平仓条件
    if (shortExitConditions.length > 0) {
        data.short_exit_conditions = shortExitConditions;
        data.short_exit_logic = document.getElementById('shortExitLogic').value;
    }
    
    // 做空止盈止损
    const shortTakeProfitPct = parseFloatOrNull(safeGetElementValue('shortTakeProfitPct'));
    const shortStopLossPct = parseFloatOrNull(safeGetElementValue('shortStopLossPct'));
    if (shortTakeProfitPct !== null) {
        data.short_take_profit_pct = shortTakeProfitPct;
    }
    if (shortStopLossPct !== null) {
        data.short_stop_loss_pct = shortStopLossPct;
    }
    
    return data;
}

function collectConditions(containerId) {
    const container = document.getElementById(containerId);
    const conditions = [];
    
    // 如果容器不存在，返回空数组
    if (!container) {
        return conditions;
    }
    
    container.querySelectorAll('.condition-item').forEach(item => {
        const indicator = item.querySelector('.indicator-select').value;
        const operator = item.querySelector('.operator-select').value;
        let value = item.querySelector('.value-input').value.trim();
        
        // 尝试转换为数字
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
            value = numValue;
        }
        
        conditions.push({ indicator, operator, value });
    });
    
    return conditions;
}

function parseFloatOrNull(value) {
    if (value === null || value === undefined || value === '') {
        return null;
    }
    const num = parseFloat(value);
    return isNaN(num) ? null : num;
}

/**
 * 安全地获取元素的值，如果元素不存在则返回空字符串
 */
function safeGetElementValue(elementId) {
    const element = document.getElementById(elementId);
    return element ? element.value : '';
}

// ============================================================================
// 状态轮询
// ============================================================================

async function pollBacktestStatus(backtestId) {
    const maxAttempts = 60; // 最多轮询60次
    let attempts = 0;
    
    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE}/backtest/${backtestId}/status`);
            const data = await response.json();
            
            console.log(`📊 回测状态: ${data.status} (${data.progress || 0}%)`);
            
            // 更新进度条
            updateProgress(data.progress || 0);
            
            if (data.status === 'completed') {
                // 回测完成，获取结果
                await loadBacktestResults(backtestId);
                return;
            } else if (data.status === 'failed') {
                throw new Error(data.error || '回测失败');
            } else if (data.status === 'running' || data.status === 'queued') {
                // 继续轮询
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(poll, 1000); // 1秒后再次轮询
                } else {
                    throw new Error('回测超时');
                }
            }
        } catch (error) {
            console.error('❌ 轮询状态失败:', error);
            showError(`获取回测状态失败: ${error.message}`);
            hideLoading();
        }
    };
    
    poll();
}

async function loadBacktestResults(backtestId) {
    try {
        const response = await fetch(`${API_BASE}/backtest/${backtestId}/results`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        currentResults = data;
        
        console.log('✅ 回测结果已加载');
        
        // 显示结果
        displayResults(data);
        hideLoading();
        
    } catch (error) {
        console.error('❌ 加载结果失败:', error);
        showError(`加载结果失败: ${error.message}`);
        hideLoading();
    }
}

// ============================================================================
// 结果显示
// ============================================================================

function displayResults(data) {
    const metrics = data.performance_metrics;
    
    // 显示结果面板
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('resultsContent').style.display = 'block';
    
    // 更新性能指标
    updateMetricCard('totalReturn', metrics.total_return, metrics.total_return_pct);
    updateMetricCard('winRate', metrics.win_rate, `${metrics.total_trades} 笔交易`);
    updateMetricCard('maxDrawdown', metrics.max_drawdown_pct);  // 使用百分比字段
    updateMetricCard('sharpeRatio', metrics.sharpe_ratio);
    
    // 绘制图表
    drawEquityChart(data.trades, data.initial_capital);
    
    // 显示交易记录
    displayTrades(data.trades);
    
    showSuccess('回测完成！');
}

function updateMetricCard(id, value, subValue = null) {
    const element = document.getElementById(id);
    
    if (id === 'totalReturn') {
        element.textContent = `$${value.toFixed(2)}`;
        element.className = 'metric-value ' + (value >= 0 ? 'positive' : 'negative');
        if (subValue !== null) {
            document.getElementById('totalReturnPct').textContent = `${subValue.toFixed(2)}%`;
        }
    } else if (id === 'winRate') {
        // 后端返回的是小数形式（0.61 = 61%），需要乘以100
        element.textContent = `${(value * 100).toFixed(2)}%`;
        if (subValue) {
            document.getElementById('tradeCount').textContent = subValue;
        }
    } else if (id === 'maxDrawdown') {
        // 后端返回的是小数形式（0.15 = 15%），需要乘以100
        element.textContent = `${(value * 100).toFixed(2)}%`;
        element.className = 'metric-value negative';
    } else if (id === 'sharpeRatio') {
        element.textContent = value.toFixed(2);
        element.className = 'metric-value ' + (value >= 1 ? 'positive' : '');
    }
}

function drawEquityChart(trades, initialCapital) {
    const ctx = document.getElementById('equityChart').getContext('2d');
    
    // 计算权益曲线数据
    const equityData = [initialCapital];
    let currentCapital = initialCapital;
    
    trades.forEach(trade => {
        currentCapital += trade.profit_loss;
        equityData.push(currentCapital);
    });
    
    // 销毁旧图表
    if (window.equityChartInstance) {
        window.equityChartInstance.destroy();
    }
    
    // 创建新图表
    window.equityChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: equityData.map((_, i) => i === 0 ? '初始' : `交易${i}`),
            datasets: [{
                label: '账户权益',
                data: equityData,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `权益: $${context.parsed.y.toFixed(2)}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: (value) => `$${value.toFixed(0)}`
                    }
                }
            }
        }
    });
}

function displayTrades(trades) {
    const tbody = document.getElementById('tradesTableBody');
    tbody.innerHTML = '';
    
    if (trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px;">没有交易记录</td></tr>';
        return;
    }
    
    // 调试：打印第一条交易记录
    if (trades.length > 0) {
        console.log('第一条交易记录:', trades[0]);
        console.log('entry_time:', trades[0].entry_time);
        console.log('exit_time:', trades[0].exit_time);
    }
    
    trades.forEach((trade, index) => {
        const row = document.createElement('tr');
        const profitClass = trade.profit_loss >= 0 ? 'profit' : 'loss';
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${formatDateTime(trade.entry_time)}</td>
            <td>$${trade.entry_price.toFixed(2)}</td>
            <td>${formatDateTime(trade.exit_time)}</td>
            <td>$${trade.exit_price.toFixed(2)}</td>
            <td>${trade.direction === 'long' ? '做多' : '做空'}</td>
            <td class="${profitClass}">$${trade.profit_loss.toFixed(2)}</td>
            <td class="${profitClass}">${trade.profit_loss_pct.toFixed(2)}%</td>
            <td>${formatExitReason(trade.exit_reason)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// ============================================================================
// 工具函数
// ============================================================================

function formatDateTime(timestamp) {
    if (!timestamp) return '--';
    
    try {
        // 如果是浮点数时间戳，转换为整数
        let ts = timestamp;
        if (typeof ts === 'number' || typeof ts === 'string') {
            ts = Math.floor(parseFloat(ts));
        }
        
        const date = new Date(ts);
        
        // 检查日期是否有效
        if (isNaN(date.getTime())) {
            console.warn('Invalid timestamp:', timestamp);
            return '--';
        }
        
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        console.error('Error formatting timestamp:', timestamp, error);
        return '--';
    }
}

function formatExitReason(reason) {
    const reasonMap = {
        'exit_condition': '平仓条件',
        'take_profit': '止盈',
        'stop_loss': '止损',
        'end_of_data': '数据结束'
    };
    return reasonMap[reason] || reason;
}

function showLoading() {
    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('resultsContent').style.display = 'none';
    document.getElementById('emptyState').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loadingState').style.display = 'none';
}

function updateProgress(progress) {
    document.getElementById('progressBar').style.width = `${progress}%`;
}

function showSuccess(message) {
    alert(`✅ ${message}`);
}

function showError(message) {
    alert(`❌ ${message}`);
}

// ============================================================================
// 导出功能
// ============================================================================

function exportCSV() {
    if (!currentResults || !currentResults.trades) {
        showError('没有可导出的数据');
        return;
    }
    
    const trades = currentResults.trades;
    const headers = ['#', '开仓时间', '开仓价格', '平仓时间', '平仓价格', '方向', '盈亏', '盈亏%', '原因'];
    
    let csv = headers.join(',') + '\n';
    
    trades.forEach((trade, index) => {
        const row = [
            index + 1,
            formatDateTime(trade.entry_time),
            trade.entry_price.toFixed(2),
            formatDateTime(trade.exit_time),
            trade.exit_price.toFixed(2),
            trade.position_side === 'long' ? '做多' : '做空',
            trade.profit_loss.toFixed(2),
            trade.profit_loss_pct.toFixed(2),
            formatExitReason(trade.exit_reason)
        ];
        csv += row.join(',') + '\n';
    });
    
    downloadFile(csv, 'backtest_trades.csv', 'text/csv');
    showSuccess('CSV 已导出');
}

function exportJSON() {
    if (!currentResults) {
        showError('没有可导出的数据');
        return;
    }
    
    const json = JSON.stringify(currentResults, null, 2);
    downloadFile(json, 'backtest_results.json', 'application/json');
    showSuccess('JSON 已导出');
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ============================================================================
// 其他功能
// ============================================================================

function saveStrategy() {
    if (!validateForm()) {
        return;
    }
    
    const strategyName = document.getElementById('strategyName').value.trim();
    const config = collectFormData();
    
    // 这里可以调用 API 保存策略
    // 暂时只显示成功消息
    showSuccess(`策略 "${strategyName}" 已保存`);
}

function resetForm() {
    if (confirm('确定要重置表单吗？')) {
        document.getElementById('strategyName').value = '';
        document.getElementById('initialCapital').value = '2000';
        document.getElementById('positionSize').value = '10000';
        document.getElementById('leverage').value = '5';
        document.getElementById('templateSelect').value = '';
        
        // 清空双向策略条件
        document.getElementById('longEntryConditions').innerHTML = '';
        document.getElementById('shortEntryConditions').innerHTML = '';
        document.getElementById('longExitConditions').innerHTML = '';
        document.getElementById('shortExitConditions').innerHTML = '';
        
        // 重置止盈止损
        document.getElementById('longTakeProfitPct').value = '';
        document.getElementById('longStopLossPct').value = '';
        document.getElementById('shortTakeProfitPct').value = '';
        document.getElementById('shortStopLossPct').value = '';
        
        // 添加初始条件
        addLongEntryCondition();
        addShortEntryCondition();
        addLongExitCondition();
        addShortExitCondition();
        
        setDefaultDates();
        
        showSuccess('表单已重置');
    }
}


// 持仓类型切换时更新标签
function updatePositionSizeLabel() {
    const type = document.getElementById('positionSizeType').value;
    const label = document.getElementById('positionSizeLabel');
    const input = document.getElementById('positionSize');
    const hint = document.getElementById('positionSizeHint');
    
    if (type === 'percentage') {
        label.textContent = '持仓百分比 (%)';
        input.value = '100';
        input.placeholder = '100表示全部本金';
        hint.textContent = '💡 100 = 全部本金×杠杆开仓，50 = 一半本金×杠杆开仓';
    } else {
        label.textContent = '持仓大小 (USDT)';
        input.value = '10000';
        input.placeholder = '每次开仓使用的金额';
        hint.textContent = '💡 每次开仓时使用的固定金额（USDT）';
    }
}
