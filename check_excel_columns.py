#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查Excel文件列名

这个脚本用于检查ETF数据Excel文件的列名，帮助我们理解文件结构
"""

import pandas as pd
import sys
import os

def check_excel_columns(excel_path):
    """读取Excel文件并打印列名"""
    try:
        print(f"读取文件: {excel_path}")
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        
        # 打印所有列名
        print("\n列名:")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")
        
        # 打印前三行数据示例
        print("\n数据示例 (前三行):")
        print(df.head(3))
        
        return True
    
    except Exception as e:
        print(f"读取Excel文件出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 如果命令行有参数，使用参数作为文件路径
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        # 否则使用最新的保有量文件
        excel_dir = "data"
        file_pattern = "客户ETF保有量"
        
        # 查找最新的保有量文件
        excel_files = [f for f in os.listdir(excel_dir) if file_pattern in f and f.endswith(".xlsx")]
        if not excel_files:
            print(f"未找到{file_pattern}*.xlsx文件")
            sys.exit(1)
        
        # 按修改时间排序
        excel_files.sort(key=lambda x: os.path.getmtime(os.path.join(excel_dir, x)), reverse=True)
        excel_path = os.path.join(excel_dir, excel_files[0])
    
    print(f"检查Excel文件: {excel_path}")
    check_excel_columns(excel_path) 