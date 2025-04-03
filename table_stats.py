#!/usr/bin/env python3
"""
统计数据库表信息脚本

此脚本连接到ETF数据库，并统计所有表的记录数和不同日期的数量
"""

import sqlite3
import os

def get_table_stats():
    """获取所有表的统计信息"""
    # 连接数据库
    db_path = 'data/etf_data.db'
    if not os.path.exists(db_path):
        print(f"错误：找不到数据库文件 {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("数据库中的表及记录数量：")
    
    for table in tables:
        table_name = table[0]
        if table_name == 'sqlite_sequence':
            continue
        
        # 获取记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        record_count = cursor.fetchone()[0]
        
        # 检查表是否有date列
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        has_date = False
        for col in columns:
            if col[1] == 'date':
                has_date = True
                break
        
        # 获取不同日期数量
        date_count = 0
        if has_date:
            cursor.execute(f"SELECT COUNT(DISTINCT date) FROM {table_name}")
            date_count = cursor.fetchone()[0]
        
        print(f"- {table_name}: {record_count}条记录, {date_count}个日期")
    
    conn.close()

if __name__ == "__main__":
    get_table_stats() 