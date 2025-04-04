#!/usr/bin/env python3
"""
生成模拟ETF历史数据

此脚本生成更多的模拟历史数据，覆盖从2月14日到4月2日的每周数据点
"""

import os
import re
from datetime import datetime, timedelta
from database.models import Database

def generate_weekly_dates(start_date_str, end_date_str):
    """生成从开始日期到结束日期之间的每周日期列表"""
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # 确保生成的是周五的日期（如果原始日期不是周五，则调整到最近的周五）
    if start_date.weekday() != 4:  # 4 表示周五
        days_to_add = (4 - start_date.weekday()) % 7
        start_date += timedelta(days=days_to_add)
    
    # 生成每周的日期
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=7)
    
    return dates

def generate_attention_history_data(db, dates):
    """生成ETF自选历史数据"""
    print("\n开始生成ETF自选历史数据...")
    
    # 获取已有的自选历史数据日期
    cursor = db.conn.cursor()
    cursor.execute("SELECT DISTINCT date FROM etf_attention_history")
    existing_dates = [row[0] for row in cursor.fetchall()]
    print(f"已有自选历史数据日期: {existing_dates}")
    
    # 获取参考日期的数据（使用最早的一个日期）
    reference_date = sorted(existing_dates)[0]
    print(f"使用参考日期: {reference_date}")
    
    cursor.execute("""
        SELECT code, attention_count
        FROM etf_attention_history
        WHERE date = ?
    """, (reference_date,))
    reference_data = cursor.fetchall()
    
    if not reference_data:
        print(f"无法找到参考日期 {reference_date} 的自选数据")
        return
    
    print(f"找到参考日期 {reference_date} 的自选数据: {len(reference_data)}条记录")
    
    # 为每个目标日期生成历史数据
    added_dates = []
    for date in dates:
        if date in existing_dates:
            print(f"日期 {date} 的ETF自选历史数据已存在，跳过生成")
            continue
        
        print(f"为日期 {date} 生成ETF自选历史数据...")
        
        # 添加更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 根据日期与参考日期的差异调整数据
        reference_datetime = datetime.strptime(reference_date, '%Y-%m-%d')
        target_datetime = datetime.strptime(date, '%Y-%m-%d')
        days_diff = (reference_datetime - target_datetime).days
        
        # 调整因子：日期越早，关注数量越少
        if days_diff > 0:
            adjustment = max(0.85, 1 - days_diff / 100)  # 确保不低于85%
        else:
            adjustment = min(1.15, 1 + abs(days_diff) / 100)  # 确保不高于115%
        
        # 插入数据
        count = 0
        for code, attention_count in reference_data:
            # 调整关注数量（添加一些随机性）
            import random
            random_factor = random.uniform(0.95, 1.05)
            adjusted_attention_count = max(1, int(attention_count * adjustment * random_factor))
            
            try:
                cursor.execute("""
                    INSERT INTO etf_attention_history (code, attention_count, date, update_time)
                    VALUES (?, ?, ?, ?)
                """, (code, adjusted_attention_count, date, current_time))
                count += 1
            except Exception as e:
                print(f"插入自选数据时出错: {str(e)}")
        
        db.conn.commit()
        print(f"成功为日期 {date} 生成 {count} 条ETF自选历史数据")
        added_dates.append((date, count))
    
    # 查询并显示最终结果
    cursor.execute("SELECT date, COUNT(*) FROM etf_attention_history GROUP BY date ORDER BY date")
    attention_dates = cursor.fetchall()
    print("\nETF自选历史数据日期统计:")
    for date, count in attention_dates:
        print(f"  - {date}: {count}条记录")
    
    return added_dates

def generate_holders_history_data(db, dates):
    """生成ETF持有人历史数据"""
    print("\n开始生成ETF持有人历史数据...")
    
    # 获取已有的持有人历史数据日期
    cursor = db.conn.cursor()
    cursor.execute("SELECT DISTINCT date FROM etf_holders_history")
    existing_dates = [row[0] for row in cursor.fetchall()]
    print(f"已有持有人历史数据日期: {existing_dates}")
    
    # 获取参考日期的数据（使用最早的一个日期）
    reference_date = sorted(existing_dates)[0]
    print(f"使用参考日期: {reference_date}")
    
    cursor.execute("""
        SELECT code, holder_count, holding_amount
        FROM etf_holders_history
        WHERE date = ?
    """, (reference_date,))
    reference_data = cursor.fetchall()
    
    if not reference_data:
        print(f"无法找到参考日期 {reference_date} 的持有人数据")
        return
    
    print(f"找到参考日期 {reference_date} 的持有人数据: {len(reference_data)}条记录")
    
    # 为每个目标日期生成历史数据
    added_dates = []
    for date in dates:
        if date in existing_dates:
            print(f"日期 {date} 的ETF持有人历史数据已存在，跳过生成")
            continue
        
        print(f"为日期 {date} 生成ETF持有人历史数据...")
        
        # 添加更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 根据日期与参考日期的差异调整数据
        reference_datetime = datetime.strptime(reference_date, '%Y-%m-%d')
        target_datetime = datetime.strptime(date, '%Y-%m-%d')
        days_diff = (reference_datetime - target_datetime).days
        
        # 调整因子：日期越早，持有人数量和持有金额越少
        if days_diff > 0:
            adjustment = max(0.85, 1 - days_diff / 100)  # 确保不低于85%
        else:
            adjustment = min(1.15, 1 + abs(days_diff) / 100)  # 确保不高于115%
        
        # 插入数据
        count = 0
        for code, holder_count, holding_amount in reference_data:
            # 调整持有人数和持有金额（添加一些随机性）
            import random
            random_factor_holder = random.uniform(0.95, 1.05)
            random_factor_amount = random.uniform(0.95, 1.05)
            
            adjusted_holder_count = max(1, int(holder_count * adjustment * random_factor_holder))
            adjusted_holding_amount = max(1, holding_amount * adjustment * random_factor_amount)
            
            try:
                cursor.execute("""
                    INSERT INTO etf_holders_history (code, holder_count, holding_amount, date, update_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (code, adjusted_holder_count, adjusted_holding_amount, date, current_time))
                count += 1
            except Exception as e:
                print(f"插入持有人数据时出错: {str(e)}")
        
        db.conn.commit()
        print(f"成功为日期 {date} 生成 {count} 条ETF持有人历史数据")
        added_dates.append((date, count))
    
    # 查询并显示最终结果
    cursor.execute("SELECT date, COUNT(*) FROM etf_holders_history GROUP BY date ORDER BY date")
    holders_dates = cursor.fetchall()
    print("\nETF持有人历史数据日期统计:")
    for date, count in holders_dates:
        print(f"  - {date}: {count}条记录")
    
    return added_dates

def main():
    """主函数"""
    # 连接数据库
    db = Database()
    
    # 确保历史表存在
    cursor = db.conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf_attention_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            attention_count INTEGER,
            date TEXT,
            update_time TIMESTAMP
        )
    """)
    
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
    
    # 生成从2月14日到4月2日的每周日期
    weekly_dates = generate_weekly_dates('2025-02-14', '2025-04-02')
    print(f"生成的每周日期: {weekly_dates}")
    
    # 生成ETF自选历史数据
    added_attention_dates = generate_attention_history_data(db, weekly_dates)
    
    # 生成ETF持有人历史数据
    added_holders_dates = generate_holders_history_data(db, weekly_dates)
    
    print("\n所有历史数据生成完成")

if __name__ == "__main__":
    main() 