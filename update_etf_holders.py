#!/usr/bin/env python3
"""
从历史表更新ETF持仓数据

此脚本从etf_holders_history表获取最新数据并更新etf_holders表
"""

import sqlite3
import os
from datetime import datetime

def update_holders_from_history():
    """从历史表更新ETF持仓数据"""
    print("开始从历史表更新ETF持仓数据...")
    
    # 连接数据库
    db_path = os.path.join('data', 'etf_data.db')
    conn = sqlite3.connect(db_path)
    # 设置行工厂，使查询结果作为字典返回
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # 获取历史表中所有ETF代码的最新数据
        cursor.execute("""
            WITH latest_dates AS (
                SELECT code, MAX(date) as latest_date
                FROM etf_holders_history
                GROUP BY code
            )
            SELECT h.*
            FROM etf_holders_history h
            JOIN latest_dates l ON h.code = l.code AND h.date = l.latest_date
        """)
        
        latest_data = cursor.fetchall()
        print(f"找到{len(latest_data)}个ETF的最新持仓数据")
        
        # 当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 清空当前表
        cursor.execute("DELETE FROM etf_holders")
        print("已清空etf_holders表")
        
        # 插入最新数据
        count = 0
        for row in latest_data:
            try:
                cursor.execute("""
                    INSERT INTO etf_holders (code, holder_count, holding_amount, holding_value, update_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['code'], row['holder_count'], row['holding_amount'], row['holding_value'], current_time))
                count += 1
            except Exception as e:
                print(f"插入{row['code']}数据时出错: {e}")
        
        conn.commit()
        print(f"成功更新{count}个ETF的持仓数据")
        
        # 检查更新结果
        cursor.execute("SELECT COUNT(*) as count FROM etf_holders")
        result = cursor.fetchone()
        print(f"更新后etf_holders表中有{result['count']}条记录")
        
        # 检查特定ETF的数据是否已更新
        check_codes = ['588000', '159915', '510300']
        for code in check_codes:
            cursor.execute("SELECT * FROM etf_holders WHERE code = ?", (code,))
            data = cursor.fetchone()
            if data:
                print(f"ETF {code} 持仓人数: {data['holder_count']}, 持仓份额: {data['holding_amount']}, 持仓价值: {data['holding_value']}")
            else:
                print(f"ETF {code} 在etf_holders表中未找到数据")
    
    except Exception as e:
        print(f"更新ETF持仓数据时出错: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_holders_from_history() 