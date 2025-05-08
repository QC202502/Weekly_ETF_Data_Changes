#!/usr/bin/env python3
"""
修改数据库表结构

此脚本为现有数据库表添加变化数据字段
"""

from database.models import Database
import sqlite3

def alter_tables():
    """修改数据库表结构，添加变化数据字段"""
    db = Database()
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 获取etf_attention_history表的列信息
        cursor.execute("PRAGMA table_info(etf_attention_history)")
        att_columns = [column[1] for column in cursor.fetchall()]
        
        # 获取etf_holders_history表的列信息
        cursor.execute("PRAGMA table_info(etf_holders_history)")
        holder_columns = [column[1] for column in cursor.fetchall()]
        
        # 为etf_attention_history表添加变化字段
        if 'daily_change' not in att_columns:
            cursor.execute("ALTER TABLE etf_attention_history ADD COLUMN daily_change INTEGER")
            print("已添加字段: etf_attention_history.daily_change")
        
        if 'five_day_change' not in att_columns:
            cursor.execute("ALTER TABLE etf_attention_history ADD COLUMN five_day_change INTEGER")
            print("已添加字段: etf_attention_history.five_day_change")
        
        # 为etf_holders_history表添加变化字段
        if 'holder_daily_change' not in holder_columns:
            cursor.execute("ALTER TABLE etf_holders_history ADD COLUMN holder_daily_change INTEGER")
            print("已添加字段: etf_holders_history.holder_daily_change")
        
        if 'holder_five_day_change' not in holder_columns:
            cursor.execute("ALTER TABLE etf_holders_history ADD COLUMN holder_five_day_change INTEGER")
            print("已添加字段: etf_holders_history.holder_five_day_change")
        
        if 'value_daily_change' not in holder_columns:
            cursor.execute("ALTER TABLE etf_holders_history ADD COLUMN value_daily_change REAL")
            print("已添加字段: etf_holders_history.value_daily_change")
        
        if 'value_five_day_change' not in holder_columns:
            cursor.execute("ALTER TABLE etf_holders_history ADD COLUMN value_five_day_change REAL")
            print("已添加字段: etf_holders_history.value_five_day_change")
        
        if 'amount_daily_change' not in holder_columns:
            cursor.execute("ALTER TABLE etf_holders_history ADD COLUMN amount_daily_change REAL")
            print("已添加字段: etf_holders_history.amount_daily_change")
        
        if 'amount_five_day_change' not in holder_columns:
            cursor.execute("ALTER TABLE etf_holders_history ADD COLUMN amount_five_day_change REAL")
            print("已添加字段: etf_holders_history.amount_five_day_change")
        
        # 更新表中的现有数据
        print("为表中的现有数据计算变化值...")
        
        # 更新etf_attention_history表变化数据
        update_attention_changes(cursor)
        
        # 更新etf_holders_history表变化数据
        update_holder_changes(cursor)
        
        # 提交事务
        conn.commit()
        
        print("数据库表修改成功")
    except Exception as e:
        print(f"修改数据库表失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def update_attention_changes(cursor):
    """更新etf_attention_history表的变化数据"""
    # 获取所有唯一的ETF代码
    cursor.execute("SELECT DISTINCT code FROM etf_attention_history")
    etf_codes = [row[0] for row in cursor.fetchall()]
    print(f"更新{len(etf_codes)}个ETF的自选人数变化数据...")
    
    for code in etf_codes:
        # 按日期降序获取所有记录
        cursor.execute("""
            SELECT code, date, attention_count
            FROM etf_attention_history
            WHERE code = ?
            ORDER BY date DESC
        """, (code,))
        
        records = cursor.fetchall()
        
        # 需要至少2条记录才能计算变化
        if len(records) < 2:
            continue
        
        # 计算并更新每个记录的变化值
        for i, (code, date, count) in enumerate(records):
            # 日变化 (需要前一天的数据)
            daily_change = None
            if i < len(records) - 1:
                prev_count = records[i+1][2]
                daily_change = count - prev_count
            
            # 5日变化 (需要5天前的数据)
            five_day_change = None
            if i + 5 < len(records):
                five_day_before_count = records[i+5][2]
                five_day_change = count - five_day_before_count
            
            # 更新记录
            if daily_change is not None or five_day_change is not None:
                update_sql = "UPDATE etf_attention_history SET "
                update_parts = []
                params = []
                
                if daily_change is not None:
                    update_parts.append("daily_change = ?")
                    params.append(daily_change)
                
                if five_day_change is not None:
                    update_parts.append("five_day_change = ?")
                    params.append(five_day_change)
                
                update_sql += ", ".join(update_parts)
                update_sql += " WHERE code = ? AND date = ?"
                params.extend([code, date])
                
                cursor.execute(update_sql, params)

def update_holder_changes(cursor):
    """更新etf_holders_history表的变化数据"""
    # 获取所有唯一的ETF代码
    cursor.execute("SELECT DISTINCT code FROM etf_holders_history")
    etf_codes = [row[0] for row in cursor.fetchall()]
    print(f"更新{len(etf_codes)}个ETF的持仓变化数据...")
    
    for code in etf_codes:
        # 按日期降序获取所有记录
        cursor.execute("""
            SELECT code, date, holder_count, holding_amount, holding_value
            FROM etf_holders_history
            WHERE code = ?
            ORDER BY date DESC
        """, (code,))
        
        records = cursor.fetchall()
        
        # 需要至少2条记录才能计算变化
        if len(records) < 2:
            continue
        
        # 计算并更新每个记录的变化值
        for i, (code, date, holder_count, holding_amount, holding_value) in enumerate(records):
            # 日变化 (需要前一天的数据)
            holder_daily_change = None
            amount_daily_change = None
            value_daily_change = None
            
            if i < len(records) - 1:
                prev_holder_count = records[i+1][2]
                prev_holding_amount = records[i+1][3]
                prev_holding_value = records[i+1][4]
                
                holder_daily_change = holder_count - prev_holder_count
                amount_daily_change = holding_amount - prev_holding_amount
                value_daily_change = holding_value - prev_holding_value
            
            # 5日变化 (需要5天前的数据)
            holder_five_day_change = None
            amount_five_day_change = None
            value_five_day_change = None
            
            if i + 5 < len(records):
                five_day_before_holder_count = records[i+5][2]
                five_day_before_holding_amount = records[i+5][3]
                five_day_before_holding_value = records[i+5][4]
                
                holder_five_day_change = holder_count - five_day_before_holder_count
                amount_five_day_change = holding_amount - five_day_before_holding_amount
                value_five_day_change = holding_value - five_day_before_holding_value
            
            # 更新记录
            has_changes = any(change is not None for change in [
                holder_daily_change, amount_daily_change, value_daily_change,
                holder_five_day_change, amount_five_day_change, value_five_day_change
            ])
            
            if has_changes:
                update_sql = "UPDATE etf_holders_history SET "
                update_parts = []
                params = []
                
                for field, value in [
                    ("holder_daily_change", holder_daily_change),
                    ("amount_daily_change", amount_daily_change),
                    ("value_daily_change", value_daily_change),
                    ("holder_five_day_change", holder_five_day_change),
                    ("amount_five_day_change", amount_five_day_change),
                    ("value_five_day_change", value_five_day_change)
                ]:
                    if value is not None:
                        update_parts.append(f"{field} = ?")
                        params.append(value)
                
                update_sql += ", ".join(update_parts)
                update_sql += " WHERE code = ? AND date = ?"
                params.extend([code, date])
                
                cursor.execute(update_sql, params)

if __name__ == "__main__":
    alter_tables() 