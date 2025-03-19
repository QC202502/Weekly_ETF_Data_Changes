#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ETF价格数据获取工具

使用tushare API获取所有ETF的每日收盘价信息，包括：
- 代码
- 场内简称
- 当日涨跌幅
- 近五日涨跌幅
- 年初至今涨跌幅

使用方法：
1. 确保已设置TUSHARE_TOKEN环境变量，或在运行时通过-t参数提供
2. 直接运行此脚本: python get_etf_prices.py
3. 可选参数:
   -t, --token: 指定tushare API令牌
   -s, --start: 指定开始日期(格式:YYYYMMDD)
   -e, --end: 指定结束日期(格式:YYYYMMDD)
   -o, --output: 指定输出文件名
"""

import os
import sys
import argparse
from etf_price_tracker import ETFPriceTracker

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='获取ETF价格数据')
    parser.add_argument('-t', '--token', help='tushare API令牌')
    parser.add_argument('-s', '--start', help='开始日期(格式:YYYYMMDD)')
    parser.add_argument('-e', '--end', help='结束日期(格式:YYYYMMDD)')
    parser.add_argument('-o', '--output', help='输出文件名')
    return parser.parse_args()

def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    # 获取tushare API令牌
    token = args.token or os.environ.get('TUSHARE_TOKEN')
    if not token:
        print("错误: 未提供tushare API令牌，请设置TUSHARE_TOKEN环境变量或使用-t参数提供")
        return 1
    
    try:
        # 初始化ETF价格追踪器
        tracker = ETFPriceTracker(token)
        
        # 获取ETF价格数据
        print("正在获取ETF价格数据...")
        etf_prices = tracker.get_all_etf_prices(args.start, args.end)
        
        if etf_prices.empty:
            print("未能获取ETF价格数据")
            return 1
        
        # 显示数据概览
        print(f"\n成功获取{len(etf_prices)}只ETF的价格数据")
        print("\n数据预览:")
        print(etf_prices.head())
        
        # 保存数据
        file_path = tracker.save_data(etf_prices, args.output)
        print(f"\n数据已保存至: {file_path}")
        
        return 0
    
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())