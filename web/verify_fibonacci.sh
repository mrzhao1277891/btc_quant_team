#!/bin/bash

echo "=========================================="
echo "斐波那契回调位卡片集成验证"
echo "=========================================="
echo ""

# Check if HTTP server is running
echo "1. 检查 HTTP 服务器..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/dashboard.html | grep -q "200"; then
    echo "   ✅ HTTP 服务器运行正常 (http://localhost:8080)"
else
    echo "   ❌ HTTP 服务器未运行"
    exit 1
fi
echo ""

# Check if FastAPI backend is running
echo "2. 检查 FastAPI 后端..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/latest | grep -q "200"; then
    echo "   ✅ FastAPI 后端运行正常 (http://127.0.0.1:8000)"
else
    echo "   ❌ FastAPI 后端未运行"
    exit 1
fi
echo ""

# Check if FibonacciCalculator.js exists
echo "3. 检查 FibonacciCalculator.js..."
if [ -f "components/FibonacciCalculator.js" ]; then
    echo "   ✅ FibonacciCalculator.js 存在"
    # Check syntax
    if node -c components/FibonacciCalculator.js 2>/dev/null; then
        echo "   ✅ JavaScript 语法正确"
    else
        echo "   ❌ JavaScript 语法错误"
        exit 1
    fi
else
    echo "   ❌ FibonacciCalculator.js 不存在"
    exit 1
fi
echo ""

# Check if CardRenderer.js has Fibonacci integration
echo "4. 检查 CardRenderer.js 集成..."
if grep -q "FibonacciCalculator" components/CardRenderer.js; then
    echo "   ✅ CardRenderer.js 已导入 FibonacciCalculator"
else
    echo "   ❌ CardRenderer.js 未导入 FibonacciCalculator"
    exit 1
fi

if grep -q "_drawFibonacciLevels" components/CardRenderer.js; then
    echo "   ✅ CardRenderer.js 包含 _drawFibonacciLevels 方法"
else
    echo "   ❌ CardRenderer.js 缺少 _drawFibonacciLevels 方法"
    exit 1
fi
echo ""

# Check if dashboard.html has Fibonacci card
echo "5. 检查 dashboard.html 配置..."
if grep -q "fibonacciCard" dashboard.html; then
    echo "   ✅ dashboard.html 包含斐波那契卡片HTML"
else
    echo "   ❌ dashboard.html 缺少斐波那契卡片HTML"
    exit 1
fi

if grep -q "fibonacciCardConfig" dashboard.html; then
    echo "   ✅ dashboard.html 包含 fibonacciCardConfig"
else
    echo "   ❌ dashboard.html 缺少 fibonacciCardConfig"
    exit 1
fi

if grep -q "fibEditModal" dashboard.html; then
    echo "   ✅ dashboard.html 包含编辑模态框"
else
    echo "   ❌ dashboard.html 缺少编辑模态框"
    exit 1
fi

if grep -q "loadFibonacciParams" dashboard.html; then
    echo "   ✅ dashboard.html 包含参数加载函数"
else
    echo "   ❌ dashboard.html 缺少参数加载函数"
    exit 1
fi
echo ""

# Check if dashboard.css has Fibonacci styles
echo "6. 检查 dashboard.css 样式..."
if grep -q ".fib-modal" dashboard.css; then
    echo "   ✅ dashboard.css 包含模态框样式"
else
    echo "   ❌ dashboard.css 缺少模态框样式"
    exit 1
fi

if grep -q ".edit-btn" dashboard.css; then
    echo "   ✅ dashboard.css 包含编辑按钮样式"
else
    echo "   ❌ dashboard.css 缺少编辑按钮样式"
    exit 1
fi

if grep -q ".fib-input-group" dashboard.css; then
    echo "   ✅ dashboard.css 包含输入组样式"
else
    echo "   ❌ dashboard.css 缺少输入组样式"
    exit 1
fi
echo ""

# Check if test files exist
echo "7. 检查测试文件..."
if [ -f "test_fibonacci.html" ]; then
    echo "   ✅ test_fibonacci.html 存在"
else
    echo "   ⚠️  test_fibonacci.html 不存在（可选）"
fi

if [ -f "test_integration.html" ]; then
    echo "   ✅ test_integration.html 存在"
else
    echo "   ⚠️  test_integration.html 不存在（可选）"
fi
echo ""

echo "=========================================="
echo "✅ 所有核心功能验证通过！"
echo "=========================================="
echo ""
echo "访问方式："
echo "  主仪表盘: http://localhost:8080/dashboard.html"
echo "  单元测试: http://localhost:8080/test_fibonacci.html"
echo "  集成测试: http://localhost:8080/test_integration.html"
echo ""
echo "使用说明："
echo "  1. 打开主仪表盘"
echo "  2. 找到第5个卡片「斐波那契回调位」"
echo "  3. 点击右上角的「⚙️ 编辑」按钮"
echo "  4. 为4个周期设置高点、低点和方向"
echo "  5. 点击「确认」保存参数"
echo "  6. 查看斐波那契回调位以点的形式显示"
echo ""
