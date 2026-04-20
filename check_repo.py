#!/usr/bin/env python3
"""
检查GitHub仓库是否存在
"""

import requests
import sys

token = "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"
username = "mrzhao1277891"
repo = "btc_quant_team"

url = f"https://api.github.com/repos/{username}/{repo}"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

print(f"🔍 检查仓库: {username}/{repo}")
print(f"📡 API URL: {url}")

try:
    response = requests.get(url, headers=headers, timeout=10)
    
    print(f"📊 响应状态: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 仓库存在!")
        print(f"   名称: {data.get('name')}")
        print(f"   描述: {data.get('description')}")
        print(f"   私有: {data.get('private')}")
        print(f"   URL: {data.get('html_url')}")
        print(f"   创建时间: {data.get('created_at')}")
        print(f"   更新时间: {data.get('updated_at')}")
    elif response.status_code == 404:
        print("❌ 仓库不存在 (404)")
        print("   需要先创建仓库: https://github.com/new")
        print("   名称: btc_quant_team")
        print("   描述: 专业的加密货币量化分析工程")
        print("   不要初始化任何文件")
    elif response.status_code == 403:
        print("❌ 权限被拒绝 (403)")
        print("   可能原因:")
        print("   1. Token无效或已过期")
        print("   2. Token权限不足")
        print("   3. 仓库是私有的且Token无访问权限")
        print("   4. 用户被阻止访问")
    else:
        print(f"⚠️  其他错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("❌ 请求超时，检查网络连接")
except requests.exceptions.ConnectionError:
    print("❌ 连接错误，检查网络")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n💡 建议:")
print("   1. 确认仓库已创建: https://github.com/mrzhao1277891/btc_quant_team")
print("   2. 确认Token有效且有repo权限")
print("   3. 尝试使用SSH方式")