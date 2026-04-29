"""
压力测试脚本 - 测试GLM-4问答系统的性能
模拟多用户并发访问，测量系统性能指标
"""
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List
import json


@dataclass
class TestResult:
    """测试结果"""
    total_requests: int = 0          # 总请求数
    success_count: int = 0           # 成功数
    failed_count: int = 0            # 失败数
    response_times: List[float] = field(default_factory=list)  # 响应时间列表
    status_codes: dict = field(default_factory=dict)  # 状态码统计
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        return (self.success_count / self.total_requests * 100) if self.total_requests > 0 else 0
    
    @property
    def avg_response_time(self) -> float:
        """平均响应时间(ms)"""
        return statistics.mean(self.response_times) * 1000 if self.response_times else 0
    
    @property
    def min_response_time(self) -> float:
        """最小响应时间(ms)"""
        return min(self.response_times) * 1000 if self.response_times else 0
    
    @property
    def max_response_time(self) -> float:
        """最大响应时间(ms)"""
        return max(self.response_times) * 1000 if self.response_times else 0
    
    @property
    def p50_response_time(self) -> float:
        """P50响应时间（中位数）"""
        return statistics.median(self.response_times) * 1000 if self.response_times else 0
    
    @property
    def p95_response_time(self) -> float:
        """P95响应时间（95%的请求在这个时间内）"""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index] * 1000
    
    @property
    def p99_response_time(self) -> float:
        """P99响应时间"""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[index] * 1000
    
    @property
    def qps(self) -> float:
        """每秒查询数"""
        if not self.response_times:
            return 0
        total_time = sum(self.response_times)
        return self.success_count / total_time if total_time > 0 else 0
    
    def print_report(self):
        """打印测试报告"""
        print("\n" + "="*70)
        print("📊 压力测试报告")
        print("="*70)
        print(f"总请求数:     {self.total_requests}")
        print(f"成功请求:     {self.success_count} ({self.success_rate:.2f}%)")
        print(f"失败请求:     {self.failed_count}")
        print(f"\n响应时间统计:")
        print(f"  平均值:     {self.avg_response_time:.2f} ms")
        print(f"  最小值:     {self.min_response_time:.2f} ms")
        print(f"  最大值:     {self.max_response_time:.2f} ms")
        print(f"  P50:        {self.p50_response_time:.2f} ms")
        print(f"  P95:        {self.p95_response_time:.2f} ms")
        print(f"  P99:        {self.p99_response_time:.2f} ms")
        print(f"\n吞吐量:")
        print(f"  QPS:        {self.qps:.2f} 请求/秒")
        print(f"\n状态码分布:")
        for code, count in sorted(self.status_codes.items()):
            print(f"  {code}: {count}")
        print("="*70)


def test_single_request(session_id: str, base_url: str) -> tuple:
    """
    发送单个请求
    
    Returns:
        (status_code, response_time, success)
    """
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/api/chatbot",
            json={
                "infos": "你好，请介绍一下自己",
                "session_id": session_id
            },
            timeout=30
        )
        elapsed = time.time() - start_time
        return response.status_code, elapsed, response.status_code == 200
    except Exception as e:
        elapsed = time.time() - start_time
        return 0, elapsed, False


def run_load_test(
    base_url: str = "http://localhost:6006",
    concurrent_users: int = 10,
    total_requests: int = 100
) -> TestResult:
    """
    运行压力测试
    
    Args:
        base_url: API基础URL
        concurrent_users: 并发用户数
        total_requests: 总请求数
    
    Returns:
        TestResult对象
    """
    print(f"\n🚀 开始压力测试")
    print(f"   目标URL: {base_url}")
    print(f"   并发用户数: {concurrent_users}")
    print(f"   总请求数: {total_requests}")
    print(f"   预计耗时: 约{total_requests/concurrent_users * 0.5:.1f}秒\n")
    
    result = TestResult()
    result.total_requests = total_requests
    
    start_time = time.time()
    
    # 使用线程池模拟并发
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = []
        
        for i in range(total_requests):
            session_id = f"load_test_user_{i % concurrent_users}"
            future = executor.submit(test_single_request, session_id, base_url)
            futures.append(future)
        
        # 收集结果
        for future in as_completed(futures):
            status_code, response_time, success = future.result()
            
            result.response_times.append(response_time)
            result.status_codes[status_code] = result.status_codes.get(status_code, 0) + 1
            
            if success:
                result.success_count += 1
            else:
                result.failed_count += 1
    
    total_elapsed = time.time() - start_time
    
    print(f"\n✅ 测试完成！总耗时: {total_elapsed:.2f}秒")
    
    return result


def test_different_concurrency_levels(base_url: str = "http://localhost:6006"):
    """
    测试不同并发级别下的性能表现
    """
    print("\n" + "="*70)
    print("📈 多级别并发测试")
    print("="*70)
    
    concurrency_levels = [5, 10, 20, 50, 100]
    requests_per_level = 50
    
    results = {}
    
    for concurrency in concurrency_levels:
        print(f"\n{'─'*70}")
        print(f"测试并发级别: {concurrency} 个用户")
        print(f"{'─'*70}")
        
        result = run_load_test(base_url, concurrency, requests_per_level)
        results[concurrency] = result
        
        # 打印简要结果
        print(f"\n简要结果:")
        print(f"  成功率: {result.success_rate:.2f}%")
        print(f"  平均响应时间: {result.avg_response_time:.2f}ms")
        print(f"  P95响应时间: {result.p95_response_time:.2f}ms")
        print(f"  QPS: {result.qps:.2f}")
        
        # 性能评估
        if result.avg_response_time < 500:
            print(f"  评级: ✅ 优秀")
        elif result.avg_response_time < 1000:
            print(f"  评级: ⚠️  良好")
        elif result.avg_response_time < 3000:
            print(f"  评级: ❌ 较慢")
        else:
            print(f"  评级: 💥 过慢")
    
    # 汇总对比
    print("\n" + "="*70)
    print("📊 性能对比汇总")
    print("="*70)
    print(f"{'并发数':<10} {'成功率':<10} {'平均RT':<12} {'P95 RT':<12} {'QPS':<10} {'评级'}")
    print("-"*70)
    
    for concurrency in concurrency_levels:
        r = results[concurrency]
        if r.avg_response_time < 500:
            rating = "✅ 优秀"
        elif r.avg_response_time < 1000:
            rating = "⚠️  良好"
        elif r.avg_response_time < 3000:
            rating = "❌ 较慢"
        else:
            rating = "💥 过慢"
        
        print(f"{concurrency:<10} {r.success_rate:<9.2f}% {r.avg_response_time:<11.2f}ms "
              f"{r.p95_response_time:<11.2f}ms {r.qps:<9.2f} {rating}")
    
    print("="*70)
    
    return results


def test_stability(base_url: str = "http://localhost:6006", duration_seconds: int = 60):
    """
    稳定性测试 - 持续压测一段时间
    
    Args:
        base_url: API基础URL
        duration_seconds: 测试持续时间（秒）
    """
    print(f"\n🔍 开始稳定性测试")
    print(f"   持续时间: {duration_seconds}秒")
    print(f"   并发用户: 10")
    print(f"   开始时间: {time.strftime('%H:%M:%S')}\n")
    
    result = TestResult()
    start_time = time.time()
    request_count = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        while time.time() - start_time < duration_seconds:
            futures = []
            for i in range(10):
                session_id = f"stability_test_{request_count}_{i}"
                future = executor.submit(test_single_request, session_id, base_url)
                futures.append(future)
                request_count += 1
            
            for future in as_completed(futures):
                status_code, response_time, success = future.result()
                result.response_times.append(response_time)
                result.status_codes[status_code] = result.status_codes.get(status_code, 0) + 1
                
                if success:
                    result.success_count += 1
                else:
                    result.failed_count += 1
            
            result.total_requests = len(result.response_times)
            
            # 每10秒输出一次进度
            elapsed = time.time() - start_time
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                current_qps = result.success_count / elapsed if elapsed > 0 else 0
                print(f"  [{int(elapsed):3d}s] 已完成: {result.total_requests:5d} 请求 | "
                      f"成功率: {result.success_rate:5.1f}% | "
                      f"QPS: {current_qps:6.2f}")
    
    print(f"\n✅ 稳定性测试完成！")
    result.print_report()
    
    # 稳定性评估
    print("\n💡 稳定性分析:")
    if result.success_rate >= 99.5:
        print("  ✅ 成功率极高，系统稳定")
    elif result.success_rate >= 95:
        print("  ⚠️  成功率良好，但有少量失败")
    else:
        print("  ❌ 成功率较低，系统不稳定")
    
    if result.p95_response_time < 1000:
        print("  ✅ P95响应时间优秀")
    elif result.p95_response_time < 3000:
        print("  ⚠️  P95响应时间可接受")
    else:
        print("  ❌ P95响应时间过长")


if __name__ == "__main__":
    import sys
    
    # 从命令行参数获取配置
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:6006"
    
    print("="*70)
    print("🎯 GLM-4 问答系统 - 压力测试工具")
    print("="*70)
    print(f"\n请选择测试模式:")
    print("  1. 单次压力测试（默认10并发，100请求）")
    print("  2. 多级别并发测试（5/10/20/50/100并发）")
    print("  3. 稳定性测试（持续60秒）")
    print("  4. 自定义测试")
    
    choice = input("\n请输入选择 (1-4，默认1): ").strip() or "1"
    
    if choice == "1":
        concurrent = input("并发用户数 (默认10): ").strip()
        total = input("总请求数 (默认100): ").strip()
        
        concurrent_users = int(concurrent) if concurrent else 10
        total_requests = int(total) if total else 100
        
        result = run_load_test(base_url, concurrent_users, total_requests)
        result.print_report()
    
    elif choice == "2":
        test_different_concurrency_levels(base_url)
    
    elif choice == "3":
        duration = input("测试时长（秒，默认60）: ").strip()
        duration_seconds = int(duration) if duration else 60
        test_stability(base_url, duration_seconds)
    
    elif choice == "4":
        print("\n自定义测试配置:")
        concurrent_users = int(input("并发用户数: "))
        total_requests = int(input("总请求数: "))
        
        result = run_load_test(base_url, concurrent_users, total_requests)
        result.print_report()
    
    else:
        print("无效选择，执行默认测试...")
        result = run_load_test(base_url, 10, 100)
        result.print_report()
