"""性能测试脚本 - 测试缓存效果"""
import requests
import time

BASE_URL = "http://localhost:6006"

# 登录获取token
r = requests.post(f"{BASE_URL}/api/login", json={
    'username': 'admin',
    'password': 'admin123'
})
token = r.json()['token']
print("✅ Token获取成功\n")

# 测试问题
question = "Python是什么"

print("="*60)
print("第1次请求（缓存未命中）")
print("="*60)
start = time.time()
r1 = requests.post(f"{BASE_URL}/api/chatbot", 
    headers={'Authorization': f'Bearer {token}'},
    json={'infos': question, 'session_id': 'perf_test'}
)
t1 = time.time() - start
data1 = r1.json()
print(f"⏱️  耗时: {t1:.3f}s")
print(f"📦 缓存命中: {data1.get('from_cache', False)}")
print(f"📝 回答长度: {len(data1.get('answer', ''))} 字符\n")

print("="*60)
print("第2次请求（应该缓存命中）")
print("="*60)
start = time.time()
r2 = requests.post(f"{BASE_URL}/api/chatbot",
    headers={'Authorization': f'Bearer {token}'},
    json={'infos': question, 'session_id': 'perf_test'}
)
t2 = time.time() - start
data2 = r2.json()
print(f"⏱️  耗时: {t2:.3f}s")
print(f"📦 缓存命中: {data2.get('from_cache', False)}")
print(f"📝 回答长度: {len(data2.get('answer', ''))} 字符\n")

print("="*60)
print("📊 性能对比")
print("="*60)
if t1 > 0:
    improvement = (t1 - t2) / t1 * 100
    speedup = t1 / t2 if t2 > 0 else float('inf')
    print(f"🚀 响应时间减少: {improvement:.1f}%")
    print(f"⚡ 速度提升: {speedup:.1f}x")
    print(f"💾 第1次: {t1*1000:.1f}ms → 第2次: {t2*1000:.1f}ms")
