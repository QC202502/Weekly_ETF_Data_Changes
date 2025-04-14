#!/usr/bin/env python3
"""
导入ETF基本信息的历史数据到etf_info_history表

此脚本将遍历data目录下的所有ETF数据文件，提取日期信息，
并将数据导入到etf_info_history表中，保持与etf_info表的列一致
"""

import os
import re
import pandas as pd
from datetime import datetime
from database.models import Database
from utils.etf_code import normalize_etf_code

def extract_date_from_filename(filename):
    """从文件名中提取日期"""
    date_match = re.search(r'(\d{8})', filename)
    if date_match:
        date_str = date_match.group(1)
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return None

def find_etf_data_files():
    """获取所有ETF数据文件及其日期"""
    data_dir = 'data'
    data_files = []
    
    # 遍历data目录
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.startswith('ETF_DATA_') and filename.endswith('.xlsx'):
                # 提取日期
                date = extract_date_from_filename(filename)
                if date:
                    file_path = os.path.join(data_dir, filename)
                    data_files.append((file_path, date))
    
    # 按日期排序
    data_files.sort(key=lambda x: x[1])
    return data_files

def process_etf_info_file(file_path, date, db):
    """处理ETF基本信息文件并导入数据到历史表"""
    print(f"处理ETF基本信息文件: {file_path}, 日期: {date}")
    try:
        # 检查该日期的数据是否已经存在
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM etf_info_history WHERE date = ?", (date,))
        if cursor.fetchone()[0] > 0:
            print(f"日期 {date} 的ETF基本信息历史数据已存在，跳过导入")
            return
        
        # 读取Excel文件
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # 标准化列名（去除多余的空格和换行符）
        df.columns = [col.strip().replace('\n', '') for col in df.columns]
        
        # 定义列名映射
        column_mapping = {
            '证券代码': 'code',
            '证券简称': 'name',
            '基金管理人': 'fund_manager',
            '基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元': 'fund_size',
            '基金上市地点': 'exchange',
            '跟踪指数代码': 'tracking_index_code',
            '跟踪指数名称': 'tracking_index_name',
            '年化跟踪误差阈值(业绩基准)[单位]%': 'tracking_error',
            '信息比率(年化)[起始交易日期]S_cal_date(enddate,-52,W,0)[截止交易日期]最新收盘日[计算周期]日[收益率计算方法]普通收益率[无风险收益率]一年定存利率（税前）[标的指数]上证综合指数': 'information_ratio',
            '基金份额持有人户数[报告期]20240630[单位]户': 'total_holder_count',
            '管理费率[单位]%': 'management_fee_rate',
            '托管费率[单位]%': 'custody_fee_rate',
            '指数使用费率': 'index_usage_fee',
            '月成交额[交易日期]最新收盘日[单位]百万元': 'monthly_volume',
            '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元': 'daily_avg_volume',
            '换手率[交易日期]最新收盘日[单位]%': 'turnover_rate',
            '成交额[交易日期]最新收盘日[单位]亿元': 'daily_volume',
            '成交笔数[交易日期]最新收盘日[单位]笔': 'transaction_count',
            '总市值[交易日期]最新收盘日[单位]亿元': 'total_market_value',
            '业绩比较基准': 'benchmark',
            '成立年限[单位] 年': 'years_since_establishment',
            '基金成立日': 'establishment_date',
            '基金场内简称': 'fund_exchange_abbr'
        }
        
        # 查找最匹配的列名
        actual_mappings = {}
        for target_col, mapped_col in column_mapping.items():
            # 尝试精确匹配
            if target_col in df.columns:
                actual_mappings[target_col] = mapped_col
                continue
            
            # 尝试模糊匹配
            potential_matches = [col for col in df.columns if target_col.split('[')[0].strip() in col]
            if potential_matches:
                # 使用最短的可能匹配（通常最精确）
                best_match = min(potential_matches, key=len)
                actual_mappings[best_match] = mapped_col
                print(f"列名映射: '{best_match}' -> '{mapped_col}'")
        
        # 重命名列
        df = df.rename(columns=actual_mappings)
        
        # 在重命名列后，标准化code列
        if 'code' in df.columns:
            df['code'] = df['code'].apply(normalize_etf_code)
            
        # 添加日期字段
        df['date'] = date
        
        # 添加更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['update_time'] = current_time
        
        # 处理规模、费率等数字数据
        if 'fund_size' in df.columns:
            df['fund_size'] = pd.to_numeric(df['fund_size'], errors='coerce').fillna(0)
        
        fee_columns = ['management_fee_rate', 'custody_fee_rate', 'index_usage_fee']
        for col in fee_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 计算总费率
        fee_cols_exist = [col for col in fee_columns if col in df.columns]
        if fee_cols_exist:
            df['total_annual_fee_rate'] = df[fee_cols_exist].sum(axis=1)
        else:
            df['total_annual_fee_rate'] = 0.0
        
        # 定义要保留的列（与etf_info_history表的列一致）
        columns_to_keep = [
            'code', 'name', 'fund_manager', 'fund_size', 'exchange', 'tracking_index_code',
            'tracking_index_name', 'tracking_error', 'information_ratio', 'total_holder_count',
            'management_fee_rate', 'custody_fee_rate', 'index_usage_fee', 'total_annual_fee_rate',
            'monthly_volume', 'daily_avg_volume', 'turnover_rate', 'daily_volume', 'transaction_count',
            'total_market_value', 'benchmark', 'years_since_establishment', 'establishment_date',
            'fund_exchange_abbr', 'date', 'update_time'
        ]
        
        # 只保留存在的列和需要的列
        existing_columns = [col for col in columns_to_keep if col in df.columns]
        df_filtered = df[existing_columns]
        
        # 保存到历史表
        df_filtered.to_sql('etf_info_history', db.conn, if_exists='append', index=False)
        
        print(f"成功导入 {len(df_filtered)} 条 {date} 的ETF基本信息历史数据")
        
    except Exception as e:
        print(f"处理ETF基本信息文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("开始导入ETF基本信息历史数据...")
    
    # 连接数据库
    db = Database()
    
    # 确保历史表存在
    cursor = db.conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf_info_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            name TEXT,
            fund_manager TEXT,
            fund_size REAL,
            exchange TEXT,
            tracking_index_code TEXT,
            tracking_index_name TEXT,
            tracking_error REAL,
            information_ratio REAL,
            total_holder_count INTEGER,
            management_fee_rate REAL,
            custody_fee_rate REAL,
            index_usage_fee REAL,
            total_annual_fee_rate REAL,
            monthly_volume REAL,
            daily_avg_volume REAL,
            turnover_rate REAL,
            daily_volume REAL,
            transaction_count INTEGER,
            total_market_value REAL,
            benchmark TEXT,
            years_since_establishment REAL,
            establishment_date TEXT,
            fund_exchange_abbr TEXT,
            date TEXT,
            update_time TIMESTAMP,
            UNIQUE(code, date)
        )
    """)
    
    # 获取所有ETF数据文件
    data_files = find_etf_data_files()
    
    if not data_files:
        print("没有找到ETF数据文件")
        return
    
    print(f"找到 {len(data_files)} 个ETF数据文件")
    
    # 处理每个文件
    processed_count = 0
    for file_path, date in data_files:
        process_etf_info_file(file_path, date, db)
        processed_count += 1
    
    # 查询并显示导入结果
    cursor.execute("SELECT date, COUNT(*) FROM etf_info_history GROUP BY date ORDER BY date")
    date_counts = cursor.fetchall()
    
    print("\nETF基本信息历史数据日期统计:")
    for date, count in date_counts:
        print(f"  {date}: {count}条记录")
    
    print(f"\n共处理了 {processed_count} 个文件")
    print("ETF基本信息历史数据导入完成")
    
    db.close()

if __name__ == "__main__":
    main() 