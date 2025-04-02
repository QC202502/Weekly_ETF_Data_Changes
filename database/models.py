#!/usr/bin/env python3
"""
数据库模型

此模块提供数据库连接和操作功能
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime
from utils.etf_code import normalize_etf_code

class Database:
    """
    数据库操作类
    """
    def __init__(self):
        """初始化数据库连接"""
        self.db_file = 'data/etf_data.db'
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
    
    def connect(self):
        """创建数据库连接"""
        # 确保数据库文件存在
        if not os.path.exists(self.db_file):
            # 创建一个空的数据库文件
            conn = sqlite3.connect(self.db_file)
            conn.close()
        return sqlite3.connect(self.db_file)
    
    def create_tables(self):
        """创建数据库表"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # 创建ETF基本信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etf_info (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    benchmark TEXT,
                    establishment_years REAL,
                    exchange TEXT,
                    establishment_date TEXT,
                    fund_manager TEXT,
                    management_fee_rate REAL,
                    custody_fee_rate REAL,
                    index_usage_fee REAL,
                    tracking_index_code TEXT,
                    daily_tracking_deviation_threshold REAL,
                    annualized_tracking_error_threshold REAL,
                    tracking_error REAL,
                    tracking_error_index REAL,
                    information_ratio REAL,
                    tracking_error_annualized REAL,
                    fund_size REAL,
                    holder_count INTEGER,
                    total_holder_count INTEGER,
                    avg_daily_turnover REAL,
                    fund_manager_short TEXT,
                    fund_short_name TEXT,
                    tracking_index_name TEXT
                )
            ''')
            
            # 创建ETF价格数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etf_price (
                    code TEXT PRIMARY KEY,
                    change_rate REAL,
                    turnover_rate REAL,
                    amount REAL,
                    transaction_count INTEGER,
                    FOREIGN KEY (code) REFERENCES etf_info(code)
                )
            ''')
            
            # 创建ETF自选数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etf_attention (
                    code TEXT PRIMARY KEY,
                    attention_count INTEGER,
                    FOREIGN KEY (code) REFERENCES etf_info(code)
                )
            ''')
            
            # 创建ETF持有人数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etf_holders (
                    code TEXT PRIMARY KEY,
                    holder_count INTEGER,
                    holder_household_count INTEGER,
                    FOREIGN KEY (code) REFERENCES etf_info(code)
                )
            ''')
            
            # 创建ETF指数分类数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etf_index_classification (
                    index_code TEXT PRIMARY KEY,
                    level1 TEXT,
                    level2 TEXT,
                    level3 TEXT,
                    index_name TEXT,
                    fund_count INTEGER
                )
            ''')
            
            # 创建ETF商务协议数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etf_business (
                    code TEXT PRIMARY KEY,
                    index_code TEXT,
                    product_name TEXT,
                    fund_company_short TEXT,
                    personal_share_ratio REAL,
                    institutional_share_ratio REAL,
                    start_date TEXT,
                    end_date TEXT,
                    management_fee_rate REAL,
                    custody_fee_rate REAL,
                    index_usage_fee REAL,
                    total_annual_fee_rate REAL,
                    establishment_date TEXT,
                    fund_size REAL,
                    exchange_short_name TEXT,
                    FOREIGN KEY (code) REFERENCES etf_info(code)
                )
            ''')
            
            conn.commit()
            print("数据库表创建成功")
            return True
        except Exception as e:
            print(f"创建数据库表失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_existing_dates(self, table_name, code=None):
        """获取指定表中已存在的日期"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            if code:
                cursor.execute(f"SELECT DISTINCT date FROM {table_name} WHERE code = ?", (code,))
            else:
                cursor.execute(f"SELECT DISTINCT date FROM {table_name}")
            dates = [row[0] for row in cursor.fetchall()]
            return dates
        except Exception as e:
            print(f"获取日期时出错: {str(e)}")
            return []
        finally:
            conn.close()
    
    def save_etf_info(self, df: pd.DataFrame) -> bool:
        """保存ETF基本信息"""
        try:
            # 标准化ETF代码
            df['证券代码'] = df['证券代码'].apply(normalize_etf_code)
            
            # 标准化列名（去除多余的空格和换行符）
            df.columns = [col.strip().replace('\n', '') for col in df.columns]
            
            # 准备列名映射
            columns_mapping = {
                '证券代码': 'code',
                '证券简称': 'name',
                '业绩比较基准': 'benchmark',
                '成立年限[单位] 年': 'establishment_years',
                '基金上市地点': 'exchange',
                '基金成立日': 'establishment_date',
                '基金管理人': 'fund_manager',
                '管理费率[单位] %': 'management_fee_rate',
                '托管费率[单位] %': 'custody_fee_rate',
                '指数使用费率': 'index_usage_fee',
                '跟踪指数代码': 'tracking_index_code',
                '日均跟踪偏离度阈值(业绩基准)[单位] %': 'daily_tracking_deviation_threshold',
                '年化跟踪误差阈值(业绩基准)[单位] %': 'annualized_tracking_error_threshold',
                '跟踪误差[起始交易日期] S_cal_date(enddate,-52,W,0)[截止交易日期] 最新收盘日[计算周期] 日[收益率计算方法] 普通收益率[标的指数] 上证综合指数[单位] %': 'tracking_error',
                '跟踪误差(跟踪指数)[起始交易日期] S_cal_date(enddate,-52,W,0)[截止交易日期] 最新收盘日[计算周期] 日[收益率计算方法] 普通收益率[单位] %': 'tracking_error_index',
                '信息比率(年化)[起始交易日期] S_cal_date(enddate,-52,W,0)[截止交易日期] 最新收盘日[计算周期] 日[收益率计算方法] 普通收益率[无风险收益率] 一年定存利率（税前）[标的指数] 上证综合指数': 'information_ratio',
                '跟踪误差(年化)[起始交易日期] S_cal_date(enddate,-52,W,0)[截止交易日期] 最新收盘日[计算周期] 日[收益率计算方法] 普通收益率[标的指数] 上证综合指数[单位] %': 'tracking_error_annualized',
                '基金规模(合计)[交易日期] S_cal_date(now(),0,D,0)[单位] 亿元': 'fund_size',
                '基金份额持有人户数[报告期] 20240630[单位] 户': 'holder_count',
                '基金份额持有人户数(合计)[报告期] 20240630[单位] 户': 'total_holder_count',
                '区间日均成交额[起始交易日期] S_cal_date(enddate,-1,M,0)[截止交易日期] 最新收盘日[单位] 亿元': 'avg_daily_turnover',
                '基金管理人简称': 'fund_manager_short',
                '基金场内简称': 'fund_short_name',
                '跟踪指数名称': 'tracking_index_name'
            }
            
            # 重命名列
            df = df.rename(columns=columns_mapping)
            
            # 检查必需字段
            required_columns = ['code', 'name', 'fund_size', 'fund_manager', 'exchange', 
                              'tracking_index_code', 'tracking_error', 'information_ratio', 
                              'total_holder_count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF基本信息缺少必需字段: {missing_columns}")
                return False
            
            # 选择需要的列
            df = df[required_columns]
            
            # 转换数据类型
            numeric_columns = ['fund_size', 'tracking_error', 'information_ratio', 'total_holder_count']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 保存到数据库
            conn = self.connect()
            try:
                df.to_sql('etf_info', conn, if_exists='replace', index=False)
                print(f"成功保存ETF基本信息，共{len(df)}条记录")
                return True
            except Exception as e:
                print(f"保存ETF基本信息失败: {str(e)}")
                return False
            finally:
                conn.close()
        except Exception as e:
            print(f"处理ETF基本信息失败: {str(e)}")
            return False
    
    def save_etf_price(self, df: pd.DataFrame) -> bool:
        """保存ETF价格数据"""
        try:
            # 标准化ETF代码
            df['证券代码'] = df['证券代码'].apply(normalize_etf_code)
            
            # 标准化列名（去除多余的空格和换行符）
            df.columns = [col.strip().replace('\n', '') for col in df.columns]
            
            # 准备列名映射
            columns_mapping = {
                '证券代码': 'code',
                '涨跌幅[交易日期] 最新收盘日[单位] %': 'change_rate',
                '换手率[交易日期] 最新收盘日[单位] %': 'turnover_rate',
                '成交额[交易日期] 最新收盘日[单位] 亿元': 'amount',
                '成交笔数[交易日期] 最新收盘日[单位] 笔': 'transaction_count'
            }
            
            # 重命名列
            df = df.rename(columns=columns_mapping)
            
            # 检查必需字段
            required_columns = ['code', 'change_rate', 'turnover_rate', 'amount', 'transaction_count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF价格数据缺少必需字段: {missing_columns}")
                return False
            
            # 选择需要的列
            df = df[required_columns]
            
            # 转换数据类型
            numeric_columns = ['change_rate', 'turnover_rate', 'amount', 'transaction_count']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 保存到数据库
            conn = self.connect()
            try:
                df.to_sql('etf_price', conn, if_exists='replace', index=False)
                print(f"成功保存ETF价格数据，共{len(df)}条记录")
                return True
            except Exception as e:
                print(f"保存ETF价格数据失败: {str(e)}")
                return False
            finally:
                conn.close()
        except Exception as e:
            print(f"处理ETF价格数据失败: {str(e)}")
            return False
    
    def save_etf_attention(self, df: pd.DataFrame) -> bool:
        """保存ETF自选数据"""
        try:
            print("原始列名：", df.columns.tolist())
            print("原始数据前5行：\n", df.head())
            
            # 检查必需字段
            required_columns = ['code', 'attention_count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF自选数据缺少必需字段: {missing_columns}")
                return False
            
            # 选择需要的列
            df = df[required_columns]
            print("选择需要的列后前5行：\n", df.head())
            
            # 转换数据类型
            df['attention_count'] = pd.to_numeric(df['attention_count'], errors='coerce')
            print("转换数据类型后前5行：\n", df.head())
            
            # 保存到数据库
            conn = self.connect()
            try:
                df.to_sql('etf_attention', conn, if_exists='replace', index=False)
                print(f"成功保存ETF自选数据，共{len(df)}条记录")
                return True
            except Exception as e:
                print(f"保存ETF自选数据失败: {str(e)}")
                return False
            finally:
                conn.close()
        except Exception as e:
            print(f"处理ETF自选数据失败: {str(e)}")
            return False
    
    def save_etf_holders(self, df: pd.DataFrame) -> bool:
        """保存ETF持有人数据"""
        try:
            print("原始列名：", df.columns.tolist())
            print("原始数据前5行：\n", df.head())
            
            # 标准化ETF代码
            df['code'] = df['code'].apply(normalize_etf_code)
            print("标准化ETF代码后前5行：\n", df.head())
            
            # 检查必需字段
            required_columns = ['code', 'name', 'holder_count', 'holder_household_count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF持有人数据缺少必需字段: {missing_columns}")
                return False
            
            # 选择需要的列
            df = df[required_columns]
            print("选择需要的列后前5行：\n", df.head())
            
            # 转换数据类型
            numeric_columns = ['holder_count', 'holder_household_count']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            print("转换数据类型后前5行：\n", df.head())
            
            # 保存到数据库
            conn = self.connect()
            try:
                df.to_sql('etf_holders', conn, if_exists='replace', index=False)
                print(f"成功保存ETF持有人数据，共{len(df)}条记录")
                return True
            except Exception as e:
                print(f"保存ETF持有人数据失败: {str(e)}")
                return False
            finally:
                conn.close()
        except Exception as e:
            print(f"处理ETF持有人数据失败: {str(e)}")
            return False
    
    def save_etf_index_classification(self, df: pd.DataFrame) -> bool:
        """保存ETF指数分类数据"""
        try:
            # 准备列名映射
            columns_mapping = {
                '跟踪指数代码': 'index_code',
                '一级分类': 'level1',
                '二级分类': 'level2',
                '三级分类': 'level3',
                '跟踪指数名称': 'index_name',
                '跟踪基金个数（9 月）': 'fund_count'
            }
            
            # 重命名列
            df = df.rename(columns=columns_mapping)
            
            # 检查必需字段
            required_columns = ['index_code', 'level1', 'level2', 'level3', 'index_name', 'fund_count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF指数分类数据缺少必需字段: {missing_columns}")
                return False
            
            # 选择需要的列
            df = df[required_columns]
            
            # 转换数据类型
            numeric_columns = ['fund_count']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 保存到数据库
            conn = self.connect()
            try:
                df.to_sql('etf_index_classification', conn, if_exists='replace', index=False)
                print(f"成功保存ETF指数分类数据，共{len(df)}条记录")
                return True
            except Exception as e:
                print(f"保存ETF指数分类数据失败: {str(e)}")
                return False
            finally:
                conn.close()
        except Exception as e:
            print(f"处理ETF指数分类数据失败: {str(e)}")
            return False
    
    def save_business_etf(self, df: pd.DataFrame) -> bool:
        """保存ETF商务协议数据"""
        try:
            # 标准化ETF代码
            df['证券代码'] = df['证券代码'].apply(normalize_etf_code)
            
            # 准备列名映射
            columns_mapping = {
                '证券代码': 'code',
                '跟踪指数代码': 'index_code',
                '产品名称': 'product_name',
                '基金公司简称': 'fund_company_short',
                '个人分成比例': 'personal_share_ratio',
                '机构分成比例': 'institutional_share_ratio',
                '开始日期': 'start_date',
                '结束日期': 'end_date',
                '管理费率': 'management_fee_rate',
                '托管费率': 'custody_fee_rate',
                '指数使用费率（人工调整）': 'index_usage_fee',
                '综合年费率（人工调整）': 'total_annual_fee_rate',
                '成立日期': 'establishment_date',
                '规模': 'fund_size',
                '场内简称': 'exchange_short_name'
            }
            
            # 重命名列
            df = df.rename(columns=columns_mapping)
            
            # 检查必需字段
            required_columns = ['code', 'index_code', 'product_name', 'fund_company_short', 
                              'personal_share_ratio', 'institutional_share_ratio', 'start_date', 
                              'end_date', 'management_fee_rate', 'custody_fee_rate', 
                              'index_usage_fee', 'total_annual_fee_rate', 'establishment_date', 
                              'fund_size', 'exchange_short_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF商务协议数据缺少必需字段: {missing_columns}")
                return False
            
            # 选择需要的列
            df = df[required_columns]
            
            # 转换数据类型
            numeric_columns = ['personal_share_ratio', 'institutional_share_ratio', 
                             'management_fee_rate', 'custody_fee_rate', 'index_usage_fee', 
                             'total_annual_fee_rate', 'fund_size']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 转换日期类型
            date_columns = ['start_date', 'end_date', 'establishment_date']
            for col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # 保存到数据库
            conn = self.connect()
            try:
                df.to_sql('etf_business', conn, if_exists='replace', index=False)
                print(f"成功保存ETF商务协议数据，共{len(df)}条记录")
                return True
            except Exception as e:
                print(f"保存ETF商务协议数据失败: {str(e)}")
                return False
            finally:
                conn.close()
        except Exception as e:
            print(f"处理ETF商务协议数据失败: {str(e)}")
            return False

    def get_etf_price_recommendations(self):
        """获取ETF价格推荐数据"""
        try:
            query = """
            SELECT p.code, i.name, p.price_change_rate, p.daily_volume, p.turnover_rate
            FROM etf_price p
            JOIN etf_info i ON p.code = i.code
            ORDER BY p.price_change_rate DESC
            LIMIT 10
            """
            result = self.execute_query(query)
            return [
                {
                    'code': row[0],
                    'name': row[1],
                    'price_change_rate': float(row[2]) if row[2] else 0,
                    'daily_volume': float(row[3]) if row[3] else 0,
                    'turnover_rate': float(row[4]) if row[4] else 0
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取ETF价格推荐数据失败: {str(e)}")
            return None

    def get_etf_holders_recommendations(self):
        """获取ETF持有人数据推荐"""
        try:
            query = """
            SELECT h.code, i.name, h.holder_count, h.holder_household_count
            FROM etf_holders h
            JOIN etf_info i ON h.code = i.code
            ORDER BY h.holder_count DESC
            LIMIT 10
            """
            result = self.execute_query(query)
            return [
                {
                    'code': row[0],
                    'name': row[1],
                    'holder_count': int(row[2]) if row[2] else 0,
                    'holder_household_count': int(row[3]) if row[3] else 0
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取ETF持有人推荐数据失败: {str(e)}")
            return None

    def get_etf_attention_recommendations(self):
        """获取ETF自选数据推荐"""
        try:
            query = """
            SELECT a.code, i.name, a.attention_count
            FROM etf_attention a
            JOIN etf_info i ON a.code = i.code
            ORDER BY a.attention_count DESC
            LIMIT 10
            """
            result = self.execute_query(query)
            return [
                {
                    'code': row[0],
                    'name': row[1],
                    'attention_count': int(row[2]) if row[2] else 0
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取ETF自选推荐数据失败: {str(e)}")
            return None

    def get_etf_amount_recommendations(self):
        """获取ETF成交额推荐数据"""
        try:
            query = """
            SELECT p.code, i.name, p.daily_volume, p.turnover_rate
            FROM etf_price p
            JOIN etf_info i ON p.code = i.code
            ORDER BY p.daily_volume DESC
            LIMIT 10
            """
            result = self.execute_query(query)
            return [
                {
                    'code': row[0],
                    'name': row[1],
                    'daily_volume': float(row[2]) if row[2] else 0,
                    'turnover_rate': float(row[3]) if row[3] else 0
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取ETF成交额推荐数据失败: {str(e)}")
            return None

    def get_all_etf_info(self):
        """获取所有ETF基本信息"""
        try:
            query = "SELECT * FROM etf_info"
            result = self.execute_query(query)
            columns = [
                'code', 'name', 'benchmark', 'years_since_establishment', 'listing_location',
                'establishment_date', 'fund_manager', 'management_fee_rate', 'custodian_fee_rate',
                'index_usage_fee_rate', 'tracking_index_code', 'tracking_deviation_threshold',
                'tracking_error_threshold', 'tracking_error', 'tracking_error_index',
                'information_ratio', 'tracking_error_annualized', 'fund_size', 'holder_count',
                'total_holder_count', 'avg_daily_volume', 'fund_manager_abbr', 'fund_exchange_abbr',
                'tracking_index_name', 'monthly_volume', 'price_change_rate', 'turnover_rate',
                'daily_volume', 'transaction_count', 'market_value'
            ]
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            print(f"获取所有ETF基本信息失败: {str(e)}")
            return []

    def get_all_business_etf(self):
        """获取所有商务ETF数据"""
        try:
            query = "SELECT * FROM etf_business"
            result = self.execute_query(query)
            columns = ['code', 'name', 'agreement_type', 'agreement_status', 'start_date', 'end_date']
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            print(f"获取所有商务ETF数据失败: {str(e)}")
            return []

    def execute_query(self, query, params=None):
        """执行SQL查询"""
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"执行SQL查询失败: {str(e)}")
            return []