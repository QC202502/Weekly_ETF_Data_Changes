#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导入ETF持仓数据 (使用xlwings)

此脚本专门用于使用xlwings读取ETF保有量Excel文件，并将持仓份额和持仓市值数据同时导入到数据库中。
"""

import os
import glob
import pandas as pd
import xlwings as xw
from datetime import datetime
from database.models import Database
import re
import traceback

def normalize_etf_code(code):
    """标准化ETF代码"""
    if not code:
        return code
    
    code = str(code).strip()
    # 去除.SH/.SZ后缀
    code = code.replace('.SH', '').replace('.SZ', '')
    # 确保是6位数字
    return code.zfill(6)

def extract_date_from_filename(filename):
    """从文件名中提取日期"""
    try:
        # 使用正则表达式匹配文件名中的日期
        match = re.search(r'(\d{8})', filename)
        if match:
            date_str = match.group(1)
            return datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        return None
    except Exception as e:
        print(f"从文件名提取日期时出错: {str(e)}")
        return None

def import_holders_data_with_xlwings():
    """使用xlwings导入ETF持仓数据"""
    try:
        print("开始导入ETF持仓数据...")
        
        # 创建数据库连接
        db = Database()
        
        # 查找ETF保有量文件
        files = sorted(glob.glob("data/客户ETF保有量*.xlsx"))
        if not files:
            print("未找到ETF保有量文件")
            return False
        
        print(f"找到 {len(files)} 个ETF保有量文件")
        
        # 启动Excel应用
        app = xw.App(visible=False)
        
        # 处理每个文件
        for file_path in files:
            print(f"\n处理文件: {file_path}")
            
            # 从文件名提取日期
            date = extract_date_from_filename(file_path)
            if not date:
                print(f"无法从文件名提取日期: {file_path}")
                continue
            
            print(f"提取的日期: {date}")
            
            try:
                # 打开工作簿
                wb = app.books.open(file_path)
                sheet = wb.sheets[0]
                
                # 获取数据范围
                used_range = sheet.used_range
                print(f"使用的数据范围: {used_range.address}")
                
                # 读取数据
                data = used_range.value
                if not data or len(data) <= 1:
                    print(f"文件为空或只有标题行: {file_path}")
                    wb.close()
                    continue
                
                # 转换为DataFrame
                df = pd.DataFrame(data[1:], columns=data[0])
                
                print(f"成功读取数据，形状: {df.shape}")
                print("列名:", list(df.columns))
                print("数据前5行:")
                print(df.head())
                
                # 关闭工作簿
                wb.close()
                
                # 查找包含关键词的列
                code_cols = [col for col in df.columns if any(key in str(col).lower() for key in ['代码', 'code'])]
                holder_cols = [col for col in df.columns if any(key in str(col).lower() for key in ['客户数', '持有人', 'holder'])]
                amount_cols = [col for col in df.columns if any(key in str(col).lower() for key in ['份额', '保有量', 'amount'])]
                value_cols = [col for col in df.columns if any(key in str(col).lower() for key in ['市值', '持仓市值', 'value'])]
                
                print(f"找到的代码列: {code_cols}")
                print(f"找到的持有人列: {holder_cols}")
                print(f"找到的份额列: {amount_cols}")
                print(f"找到的市值列: {value_cols}")
                
                # 如果找不到必要的列，跳过此文件
                if not code_cols:
                    print(f"文件中缺少必要的代码列: {file_path}")
                    continue
                
                # 准备列名映射
                columns_mapping = {}
                columns_mapping[code_cols[0]] = 'code'
                if holder_cols:
                    columns_mapping[holder_cols[0]] = 'holder_count'
                if amount_cols:
                    columns_mapping[amount_cols[0]] = 'holding_amount'
                if value_cols:
                    columns_mapping[value_cols[0]] = 'holding_value'
                
                print("列名映射:", columns_mapping)
                
                # 重命名列
                df = df.rename(columns=columns_mapping)
                
                # 标准化ETF代码
                df['code'] = df['code'].astype(str).apply(normalize_etf_code)
                
                # 转换为数字类型
                if 'holder_count' in df.columns:
                    df['holder_count'] = pd.to_numeric(df['holder_count'], errors='coerce').fillna(0).astype(int)
                else:
                    df['holder_count'] = 0
                
                if 'holding_amount' in df.columns:
                    df['holding_amount'] = pd.to_numeric(df['holding_amount'], errors='coerce').fillna(0).astype(float)
                else:
                    df['holding_amount'] = 0.0
                
                if 'holding_value' in df.columns:
                    df['holding_value'] = pd.to_numeric(df['holding_value'], errors='coerce').fillna(0).astype(float)
                else:
                    df['holding_value'] = 0.0
                
                # 添加日期和更新时间
                df['date'] = date
                df['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 获取所有的ETF代码
                conn = db.connect()
                cursor = conn.cursor()
                
                try:
                    cursor.execute("SELECT code FROM etf_info")
                    valid_codes = [row[0] for row in cursor.fetchall()]
                except Exception as e:
                    print(f"获取ETF代码时出错: {str(e)}")
                    valid_codes = []
                
                # 过滤有效的ETF代码
                if valid_codes:
                    df_filtered = df[df['code'].isin(valid_codes)]
                    if df_filtered.empty:
                        print("没有有效的ETF代码，使用所有数据")
                        df_filtered = df
                else:
                    df_filtered = df
                
                # 保存到数据库
                for _, row in df_filtered.iterrows():
                    try:
                        # 检查记录是否存在
                        cursor.execute("""
                            SELECT COUNT(*) FROM etf_holders_history 
                            WHERE code = ? AND date = ?
                        """, (row['code'], date))
                        
                        exists = cursor.fetchone()[0] > 0
                        
                        if exists:
                            # 更新现有记录
                            cursor.execute("""
                                UPDATE etf_holders_history 
                                SET holder_count = ?, holding_amount = ?, holding_value = ?, update_time = ?
                                WHERE code = ? AND date = ?
                            """, (row['holder_count'], row['holding_amount'], row['holding_value'], 
                                  row['update_time'], row['code'], date))
                        else:
                            # 插入新记录
                            cursor.execute("""
                                INSERT INTO etf_holders_history 
                                (code, holder_count, holding_amount, holding_value, date, update_time)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (row['code'], row['holder_count'], row['holding_amount'], row['holding_value'], 
                                 date, row['update_time']))
                        
                    except Exception as e:
                        print(f"处理记录出错 {row['code']}: {str(e)}")
                
                conn.commit()
                print(f"成功保存 {len(df_filtered)} 条记录到 etf_holders_history 表")
                
            except Exception as e:
                print(f"处理文件出错: {file_path}")
                print(f"错误: {str(e)}")
                traceback.print_exc()
        
        # 关闭Excel应用
        app.quit()
        return True
        
    except Exception as e:
        print(f"导入ETF持仓数据失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始导入ETF持仓数据（使用xlwings）...")
    result = import_holders_data_with_xlwings()
    if result:
        print("ETF持仓数据导入完成")
    else:
        print("ETF持仓数据导入失败") 