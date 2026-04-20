#!/usr/bin/env python3
"""
检查GitHub仓库文件
"""

import requests
import base64

token = "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"
username = "mrzhao1277891"
repo = "btc_quant_team"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

print("📁 检查GitHub仓库文件")
print("=" * 60)

# 检查根目录文件
url = f"https://api.github.com/repos/{username}/{repo}/contents/"

try:
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        contents = response.json()
        print(f"✅ 仓库有 {len(contents)} 个文件/目录:")
        
        for item in contents:
            item_type = "📁 目录" if item['type'] == 'dir' else "📄 文件"
            print(f"   {item_type} {item['name']} ({item['size']} bytes)")
            
            # 如果是文件，显示前几行
            if item['type'] == 'file' and item['name'] in ['README.md', '.gitignore']:
                file_url = item['url']
                file_response = requests.get(file_url, headers=headers, timeout=10)
                if file_response.status_code == 200:
                    file_data = file_response.json()
                    content = base64.b64decode(file_data['content']).decode('utf-8')
                    print(f"      内容预览: {content[:100]}...")
    
    elif response.status_code == 404:
        print("❌ 仓库目录不存在或为空")
        print("   这可能是好事 - 说明仓库是空的，可以推送")
    elif response.status_code == 403:
        print("❌ 权限被拒绝 (403)")
        error_data = response.json()
        print(f"   错误: {error_data.get('message', '未知错误')}")
    else:
        print(f"⚠️  其他错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")

except Exception as e:
    print(f"❌ 错误: {e}")

print("\n💡 分析:")
print("   如果仓库是空的 (404)，可以尝试:")
print("   1. 使用SSH方式推送")
print("   2. 检查Token是否是正确的类型")
print("   3. 确认仓库没有分支保护规则")

print("\n🔍 检查仓库页面:")
print(f"   访问: https://github.com/{username}/{repo}")
print("   查看是否有文件")