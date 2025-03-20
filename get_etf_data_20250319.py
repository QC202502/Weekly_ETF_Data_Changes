#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
获取2025年3月19日的ETF数据

本脚本基于AKShare库获取2025年3月19日的ETF价格数据，并将结果保存为CSV文件。
文件名格式为etf_prices_YYYYMMDD.csv，其中YYYYMMDD为数据中的实际交易日期。

使用方法：
python get_etf_data_20250319.py
"""

import os
import sys
import datetime
import pandas as pd

# 导入ETF价格追踪器
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from get_etf_prices_akshare_fixed import ETFPriceTrackerAKShare

def main():
    # 指定目标日期：2025年3月19日
    target_date = "2025-03-19"
    
    # 为确保能获取到目标日期的数据，设置日期范围为前后各1天
    start_date = "2025-03-18"
    end_date = "2025-03-20"
    
    print(f"正在获取{target_date}的ETF数据...")
    
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
        # 找到最接近目标日期的交易日期
        target_date_fmt = datetime.datetime.strptime(target_date, '%Y-%m-%d').strftime('%Y%m%d')
        closest_date = min(trade_dates, key=lambda x: abs(int(x) - int(target_date_fmt)))
        
        print(f"\n找到最接近{target_date}的交易日期: {closest_date}")
        
        # 使用实际交易日期作为文件名
        filename = f"etf_prices_{closest_date}.csv"
    else:
        # 如果没有交易日期列，使用目标日期作为文件名
        filename = f"etf_prices_{target_date_fmt}.csv"
    
    # 保存数据
    file_path = tracker.save_data(etf_prices, filename)
    print(f"\n数据已保存至: {file_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())