#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from database.models import Database
import re
import os
import glob

def normalize_etf_code(code):
    """标准化ETF代码"""
    if not code:
        return ""
    
    # 去除可能的空格
    code = str(code).strip()
    
    # 如果是纯数字6位代码，保持原样
    if re.match(r'^\d{6}$', code):
        return code
    
    # 如果是带交易所后缀的代码，保持原样
    if re.match(r'^\d{6}\.(SZ|SH|BJ)$', code):
        return code
    
    # 如果是带sh/sz/bj前缀的代码，标准化为后缀形式
    match = re.match(r'^(sh|sz|bj)(\d{6})$', code.lower())
    if match:
        prefix, num = match.groups()
        suffix = prefix.upper()  # 转为大写
        return f"{num}.{suffix}"
    
    # 其他情况，仅保留数字部分
    digits = re.sub(r'\D', '', code)
    if len(digits) >= 6:
        return digits[:6]
    
    return code  # 无法标准化时返回原代码

def import_etf_holders_data():
    """导入ETF持有人数据"""
    try:
        print("开始导入ETF持有人数据...")
        
        # 创建数据库连接
        db = Database()
        
        # 获取最新的ETF持有人数据文件
        holder_files = glob.glob("data/客户ETF保有量*.xlsx")
        if not holder_files:
            print("未找到ETF持有人数据文件")
            return False
        
        latest_file = max(holder_files, key=os.path.getmtime)
        print(f"使用文件: {latest_file}")
        
        # 读取Excel文件
        try:
            df = pd.read_excel(latest_file, engine='openpyxl')
            
            # 检查数据是否为空
            if df.empty:
                print("读取的文件为空")
                return False
            
            # 显示列名和前几行数据
            print("文件列名:", df.columns.tolist())
            print("数据示例:")
            print(df.head())
            
            # 标准化列名
            df.columns = [str(col).strip() for col in df.columns]
            
            # 检查是否包含必要的列
            required_cols = ['标的代码', '持仓客户数', '客户保有量（元）']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"文件缺少必要的列: {missing_cols}")
                return False
            
            # 重命名列
            column_mapping = {
                '标的代码': 'code',
                '持仓客户数': 'holder_count',
                '客户保有量（元）': 'holding_amount'
            }
            
            df = df.rename(columns=column_mapping)
            
            # 标准化ETF代码
            df['code'] = df['code'].apply(normalize_etf_code)
            
            # 只保留必要的列
            df = df[['code', 'holder_count', 'holding_amount']]
            
            # 转换数据类型
            df['holder_count'] = pd.to_numeric(df['holder_count'], errors='coerce').fillna(0).astype(int)
            df['holding_amount'] = pd.to_numeric(df['holding_amount'], errors='coerce').fillna(0)
            
            # 打印处理后的数据
            print("处理后的数据:")
            print(df.head())
            print(f"总行数: {len(df)}")
            
            # 保存到数据库
            success = db.save_etf_holders(df)
            if success:
                print(f"成功保存ETF持有人数据，共{len(df)}条记录")
                return True
            else:
                print("保存ETF持有人数据失败")
                return False
                
        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"导入ETF持有人数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import_etf_holders_data() 