#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建历史测试数据

此脚本创建多天的测试数据并保存为CSV文件，用于测试持仓市值数据导入。
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import random

# 创建测试数据目录
os.makedirs('test_data', exist_ok=True)

# ETF代码和名称
etfs = [
    ('510050', '上证50ETF'),
    ('510300', '沪深300ETF'),
    ('510500', '中证500ETF'),
    ('159915', '创业板ETF'),
    ('512880', '证券ETF'),
    ('510180', '上证180ETF'),
    ('510900', '中证国债ETF')
]

# 生成过去14天的数据
today = datetime.now()
dates = [(today - timedelta(days=i)) for i in range(14)]

# 为每一天创建测试数据
for date in dates:
    date_str = date.strftime('%Y%m%d')
    
    # 创建当天的数据
    data = {
        '证券代码': [],
        '证券名称': [],
        '持仓客户数': [],
        '持仓份额': [],
        '持仓市值': []
    }
    
    # 为每个ETF生成略有变化的数据
    for code, name in etfs:
        # 基础值
        base_holder_count = random.randint(30000, 200000)
        base_amount = random.uniform(100.0, 2000.0)
        base_value = base_amount * random.uniform(3.0, 5.0)  # 市值通常是份额的3-5倍
        
        # 添加随机波动（每天变化±5%）
        holder_count = int(base_holder_count * (1 + random.uniform(-0.05, 0.05)))
        amount = round(base_amount * (1 + random.uniform(-0.05, 0.05)), 1)
        value = round(base_value * (1 + random.uniform(-0.05, 0.05)), 1)
        
        # 添加到数据集
        data['证券代码'].append(code)
        data['证券名称'].append(name)
        data['持仓客户数'].append(holder_count)
        data['持仓份额'].append(amount)
        data['持仓市值'].append(value)
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存为CSV文件
    filename = f'test_data/ETF测试数据_{date_str}.csv'
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"创建数据文件 {filename}，包含 {len(etfs)} 条记录")

print("\n总共创建了 14 天的测试数据文件")
print(f"文件保存在 test_data/ 目录") 