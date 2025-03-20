#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ETF价格推荐模块

根据最新交易日的涨幅数据，提取涨幅最高的ETF，并按照跟踪指数分组，
从每组中选取涨幅最大的一只ETF，最后取前20个展示在推荐模块中。

使用方法：
python etf_price_recommendation.py [csv文件路径]
"""

import pandas as pd
import os
import sys
import json
from datetime import datetime

def load_etf_price_data(file_path):
    """
    加载ETF价格数据
    
    参数:
        file_path: CSV文件路径
        
    返回:
        pandas.DataFrame: 包含ETF价格数据的DataFrame
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        print(f"成功读取ETF价格数据，共{len(df)}条记录")
        return df
    except Exception as e:
        print(f"读取ETF价格数据失败: {str(e)}")
        return pd.DataFrame()

def get_top_etfs_by_return(df, top_n=20):
    """
    获取涨幅最高的ETF，按照跟踪指数分组，每组取涨幅最大的一只
    
    参数:
        df: 包含ETF价格数据的DataFrame
        top_n: 返回的ETF数量
        
    返回:
        pandas.DataFrame: 包含涨幅最高的ETF数据
    """
    try:
        # 确保必要的列存在
        required_columns = ['TS代码', '代码', '场内简称', '当日涨跌幅(%)', '交易日期']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"警告：缺少以下列：{missing_columns}")
            return pd.DataFrame()
        
        # 获取最新交易日期
        latest_date = df['交易日期'].max()
        print(f"最新交易日期: {latest_date}")
        
        # 筛选最新交易日的数据
        latest_data = df[df['交易日期'] == latest_date].copy()
        
        # 添加跟踪指数列（如果不存在）
        if '跟踪指数代码' not in latest_data.columns:
            # 尝试从TS代码中提取跟踪指数信息
            # 这里假设TS代码的格式可以用来识别跟踪指数
            # 实际应用中可能需要更复杂的逻辑或外部数据源
            latest_data['跟踪指数代码'] = latest_data['TS代码'].apply(lambda x: x.split('.')[0][:6])
            print("警告：数据中缺少'跟踪指数代码'列，已根据TS代码生成临时列")
        
        # 按跟踪指数分组，每组取涨幅最大的一只ETF
        top_etfs_by_index = latest_data.sort_values('当日涨跌幅(%)', ascending=False).groupby('跟踪指数代码').first().reset_index()
        
        # 按涨幅排序，取前N个
        top_etfs = top_etfs_by_index.sort_values('当日涨跌幅(%)', ascending=False).head(top_n)
        
        print(f"成功获取{len(top_etfs)}只涨幅最高的ETF")
        return top_etfs
    except Exception as e:
        print(f"获取涨幅最高的ETF失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def format_recommendations(top_etfs):
    """
    格式化推荐数据，用于前端展示
    
    参数:
        top_etfs: 包含涨幅最高的ETF数据的DataFrame
        
    返回:
        dict: 包含推荐数据的字典
    """
    recommendations = {
        "price_return": []  # 按涨幅排序的ETF
    }
    
    for _, row in top_etfs.iterrows():
        etf_code = row['代码']
        etf_name = row['场内简称']
        daily_return = row['当日涨跌幅(%)']
        
        # 添加到推荐列表
        recommendations["price_return"].append({
            'code': etf_code,
            'name': etf_name,
            'manager': row.get('基金管理人', '未知'),
            'is_business': False,  # 默认为非商务品，实际应用中可能需要从其他数据源获取
            'business_text': "非商务品",
            'index_code': row.get('跟踪指数代码', ''),
            'index_name': row.get('跟踪指数名称', ''),
            'daily_return': round(float(daily_return), 2) if pd.notna(daily_return) else 0
        })
    
    return recommendations

def save_recommendations(recommendations, output_file=None):
    """
    保存推荐数据到JSON文件
    
    参数:
        recommendations: 包含推荐数据的字典
        output_file: 输出文件路径，如果为None，则使用默认路径
        
    返回:
        str: 保存的文件路径
    """
    if not output_file:
        # 创建数据目录
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 使用当前日期生成文件名
        today = datetime.now().strftime('%Y%m%d')
        output_file = os.path.join(data_dir, f"etf_price_recommendations_{today}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, ensure_ascii=False, indent=2)
    
    print(f"推荐数据已保存至: {output_file}")
    return output_file

def main():
    """
    主函数
    """
    # 获取命令行参数中的CSV文件路径
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # 尝试查找默认文件
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        file_path = os.path.join(data_dir, "etf_prices_20250319.csv")
        if not os.path.exists(file_path):
            print(f"错误: 未找到ETF价格数据文件 {file_path}")
            print("使用方法: python etf_price_recommendation.py [csv文件路径]")
            return 1
    
    try:
        # 加载ETF价格数据
        df = load_etf_price_data(file_path)
        if df.empty:
            return 1
        
        # 获取涨幅最高的ETF
        top_etfs = get_top_etfs_by_return(df)
        if top_etfs.empty:
            return 1
        
        # 格式化推荐数据
        recommendations = format_recommendations(top_etfs)
        
        # 保存推荐数据
        save_recommendations(recommendations)
        
        # 打印推荐数据预览
        print("\n推荐数据预览:")
        for i, item in enumerate(recommendations["price_return"][:5]):
            print(f"{i+1}. {item['name']} ({item['code']}): 涨幅 {item['daily_return']}%")
        
        return 0
    
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())