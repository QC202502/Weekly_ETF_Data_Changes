#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys

# 默认关键词
keyword = "半导体" if len(sys.argv) < 2 else sys.argv[1]

print(f"搜索关键词: {keyword}")

# 发送请求到API
response = requests.get(f"http://localhost:5000/api/search?keyword={keyword}")

# 检查响应状态码
if response.status_code != 200:
    print(f"请求失败，状态码: {response.status_code}")
    print(response.text)
    sys.exit(1)

# 解析JSON响应
data = response.json()

# 显示结果基本信息
print(f"搜索类型: {data.get('search_type', 'N/A')}")
print(f"总ETF数量: {data.get('count', 'N/A')}")
print(f"是否分组展示: {data.get('is_grouped', 'N/A')}")

# 显示第一个ETF的详情
if data.get('etfs') and len(data['etfs']) > 0:
    result = data['etfs'][0]
    print("\n第一个ETF详情:")
    print(f"代码: {result.get('code', 'N/A')}")
    print(f"名称: {result.get('name', 'N/A')}")
    print(f"持仓人数: {result.get('holder_count', 'N/A')}")
    print(f"持仓价值: {result.get('holding_amount', 'N/A')}")
    print(f"关注度: {result.get('attention_count', 'N/A')}")
    
    # 显示变化数据
    print("\n变化数据:")
    print(f"关注度日变化: {result.get('attention_day_change', 'N/A')}")
    print(f"关注度五日变化: {result.get('attention_5day_change', 'N/A')}")
    print(f"持仓日变化: {result.get('holder_day_change', 'N/A')}")
    print(f"持仓五日变化: {result.get('holder_5day_change', 'N/A')}")
else:
    print("未找到ETF数据")

# 输出完整JSON到文件
with open(f"search_result_{keyword}.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到 search_result_{keyword}.json") 