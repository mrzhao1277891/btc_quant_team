#!/usr/bin/env python3
"""
测试GitHub Token权限
"""

import requests
import sys

token = "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"

# 测试1: 检查Token基本信息
print("🔑 测试GitHub Token权限")
print("=" * 60)

url = "https://api.github.com/user"
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

try:
    # 测试用户信息
    print("1. 检查Token关联的用户...")
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"   ✅ Token有效")
        print(f"   用户: {user_data.get('login')}")
        print(f"   名称: {user_data.get('name')}")
        print(f"   ID: {user_data.get('id')}")
    else:
        print(f"   ❌ Token无效: {response.status_code}")
        print(f"   响应: {response.text[:100]}")
        sys.exit(1)
    
    # 测试2: 检查仓库权限
    print("\n2. 检查仓库权限...")
    repo_url = "https://api.github.com/repos/mrzhao1277891/btc_quant_team"
    response = requests.get(repo_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        repo_data = response.json()
        permissions = repo_data.get('permissions', {})
        print(f"   ✅ 可以访问仓库")
        print(f"   权限: {permissions}")
        
        if permissions.get('push'):
            print("   ✅ 有推送权限")
        else:
            print("   ❌ 无推送权限")
            
        if permissions.get('admin'):
            print("   ✅ 有管理权限")
    else:
        print(f"   ❌ 无法访问仓库: {response.status_code}")
    
    # 测试3: 尝试创建测试文件 (验证写入权限)
    print("\n3. 测试写入权限...")
    test_url = "https://api.github.com/repos/mrzhao1277891/btc_quant_team/contents/test_token.txt"
    
    test_data = {
        "message": "测试Token写入权限",
        "content": "dGVzdCB0b2tlbiBwZXJtaXNzaW9ucyA6KQ==",  # "test token permissions :)" in base64
        "branch": "main"
    }
    
    response = requests.put(test_url, headers=headers, json=test_data, timeout=10)
    
    if response.status_code == 201:
        print("   ✅ Token有写入权限")
        
        # 删除测试文件
        delete_data = {
            "message": "删除测试文件",
            "sha": response.json().get('content', {}).get('sha'),
            "branch": "main"
        }
        delete_response = requests.delete(test_url, headers=headers, json=delete_data, timeout=10)
        if delete_response.status_code == 200:
            print("   ✅ 已清理测试文件")
    elif response.status_code == 403:
        print("   ❌ Token无写入权限 (403)")
        error_data = response.json()
        print(f"   错误: {error_data.get('message', '未知错误')}")
    else:
        print(f"   ⚠️  写入测试返回: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
    
    # 测试4: 检查Token范围
    print("\n4. 检查Token范围...")
    # GitHub API没有直接获取token范围的方法，但我们可以通过其他方式推断
    
    # 测试repo范围
    repo_scope_test = "https://api.github.com/user/repos"
    response = requests.get(repo_scope_test, headers=headers, timeout=10)
    
    if response.status_code == 200:
        print("   ✅ Token有repo范围权限")
    else:
        print(f"   ❌ Token可能缺少repo范围: {response.status_code}")
    
except requests.exceptions.Timeout:
    print("❌ 请求超时")
except requests.exceptions.ConnectionError:
    print("❌ 连接错误")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 60)
print("📋 总结:")
print("   如果Token有写入权限但git push失败，可能是:")
print("   1. 仓库有分支保护规则")
print("   2. 需要强制推送 (仓库可能是空的)")
print("   3. 本地分支与远程不匹配")
print("   4. 网络或代理问题")

print("\n🚀 建议尝试:")
print("   1. 强制推送: git push -u origin main --force")
print("   2. 使用SSH: git remote set-url origin git@github.com:mrzhao1277891/btc_quant_team.git")
print("   3. 检查分支: git branch -a")
print("   4. 拉取更新: git pull origin main --allow-unrelated-histories")