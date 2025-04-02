#!/usr/bin/env python3
"""
数据库分析脚本

此脚本用于分析ETF数据库的结构和内容，提供数据库表、字段、记录数量和数据分布的概览。
"""

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_database():
    """
    分析数据库结构和内容
    """
    # 连接数据库
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/etf_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\n{'='*50}")
    print(f"数据库文件: {db_path}")
    print(f"数据库大小: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
    print(f"表数量: {len(tables)}")
    print(f"{'='*50}\n")
    
    # 分析每个表
    for table in tables:
        table_name = table[0]
        print(f"\n{'-'*50}")
        print(f"表名: {table_name}")
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("\n字段结构:")
        for col in columns:
            col_id, col_name, col_type, not_null, default_value, is_pk = col
            pk_str = "(主键)" if is_pk else ""
            null_str = "NOT NULL" if not_null else "NULL"
            print(f"  - {col_name} ({col_type}) {null_str} {pk_str}")
        
        # 获取记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        record_count = cursor.fetchone()[0]
        print(f"\n记录数: {record_count}")
        
        # 如果表有数据，分析数据分布
        if record_count > 0:
            # 获取表的主键
            primary_keys = [col[1] for col in columns if col[5]]
            
            # 如果是etf_info表，分析基金管理人分布
            if table_name == 'etf_info':
                try:
                    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                    
                    # 分析基金管理人分布
                    if 'manager' in df.columns:
                        manager_counts = df['manager'].value_counts().head(10)
                        print("\n基金管理人分布(Top 10):")
                        for manager, count in manager_counts.items():
                            print(f"  - {manager}: {count}个ETF")
                    
                    # 分析商务协议ETF比例
                    if 'is_business' in df.columns:
                        business_count = df[df['is_business'] == 1].shape[0]
                        print(f"\n商务协议ETF数量: {business_count}")
                        print(f"商务协议ETF占比: {business_count/record_count*100:.2f}%")
                except Exception as e:
                    print(f"分析etf_info表时出错: {str(e)}")
            
            # 如果是etf_price表，分析价格数据的时间范围
            elif table_name == 'etf_price':
                try:
                    # 获取最早和最晚的日期
                    cursor.execute(f"SELECT MIN(date), MAX(date) FROM {table_name}")
                    min_date, max_date = cursor.fetchone()
                    print(f"\n价格数据时间范围: {min_date} 至 {max_date}")
                    
                    # 获取不同ETF的数量
                    cursor.execute(f"SELECT COUNT(DISTINCT code) FROM {table_name}")
                    etf_count = cursor.fetchone()[0]
                    print(f"价格数据覆盖的ETF数量: {etf_count}")
                    
                    # 获取每个日期的数据量
                    cursor.execute(f"SELECT date, COUNT(*) FROM {table_name} GROUP BY date ORDER BY date DESC LIMIT 10")
                    date_counts = cursor.fetchall()
                    print("\n最近10个交易日的数据量:")
                    for date, count in date_counts:
                        print(f"  - {date}: {count}条记录")
                except Exception as e:
                    print(f"分析etf_price表时出错: {str(e)}")
            
            # 如果是etf_attention表，分析关注度数据
            elif table_name == 'etf_attention':
                try:
                    # 获取最早和最晚的日期
                    cursor.execute(f"SELECT MIN(date), MAX(date) FROM {table_name}")
                    min_date, max_date = cursor.fetchone()
                    print(f"\n关注度数据时间范围: {min_date} 至 {max_date}")
                    
                    # 获取不同ETF的数量
                    cursor.execute(f"SELECT COUNT(DISTINCT code) FROM {table_name}")
                    etf_count = cursor.fetchone()[0]
                    print(f"关注度数据覆盖的ETF数量: {etf_count}")
                    
                    # 获取关注度最高的ETF
                    cursor.execute(f"""
                        SELECT a.code, i.name, AVG(a.attention_count) as avg_attention
                        FROM {table_name} a
                        JOIN etf_info i ON a.code = i.code
                        GROUP BY a.code
                        ORDER BY avg_attention DESC
                        LIMIT 5
                    """)
                    top_attention = cursor.fetchall()
                    print("\n平均关注度最高的ETF(Top 5):")
                    for code, name, avg_attention in top_attention:
                        print(f"  - {code} {name}: {avg_attention:.2f}")
                except Exception as e:
                    print(f"分析etf_attention表时出错: {str(e)}")
            
            # 如果是etf_holders表，分析持有人数据
            elif table_name == 'etf_holders':
                try:
                    # 获取最早和最晚的日期
                    cursor.execute(f"SELECT MIN(date), MAX(date) FROM {table_name}")
                    min_date, max_date = cursor.fetchone()
                    print(f"\n持有人数据时间范围: {min_date} 至 {max_date}")
                    
                    # 获取不同ETF的数量
                    cursor.execute(f"SELECT COUNT(DISTINCT code) FROM {table_name}")
                    etf_count = cursor.fetchone()[0]
                    print(f"持有人数据覆盖的ETF数量: {etf_count}")
                    
                    # 获取持有人数最多的ETF
                    cursor.execute(f"""
                        SELECT h.code, i.name, AVG(h.holder_count) as avg_holders
                        FROM {table_name} h
                        JOIN etf_info i ON h.code = i.code
                        GROUP BY h.code
                        ORDER BY avg_holders DESC
                        LIMIT 5
                    """)
                    top_holders = cursor.fetchall()
                    print("\n平均持有人数最多的ETF(Top 5):")
                    for code, name, avg_holders in top_holders:
                        print(f"  - {code} {name}: {avg_holders:.2f}")
                except Exception as e:
                    print(f"分析etf_holders表时出错: {str(e)}")
    
    # 分析表之间的关系
    print(f"\n{'='*50}")
    print("数据库表关系分析:")
    print(f"{'='*50}\n")
    
    # 检查etf_info表中的ETF在其他表中的覆盖情况
    try:
        cursor.execute("SELECT COUNT(*) FROM etf_info")
        total_etfs = cursor.fetchone()[0]
        
        # 检查在etf_price表中的覆盖
        cursor.execute("""
            SELECT COUNT(DISTINCT i.code)
            FROM etf_info i
            JOIN etf_price p ON i.code = p.code
        """)
        etfs_with_price = cursor.fetchone()[0]
        print(f"ETF基本信息表中共有{total_etfs}个ETF")
        print(f"其中{etfs_with_price}个ETF在价格表中有数据 (覆盖率: {etfs_with_price/total_etfs*100:.2f}%)")
        
        # 检查在etf_attention表中的覆盖
        cursor.execute("""
            SELECT COUNT(DISTINCT i.code)
            FROM etf_info i
            JOIN etf_attention a ON i.code = a.code
        """)
        etfs_with_attention = cursor.fetchone()[0]
        print(f"其中{etfs_with_attention}个ETF在关注度表中有数据 (覆盖率: {etfs_with_attention/total_etfs*100:.2f}%)")
        
        # 检查在etf_holders表中的覆盖
        cursor.execute("""
            SELECT COUNT(DISTINCT i.code)
            FROM etf_info i
            JOIN etf_holders h ON i.code = h.code
        """)
        etfs_with_holders = cursor.fetchone()[0]
        print(f"其中{etfs_with_holders}个ETF在持有人表中有数据 (覆盖率: {etfs_with_holders/total_etfs*100:.2f}%)")
        
        # 检查在所有表中都有数据的ETF数量
        cursor.execute("""
            SELECT COUNT(DISTINCT i.code)
            FROM etf_info i
            JOIN etf_price p ON i.code = p.code
            JOIN etf_attention a ON i.code = a.code
            JOIN etf_holders h ON i.code = h.code
        """)
        etfs_in_all_tables = cursor.fetchone()[0]
        print(f"其中{etfs_in_all_tables}个ETF在所有表中都有数据 (完整覆盖率: {etfs_in_all_tables/total_etfs*100:.2f}%)")
    except Exception as e:
        print(f"分析表关系时出错: {str(e)}")
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    analyze_database()