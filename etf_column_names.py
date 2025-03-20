#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ETF列名信息保存工具

这个脚本用于保存AKShare获取的ETF列表原始列名信息，
这些列名对于理解和处理ETF数据结构非常重要。

使用方法：
python etf_column_names.py
"""

import os
import json
import pandas as pd

def save_etf_column_names():
    """
    保存ETF列表的原始列名信息
    """
    # 从Terminal#114-115获取的ETF列表原始列名
    column_names = ['代码', '名称', '最新价', '涨跌额', '涨跌幅', '买入', '卖出', '昨收', '今开', '最高', '最低', '成交量', '成交额']
    
    # 创建数据目录（如果不存在）
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 保存为JSON文件
    json_file_path = os.path.join(data_dir, 'etf_column_names.json')
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump({
            'column_names': column_names,
            'description': 'AKShare获取的ETF列表原始列名',
            'source': 'Terminal#114-115'
        }, f, ensure_ascii=False, indent=4)
    
    print(f"ETF列名信息已保存至: {json_file_path}")
    
    # 同时保存为CSV文件，方便在Excel中查看
    csv_file_path = os.path.join(data_dir, 'etf_column_names.csv')
    pd.DataFrame({'column_name': column_names}).to_csv(csv_file_path, index=False, encoding='utf-8')
    
    print(f"ETF列名信息已保存至: {csv_file_path}")
    
    return json_file_path, csv_file_path

def main():
    """
    主函数
    """
    print("正在保存ETF列表原始列名信息...")
    json_path, csv_path = save_etf_column_names()
    
    # 显示列名信息
    print("\nETF列表原始列名:")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(data['column_names'])
    
    print("\n列名信息已成功保存!")
    return 0

if __name__ == "__main__":
    main()