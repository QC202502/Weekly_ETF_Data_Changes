#!/usr/bin/env python3
"""
初始化历史数据表

此脚本用于创建历史数据表并将当前的ETF持有人数据、ETF自选数据和ETF规模数据导入到对应的历史表中
"""

from database.models import Database
from datetime import datetime

def init_history_tables():
    """初始化所有历史数据表"""
    print("开始初始化历史数据表...")
    
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    
    # 当前日期和时间
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 创建ETF自选历史表
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS etf_attention_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                attention_count INTEGER,
                date TEXT,
                update_time TIMESTAMP
            )
        """)
        print("成功创建 etf_attention_history 表")
    except Exception as e:
        print(f"创建 etf_attention_history 表出错: {str(e)}")
    
    # 创建ETF持有人历史表
    try:
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
        print("成功创建 etf_holders_history 表")
    except Exception as e:
        print(f"创建 etf_holders_history 表出错: {str(e)}")
    
    # 创建ETF规模历史表
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS etf_fund_size_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                fund_size REAL,
                date TEXT,
                update_time TIMESTAMP
            )
        """)
        print("成功创建 etf_fund_size_history 表")
    except Exception as e:
        print(f"创建 etf_fund_size_history 表出错: {str(e)}")
    
    # 导入ETF自选数据
    try:
        # 先检查历史表中是否已有当天数据
        cursor.execute(f"SELECT COUNT(*) FROM etf_attention_history WHERE date = ?", (current_date,))
        if cursor.fetchone()[0] > 0:
            print(f"etf_attention_history 表中已存在 {current_date} 的数据，跳过导入")
        else:
            # 获取当前自选数据
            cursor.execute("SELECT code, attention_count FROM etf_attention")
            attention_data = cursor.fetchall()
            
            # 导入到历史表
            for code, attention_count in attention_data:
                cursor.execute("""
                    INSERT INTO etf_attention_history (code, attention_count, date, update_time)
                    VALUES (?, ?, ?, ?)
                """, (code, attention_count, current_date, current_time))
            
            print(f"成功导入 {len(attention_data)} 条自选数据到 etf_attention_history 表")
    except Exception as e:
        print(f"导入自选历史数据出错: {str(e)}")
    
    # 导入ETF持有人数据
    try:
        # 先检查历史表中是否已有当天数据
        cursor.execute(f"SELECT COUNT(*) FROM etf_holders_history WHERE date = ?", (current_date,))
        if cursor.fetchone()[0] > 0:
            print(f"etf_holders_history 表中已存在 {current_date} 的数据，跳过导入")
        else:
            # 获取当前持有人数据
            cursor.execute("SELECT code, holder_count, holding_amount FROM etf_holders")
            holders_data = cursor.fetchall()
            
            # 导入到历史表
            for code, holder_count, holding_amount in holders_data:
                cursor.execute("""
                    INSERT INTO etf_holders_history (code, holder_count, holding_amount, date, update_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (code, holder_count, holding_amount, current_date, current_time))
            
            print(f"成功导入 {len(holders_data)} 条持有人数据到 etf_holders_history 表")
    except Exception as e:
        print(f"导入持有人历史数据出错: {str(e)}")
    
    # 导入ETF规模数据
    try:
        # 先检查历史表中是否已有当天数据
        cursor.execute(f"SELECT COUNT(*) FROM etf_fund_size_history WHERE date = ?", (current_date,))
        if cursor.fetchone()[0] > 0:
            print(f"etf_fund_size_history 表中已存在 {current_date} 的数据，跳过导入")
        else:
            # 获取当前规模数据
            cursor.execute("SELECT code, fund_size FROM etf_info WHERE fund_size > 0")
            fund_size_data = cursor.fetchall()
            
            # 导入到历史表
            for code, fund_size in fund_size_data:
                cursor.execute("""
                    INSERT INTO etf_fund_size_history (code, fund_size, date, update_time)
                    VALUES (?, ?, ?, ?)
                """, (code, fund_size, current_date, current_time))
            
            print(f"成功导入 {len(fund_size_data)} 条规模数据到 etf_fund_size_history 表")
    except Exception as e:
        print(f"导入规模历史数据出错: {str(e)}")
    
    # 提交事务
    conn.commit()
    print("所有历史数据导入完成")

if __name__ == "__main__":
    init_history_tables() 