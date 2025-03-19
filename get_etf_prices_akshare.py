#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ETF价格数据获取工具 (使用AKShare替代方案)

由于Tushare API需要特定权限才能访问ETF数据，本脚本使用AKShare库作为替代方案获取ETF数据。
AKShare是一个开源的金融数据接口库，可以免费获取ETF数据。

使用方法：
1. 安装依赖: pip install akshare pandas matplotlib
2. 直接运行此脚本: python get_etf_prices_akshare.py
3. 可选参数:
   -s, --start: 指定开始日期(格式:YYYY-MM-DD)
   -e, --end: 指定结束日期(格式:YYYY-MM-DD)
   -o, --output: 指定输出文件名
"""

import os
import sys
import argparse
import datetime
import time
import pandas as pd
import akshare as ak

class ETFPriceTrackerAKShare:
    def __init__(self):
        """
        初始化ETF价格追踪器
        """
        # 创建数据目录
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_all_etfs(self):
        """
        获取所有ETF基金列表
        
        返回:
            pandas.DataFrame: 包含所有ETF基金的基本信息
        """
        try:
            # 获取所有ETF基金列表
            etfs = ak.fund_etf_category_sina(symbol="ETF基金")
            # 重命名列以匹配原有格式
            etfs = etfs.rename(columns={
                "代码": "symbol",
                "名称": "name",
                "净值": "nav",
                "增长率": "growth_rate"
            })
            # 添加ts_code列（格式：代码.交易所）
            etfs['ts_code'] = etfs['symbol'].apply(lambda x: f"{x}.SH" if x.startswith('5') else f"{x}.SZ")
            print(f"成功获取{len(etfs)}只ETF基金信息")
            return etfs
        except Exception as e:
            print(f"获取ETF列表失败: {str(e)}")
            return pd.DataFrame()
    
    def get_etf_daily_price(self, symbol, start_date=None, end_date=None):
        """
        获取单个ETF的每日价格数据
        
        参数:
            symbol: ETF的代码
            start_date: 开始日期，格式YYYY-MM-DD
            end_date: 结束日期，格式YYYY-MM-DD
            
        返回:
            pandas.DataFrame: 包含ETF每日价格数据
        """
        try:
            # 如果未指定日期，默认获取最近30个交易日数据
            if not end_date:
                end_date = datetime.datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                # 默认获取近30个交易日的数据
                start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
            
            # 获取ETF每日价格
            df = ak.fund_etf_hist_sina(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)
            
            # 重命名列以匹配原有格式
            df = df.rename(columns={
                "date": "trade_date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "vol"
            })
            
            # 转换日期格式为YYYYMMDD
            df['trade_date'] = df['trade_date'].apply(lambda x: x.replace('-', ''))
            
            # 按日期升序排序
            df = df.sort_values('trade_date')
            return df
        except Exception as e:
            print(f"获取ETF {symbol} 价格数据失败: {str(e)}")
            # 添加延迟以避免频繁请求
            time.sleep(1)
            return pd.DataFrame()
    
    def calculate_returns(self, price_data):
        """
        计算涨跌幅
        
        参数:
            price_data: 包含价格数据的DataFrame
            
        返回:
            pandas.DataFrame: 添加了涨跌幅计算的DataFrame
        """
        if price_data.empty:
            return price_data
        
        # 确保按日期排序
        price_data = price_data.sort_values('trade_date')
        
        # 计算日涨跌幅
        price_data['daily_return'] = price_data['close'].pct_change() * 100
        
        # 计算近5日涨跌幅
        price_data['5d_return'] = (price_data['close'] / price_data['close'].shift(5) - 1) * 100
        
        # 计算年初至今涨跌幅
        current_year = datetime.datetime.now().year
        year_start_date = f"{current_year}0101"
        
        # 查找年初第一个交易日的收盘价
        year_start_prices = price_data[price_data['trade_date'] >= year_start_date]
        if not year_start_prices.empty:
            first_price = year_start_prices.iloc[0]['close']
            price_data['ytd_return'] = (price_data['close'] / first_price - 1) * 100
        
        return price_data
    
    def get_limited_etf_prices(self, limit=5, start_date=None, end_date=None):
        """
        获取指定数量ETF的价格数据并计算涨跌幅
        
        参数:
            limit: 要获取的ETF数量，默认为5
            start_date: 开始日期，格式YYYY-MM-DD
            end_date: 结束日期，格式YYYY-MM-DD
            
        返回:
            pandas.DataFrame: 包含指定数量ETF最新价格和涨跌幅的汇总数据
        """
        # 获取所有ETF列表
        etfs = self.get_all_etfs()
        if etfs.empty:
            return pd.DataFrame()
        
        # 限制ETF数量
        if limit > 0 and limit < len(etfs):
            etfs = etfs.head(limit)
            print(f"已限制获取前{limit}只ETF数据")
        
        # 存储所有ETF的最新数据
        results = []
        
        # 获取当前日期作为默认结束日期
        if not end_date:
            end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 处理每个ETF
        for i, row in etfs.iterrows():
            symbol = row['symbol']
            fund_name = row['name']
            ts_code = row['ts_code']
            
            print(f"正在处理 {i+1}/{len(etfs)}: {fund_name} ({symbol})")
            
            # 获取价格数据
            price_data = self.get_etf_daily_price(symbol, start_date, end_date)
            if price_data.empty:
                continue
            
            # 计算涨跌幅
            price_data = self.calculate_returns(price_data)
            
            # 获取最新一天的数据
            latest_data = price_data.iloc[-1].to_dict()
            
            # 添加基金名称和代码
            latest_data['fund_name'] = fund_name
            latest_data['ts_code'] = ts_code
            latest_data['symbol'] = symbol
            
            results.append(latest_data)
            
            # 添加延迟以避免频繁请求
            time.sleep(0.5)
        
        # 转换为DataFrame
        if results:
            result_df = pd.DataFrame(results)
            
            # 选择需要的列并重命名
            columns = {
                'ts_code': 'TS代码',
                'symbol': '代码',
                'fund_name': '场内简称',
                'trade_date': '交易日期',
                'close': '收盘价',
                'daily_return': '当日涨跌幅(%)',
                '5d_return': '近五日涨跌幅(%)',
                'ytd_return': '年初至今涨跌幅(%)'
            }
            
            # 选择并重命名列
            available_columns = [col for col in columns.keys() if col in result_df.columns]
            result_df = result_df[available_columns].rename(columns={col: columns[col] for col in available_columns})
            
            # 格式化数值列，保留两位小数
            for col in ['当日涨跌幅(%)', '近五日涨跌幅(%)', '年初至今涨跌幅(%)']:
                if col in result_df.columns:
                    result_df[col] = result_df[col].round(2)
            
            return result_df
        
        return pd.DataFrame()
        
    def get_all_etf_prices(self, start_date=None, end_date=None):
        """
        获取所有ETF的价格数据并计算涨跌幅
        
        参数:
            start_date: 开始日期，格式YYYY-MM-DD
            end_date: 结束日期，格式YYYY-MM-DD
            
        返回:
            pandas.DataFrame: 包含所有ETF最新价格和涨跌幅的汇总数据
        """
        # 获取所有ETF列表
        etfs = self.get_all_etfs()
        if etfs.empty:
            return pd.DataFrame()
        
        # 存储所有ETF的最新数据
        results = []
        
        # 获取当前日期作为默认结束日期
        if not end_date:
            end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 处理每个ETF
        for i, row in etfs.iterrows():
            symbol = row['symbol']
            fund_name = row['name']
            ts_code = row['ts_code']
            
            print(f"正在处理 {i+1}/{len(etfs)}: {fund_name} ({symbol})")
            
            # 获取价格数据
            price_data = self.get_etf_daily_price(symbol, start_date, end_date)
            if price_data.empty:
                continue
            
            # 计算涨跌幅
            price_data = self.calculate_returns(price_data)
            
            # 获取最新一天的数据
            latest_data = price_data.iloc[-1].to_dict()
            
            # 添加基金名称和代码
            latest_data['fund_name'] = fund_name
            latest_data['ts_code'] = ts_code
            latest_data['symbol'] = symbol
            
            results.append(latest_data)
            
            # 添加延迟以避免频繁请求
            time.sleep(0.5)
        
        # 转换为DataFrame
        if results:
            result_df = pd.DataFrame(results)
            
            # 选择需要的列并重命名
            columns = {
                'ts_code': 'TS代码',
                'symbol': '代码',
                'fund_name': '场内简称',
                'trade_date': '交易日期',
                'close': '收盘价',
                'daily_return': '当日涨跌幅(%)',
                '5d_return': '近五日涨跌幅(%)',
                'ytd_return': '年初至今涨跌幅(%)'
            }
            
            # 选择并重命名列
            available_columns = [col for col in columns.keys() if col in result_df.columns]
            result_df = result_df[available_columns].rename(columns={col: columns[col] for col in available_columns})
            
            # 格式化数值列，保留两位小数
            for col in ['当日涨跌幅(%)', '近五日涨跌幅(%)', '年初至今涨跌幅(%)']:
                if col in result_df.columns:
                    result_df[col] = result_df[col].round(2)
            
            return result_df
        
        return pd.DataFrame()
    
    def save_data(self, data, filename=None):
        """
        保存ETF价格数据到CSV文件
        
        参数:
            data: 包含ETF价格数据的DataFrame
            filename: 输出文件名，如果为None，则使用默认文件名
            
        返回:
            str: 保存的文件路径
        """
        if data.empty:
            return None
        
        # 如果未指定文件名，使用默认文件名
        if not filename:
            today = datetime.datetime.now().strftime('%Y%m%d')
            filename = f"ETF_价格数据_{today}.csv"
        
        # 确保文件名有.csv后缀
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # 保存文件
        file_path = os.path.join(self.data_dir, filename)
        data.to_csv(file_path, index=False, encoding='utf-8-sig')
        return file_path

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='获取ETF价格数据 (AKShare版)')
    parser.add_argument('-s', '--start', help='开始日期(格式:YYYY-MM-DD)')
    parser.add_argument('-e', '--end', help='结束日期(格式:YYYY-MM-DD)')
    parser.add_argument('-o', '--output', help='输出文件名')
    parser.add_argument('-n', '--number', type=int, default=5, help='要获取的ETF数量，默认为5')
    parser.add_argument('-a', '--all', action='store_true', help='获取所有ETF数据，如果指定此参数，则忽略-n参数')
    return parser.parse_args()

def main():
    """
    主函数
    """
    # 解析命令行参数
    args = parse_args()
    
    try:
        # 初始化ETF价格追踪器
        tracker = ETFPriceTrackerAKShare()
        
        # 获取ETF价格数据
        if args.all:
            print("正在获取所有ETF价格数据...")
            etf_prices = tracker.get_all_etf_prices(args.start, args.end)
        else:
            print(f"正在获取{args.number}只ETF价格数据...")
            etf_prices = tracker.get_limited_etf_prices(args.number, args.start, args.end)
        
        if etf_prices.empty:
            print("未能获取ETF价格数据")
            return 1
        
        # 显示数据概览
        print(f"\n成功获取{len(etf_prices)}只ETF的价格数据")
        print("\n数据预览:")
        print(etf_prices)
        
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