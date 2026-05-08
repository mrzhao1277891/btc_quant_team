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
    
    // 添加初始条件
    addEntryCondition();
    addExitCondition();
    
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

function addEntryCondition() {
    const container = document.getElementById('entryConditions');
    const conditionHtml = createConditionHtml('entry');
    container.insertAdjacentHTML('beforeend', conditionHtml);
}

function addExitCondition() {
    const container = document.getElementById('exitConditions');
    const conditionHtml = createConditionHtml('exit');
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
    document.getElementById('positionSize').value = config.position_size;
    document.getElementById('positionSizeType').value = config.position_size_type;
    document.querySelector(`input[name="positionSide"][value="${config.position_side}"]`).checked = true;
    
    if (config.take_profit_pct) {
        document.getElementById('takeProfitPct').value = config.take_profit_pct;
    }
    if (config.stop_loss_pct) {
        document.getElementById('stopLossPct').value = config.stop_loss_pct;
    }
    
    // 清空现有条件
    document.getElementById('entryConditions').innerHTML = '';
    document.getElementById('exitConditions').innerHTML = '';
    
    // 添加开仓条件
    config.entry_conditions.forEach(cond => {
        addEntryCondition();
        const container = document.getElementById('entryConditions');
        const lastCondition = container.lastElementChild;
        lastCondition.querySelector('.indicator-select').value = cond.indicator;
        lastCondition.querySelector('.operator-select').value = cond.operator;
        lastCondition.querySelector('.value-input').value = cond.value;
    });
    
    // 添加平仓条件
    config.exit_conditions.forEach(cond => {
        addExitCondition();
        const container = document.getElementById('exitConditions');
        const lastCondition = container.lastElementChild;
        lastCondition.querySelector('.indicator-select').value = cond.indicator;
        lastCondition.querySelector('.operator-select').value = cond.operator;
        lastCondition.querySelector('.value-input').value = cond.value;
    });
    
    // 设置逻辑运算符
    document.getElementById('entryLogic').value = config.entry_logic;
    document.getElementById('exitLogic').value = config.exit_logic;
    
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
    
    const entryConditions = collectConditions('entryConditions');
    if (entryConditions.length === 0) {
        showError('请至少添加一个开仓条件');
        return false;
    }
    
    return true;
}

function collectFormData() {
    return {
        strategy_name: document.getElementById('strategyName').value.trim(),
        timeframe: document.getElementById('timeframe').value,
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value,
        initial_capital: parseFloat(document.getElementById('initialCapital').value),
        entry_conditions: collectConditions('entryConditions'),
        entry_logic: document.getElementById('entryLogic').value,
        exit_conditions: collectConditions('exitConditions'),
        exit_logic: document.getElementById('exitLogic').value,
        position_side: document.querySelector('input[name="positionSide"]:checked').value,
        position_size: parseFloat(document.getElementById('positionSize').value),
        position_size_type: document.getElementById('positionSizeType').value,
        take_profit_pct: parseFloatOrNull(document.getElementById('takeProfitPct').value),
        stop_loss_pct: parseFloatOrNull(document.getElementById('stopLossPct').value)
    };
}

function collectConditions(containerId) {
    const container = document.getElementById(containerId);
    const conditions = [];
    
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
    const num = parseFloat(value);
    return isNaN(num) ? null : num;
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
    updateMetricCard('maxDrawdown', metrics.max_drawdown);
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
        element.textContent = `${value.toFixed(2)}%`;
        if (subValue) {
            document.getElementById('tradeCount').textContent = subValue;
        }
    } else if (id === 'maxDrawdown') {
        element.textContent = `${value.toFixed(2)}%`;
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
    
    trades.forEach((trade, index) => {
        const row = document.createElement('tr');
        const profitClass = trade.profit_loss >= 0 ? 'profit' : 'loss';
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${formatDateTime(trade.entry_time)}</td>
            <td>$${trade.entry_price.toFixed(2)}</td>
            <td>${formatDateTime(trade.exit_time)}</td>
            <td>$${trade.exit_price.toFixed(2)}</td>
            <td>${trade.position_side === 'long' ? '做多' : '做空'}</td>
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
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
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
        document.getElementById('initialCapital').value = '10000';
        document.getElementById('positionSize').value = '10';
        document.getElementById('takeProfitPct').value = '';
        document.getElementById('stopLossPct').value = '';
        document.getElementById('templateSelect').value = '';
        
        document.getElementById('entryConditions').innerHTML = '';
        document.getElementById('exitConditions').innerHTML = '';
        
        addEntryCondition();
        addExitCondition();
        
        setDefaultDates();
        
        showSuccess('表单已重置');
    }
}
