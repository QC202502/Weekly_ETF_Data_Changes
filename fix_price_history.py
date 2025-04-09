#!/usr/bin/env python3
"""
创建和初始化etf_price_history表

此脚本用于创建etf_price_history表并将当前的ETF价格数据导入到该表中
"""

from database.models import Database
from datetime import datetime
import traceback

def init_price_history_table():
    """初始化ETF价格历史表"""
    print("开始初始化ETF价格历史表...")
    
    db = Database()
    
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 使用固定的交易日期，而不是当前日期
        current_date = "2024-04-09"  # 使用实际交易日期
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 创建ETF价格历史表
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etf_price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    price_change_rate REAL,
                    turnover_rate REAL,
                    daily_volume REAL,
                    transaction_count INTEGER,
                    market_value REAL,
                    date TEXT,
                    update_time TIMESTAMP,
                    UNIQUE(code, date)
                )
            """)
            print("成功创建 etf_price_history 表")
        except Exception as e:
            print(f"创建 etf_price_history 表出错: {str(e)}")
            traceback.print_exc()
        
        # 清除表中可能存在的错误日期数据
        try:
            cursor.execute("DELETE FROM etf_price_history WHERE date = '2025-04-09'")
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"已删除 {deleted_count} 条错误日期的记录")
            conn.commit()
        except Exception as e:
            print(f"清除错误日期数据失败: {str(e)}")
            conn.rollback()
        
        # 尝试从etf_price表导入数据
        try:
            # 先检查历史表中是否已有指定日期的数据
            cursor.execute(f"SELECT COUNT(*) FROM etf_price_history WHERE date = ?", (current_date,))
            if cursor.fetchone()[0] > 0:
                print(f"etf_price_history 表中已存在 {current_date} 的数据，跳过导入")
            else:
                # 从etf_price表获取当前价格数据
                cursor.execute("""
                    SELECT 
                        code, 
                        change_rate, 
                        turnover_rate, 
                        amount, 
                        transaction_count 
                    FROM etf_price
                """)
                price_data = cursor.fetchall()
                
                # 导入到历史表
                if price_data:
                    counter = 0
                    for row in price_data:
                        if len(row) >= 5:
                            code = row[0]
                            change_rate = row[1]
                            turnover_rate = row[2]
                            amount = row[3]  # daily_volume
                            transaction_count = row[4]
                            
                            # 市值暂时设为NULL
                            market_value = None
                            
                            # 插入到历史表
                            cursor.execute("""
                                INSERT OR REPLACE INTO etf_price_history 
                                (code, price_change_rate, turnover_rate, daily_volume, transaction_count, market_value, date, update_time)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (code, change_rate, turnover_rate, amount, transaction_count, market_value, current_date, current_time))
                            counter += 1
                    
                    # 提交事务
                    conn.commit()
                    print(f"成功导入 {counter} 条价格数据到 etf_price_history 表，日期为 {current_date}")
                else:
                    print("etf_price 表中没有数据，无法导入")
        except Exception as e:
            print(f"导入价格历史数据出错: {str(e)}")
            traceback.print_exc()
            conn.rollback()
        
        # 查询和打印导入后的结果
        try:
            cursor.execute("SELECT date, COUNT(*) FROM etf_price_history GROUP BY date ORDER BY date")
            date_counts = cursor.fetchall()
            if date_counts:
                print("\nETF价格历史数据日期统计:")
                for date, count in date_counts:
                    print(f"  {date}: {count}条记录")
            else:
                print("ETF价格历史表中没有数据")
        except Exception as e:
            print(f"查询价格历史数据统计出错: {str(e)}")
        
        print("\nETF价格历史表初始化完成")
    except Exception as e:
        print(f"初始化ETF价格历史表出错: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()

def main():
    """主函数"""
    init_price_history_table()

if __name__ == "__main__":
    main() 