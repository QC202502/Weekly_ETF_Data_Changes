import requests
import json
import time

# 等待Flask服务器启动
print("等待Flask服务器启动...")
time.sleep(5)

# 测试ETF代码搜索
print("发送请求到: http://localhost:5007/search")
response = requests.post('http://localhost:5007/search', json={'code': '560050'})

try:
    data = response.json()
    
    # 打印搜索类型和结果数
    print(f"搜索类型: {data.get('search_type', 'N/A')}")
    print(f"结果数量: {data.get('count', 0)}")
    
    # 检查第一个结果
    if data.get('results') and len(data['results']) > 0:
        result = data['results'][0]
        print("\n第一个结果详情:")
        print(f"代码: {result.get('code', 'N/A')}")
        print(f"名称: {result.get('name', 'N/A')}")
        print(f"管理人: {result.get('manager', 'N/A')}")
        print(f"基金规模: {result.get('fund_size', 'N/A')}")
        print(f"管理费率: {result.get('management_fee_rate', 'N/A')}")
        print(f"总持有人数: {result.get('total_holder_count', 'N/A')}")
        print(f"关注人数: {result.get('attention_count', 'N/A')}")
        print(f"持仓人数: {result.get('holder_count', 'N/A')}")
        print(f"持仓金额: {result.get('holding_amount', 'N/A')}")
        
    # 保存完整响应到文件
    with open('search_response.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\n完整响应已保存到 search_response.json")
        
except Exception as e:
    print(f"解析响应失败: {e}")
    print(f"原始响应: {response.text}")
    print(f"状态码: {response.status_code}") 