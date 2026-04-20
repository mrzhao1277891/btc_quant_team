#!/usr/bin/env python3
"""
检查Token权限
"""

import requests

token = "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"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

print("🔑 检查Token权限")
print("=" * 60)

# 检查用户信息
try:
    response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
    if response.status_code == 200:
        user = response.json()
        print(f"✅ Token有效 - 用户: {user.get('login')}")
    else:
        print(f"❌ Token无效: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
        exit(1)
except Exception as e:
    print(f"❌ 错误: {e}")
    exit(1)

# 尝试检测Token权限
print("\n📋 尝试检测Token权限范围...")

# 测试不同权限
tests = [
    ("repo权限", "https://api.github.com/user/repos"),
    ("workflow权限", "https://api.github.com/repos/mrzhao1277891/btc_quant_team/actions/workflows"),
    ("内容写入", "https://api.github.com/repos/mrzhao1277891/btc_quant_team/contents/test.txt"),
]

for test_name, test_url in tests:
    try:
        if "contents" in test_url:
            # 对于写入测试，使用GET而不是PUT
            response = requests.get(test_url.replace("/test.txt", ""), headers=headers, timeout=10)
        else:
            response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ {test_name}: 有权限")
        elif response.status_code == 403:
            error_data = response.json()
            message = error_data.get('message', '未知错误')
            print(f"   ❌ {test_name}: 无权限 - {message}")
            
            # 检查是否需要特定scope
            if "workflow" in message.lower():
                print(f"      需要添加 'workflow' scope")
            elif "token" in message.lower() and "scope" in message.lower():
                print(f"      Token缺少必要scope")
        elif response.status_code == 404:
            print(f"   ⚠️  {test_name}: 资源不存在 (404)")
        else:
            print(f"   ⚠️  {test_name}: 状态 {response.status_code}")
    except Exception as e:
        print(f"   ❌ {test_name}: 错误 - {e}")

print("\n" + "=" * 60)
print("📋 错误分析:")
print("   错误信息: 'refusing to allow a Personal Access Token to create or update")
print("             workflow `.github/workflows/ci.yml` without `workflow` scope'")
print("")
print("🔧 解决方案:")
print("   1. 重新生成Token，添加 'workflow' scope")
print("   2. 或者临时移除 .github/workflows/ci.yml 文件")
print("   3. 推送后再添加workflow文件")

print("\n🚀 建议操作:")
print("   1. 访问: https://github.com/settings/tokens")
print("   2. 编辑或重新生成Token")
print("   3. 添加权限: ✅ repo (全部) + ✅ workflow")
print("   4. 使用新Token推送")