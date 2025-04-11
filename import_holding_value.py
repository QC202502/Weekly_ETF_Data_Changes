#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导入ETF持仓市值数据

此脚本专门用于读取ETF保有量Excel或CSV文件，并将持仓市值数据导入到数据库中。
"""

import os
import glob
import pandas as pd
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

def read_data_file(file_path):
    """读取Excel或CSV文件，返回DataFrame"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            try:
                # 尝试不同编码读取CSV
                encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb18030']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        if not df.empty:
                            return df
                    except:
                        continue
                return pd.DataFrame()  # 如果所有编码都失败，返回空DataFrame
            except Exception as e:
                print(f"读取CSV文件失败: {str(e)}")
                return pd.DataFrame()
        else:  # Excel文件
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
                return df
            except Exception as e:
                print(f"读取Excel文件失败: {str(e)}")
                return pd.DataFrame()
    except Exception as e:
        print(f"读取文件失败: {str(e)}")
        return pd.DataFrame()

def import_holding_value():
    """导入ETF持仓市值数据"""
    try:
        # 创建数据库连接
        db = Database()
        
        # 查找ETF保有量文件（Excel和CSV）
        excel_files = sorted(glob.glob("data/客户ETF保有量*.xlsx"))
        csv_files = sorted(glob.glob("test_data/ETF测试数据_*.csv"))
        files = excel_files + csv_files
        
        if not files:
            print("未找到ETF保有量文件")
            return False
        
        print(f"找到 {len(files)} 个ETF保有量文件（{len(excel_files)}个Excel, {len(csv_files)}个CSV）")
        
        # 处理每个文件
        for file_path in files:
            print(f"\n处理文件: {file_path}")
            
            # 从文件名提取日期
            date = extract_date_from_filename(file_path)
            if not date:
                print(f"无法从文件名提取日期: {file_path}")
                date = datetime.now().strftime('%Y-%m-%d')  # 使用当前日期作为默认值
                print(f"使用当前日期作为默认值: {date}")
            else:
                print(f"提取的日期: {date}")
            
            try:
                # 读取文件
                df = read_data_file(file_path)
                if df.empty:
                    print(f"文件为空或无法读取: {file_path}")
                    continue
                
                # 标准化列名
                df.columns = [str(col).strip().replace('\n', '') for col in df.columns]
                
                print("原始列名:", list(df.columns))
                print("原始数据前5行:")
                print(df.head())
                
                # 查找包含关键词的列
                code_cols = [col for col in df.columns if any(key in col.lower() for key in ['代码', 'code'])]
                holder_cols = [col for col in df.columns if any(key in col.lower() for key in ['客户数', '持有人', 'holder'])]
                amount_cols = [col for col in df.columns if any(key in col.lower() for key in ['份额', '保有量', 'amount'])]
                value_cols = [col for col in df.columns if any(key in col.lower() for key in ['市值', '持仓市值', 'value'])]
                
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
                
                # 连接数据库
                conn = db.connect()
                cursor = conn.cursor()
                
                # 获取有效的ETF代码
                cursor.execute("SELECT code FROM etf_info")
                valid_codes = [row[0] for row in cursor.fetchall()]
                valid_codes = valid_codes or df['code'].tolist()  # 如果没有有效代码，使用文件中的代码
                
                # 过滤有效的ETF
                df_filtered = df[df['code'].isin(valid_codes)]
                
                if df_filtered.empty:
                    print(f"过滤后没有有效的ETF记录，尝试使用所有记录")
                    df_filtered = df  # 如果过滤后为空，使用所有记录
                
                # 更新历史表中的持仓市值
                updated_count = 0
                for _, row in df_filtered.iterrows():
                    try:
                        # 首先检查记录是否存在
                        cursor.execute("""
                            SELECT COUNT(*) FROM etf_holders_history 
                            WHERE code = ? AND date = ?
                        """, (row['code'], date))
                        
                        exists = cursor.fetchone()[0] > 0
                        print(f"ETF代码 {row['code']}, 日期 {date}, 记录{'存在' if exists else '不存在'}")
                        
                        if exists:
                            # 更新现有记录
                            print(f"更新记录: 代码={row['code']}, 日期={date}, 持仓市值={row['holding_value']}")
                            cursor.execute("""
                                UPDATE etf_holders_history 
                                SET holding_value = ?, holder_count = ?, holding_amount = ?
                                WHERE code = ? AND date = ?
                            """, (row['holding_value'], row['holder_count'], row['holding_amount'], row['code'], date))
                        else:
                            # 插入新记录
                            print(f"插入新记录: 代码={row['code']}, 日期={date}, 持仓市值={row['holding_value']}")
                            cursor.execute("""
                                INSERT INTO etf_holders_history 
                                (code, holder_count, holding_amount, holding_value, date, update_time)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (row['code'], row['holder_count'], row['holding_amount'], row['holding_value'], date, row['update_time']))
                        
                        # 验证数据是否已保存
                        cursor.execute("""
                            SELECT code, date, holding_value FROM etf_holders_history 
                            WHERE code = ? AND date = ?
                        """, (row['code'], date))
                        verification = cursor.fetchone()
                        if verification:
                            print(f"数据验证成功: 代码={verification[0]}, 日期={verification[1]}, 持仓市值={verification[2]}")
                        else:
                            print(f"数据验证失败: 无法找到刚刚插入/更新的记录")
                        
                        updated_count += 1
                    except Exception as e:
                        print(f"处理记录出错: {row['code']}, {str(e)}")
                        traceback.print_exc()
                
                conn.commit()
                
                print(f"成功更新 {updated_count} 条持仓市值数据，日期: {date}")
                
            except Exception as e:
                print(f"处理文件出错: {file_path}")
                print(f"错误: {str(e)}")
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"导入ETF持仓市值数据失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始导入ETF持仓市值数据...")
    result = import_holding_value()
    if result:
        print("ETF持仓市值数据导入完成")
    else:
        print("ETF持仓市值数据导入失败") 