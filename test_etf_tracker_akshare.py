#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试ETF价格追踪器 (AKShare版本)

这个脚本用于测试使用AKShare库的ETF价格追踪器功能，获取ETF价格数据并保存到CSV文件。
使用方法：
python test_etf_tracker_akshare.py
"""

import sys
import os
import pandas as pd
import datetime
import time
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
            })
            # 添加ts_code列，格式为代码.交易所
            etfs['ts_code'] = etfs['symbol'] + '.SH'
            etfs.loc[etfs['symbol'].str.startswith('1') | etfs['symbol'].str.startswith('5'), 'ts_code'] = etfs.loc[etfs['symbol'].str.startswith('1') | etfs['symbol'].str.startswith('5'), 'symbol'] + '.SZ'
            
            # 添加其他必要的列
            etfs['fund_type'] = 'ETF'
            etfs['management'] = ''
            
            print(f"成功获取{len(etfs)}只ETF基金信息")
            return etfs
        except Exception as e:
            print(f"获取ETF列表失败: {str(e)}")
            return pd.DataFrame()
    
    def get_etf_daily_price(self, ts_code, start_date=None, end_date=None):
        """
        获取单个ETF的每日价格数据
        
        参数:
            ts_code: ETF的TS代码
            start_date: 开始日期，格式YYYY-MM-DD
            end_date: 结束日期，格式YYYY-MM-DD
            
        返回:
            pandas.DataFrame: 包含ETF每日价格数据
        """
        try:
            # 从ts_code中提取代码
            symbol = ts_code.split('.')[0]
            
            # 如果未指定日期，默认获取最近30个交易日数据
            if not end_date:
                end_date = datetime.datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                # 获取近30个交易日的数据
                start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
            
            # 获取ETF每日价格
            df = ak.fund_etf_hist_sina(symbol=symbol)
            
            # 转换日期格式
            df['trade_date'] = pd.to_datetime(df['date']).dt.strftime('%Y%m%d')
            
            # 重命名列以匹配原有格式
            df = df.rename(columns={
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "vol"
            })
            
            # 筛选日期范围
            start_date_fmt = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y%m%d')
            end_date_fmt = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y%m%d')
            df = df[(df['trade_date'] >= start_date_fmt) & (df['trade_date'] <= end_date_fmt)]
            
            # 按日期升序排序
            df = df.sort_values('trade_date')
            
            return df
        except Exception as e:
            print(f"获取ETF {ts_code} 价格数据失败: {str(e)}")
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
            ts_code = row['ts_code']
            fund_name = row['name']
            
            print(f"正在处理 {i+1}/{len(etfs)}: {fund_name} ({ts_code})")
            
            # 获取价格数据
            price_data = self.get_etf_daily_price(ts_code, start_date, end_date)
            if price_data.empty:
                continue
            
            # 计算涨跌幅
            price_data = self.calculate_returns(price_data)
            
            # 获取最新一天的数据
            latest_data = price_data.iloc[-1].to_dict()
            
            # 添加基金名称和代码
            latest_data['fund_name'] = fund_name
            latest_data['ts_code'] = ts_code
            latest_data['symbol'] = ts_code.split('.')[0]
            
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
            return ""
        
        # 如果未指定文件名，使用默认文件名
        if not filename:
            today = datetime.datetime.now().strftime('%Y%m%d')
            filename = f"etf_prices_{today}.csv"
        
        # 确保文件名有.csv后缀
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # 保存到数据目录
        file_path = os.path.join(self.data_dir, filename)
        data.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return file_path

def main():
    try:
        # 初始化ETF价格追踪器
        print("正在初始化ETF价格追踪器(AKShare版本)...")
        tracker = ETFPriceTrackerAKShare()
        
        # 获取所有ETF基金列表
        print("\n正在获取ETF基金列表...")
        etfs = tracker.get_all_etfs()
        if etfs.empty:
            print("获取ETF列表失败")
            return 1
        
        print(f"成功获取{len(etfs)}只ETF基金信息")
        print("\nETF列表预览:")
        print(etfs[['ts_code', 'name']].head())
        
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