#!/usr/bin/env python3
"""
SQL审查结果页面功能演示脚本
"""

import requests
import json
import time
from urllib.parse import quote

# API基础URL
BASE_URL = "http://localhost:8000"

def print_separator(title):
    """打印分隔符"""
    print("\n" + "="*60)
    print(f" {title} ")
    print("="*60)

def test_health():
    """测试应用健康状态"""
    print_separator("测试应用健康状态")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 应用状态: {data['status']}")
            print(f"📱 应用名称: {data['app_name']}")
            print(f"🔢 版本: {data['version']}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")

def test_basic_pagination():
    """测试基本分页功能"""
    print_separator("测试基本分页功能")
    
    # 测试第一页
    response = requests.get(f"{BASE_URL}/api/reviews/results?page=1&page_size=3")
    if response.status_code == 200:
        data = response.json()
        print(f"📄 第1页结果:")
        print(f"   - 当前页: {data['page']}")
        print(f"   - 每页数量: {data['page_size']}")
        print(f"   - 总页数: {data['pages']}")
        print(f"   - 总记录数: {data['total']}")
        print(f"   - 本页记录数: {len(data['items'])}")
        
        if data['items']:
            first_item = data['items'][0]
            print(f"   - 第一条记录: {first_item['sql_title'][:30]}...")
    else:
        print(f"❌ 分页测试失败: {response.status_code}")

def test_database_filter():
    """测试数据库筛选功能"""
    print_separator("测试数据库筛选功能")
    
    # 先获取可用数据库列表
    response = requests.get(f"{BASE_URL}/api/reviews/databases")
    if response.status_code == 200:
        databases = response.json()
        print(f"📊 可用数据库 ({len(databases)}个):")
        for db in databases:
            print(f"   - {db['name']}")
        
        # 测试按第一个数据库筛选
        if databases:
            first_db = databases[0]['name']
            response = requests.get(f"{BASE_URL}/api/reviews/results?database_name={quote(first_db)}&page_size=2")
            if response.status_code == 200:
                data = response.json()
                print(f"\n🔍 按数据库 '{first_db}' 筛选结果:")
                print(f"   - 筛选后记录数: {data['total']}")
                for item in data['items']:
                    print(f"   - {item['sql_title'][:40]}... (数据库: {item['database_name']})")
    else:
        print(f"❌ 数据库列表获取失败: {response.status_code}")

def test_score_filter():
    """测试评分筛选功能"""
    print_separator("测试评分筛选功能")
    
    # 测试高分筛选
    response = requests.get(f"{BASE_URL}/api/reviews/results?min_score=85&page_size=3")
    if response.status_code == 200:
        data = response.json()
        print(f"⭐ 高分筛选 (≥85分) 结果:")
        print(f"   - 符合条件记录数: {data['total']}")
        for item in data['items']:
            print(f"   - {item['sql_title'][:40]}... (评分: {item['overall_score']})")
    
    # 测试评分范围筛选
    response = requests.get(f"{BASE_URL}/api/reviews/results?min_score=80&max_score=90&page_size=3")
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 评分范围筛选 (80-90分) 结果:")
        print(f"   - 符合条件记录数: {data['total']}")
        for item in data['items']:
            print(f"   - {item['sql_title'][:40]}... (评分: {item['overall_score']})")

def test_title_search():
    """测试SQL标题搜索功能"""
    print_separator("测试SQL标题搜索功能")
    
    # 测试中文搜索
    search_term = "查询"
    encoded_term = quote(search_term)
    response = requests.get(f"{BASE_URL}/api/reviews/results?sql_title={encoded_term}&page_size=3")
    if response.status_code == 200:
        data = response.json()
        print(f"🔍 标题搜索 ('{search_term}') 结果:")
        print(f"   - 匹配记录数: {data['total']}")
        for item in data['items']:
            print(f"   - {item['sql_title']}")
    else:
        print(f"❌ 标题搜索失败: {response.status_code}")

def test_complex_filter():
    """测试复合筛选功能"""
    print_separator("测试复合筛选功能")
    
    # 组合多个筛选条件
    search_term = quote("查询")
    response = requests.get(
        f"{BASE_URL}/api/reviews/results?"
        f"sql_title={search_term}&"
        f"min_score=80&"
        f"max_score=90&"
        f"page_size=5"
    )
    if response.status_code == 200:
        data = response.json()
        print(f"🎯 复合筛选结果:")
        print(f"   - 条件: 标题包含'查询' + 评分80-90分")
        print(f"   - 匹配记录数: {data['total']}")
        for item in data['items']:
            print(f"   - {item['sql_title'][:50]}... (评分: {item['overall_score']})")
    else:
        print(f"❌ 复合筛选失败: {response.status_code}")

def test_sorting():
    """测试排序功能"""
    print_separator("测试排序功能")
    
    # 按评分升序排列
    response = requests.get(f"{BASE_URL}/api/reviews/results?order_by=overall_score&order_dir=asc&page_size=3")
    if response.status_code == 200:
        data = response.json()
        print(f"📈 按评分升序排列:")
        for item in data['items']:
            print(f"   - 评分: {item['overall_score']} | {item['sql_title'][:40]}...")
    
    # 按评分降序排列
    response = requests.get(f"{BASE_URL}/api/reviews/results?order_by=overall_score&order_dir=desc&page_size=3")
    if response.status_code == 200:
        data = response.json()
        print(f"\n📉 按评分降序排列:")
        for item in data['items']:
            print(f"   - 评分: {item['overall_score']} | {item['sql_title'][:40]}...")

def show_detailed_result():
    """展示详细的审查结果"""
    print_separator("展示详细审查结果")
    
    response = requests.get(f"{BASE_URL}/api/reviews/results?page_size=1")
    if response.status_code == 200:
        data = response.json()
        if data['items']:
            item = data['items'][0]
            print(f"📋 详细审查结果示例:")
            print(f"   🏷️  标题: {item['sql_title']}")
            print(f"   🗄️  数据库: {item['database_name']}")
            print(f"   ⭐ 总体评分: {item['overall_score']} ({item['overall_status']})")
            print(f"   📝 总体评估: {item['overall_summary'][:100]}...")
            print(f"   📊 各维度评分:")
            print(f"      - 一致性: {item['consistency_score']} ({item['consistency_status']})")
            print(f"      - 规范性: {item['conventions_score']} ({item['conventions_status']})")
            print(f"      - 性能: {item['performance_score']} ({item['performance_status']})")
            print(f"      - 安全性: {item['security_score']} ({item['security_status']})")
            print(f"      - 可读性: {item['readability_score']} ({item['readability_status']})")
            print(f"      - 可维护性: {item['maintainability_score']} ({item['maintainability_status']})")
            print(f"   🤖 AI模型: {item['llm_provider']} - {item['llm_model']}")
            print(f"   📅 创建时间: {item['created_at']}")

def main():
    """主函数"""
    print("🚀 SQL审查结果页面功能演示")
    print("=" * 60)
    
    # 等待用户确认
    input("按回车键开始演示...")
    
    # 执行各项测试
    test_health()
    time.sleep(1)
    
    test_basic_pagination()
    time.sleep(1)
    
    test_database_filter()
    time.sleep(1)
    
    test_score_filter()
    time.sleep(1)
    
    test_title_search()
    time.sleep(1)
    
    test_complex_filter()
    time.sleep(1)
    
    test_sorting()
    time.sleep(1)
    
    show_detailed_result()
    
    print_separator("演示完成")
    print("🎉 所有功能演示完成！")
    print(f"🌐 访问 {BASE_URL}/review-results 查看完整界面")
    print(f"🏠 访问 {BASE_URL}/ 返回主页")

if __name__ == "__main__":
    main() 