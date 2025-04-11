#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建测试数据

此脚本创建测试数据并保存为CSV文件，用于测试持仓市值数据导入。
"""

import pandas as pd
import os
from datetime import datetime

# 创建测试数据目录
os.makedirs('test_data', exist_ok=True)

# 创建测试数据
data = {
    '证券代码': ['510050', '510300', '510500', '159915', '512880', '510180', '510900'],
    '证券名称': ['上证50ETF', '沪深300ETF', '中证500ETF', '创业板ETF', '证券ETF', '上证180ETF', '中证国债ETF'],
    '持仓客户数': [125689, 158942, 96532, 145671, 78542, 54982, 32158],
    '持仓份额': [1352.6, 1965.3, 874.5, 1567.8, 432.1, 258.7, 135.9],
    '持仓市值': [4580.5, 6789.2, 3156.8, 5467.9, 1876.3, 978.4, 489.6]
}

# 创建DataFrame
df = pd.DataFrame(data)

# 保存为CSV文件
date_str = datetime.now().strftime('%Y%m%d')
filename = f'test_data/ETF测试数据_{date_str}.csv'
df.to_csv(filename, index=False, encoding='utf-8-sig')

print(f"测试数据已保存到 {filename}")

# 显示数据
print("\n创建的测试数据:")
print(df) 