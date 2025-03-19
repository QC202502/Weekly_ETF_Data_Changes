import pandas as pd
import tushare as ts
import os
import datetime
import time

class ETFPriceTracker:
    def __init__(self, token=None):
        """
        初始化ETF价格追踪器
        
        参数:
            token: tushare API令牌，如果为None，则尝试从环境变量获取
        """
        self.token = token or os.environ.get('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("请提供tushare API令牌，或设置TUSHARE_TOKEN环境变量")
        
        # 初始化tushare
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        
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
            # 获取所有基金列表
            funds = self.pro.fund_basic(market='E')
            # 筛选ETF基金
            etfs = funds[funds['fund_type'].str.contains('ETF', na=False)]
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
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        返回:
            pandas.DataFrame: 包含ETF每日价格数据
        """
        try:
            # 如果未指定日期，默认获取最近30个交易日数据
            if not end_date:
                end_date = datetime.datetime.now().strftime('%Y%m%d')
            if not start_date:
                # 获取近30个交易日的数据
                cal_df = self.pro.trade_cal(exchange='SSE', start_date=(datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y%m%d'), end_date=end_date)
                trade_dates = cal_df[cal_df['is_open'] == 1]['cal_date'].values
                if len(trade_dates) >= 30:
                    start_date = trade_dates[-30]
                else:
                    start_date = trade_dates[0] if len(trade_dates) > 0 else (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')
            
            # 获取ETF每日价格
            df = self.pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
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
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
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
    
    def save_data(self, data, filename=None):
        """
        保存ETF价格数据到CSV文件
        
        参数:
            data: 要保存的DataFrame
            filename: 文件名，如果为None，则使用当前日期生成文件名
            
        返回:
            str: 保存的文件路径
        """
        if data.empty:
            print("没有数据可保存")
            return None
        
        # 如果未指定文件名，使用当前日期
        if not filename:
            today = datetime.datetime.now().strftime('%Y%m%d')
            filename = f"ETF_价格数据_{today}.csv"
        
        # 确保文件名有.csv后缀
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # 完整文件路径
        file_path = os.path.join(self.data_dir, filename)
        
        # 保存数据
        data.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"数据已保存至: {file_path}")
        
        return file_path

def main():
    """
    主函数，用于测试ETF价格追踪器
    """
    # 从环境变量获取token，或者直接在这里设置
    token = os.environ.get('TUSHARE_TOKEN')
    
    try:
        # 初始化追踪器
        tracker = ETFPriceTracker(token)
        
        # 获取所有ETF的价格数据
        print("正在获取所有ETF的价格数据...")
        etf_prices = tracker.get_all_etf_prices()
        
        if not etf_prices.empty:
            # 显示数据概览
            print(f"\n成功获取{len(etf_prices)}只ETF的价格数据")
            print("\n数据预览:")
            print(etf_prices.head())
            
            # 保存数据
            file_path = tracker.save_data(etf_prices)
            print(f"\n数据已保存至: {file_path}")
        else:
            print("未能获取ETF价格数据")
    
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()