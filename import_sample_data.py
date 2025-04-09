#!/usr/bin/env python3
"""
从示例文件导入ETF数据到数据库

此脚本从sample_etf_data.csv读取ETF数据，并导入到数据库中
这是一个一次性脚本，用于初始化数据库
"""

import os
import pandas as pd
from datetime import datetime
from database.models import Database
from services.data_service import initialize_database

def import_sample_data():
    """导入示例数据到数据库"""
    # 初始化数据库表结构
    initialize_database()
    
    # 创建数据库连接
    db = Database()
    
    # 检查样本数据文件是否存在
    sample_file = os.path.join('data', 'sample_etf_data.csv')
    if not os.path.exists(sample_file):
        print(f"样本数据文件 {sample_file} 不存在")
        return False
    
    try:
        # 读取CSV文件
        df = pd.read_csv(sample_file)
        print(f"从 {sample_file} 读取了 {len(df)} 条记录")
        
        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 导入ETF基本信息
        cursor = db.conn.cursor()
        
        # 清空现有数据
        cursor.execute("DELETE FROM etf_info")
        print("已清空etf_info表")
        
        # 批量插入数据
        count = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO etf_info (
                        code, name, manager, fund_size, management_fee_rate, tracking_error,
                        tracking_index_code, tracking_index_name, total_holder_count, update_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['code'], row['name'], row['manager'], row['fund_size'], 
                    row['management_fee_rate'], row['tracking_error'], 
                    row['tracking_index_code'], row['tracking_index_name'],
                    row['total_holder_count'], current_time
                ))
                count += 1
                
                # 如果是商务品，添加到商务品表
                if row.get('is_business', 0) == 1:
                    cursor.execute("""
                        INSERT OR REPLACE INTO etf_business (code, name, update_time)
                        VALUES (?, ?, ?)
                    """, (row['code'], row['name'], current_time))
            except Exception as e:
                print(f"插入记录 {row['code']} 时出错: {str(e)}")
        
        # 提交事务
        db.conn.commit()
        print(f"成功导入 {count} 条ETF基本信息")
        
        # 创建一些模拟的历史数据
        # 自选历史数据
        dates = ['2025-03-19', '2025-03-26', '2025-04-01', '2025-04-08']
        for date in dates:
            for _, row in df.iterrows():
                # 生成一些递增的自选人数
                base_attention = int(row['total_holder_count'] * 0.1)  # 基础自选人数为持有人的10%
                cursor.execute("""
                    INSERT OR REPLACE INTO etf_attention_history (code, attention_count, date, update_time)
                    VALUES (?, ?, ?, ?)
                """, (row['code'], base_attention, date, current_time))
        
        # 持有人历史数据
        for date in dates:
            for _, row in df.iterrows():
                # 使用基本信息中的持有人数作为基础
                cursor.execute("""
                    INSERT OR REPLACE INTO etf_holders_history (code, holder_count, holding_amount, date, update_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['code'], row['total_holder_count'], row['fund_size'] * 10, date, current_time))
        
        # 规模历史数据
        for date in dates:
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO etf_fund_size_history (code, fund_size, date, update_time)
                    VALUES (?, ?, ?, ?)
                """, (row['code'], row['fund_size'], date, current_time))
        
        # 提交事务
        db.conn.commit()
        print(f"成功导入历史数据，日期范围: {dates[0]} 至 {dates[-1]}")
        
        return True
    
    except Exception as e:
        print(f"导入样本数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 关闭数据库连接
        db.close()

if __name__ == "__main__":
    result = import_sample_data()
    if result:
        print("示例数据导入成功")
    else:
        print("示例数据导入失败") 