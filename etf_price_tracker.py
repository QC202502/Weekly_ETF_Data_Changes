import pandas as pd
import os
import datetime
import time
import akshare as ak
import requests
import random
from functools import wraps

def retry_on_exception(max_retries=3, delay=2):
    """
    重试装饰器，用于在发生异常时自动重试函数
    
    参数:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        print(f"达到最大重试次数 {max_retries}，操作失败: {str(e)}")
                        raise
                    print(f"发生错误: {str(e)}，{delay}秒后进行第{retries}次重试...")
                    time.sleep(delay * retries)  # 指数退避策略
        return wrapper
    return decorator

class ETFPriceTracker:
    def __init__(self, token=None, use_proxy=False, proxy_list=None, max_retries=3):
        """
        初始化ETF价格追踪器
        
        参数:
            token: 为了保持与原接口兼容，保留此参数，但AKShare不需要token
            use_proxy: 是否使用代理
            proxy_list: 代理列表，格式为["http://ip:port", ...]
            max_retries: 最大重试次数
        """
        # 创建数据目录
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # 代理设置
        self.use_proxy = use_proxy
        self.proxy_list = proxy_list or []
        self.max_retries = max_retries
        
        # 如果启用代理但没有提供代理列表，使用默认免费代理
        if self.use_proxy and not self.proxy_list:
            self.proxy_list = [
                None,  # 无代理选项
                # 可以在这里添加可靠的代理服务器
            ]
        
        # 设置AKShare的HTTP请求超时时间
        if hasattr(ak, "set_http_timeout"):
            ak.set_http_timeout(20)  # 设置超时时间为20秒
    
    def _set_proxy(self):
        """
        设置代理
        """
        if not self.use_proxy or not self.proxy_list:
            return
            
        # 随机选择一个代理
        proxy = random.choice(self.proxy_list)
        if proxy:
            os.environ['http_proxy'] = proxy
            os.environ['https_proxy'] = proxy
            print(f"使用代理: {proxy}")
        else:
            # 清除代理设置
            if 'http_proxy' in os.environ:
                del os.environ['http_proxy']
            if 'https_proxy' in os.environ:
                del os.environ['https_proxy']
            print("不使用代理")
    
    @retry_on_exception(max_retries=3, delay=2)
    def get_all_etfs(self):
        """
        获取所有ETF基金列表
        
        返回:
            pandas.DataFrame: 包含所有ETF基金的基本信息
        """
        try:
            # 设置代理
            self._set_proxy()
            
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
            # 如果使用代理失败，尝试不使用代理
            if self.use_proxy and 'http_proxy' in os.environ:
                print("尝试不使用代理重新获取...")
                if 'http_proxy' in os.environ:
                    del os.environ['http_proxy']
                if 'https_proxy' in os.environ:
                    del os.environ['https_proxy']
                try:
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
                except Exception as inner_e:
                    print(f"不使用代理获取ETF列表也失败: {str(inner_e)}")
            return pd.DataFrame()
    
    @retry_on_exception(max_retries=3, delay=2)
    def get_etf_daily_price(self, ts_code, start_date=None, end_date=None):
        """
        获取单个ETF的每日价格数据
        
        参数:
            ts_code: ETF的TS代码
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        返回:
            pandas.DataFrame: 包含ETF每日价格数据
        """
        try:
            # 设置代理
            self._set_proxy()
            
            # 从ts_code中提取代码
            symbol = ts_code.split('.')[0]
            
            # 如果未指定日期，默认获取最近30个交易日数据
            if not end_date:
                end_date = datetime.datetime.now().strftime('%Y-%m-%d')
            else:
                # 转换日期格式从YYYYMMDD到YYYY-MM-DD
                end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"
                
            if not start_date:
                # 获取近30个交易日的数据
                start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
            else:
                # 转换日期格式从YYYYMMDD到YYYY-MM-DD
                start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
            
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
            # 如果使用代理失败，尝试不使用代理
            if self.use_proxy and 'http_proxy' in os.environ:
                print("尝试不使用代理重新获取...")
                if 'http_proxy' in os.environ:
                    del os.environ['http_proxy']
                if 'https_proxy' in os.environ:
                    del os.environ['https_proxy']
                try:
                    # 重新获取ETF每日价格
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
                except Exception as inner_e:
                    print(f"不使用代理获取ETF {ts_code} 价格数据也失败: {str(inner_e)}")
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
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
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
        
        # 调用通用方法处理ETF数据
        return self._process_etf_prices(etfs, start_date, end_date)
    
    def get_all_etf_prices(self, start_date=None, end_date=None):
        """
        获取所有ETF的价格数据并计算涨跌幅
        
        参数:
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        返回:
            pandas.DataFrame: 包含所有ETF最新价格和涨跌幅的汇总数据
        """
        # 获取所有ETF列表
        etfs = self.get_all_etfs()
        if etfs.empty:
            return pd.DataFrame()
        
        # 调用通用方法处理ETF数据
        return self._process_etf_prices(etfs, start_date, end_date)
    
    def _process_etf_prices(self, etfs, start_date=None, end_date=None):
        """
        处理ETF价格数据的通用方法
        
        参数:
            etfs: 包含ETF基本信息的DataFrame
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        返回:
            pandas.DataFrame: 包含ETF最新价格和涨跌幅的汇总数据
        """
        # 存储所有ETF的最新数据
        results = []
        
        # 获取当前日期作为默认结束日期
        if not end_date:
            end_date = datetime.datetime.now().strftime('%Y%m%d')
        
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
    
    def save_data(self, data, filename=None, legacy_format=True):
        """
        保存ETF价格数据到CSV文件
        
        参数:
            data: 包含ETF价格数据的DataFrame
            filename: 输出文件名，如果为None，则使用默认文件名
            legacy_format: 是否同时保存为旧格式文件名(etf_prices_YYYYMMDD.csv)，默认为True
            
        返回:
            str: 保存的文件路径(新格式文件路径)
        """
        if data.empty:
            return None
        
        # 如果未指定文件名，使用默认文件名
        if not filename:
            today = datetime.datetime.now().strftime('%Y%m%d')
            filename = f"ETF_价格数据_{today}.csv"
            
            # 同时创建旧格式文件名(用于兼容旧应用)
            if legacy_format:
                legacy_filename = f"etf_prices_{today}.csv"
                legacy_file_path = os.path.join(self.data_dir, legacy_filename)
                data.to_csv(legacy_file_path, index=False, encoding='utf-8-sig')
                print(f"已同时保存兼容格式文件: {legacy_file_path}")
        
        # 确保文件名有.csv后缀
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # 保存文件
        file_path = os.path.join(self.data_dir, filename)
        data.to_csv(file_path, index=False, encoding='utf-8-sig')
        return file_path