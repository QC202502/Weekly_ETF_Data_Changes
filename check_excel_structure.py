#!/usr/bin/env python3
"""
检查Excel文件结构

此脚本用于检查Excel文件的结构，特别是ETF自选人数和持有人数据文件的表结构
"""

import os
import pandas as pd
import re
from datetime import datetime

def check_excel_file(file_path):
    """检查Excel文件的结构"""
    print(f"\n检查文件: {file_path}")
    try:
        # 尝试不同的引擎读取
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            print(f"使用openpyxl引擎读取失败: {str(e)}")
            try:
                df = pd.read_excel(file_path, engine='xlrd')
            except Exception as e:
                print(f"使用xlrd引擎读取失败: {str(e)}")
                return
        
        # 基本信息
        print(f"文件大小: {os.path.getsize(file_path) / 1024:.2f} KB")
        print(f"表格形状: {df.shape}")
        
        # 获取所有工作表
        try:
            with pd.ExcelFile(file_path) as xls:
                sheets = xls.sheet_names
                print(f"工作表列表: {sheets}")
                
                # 对每个工作表进行检查
                for sheet in sheets:
                    try:
                        sheet_df = pd.read_excel(file_path, sheet_name=sheet)
                        print(f"\n工作表 '{sheet}' 形状: {sheet_df.shape}")
                        print(f"工作表 '{sheet}' 列名: {sheet_df.columns.tolist()}")
                        
                        # 尝试找到关键列
                        code_columns = [col for col in sheet_df.columns if isinstance(col, str) and ('代码' in col or '码' in col)]
                        if code_columns:
                            print(f"可能的代码列: {code_columns}")
                            # 显示第一个代码列的前5行数据
                            if code_columns:
                                print(f"代码列 '{code_columns[0]}' 前5行: {sheet_df[code_columns[0]].head().tolist()}")
                        
                        # 检查是自选人数文件还是持有人文件
                        if '自选人数' in file_path:
                            attention_columns = [col for col in sheet_df.columns if isinstance(col, str) and 
                                      ('自选' in col or '人数' in col or '加自' in col)]
                            if attention_columns:
                                print(f"可能的自选人数列: {attention_columns}")
                                # 显示第一个自选人数列的前5行数据
                                if attention_columns:
                                    print(f"自选人数列 '{attention_columns[0]}' 前5行: {sheet_df[attention_columns[0]].head().tolist()}")
                        elif '保有量' in file_path:
                            holder_columns = [col for col in sheet_df.columns if isinstance(col, str) and 
                                     ('持有' in col or '人数' in col or '客户' in col)]
                            amount_columns = [col for col in sheet_df.columns if isinstance(col, str) and 
                                     ('持有' in col or '份额' in col or '保有' in col or '金额' in col)]
                            if holder_columns:
                                print(f"可能的持有人数列: {holder_columns}")
                                # 显示第一个持有人数列的前5行数据
                                if holder_columns:
                                    print(f"持有人数列 '{holder_columns[0]}' 前5行: {sheet_df[holder_columns[0]].head().tolist()}")
                            if amount_columns:
                                print(f"可能的持有份额列: {amount_columns}")
                                # 显示第一个持有份额列的前5行数据
                                if amount_columns:
                                    print(f"持有份额列 '{amount_columns[0]}' 前5行: {sheet_df[amount_columns[0]].head().tolist()}")
                    except Exception as e:
                        print(f"读取工作表 '{sheet}' 出错: {str(e)}")
        except Exception as e:
            print(f"获取工作表列表出错: {str(e)}")
            # 尝试直接处理默认工作表
            print(f"列名: {df.columns.tolist()}")
            # 尝试找到关键列
            code_columns = [col for col in df.columns if isinstance(col, str) and ('代码' in col or '码' in col)]
            if code_columns:
                print(f"可能的代码列: {code_columns}")
            
            # 检查是自选人数文件还是持有人文件
            if '自选人数' in file_path:
                attention_columns = [col for col in df.columns if isinstance(col, str) and 
                          ('自选' in col or '人数' in col or '加自' in col)]
                if attention_columns:
                    print(f"可能的自选人数列: {attention_columns}")
            elif '保有量' in file_path:
                holder_columns = [col for col in df.columns if isinstance(col, str) and 
                         ('持有' in col or '人数' in col or '客户' in col)]
                amount_columns = [col for col in df.columns if isinstance(col, str) and 
                         ('持有' in col or '份额' in col or '保有' in col or '金额' in col)]
                if holder_columns:
                    print(f"可能的持有人数列: {holder_columns}")
                if amount_columns:
                    print(f"可能的持有份额列: {amount_columns}")
    
    except Exception as e:
        print(f"检查文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def check_all_excel_files():
    """检查所有Excel文件的结构"""
    # 查找所有自选人数和持有人数据文件
    data_dir = 'data'
    attention_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if '自选人数' in f and f.endswith('.xlsx')]
    holders_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if '保有量' in f and f.endswith('.xlsx')]
    
    # 按日期排序
    attention_files.sort()
    holders_files.sort()
    
    print("=== 检查ETF自选人数文件 ===")
    for file_path in attention_files:
        check_excel_file(file_path)
    
    print("\n=== 检查ETF持有人数据文件 ===")
    for file_path in holders_files:
        check_excel_file(file_path)

if __name__ == "__main__":
    check_all_excel_files() 