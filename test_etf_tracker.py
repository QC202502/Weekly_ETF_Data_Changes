#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试ETF价格追踪器

这个脚本用于测试ETF价格追踪器的功能，获取ETF价格数据并保存到CSV文件。
使用方法：
python test_etf_tracker.py
"""

import sys
import os
from etf_price_tracker import ETFPriceTracker

def main():
    try:
        # 初始化ETF价格追踪器
        print(f"正在初始化ETF价格追踪器...")
        tracker = ETFPriceTracker()
        
        # 获取所有ETF基金列表
        print("\n正在获取ETF基金列表...")
        etfs = tracker.get_all_etfs()
        if etfs.empty:
            print("获取ETF列表失败")
            return 1
        
        print(f"成功获取{len(etfs)}只ETF基金信息")
        print("\nETF列表预览:")
        print(etfs[['ts_code', 'name', 'management', 'fund_type']].head())
        
        # 获取单个ETF的价格数据作为示例
        if len(etfs) > 0:
            sample_etf = etfs.iloc[0]
            ts_code = sample_etf['ts_code']
            fund_name = sample_etf['name']
            
            print(f"\n正在获取示例ETF {fund_name} ({ts_code}) 的价格数据...")
            price_data = tracker.get_etf_daily_price(ts_code)
            
            if not price_data.empty:
                # 计算涨跌幅
                price_data = tracker.calculate_returns(price_data)
                
                print("\n价格数据预览:")
                print(price_data.head())
                
                # 获取最新一天的数据
                latest_data = price_data.iloc[-1]
                print(f"\n最新交易日 {latest_data['trade_date']} 的数据:")
                print(f"收盘价: {latest_data['close']}")
                if 'daily_return' in latest_data:
                    print(f"当日涨跌幅: {latest_data['daily_return']:.2f}%")
                if '5d_return' in latest_data:
                    print(f"近五日涨跌幅: {latest_data['5d_return']:.2f}%")
                if 'ytd_return' in latest_data:
                    print(f"年初至今涨跌幅: {latest_data['ytd_return']:.2f}%")
            else:
                print(f"获取ETF {ts_code} 价格数据失败")
        
        # 获取所有ETF的价格数据
        print("\n是否获取所有ETF的价格数据? 这可能需要较长时间 (y/n)")
        choice = input().strip().lower()
        
        if choice == 'y':
            print("\n正在获取所有ETF的价格数据...")
            etf_prices = tracker.get_all_etf_prices()
            
            if not etf_prices.empty:
                print(f"\n成功获取{len(etf_prices)}只ETF的价格数据")
                print("\n数据预览:")
                print(etf_prices.head())
                
                # 保存数据
                file_path = tracker.save_data(etf_prices)
                print(f"\n数据已保存至: {file_path}")
            else:
                print("未能获取ETF价格数据")
        else:
            print("跳过获取所有ETF的价格数据")
        
        return 0
    
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())