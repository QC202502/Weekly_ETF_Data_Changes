#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试ETF涨幅排行查询
"""

import sqlite3
import json
from datetime import datetime

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('data/etf_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def test_price_return_query():
    """测试ETF涨幅排行查询"""
    # 准备推荐榜单数据
    recommendations = {
        "price_return": [], # 涨幅TOP20
        "trade_date": ""
    }
    
    # 获取数据库连接
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取最新的日期
        cursor.execute("SELECT MAX(date) FROM etf_price")
        latest_date = cursor.fetchone()[0]
        print(f"最新日期: {latest_date}")
        
        # 使用GROUP BY和MAX来找出每个指数最大涨幅的ETF
        query = """
        SELECT i1.code, i1.name, p1.change_rate, i1.fund_manager, i1.fund_size, 
               i1.tracking_index_code, i1.tracking_index_name,
               CASE WHEN b1.code IS NOT NULL THEN 1 ELSE 0 END as is_business
        FROM etf_price p1
        JOIN etf_info i1 ON p1.code = i1.code
        LEFT JOIN etf_business b1 ON p1.code = b1.code
        JOIN (
            SELECT i.tracking_index_code, MAX(p.change_rate) as max_change_rate
            FROM etf_price p
            JOIN etf_info i ON p.code = i.code
            WHERE p.date = ? AND i.tracking_index_code IS NOT NULL AND i.tracking_index_code != ''
            GROUP BY i.tracking_index_code
        ) sub ON i1.tracking_index_code = sub.tracking_index_code AND p1.change_rate = sub.max_change_rate
        WHERE p1.date = ?
        ORDER BY p1.change_rate DESC
        LIMIT 20
        """
        
        cursor.execute(query, (latest_date, latest_date))
        
        for row in cursor.fetchall():
            row_dict = dict(row)
            print(f"ETF: {row_dict['code']}, 涨幅: {row_dict['change_rate']}, 指数: {row_dict['tracking_index_code']}")
            
            # 添加到推荐列表
            recommendations["price_return"].append({
                'code': row_dict['code'],
                'name': row_dict['name'],
                'daily_return': round(float(row_dict['change_rate']), 2) if row_dict['change_rate'] else 0,
                'manager': row_dict['fund_manager'],
                'scale': round(float(row_dict['fund_size']), 2) if row_dict['fund_size'] else 0,
                'is_business': bool(row_dict['is_business']),
                'business_text': "商务品" if row_dict['is_business'] else "非商务品",
                'index_code': row_dict['tracking_index_code'],
                'index_name': row_dict['tracking_index_name'] or row_dict['tracking_index_code']
            })
        
        # 添加交易日期信息
        if latest_date:
            try:
                # 将日期格式化为"月日"格式
                date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
                formatted_date = f"{date_obj.month}月{date_obj.day}日"
                recommendations["trade_date"] = formatted_date
            except Exception as e:
                print(f"日期格式化错误: {str(e)}")
                recommendations["trade_date"] = latest_date
        
        print(f"成功获取ETF涨幅推荐数据，共{len(recommendations['price_return'])}条记录")
        
        # 将结果保存为JSON文件
        with open('price_return_recommendations.json', 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2)
        
        print("推荐数据已保存到 price_return_recommendations.json")
        
    except Exception as e:
        print(f"获取涨幅数据出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_price_return_query() 