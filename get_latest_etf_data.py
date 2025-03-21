#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
获取最新ETF数据

本脚本基于AKShare库获取最新的ETF价格数据，并将结果保存为CSV文件。
文件名格式为etf_prices_YYYYMMDD.csv，其中YYYYMMDD为数据中的实际交易日期。
然后自动生成ETF价格推荐数据。

使用方法：
python get_latest_etf_data.py
"""

import os
import sys
import datetime
import pandas as pd

# 导入ETF价格追踪器
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from get_etf_prices_akshare_fixed import ETFPriceTrackerAKShare
from etf_price_recommendation import main as generate_price_recommendations

def main():
    # 获取当前日期
    today = datetime.datetime.now()
    
    # 设置日期范围为前3天到今天，确保能获取到最近的交易日数据
    end_date = today.strftime('%Y-%m-%d')
    start_date = (today - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
    
    print(f"正在获取{start_date}至{end_date}的ETF数据...")
    
    # 初始化ETF价格追踪器
    tracker = ETFPriceTrackerAKShare(debug=True)
    
    # 获取所有ETF的价格数据
    print("正在获取所有ETF价格数据...")
    etf_prices = tracker.get_all_etf_prices(start_date, end_date)
    
    if etf_prices.empty:
        print("未能获取ETF价格数据")
        return 1
    
    # 显示数据概览
    print(f"\n成功获取{len(etf_prices)}只ETF的价格数据")
    print("\n数据预览:")
    print(etf_prices.head())
    
    # 获取数据中的实际交易日期（取最新的一个交易日期）
    if '交易日期' in etf_prices.columns:
        # 提取所有交易日期
        trade_dates = etf_prices['交易日期'].unique()
        # 找到最新的交易日期
        latest_date = max(trade_dates)
        
        print(f"\n找到最新的交易日期: {latest_date}")
        
        # 使用实际交易日期作为文件名
        filename = f"etf_prices_{latest_date}.csv"
    else:
        # 如果没有交易日期列，使用当前日期作为文件名
        filename = f"etf_prices_{today.strftime('%Y%m%d')}.csv"
    
    # 保存数据
    file_path = tracker.save_data(etf_prices, filename)
    print(f"\n数据已保存至: {file_path}")
    
    # 生成ETF价格推荐数据
    print("\n正在生成ETF价格推荐数据...")
    generate_price_recommendations()
    print("ETF价格推荐数据生成完成")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())