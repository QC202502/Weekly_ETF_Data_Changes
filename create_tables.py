#!/usr/bin/env python3
"""
创建数据库表

此脚本创建ETF数据所需的数据库表
"""

from database.models import Database

def create_tables():
    """创建数据库表"""
    db = Database()
    try:
        cursor = db.conn.cursor()
        
        # 创建ETF自选历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS etf_attention_history (
                code TEXT,
                attention_count INTEGER,
                date TEXT,
                update_time TIMESTAMP,
                PRIMARY KEY (code, date)
            )
        """)
        
        # 创建ETF持有人历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS etf_holders_history (
                code TEXT,
                holder_count INTEGER,
                holding_amount REAL,
                date TEXT,
                update_time TIMESTAMP,
                PRIMARY KEY (code, date)
            )
        """)
        
        # 创建ETF规模历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS etf_fund_size_history (
                code TEXT,
                fund_size REAL,
                date TEXT,
                update_time TIMESTAMP,
                PRIMARY KEY (code, date)
            )
        """)
        
        # 创建市场可交易指数表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_index (
                index_code TEXT PRIMARY KEY,
                index_name TEXT,
                index_intro TEXT,
                publisher TEXT,
                components_count INTEGER,
                weight_method TEXT,
                base_date TEXT,
                base_point REAL,
                currency TEXT,
                update_time TIMESTAMP
            )
        """)
        
        # 提交事务
        db.conn.commit()
        
        print("数据库表创建成功")
    except Exception as e:
        print(f"创建数据库表失败: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_tables() 