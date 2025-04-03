#!/usr/bin/env python3
"""
从历史Excel文件导入ETF数据到历史表

此脚本会遍历data目录下的所有历史Excel文件，提取日期信息，并将数据导入到相应的历史表中
"""

import os
import pandas as pd
import re
from datetime import datetime
from database.models import Database

def extract_date_from_filename(filename):
    """从文件名中提取日期"""
    # 尝试查找格式为YYYYMMDD的日期
    date_match = re.search(r'(\d{8})', filename)
    if date_match:
        date_str = date_match.group(1)
        try:
            # 将YYYYMMDD转换为YYYY-MM-DD
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None

def get_all_data_files():
    """获取所有数据文件及其日期"""
    data_dir = 'data'
    data_files = {
        'etf_info': [],      # ETF基本信息文件
        'etf_attention': [], # ETF自选数据文件
        'etf_holders': []    # ETF持有人数据文件
    }
    
    # 遍历data目录
    for filename in os.listdir(data_dir):
        # 提取日期
        date = extract_date_from_filename(filename)
        if not date:
            continue
        
        # 文件完整路径
        file_path = os.path.join(data_dir, filename)
        
        # 分类文件
        if filename.startswith('ETF_DATA_'):
            data_files['etf_info'].append((file_path, date))
        elif filename.startswith('客户ETF自选人数'):
            data_files['etf_attention'].append((file_path, date))
        elif filename.startswith('客户ETF保有量'):
            data_files['etf_holders'].append((file_path, date))
    
    # 按日期排序
    for key in data_files:
        data_files[key].sort(key=lambda x: x[1])
    
    return data_files

def process_etf_info_file(file_path, date, db):
    """处理ETF基本信息文件并导入数据到历史表"""
    print(f"处理ETF基本信息文件: {file_path}, 日期: {date}")
    try:
        # 检查该日期的数据是否已经存在
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM etf_fund_size_history WHERE date = ?", (date,))
        if cursor.fetchone()[0] > 0:
            print(f"日期 {date} 的ETF规模历史数据已存在，跳过导入")
            return
        
        # 读取Excel文件
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # 处理ETF代码（确保是6位字符串）
        if '证券代码' in df.columns:
            code_column = '证券代码'
        else:
            # 查找可能的代码列
            code_columns = [col for col in df.columns if '代码' in col]
            if not code_columns:
                print(f"无法在文件 {file_path} 中找到代码列")
                return
            code_column = code_columns[0]
        
        # 处理规模列
        scale_columns = [col for col in df.columns if '规模' in col and '亿元' in col]
        if not scale_columns:
            print(f"无法在文件 {file_path} 中找到规模列")
            return
        scale_column = scale_columns[0]
        
        # 准备数据
        df['code'] = df[code_column].astype(str)
        df['fund_size'] = pd.to_numeric(df[scale_column], errors='coerce').fillna(0)
        
        # 添加日期和更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 过滤有效数据
        valid_data = df[['code', 'fund_size']].dropna(subset=['code'])
        valid_data = valid_data[valid_data['fund_size'] > 0]
        
        # 插入数据
        for _, row in valid_data.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO etf_fund_size_history (code, fund_size, date, update_time)
                    VALUES (?, ?, ?, ?)
                """, (row['code'], row['fund_size'], date, current_time))
            except Exception as e:
                print(f"插入规模数据时出错: {str(e)}")
        
        db.conn.commit()
        print(f"成功导入 {len(valid_data)} 条 {date} 的ETF规模历史数据")
    
    except Exception as e:
        print(f"处理ETF基本信息文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def process_etf_attention_file(file_path, date, db):
    """处理ETF自选数据文件并导入数据到历史表"""
    print(f"处理ETF自选数据文件: {file_path}, 日期: {date}")
    try:
        # 检查该日期的数据是否已经存在
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM etf_attention_history WHERE date = ?", (date,))
        if cursor.fetchone()[0] > 0:
            print(f"日期 {date} 的ETF自选历史数据已存在，跳过导入")
            return
        
        # 读取Excel文件
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # 打印所有列名以便调试
        print(f"文件 {file_path} 的列名: {df.columns.tolist()}")
        
        # 使用更宽松的匹配方式查找代码列和自选人数列
        code_columns = [col for col in df.columns if '代码' in str(col)]
        if not code_columns:
            code_columns = [col for col in df.columns if '码' in str(col)]
        if not code_columns:
            code_columns = [col for col in df.columns if 'code' in str(col).lower()]
        
        attention_columns = [col for col in df.columns if '自选' in str(col) and '人数' in str(col)]
        if not attention_columns:
            attention_columns = [col for col in df.columns if '自选' in str(col)]
        if not attention_columns:
            attention_columns = [col for col in df.columns if '人数' in str(col) and '自' in str(col)]
        if not attention_columns:
            attention_columns = [col for col in df.columns if '加自' in str(col)]
        
        if not code_columns or not attention_columns:
            print(f"无法在文件 {file_path} 中找到必要的列")
            print(f"可能的代码列: {[col for col in df.columns if '代' in str(col) or '码' in str(col) or 'code' in str(col).lower()]}")
            print(f"可能的自选人数列: {[col for col in df.columns if '自' in str(col) or '人数' in str(col) or '加自' in str(col)]}")
            return
        
        code_column = code_columns[0]
        attention_column = attention_columns[0]
        
        print(f"使用代码列: {code_column}")
        print(f"使用自选人数列: {attention_column}")
        
        # 准备数据
        df['code'] = df[code_column].astype(str).str.strip()
        # 确保是6位数字代码（移除可能的前缀和后缀）
        df['code'] = df['code'].str.extract(r'(\d{6})').fillna('')
        # 过滤掉无效代码
        df = df[df['code'] != '']
        
        # 转换自选人数为数字
        df['attention_count'] = pd.to_numeric(df[attention_column], errors='coerce').fillna(0).astype(int)
        
        # 添加日期和更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 过滤有效数据
        valid_data = df[['code', 'attention_count']].dropna(subset=['code'])
        
        # 插入数据
        for _, row in valid_data.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO etf_attention_history (code, attention_count, date, update_time)
                    VALUES (?, ?, ?, ?)
                """, (row['code'], row['attention_count'], date, current_time))
            except Exception as e:
                print(f"插入自选数据时出错: {str(e)}")
        
        db.conn.commit()
        print(f"成功导入 {len(valid_data)} 条 {date} 的ETF自选历史数据")
    
    except Exception as e:
        print(f"处理ETF自选数据文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def process_etf_holders_file(file_path, date, db):
    """处理ETF持有人数据文件并导入数据到历史表"""
    print(f"处理ETF持有人数据文件: {file_path}, 日期: {date}")
    try:
        # 检查该日期的数据是否已经存在
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM etf_holders_history WHERE date = ?", (date,))
        if cursor.fetchone()[0] > 0:
            print(f"日期 {date} 的ETF持有人历史数据已存在，跳过导入")
            return
        
        # 读取Excel文件
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # 打印所有列名以便调试
        print(f"文件 {file_path} 的列名: {df.columns.tolist()}")
        
        # 使用更宽松的匹配方式查找代码列、持有人数列和持有份额列
        code_columns = [col for col in df.columns if '代码' in str(col)]
        if not code_columns:
            code_columns = [col for col in df.columns if '码' in str(col)]
        if not code_columns:
            code_columns = [col for col in df.columns if 'code' in str(col).lower()]
        
        holder_columns = [col for col in df.columns if '持有' in str(col) and '人数' in str(col)]
        if not holder_columns:
            holder_columns = [col for col in df.columns if '客户' in str(col) and '数' in str(col)]
        if not holder_columns:
            holder_columns = [col for col in df.columns if '持仓' in str(col) and '数' in str(col)]
        if not holder_columns:
            holder_columns = [col for col in df.columns if '人数' in str(col)]
        
        amount_columns = [col for col in df.columns if '持有' in str(col) and ('金额' in str(col) or '份额' in str(col))]
        if not amount_columns:
            amount_columns = [col for col in df.columns if '保有' in str(col) and ('金额' in str(col) or '份额' in str(col))]
        if not amount_columns:
            amount_columns = [col for col in df.columns if '持仓' in str(col) and ('金额' in str(col) or '份额' in str(col))]
        if not amount_columns:
            amount_columns = [col for col in df.columns if '份额' in str(col) or '保有量' in str(col)]
        
        if not code_columns or not holder_columns or not amount_columns:
            print(f"无法在文件 {file_path} 中找到必要的列")
            print(f"可能的代码列: {[col for col in df.columns if '代' in str(col) or '码' in str(col) or 'code' in str(col).lower()]}")
            print(f"可能的持有人数列: {[col for col in df.columns if '持有' in str(col) or '人数' in str(col) or '客户' in str(col)]}")
            print(f"可能的持有份额列: {[col for col in df.columns if '持有' in str(col) or '份额' in str(col) or '保有' in str(col) or '金额' in str(col)]}")
            return
        
        code_column = code_columns[0]
        holder_column = holder_columns[0]
        amount_column = amount_columns[0]
        
        print(f"使用代码列: {code_column}")
        print(f"使用持有人数列: {holder_column}")
        print(f"使用持有份额列: {amount_column}")
        
        # 准备数据
        df['code'] = df[code_column].astype(str).str.strip()
        # 确保是6位数字代码（移除可能的前缀和后缀）
        df['code'] = df['code'].str.extract(r'(\d{6})').fillna('')
        # 过滤掉无效代码
        df = df[df['code'] != '']
        
        # 转换为数字类型
        df['holder_count'] = pd.to_numeric(df[holder_column], errors='coerce').fillna(0).astype(int)
        df['holding_amount'] = pd.to_numeric(df[amount_column], errors='coerce').fillna(0)
        
        # 添加日期和更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 过滤有效数据
        valid_data = df[['code', 'holder_count', 'holding_amount']].dropna(subset=['code'])
        
        # 插入数据
        for _, row in valid_data.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO etf_holders_history (code, holder_count, holding_amount, date, update_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['code'], row['holder_count'], row['holding_amount'], date, current_time))
            except Exception as e:
                print(f"插入持有人数据时出错: {str(e)}")
        
        db.conn.commit()
        print(f"成功导入 {len(valid_data)} 条 {date} 的ETF持有人历史数据")
    
    except Exception as e:
        print(f"处理ETF持有人数据文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def import_all_history_data():
    """导入所有历史数据"""
    print("开始导入所有历史数据...")
    
    # 连接数据库
    db = Database()
    
    # 确保历史表存在
    cursor = db.conn.cursor()
    
    # 创建ETF自选历史表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf_attention_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            attention_count INTEGER,
            date TEXT,
            update_time TIMESTAMP
        )
    """)
    
    # 创建ETF持有人历史表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf_holders_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            holder_count INTEGER,
            holding_amount REAL,
            date TEXT,
            update_time TIMESTAMP
        )
    """)
    
    # 创建ETF规模历史表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf_fund_size_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            fund_size REAL,
            date TEXT,
            update_time TIMESTAMP
        )
    """)
    
    # 获取所有数据文件
    data_files = get_all_data_files()
    
    # 处理ETF基本信息文件
    for file_path, date in data_files['etf_info']:
        process_etf_info_file(file_path, date, db)
    
    # 处理ETF自选数据文件
    for file_path, date in data_files['etf_attention']:
        process_etf_attention_file(file_path, date, db)
    
    # 处理ETF持有人数据文件
    for file_path, date in data_files['etf_holders']:
        process_etf_holders_file(file_path, date, db)
    
    # 查询并显示导入结果
    cursor.execute("SELECT date, COUNT(*) FROM etf_fund_size_history GROUP BY date ORDER BY date")
    fund_size_dates = cursor.fetchall()
    print("\nETF规模历史数据日期统计:")
    for date, count in fund_size_dates:
        print(f"  - {date}: {count}条记录")
    
    cursor.execute("SELECT date, COUNT(*) FROM etf_attention_history GROUP BY date ORDER BY date")
    attention_dates = cursor.fetchall()
    print("\nETF自选历史数据日期统计:")
    for date, count in attention_dates:
        print(f"  - {date}: {count}条记录")
    
    cursor.execute("SELECT date, COUNT(*) FROM etf_holders_history GROUP BY date ORDER BY date")
    holders_dates = cursor.fetchall()
    print("\nETF持有人历史数据日期统计:")
    for date, count in holders_dates:
        print(f"  - {date}: {count}条记录")
    
    print("\n所有历史数据导入完成")

if __name__ == "__main__":
    import_all_history_data() 