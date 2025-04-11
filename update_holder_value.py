#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新ETF持仓数据

从Excel文件导入持仓数据，包括持仓份额(holding_amount)和持仓市值(holding_value)，
并更新到etf_holders_history表中。

持仓份额(holding_amount)是指持有的基金份额数量
持仓市值(holding_value)是指持有的基金市值，通常是持仓份额乘以净值
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime
import glob
import re

# 数据库路径
DB_PATH = "data/etf_data.db"
# Excel文件目录
EXCEL_DIR = "data"
# Excel文件名模式
EXCEL_PATTERN = "客户ETF保有量*.xlsx"

def normalize_etf_code(code):
    """标准化ETF代码"""
    if not code:
        return ""
    
    # 移除可能的后缀
    if '.' in code:
        code = code.split('.')[0]
    elif code.startswith('sh') or code.startswith('sz'):
        code = code[2:]
    
    # 确保是6位数字
    return code.zfill(6)

def extract_date_from_filename(filename):
    """从文件名中提取日期"""
    match = re.search(r'(\d{8})', filename)
    if match:
        date_str = match.group(1)
        # 转换为YYYY-MM-DD格式
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return None

def read_excel_data(excel_path):
    """读取Excel文件中的ETF保有量数据"""
    try:
        print(f"读取文件: {excel_path}")
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        
        # 列名识别
        code_columns = ['标的代码', '标的代碼', '证券代码', '证券代碼']
        amount_columns = ['持仓份额', '持有份额', '份额', '持仓数量']  # 持仓份额列
        value_columns = ['持仓市值', '持仓价值', '保有金额', '保有價值', '持仓金额']  # 持仓市值列
        holder_columns = ['持仓客户数', '持仓户数', '客户数', '持有人数'] # 持仓客户数列
        
        # 查找证券代码列
        code_col = None
        for col_name in code_columns:
            if col_name in df.columns:
                code_col = col_name
                break
        
        if not code_col:
            print(f"无法在{excel_path}中找到证券代码列")
            print(f"可用列: {', '.join(df.columns)}")
            return None
        
        # 查找持仓份额列
        amount_col = None
        for col_name in amount_columns:
            if col_name in df.columns:
                amount_col = col_name
                break
        
        # 查找持仓市值列
        value_col = None
        for col_name in value_columns:
            if col_name in df.columns:
                value_col = col_name
                break
        
        if not value_col:
            print(f"无法在{excel_path}中找到持仓市值列")
            print(f"可用列: {', '.join(df.columns)}")
            return None
        
        # 查找持仓客户数列
        holder_col = None
        for col_name in holder_columns:
            if col_name in df.columns:
                holder_col = col_name
                break
        
        # 打印找到的列
        columns_info = [f"{code_col}(代码列)", f"{value_col}(市值列)"]
        if amount_col:
            columns_info.append(f"{amount_col}(份额列)")
        if holder_col:
            columns_info.append(f"{holder_col}(客户数列)")
        
        print(f"使用列: {', '.join(columns_info)}")
        
        # 准备结果DataFrame的列
        result_columns = ['code', 'holding_value']
        df_columns = [code_col, value_col]
        
        # 如果找到持仓份额列，添加到提取列中
        if amount_col:
            df_columns.append(amount_col)
            result_columns.append('holding_amount')
        
        # 如果找到持仓客户数列，添加到提取列中
        if holder_col:
            df_columns.append(holder_col)
            result_columns.append('holder_count')
        
        # 提取证券代码、持仓价值和可能的持仓份额、持仓客户数
        result_df = df[df_columns].copy()
        result_df.columns = result_columns
        
        # 标准化证券代码
        result_df['code'] = result_df['code'].apply(lambda x: normalize_etf_code(str(x)))
        
        # 过滤出有效的ETF代码(6位数字)
        result_df = result_df[result_df['code'].str.match(r'^\d{6}$')]
        
        # 去除NaN值
        result_df = result_df.dropna(subset=['holding_value'])
        
        # 如果没有找到持仓份额列，添加默认值
        if 'holding_amount' not in result_df.columns:
            result_df['holding_amount'] = 0.0
        
        # 如果没有找到持仓客户数列，添加默认值
        if 'holder_count' not in result_df.columns:
            result_df['holder_count'] = 0
        
        # 显示数据统计
        print(f"提取到 {len(result_df)} 条有效数据")
        if len(result_df) > 0:
            print(f"持仓市值范围: {result_df['holding_value'].min()} - {result_df['holding_value'].max()}")
            if amount_col:
                print(f"持仓份额范围: {result_df['holding_amount'].min()} - {result_df['holding_amount'].max()}")
            if holder_col:
                print(f"持仓客户数范围: {result_df['holder_count'].min()} - {result_df['holder_count'].max()}")
            print(f"前5条数据示例:")
            print(result_df.head())
        
        return result_df
    
    except Exception as e:
        print(f"读取Excel文件出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def update_database(date_str, data_df):
    """更新数据库中的持仓份额和持仓市值数据"""
    if data_df is None or data_df.empty:
        print("没有有效数据可更新")
        return 0
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取当前时间
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 更新计数器
        update_count = 0
        
        for _, row in data_df.iterrows():
            code = row['code']
            holding_value = row['holding_value']
            holding_amount = row.get('holding_amount', 0.0)
            holder_count = row.get('holder_count', 0)
            
            # 检查记录是否存在
            cursor.execute("""
                SELECT id 
                FROM etf_holders_history 
                WHERE code = ? AND date = ?
            """, (code, date_str))
            
            record = cursor.fetchone()
            
            if record:
                # 更新现有记录
                record_id = record[0]
                cursor.execute("""
                    UPDATE etf_holders_history 
                    SET holding_value = ?, holding_amount = ?, holder_count = ?, update_time = ? 
                    WHERE id = ?
                """, (holding_value, holding_amount, holder_count, update_time, record_id))
                update_count += 1
            else:
                # 创建新记录
                cursor.execute("""
                    INSERT INTO etf_holders_history 
                    (code, date, holder_count, holding_amount, holding_value, update_time) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (code, date_str, holder_count, holding_amount, holding_value, update_time))
                update_count += 1
        
        # 提交事务
        conn.commit()
        print(f"成功更新{update_count}条记录")
        
        return update_count
    
    except Exception as e:
        print(f"更新数据库出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0
    
    finally:
        if conn:
            conn.close()

def process_all_excel_files():
    """处理所有符合条件的Excel文件"""
    # 查找所有符合模式的Excel文件
    excel_pattern = os.path.join(EXCEL_DIR, EXCEL_PATTERN)
    excel_files = glob.glob(excel_pattern)
    
    if not excel_files:
        print(f"未找到符合模式的Excel文件: {excel_pattern}")
        return 0
    
    total_updated = 0
    
    for excel_path in excel_files:
        # 从文件名中提取日期
        date_str = extract_date_from_filename(excel_path)
        if not date_str:
            print(f"无法从文件名中提取日期: {excel_path}")
            continue
        
        # 读取数据
        data_df = read_excel_data(excel_path)
        
        # 更新数据库
        updated = update_database(date_str, data_df)
        total_updated += updated
        
        print(f"处理文件 {os.path.basename(excel_path)} 完成, 更新了 {updated} 条记录")
    
    return total_updated

def rename_function_amount_to_value():
    """说明持仓份额和持仓市值的区别"""
    print("数据库中的持仓数据字段说明:")
    print("  holding_amount: 持仓份额，指持有的基金份额数量")
    print("  holding_value: 持仓市值，指持有的基金市值，通常是持仓份额乘以净值")
    print("不再需要修改函数名，因为代码已经正确区分了这两个字段")
    return True

def main():
    """主函数"""
    print("ETF持仓数据更新工具")
    print("功能: 从Excel文件导入ETF持仓份额和持仓市值数据，并更新到数据库中")
    print("=" * 60)
    
    # 创建一个备份SQL命令，在修改前打印
    backup_cmd = f"sqlite3 {DB_PATH} '.backup {DB_PATH}.bak'"
    print(f"建议在修改前执行以下命令备份数据库:\n{backup_cmd}")
    print("=" * 60)
    
    # 输出持仓份额和持仓市值的区别说明
    rename_function_amount_to_value()
    print("=" * 60)
    
    # 处理所有Excel文件
    total_updated = process_all_excel_files()
    print(f"总共更新了 {total_updated} 条记录")

if __name__ == "__main__":
    main() 