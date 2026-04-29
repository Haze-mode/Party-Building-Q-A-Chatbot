# 知识库管理接口测试脚本
# 使用方法: python test_kb_api.py

import requests
import json
import os

BASE_URL = "http://localhost:6006"
USERNAME = "admin"
PASSWORD = "admin123"

def print_section(title):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def get_token():
    """获取管理员Token"""
    print_section("1. 登录获取Token")
    
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ Token获取成功: {token[:20]}...")
        return token
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def test_get_files(token):
    """测试获取文件列表"""
    print_section("2. 获取知识库文件列表")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/kb/files", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 请求成功")
        print(f"   文件总数: {data.get('total_count', 0)}")
        print(f"\n   文件列表:")
        for file in data.get('files', []):
            print(f"   - {file['name']} ({file['size']} bytes)")
            print(f"     上传时间: {file['uploadTime']}")
            print(f"     路径: {file['path']}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"   {response.text}")

def test_reload_kb(token):
    """测试重载知识库"""
    print_section("3. 重载知识库")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{BASE_URL}/api/kb/reload",
        headers=headers,
        json={}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 知识库重载成功")
        print(f"   消息: {data.get('message')}")
        print(f"   文件数量: {data.get('file_count')}")
        print(f"   段落数量: {data.get('paragraph_count')}")
        print(f"   知识库目录: {data.get('kb_dir')}")
    else:
        print(f"❌ 重载失败: {response.status_code}")
        print(f"   {response.text}")

def test_upload_file(token):
    """测试上传文件"""
    print_section("4. 上传文件到知识库")
    
    # 创建测试文件
    test_file_path = "test_upload.txt"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件，用于测试上传功能。\n")
        f.write("测试完成后会被删除。")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(test_file_path, 'rb') as f:
            files = {'file': (test_file_path, f, 'text/plain')}
            response = requests.post(
                f"{BASE_URL}/api/kb/upload",
                headers=headers,
                files=files
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 文件上传成功")
            print(f"   消息: {data.get('message')}")
            
            # 单文件上传
            if 'file' in data:
                file_info = data['file']
                print(f"   文件名: {file_info.get('name')}")
                print(f"   文件大小: {file_info.get('size')} bytes")
                print(f"   文件路径: {file_info.get('path')}")
            # 多文件上传
            elif 'saved_files' in data:
                print(f"   保存的文件: {data.get('saved_files')}")
            
            print(f"   知识库目录: {data.get('kb_dir')}")
            print(f"   段落数量: {data.get('paragraph_count')}")
        else:
            print(f"❌ 上传失败: {response.status_code}")
            print(f"   {response.text}")
    
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"\n   🗑️  已清理测试文件: {test_file_path}")

def test_delete_file_post(token):
    """测试删除文件（POST方式）"""
    print_section("5. 删除文件（POST方式）")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 先上传一个测试文件
    test_file = "test_delete.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("这个文件将被删除")
    
    try:
        # 上传
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/plain')}
            upload_response = requests.post(
                f"{BASE_URL}/api/kb/upload",
                headers={"Authorization": f"Bearer {token}"},
                files=files
            )
        
        if upload_response.status_code == 200:
            print(f"✅ 测试文件上传成功")
        
        # 删除
        delete_response = requests.post(
            f"{BASE_URL}/api/kb/files/delete",
            headers=headers,
            json={"file_name": test_file}
        )
        
        if delete_response.status_code == 200:
            data = delete_response.json()
            print(f"✅ 文件删除成功")
            print(f"   消息: {data.get('message')}")
            print(f"   文件名: {data.get('file_name')}")
        else:
            print(f"❌ 删除失败: {delete_response.status_code}")
            print(f"   {delete_response.text}")
    
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_delete_file_delete_method(token):
    """测试删除文件（DELETE方式）"""
    print_section("6. 删除文件（DELETE方式）")
    
    from urllib.parse import quote
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 先上传一个测试文件
    test_file = "test_delete_method.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("这个文件将通过DELETE方法删除")
    
    try:
        # 上传
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/plain')}
            upload_response = requests.post(
                f"{BASE_URL}/api/kb/upload",
                headers={"Authorization": f"Bearer {token}"},
                files=files
            )
        
        if upload_response.status_code == 200:
            print(f"✅ 测试文件上传成功")
        
        # 删除（URL编码文件名）
        encoded_filename = quote(test_file, safe='')
        delete_response = requests.delete(
            f"{BASE_URL}/api/kb/files/{encoded_filename}",
            headers=headers
        )
        
        if delete_response.status_code == 200:
            data = delete_response.json()
            print(f"✅ 文件删除成功（DELETE方法）")
            print(f"   消息: {data.get('message')}")
            print(f"   文件名: {data.get('file_name')}")
        else:
            print(f"❌ 删除失败: {delete_response.status_code}")
            print(f"   {delete_response.text}")
    
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_permission_denied():
    """测试权限不足"""
    print_section("7. 测试权限控制（普通用户）")
    
    # 使用普通用户登录
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": "user", "password": "user123"}
    )
    
    if response.status_code == 200:
        token = response.json().get('token')
        print(f"✅ 普通用户登录成功")
        
        # 尝试访问需要管理员权限的接口
        headers = {"Authorization": f"Bearer {token}"}
        kb_response = requests.get(f"{BASE_URL}/api/kb/files", headers=headers)
        
        if kb_response.status_code == 403:
            print(f"✅ 权限控制正常: 普通用户被拒绝访问")
            print(f"   响应: {kb_response.json()}")
        else:
            print(f"⚠️  权限控制异常: {kb_response.status_code}")
    else:
        print(f"❌ 普通用户登录失败")

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("  知识库管理接口测试")
    print("="*60)
    
    # 获取Token
    token = get_token()
    if not token:
        print("\n❌ 无法获取Token，测试终止")
        return
    
    # 执行测试
    test_get_files(token)
    test_reload_kb(token)
    test_upload_file(token)
    test_delete_file_post(token)
    test_delete_file_delete_method(token)
    test_permission_denied()
    
    print_section("测试完成")
    print("✅ 所有测试已完成！\n")

if __name__ == "__main__":
    main()
