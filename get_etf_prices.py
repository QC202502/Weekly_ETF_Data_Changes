#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ETF价格数据获取工具

使用AKShare获取所有ETF的每日收盘价信息，包括：
- 代码
- 场内简称
- 当日涨跌幅
- 近五日涨跌幅
- 年初至今涨跌幅

使用方法：
1. 直接运行此脚本: python get_etf_prices.py
2. 可选参数:
   -s, --start: 指定开始日期(格式:YYYYMMDD)
   -e, --end: 指定结束日期(格式:YYYYMMDD)
   -o, --output: 指定输出文件名
"""

import os
import sys
import argparse
import time
from etf_price_tracker import ETFPriceTracker

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='获取ETF价格数据')
    parser.add_argument('-s', '--start', help='开始日期(格式:YYYYMMDD)')
    parser.add_argument('-e', '--end', help='结束日期(格式:YYYYMMDD)')
    parser.add_argument('-o', '--output', help='输出文件名')
    parser.add_argument('-n', '--number', type=int, default=0, help='要获取的ETF数量，默认为0表示获取所有ETF')
    parser.add_argument('-a', '--all', action='store_true', help='获取所有ETF数据，如果指定此参数，则忽略-n参数')
    parser.add_argument('-p', '--proxy', action='store_true', help='启用代理功能')
    parser.add_argument('-r', '--retries', type=int, default=3, help='最大重试次数，默认为3')
    parser.add_argument('--no-proxy', action='store_true', help='禁用所有代理设置')
    return parser.parse_args()

def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    try:
        # 处理代理设置
        use_proxy = args.proxy
        if args.no_proxy:
            use_proxy = False
            # 清除可能存在的代理环境变量
            if 'http_proxy' in os.environ:
                del os.environ['http_proxy']
            if 'https_proxy' in os.environ:
                del os.environ['https_proxy']
            print("已禁用所有代理设置")
        
        # 初始化ETF价格追踪器，根据命令行参数设置代理和重试次数
        tracker = ETFPriceTracker(use_proxy=use_proxy, max_retries=args.retries)
        
        # 确定要获取的ETF数量
        limit = 0  # 默认获取所有ETF
        if args.all:
            limit = 0
            print("正在获取所有ETF价格数据...")
        elif args.number > 0:
            limit = args.number
            print(f"正在获取{limit}只ETF价格数据...")
        else:
            print("正在获取ETF价格数据...")
            
        if use_proxy:
            print("已启用代理功能，最大重试次数：", args.retries)
            
        # 获取ETF价格数据
        if limit > 0:
            # 使用ETFPriceTracker中的get_limited_etf_prices方法获取指定数量的ETF数据
            etf_prices = tracker.get_limited_etf_prices(limit, args.start, args.end)
        else:
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