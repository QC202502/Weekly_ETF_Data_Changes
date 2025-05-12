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
from typing import List, Dict
from services.index_service import get_index_intro  # 导入get_index_intro函数

# 数据库路径
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/etf_data.db')

class Database:
    """
    数据库操作类
    """
    def __init__(self):
        """初始化数据库连接"""
        self.db_file = DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        self.conn = None
        
        # 检查数据库文件是否存在
        if not os.path.exists(self.db_file):
            print(f"警告：数据库文件 {self.db_file} 不存在")
            print("请确保已经导入了ETF数据")
        
        # 初始化连接，但不立即关闭
        self.connect()
        
        # 尝试检查表是否存在，但不关闭连接
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='etf_info'")
            if not cursor.fetchone():
                print("警告：数据库表不存在")
                print("请确保已经导入了ETF数据")
            cursor.close()
        except Exception as e:
            print(f"检查数据库表时出错: {str(e)}")
    
    def connect(self):
        """创建数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_file)
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def execute_query(self, query, params=None):
        """执行SQL查询"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()  # 关闭游标，但不关闭连接
            return result
        except Exception as e:
            print(f"执行SQL查询失败: {str(e)}")
            return []
    
    def get_etf_price_recommendations(self):
        """获取ETF价格推荐数据"""
        try:
            query = """
            SELECT i.code, i.name, i.fund_size, i.total_holder_count
            FROM etf_info i
            ORDER BY i.fund_size DESC
            LIMIT 10
            """
            result = self.execute_query(query)
            return [
                {
                    'code': row[0],
                    'name': row[1],
                    'price_change_rate': 0.0,  # 暂时使用0
                    'amount': float(row[2]) if row[2] else 0,  # 使用基金规模代替
                    'turnover_rate': 0.0  # 暂时使用0
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取ETF价格推荐数据失败: {str(e)}")
            return []
    
    def get_etf_holders_recommendations(self):
        """获取ETF持有人数据推荐"""
        try:
            query = """
            SELECT i.code, i.name, i.total_holder_count, i.fund_size
            FROM etf_info i
            ORDER BY i.total_holder_count DESC
            LIMIT 10
            """
            result = self.execute_query(query)
            return [
                {
                    'code': row[0],
                    'name': row[1],
                    'holder_count': int(row[2]) if row[2] else 0,
                    'holder_household_count': int(row[2]) if row[2] else 0  # 使用total_holder_count代替
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取ETF持有人推荐数据失败: {str(e)}")
            return []
    
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
            return []
    
    def get_etf_amount_recommendations(self):
        """获取ETF成交额推荐数据"""
        try:
            query = """
            SELECT i.code, i.name, i.fund_size, i.total_holder_count
            FROM etf_info i
            ORDER BY i.fund_size DESC
            LIMIT 10
            """
            result = self.execute_query(query)
            return [
                {
                    'code': row[0],
                    'name': row[1],
                    'amount': float(row[2]) if row[2] else 0,  # 使用基金规模代替
                    'turnover_rate': 0.0  # 暂时使用0
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取ETF成交额推荐数据失败: {str(e)}")
            return []
    
    def get_etf_value_recommendations(self):
        """获取ETF持仓价值推荐数据"""
        try:
            query = """
            SELECT i.code, i.name, i.fund_size, i.total_holder_count
            FROM etf_info i
            ORDER BY i.fund_size DESC
            LIMIT 10
            """
            result = self.execute_query(query)
            return [
                {
                    'code': row[0],
                    'name': row[1],
                    'holding_value': float(row[2]) if row[2] else 0,  # 使用基金规模代替
                    'turnover_rate': 0.0  # 暂时使用0
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取ETF持仓价值推荐数据失败: {str(e)}")
            return []
    
    def get_all_etf_info(self):
        """获取所有ETF基本信息"""
        try:
            query = """
            SELECT code, name, fund_size, fund_manager, exchange, tracking_index_code,
                   tracking_error, information_ratio, total_holder_count
            FROM etf_info
            """
            result = self.execute_query(query)
            columns = ['code', 'name', 'fund_size', 'fund_manager', 'exchange', 'tracking_index_code',
                      'tracking_error', 'information_ratio', 'total_holder_count']
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            print(f"获取所有ETF基本信息失败: {str(e)}")
            return []
    
    def get_all_business_etf(self):
        """获取所有商务ETF数据"""
        try:
            query = """
            SELECT code, product_name, fund_company_short, start_date, end_date,
                   management_fee_rate, custody_fee_rate, fund_size
            FROM etf_business
            """
            result = self.execute_query(query)
            columns = ['code', 'name', 'fund_company', 'start_date', 'end_date',
                      'management_fee_rate', 'custody_fee_rate', 'fund_size']
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            print(f"获取所有商务ETF数据失败: {str(e)}")
            return []
    
    def __del__(self):
        """析构函数，确保关闭数据库连接"""
        self.close()

    def create_tables(self):
        """创建数据库表"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # 删除已存在的表
            cursor.execute("DROP TABLE IF EXISTS etf_info")
            cursor.execute("DROP TABLE IF EXISTS etf_business")
            cursor.execute("DROP TABLE IF EXISTS etf_holders")
            cursor.execute("DROP TABLE IF EXISTS etf_attention")
            cursor.execute("DROP TABLE IF EXISTS etf_price") # 假设etf_price表也在这里管理
            cursor.execute("DROP TABLE IF EXISTS etf_index_classification") # 假设etf_index_classification表也在这里管理
            cursor.execute("DROP TABLE IF EXISTS etf_company_analytics") # 新增：删除旧的基金公司分析表
            
            # 创建ETF基本信息表
            cursor.execute("""
                CREATE TABLE etf_info (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    fund_manager TEXT,
                    fund_size REAL,
                    exchange TEXT,
                    tracking_index_code TEXT,
                    tracking_index_name TEXT,
                    tracking_error REAL,
                    information_ratio REAL,
                    total_holder_count INTEGER,
                    management_fee_rate REAL,
                    custody_fee_rate REAL,
                    index_usage_fee REAL,
                    total_annual_fee_rate REAL,
                    monthly_volume REAL,
                    daily_avg_volume REAL,
                    turnover_rate REAL,
                    daily_volume REAL,
                    transaction_count INTEGER,
                    total_market_value REAL,
                    benchmark TEXT,
                    years_since_establishment REAL,
                    establishment_date TEXT,
                    fund_exchange_abbr TEXT,
                    date TEXT,
                    update_time TIMESTAMP
                )
            """)
            
            # 创建ETF商务协议表
            cursor.execute("""
                CREATE TABLE etf_business (
                    code TEXT PRIMARY KEY,
                    product_name TEXT,
                    fund_company_short TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    management_fee_rate REAL,
                    custody_fee_rate REAL,
                    index_usage_fee REAL,
                    total_annual_fee_rate REAL,
                    fund_size REAL,
                    update_time TIMESTAMP,
                    FOREIGN KEY (code) REFERENCES etf_info(code)
                )
            """)
            
            # 创建ETF持有人表
            cursor.execute("""
                CREATE TABLE etf_holders (
                    code TEXT PRIMARY KEY,
                    holder_count INTEGER,
                    holding_amount REAL,
                    holding_value REAL,
                    update_time TIMESTAMP,
                    date TEXT,
                    FOREIGN KEY (code) REFERENCES etf_info(code)
                )
            """)
            
            # 创建ETF自选表
            cursor.execute("""
                CREATE TABLE etf_attention (
                    code TEXT PRIMARY KEY,
                    attention_count INTEGER,
                    update_time TIMESTAMP,
                    FOREIGN KEY (code) REFERENCES etf_info(code)
                )
            """)
            
            # 创建ETF价格表
            cursor.execute("""
                CREATE TABLE etf_price (
                    code TEXT,
                    date TEXT,
                    price_change_rate REAL,
                    turnover_rate REAL,
                    amount REAL,
                    transaction_count INTEGER,
                    total_market_value REAL,
                    close_price REAL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    amplitude REAL,
                    premium_discount REAL,
                    premium_discount_rate REAL,
                    update_time TIMESTAMP,
                    PRIMARY KEY (code, date)
                )
            """)
            
            # 创建ETF指数分类表
            cursor.execute("""
                CREATE TABLE etf_index_classification (
                    index_code TEXT PRIMARY KEY,
                    level1 TEXT,
                    level2 TEXT,
                    level3 TEXT,
                    index_name TEXT,
                    fund_count INTEGER
                )
            """)
            
            # 创建基金公司分析表
            self.create_company_analytics_table(conn)
            
            conn.commit()
            cursor.close() # 关闭游标，但不关闭连接
            print("数据库表创建成功")
            
            # 创建基金公司分析表
            self.create_company_analytics_table(conn)
            
        except Exception as e:
            print(f"创建数据库表失败: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def create_company_analytics_table(self, conn):
        """创建基金公司分析表"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etf_company_analytics (
                    company_short_name TEXT PRIMARY KEY,
                    product_count INTEGER,
                    business_agreement_count INTEGER,
                    business_agreement_ratio REAL,
                    total_fund_size REAL,
                    total_amount REAL,
                    total_attention_count INTEGER,
                    total_holder_count_holders INTEGER,
                    holder_attention_ratio REAL,
                    total_holding_value REAL,
                    business_total_holding_value REAL, -- 新增：商务品总持仓价值
                    business_holding_value_ratio REAL,  -- 新增：商务品持仓价值占比
                    latest_date TEXT,
                    company_name TEXT, -- 需求12: 增加公司全称
                    avg_fund_size REAL, -- 需求12: 增加平均管理规模
                    total_holder_count_info REAL, -- 来自etf_info的持有人数，可能与etf_holders不同
                    avg_turnover_rate REAL, -- 平均换手率
                    total_shares_holders REAL, -- 总持股数量（来自etf_holders）
                    business_agreement_total_size REAL, -- 商务协议产品总规模
                    business_agreement_avg_mgmt_fee REAL, -- 商务协议产品平均管理费率
                    business_agreement_avg_cust_fee REAL, -- 商务协议产品平均托管费率
                    update_timestamp TEXT -- 需求11: 增加更新时间戳
                );
            """)
            conn.commit()
            cursor.close()
            print("基金公司分析表 'etf_company_analytics' 创建成功或已存在。")
        except Exception as e:
            print(f"创建基金公司分析表 'etf_company_analytics' 失败: {str(e)}")

    def update_company_analytics_data(self):
        """更新基金公司层面的聚合分析数据"""
        print("开始更新基金公司层面聚合分析数据...")
        try:
            conn = self.connect()
            
            # 确保表存在且是最新结构：先删除旧表（如果存在），再创建新表
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS etf_company_analytics")
            conn.commit()
            cursor.close()
            print("已删除旧的 'etf_company_analytics' 表（如果存在）。")
            self.create_company_analytics_table(conn) # 用最新定义创建表
            
            # 清空旧数据 (现在不需要了，因为表是新创建的)
            # cursor = conn.cursor()
            # cursor.execute("DELETE FROM etf_company_analytics")
            # conn.commit()
            # cursor.close()
            # print("已清空 'etf_company_analytics' 表中的旧数据。")

            # 1. 从 etf_info 获取基础公司信息和产品统计
            # 确保 manager_company_name 不为空，因为它是主键
            query_info = """
            SELECT
                fund_manager as company_name, -- 使用 fund_manager 作为公司名称
                manager_short as company_short_name, -- 获取管理人简称
                COUNT(code) as product_count,
                SUM(fund_size) as total_fund_size,
                AVG(fund_size) as avg_fund_size,
                SUM(total_holder_count) as total_holder_count_info
            FROM etf_info
            WHERE fund_manager IS NOT NULL AND fund_manager != ''
            GROUP BY fund_manager, manager_short;
            """
            df_info = pd.read_sql_query(query_info, conn)
            if df_info.empty:
                print("未从 etf_info 获取到基金公司数据。")
                return False
            # 确保关键计数列是整数类型
            if 'product_count' in df_info.columns:
                df_info['product_count'] = pd.to_numeric(df_info['product_count'], errors='coerce').fillna(0).astype(int)
            if 'total_holder_count_info' in df_info.columns:
                 df_info['total_holder_count_info'] = pd.to_numeric(df_info['total_holder_count_info'], errors='coerce').fillna(0).astype(int)

            df_info = df_info.set_index('company_name')

            # 2. 获取各项数据的最新日期
            def get_latest_data_date(table_name, date_column='date'):
                try:
                    query = f"SELECT MAX({date_column}) FROM {table_name}"
                    cursor = conn.cursor()
                    cursor.execute(query)
                    latest_date = cursor.fetchone()[0]
                    cursor.close()
                    return latest_date
                except Exception as e:
                    print(f"获取表 {table_name} 的最新日期失败: {e}")
                    return None

            latest_price_date = get_latest_data_date('etf_price')
            latest_attention_date = get_latest_data_date('etf_attention')
            latest_holders_date = get_latest_data_date('etf_holders')
            
            print(f"最新价格日期: {latest_price_date}, 最新关注日期: {latest_attention_date}, 最新持有人日期: {latest_holders_date}")

            all_company_data = df_info
            all_company_data['latest_date'] = latest_price_date # 主数据日期

            # 3. 从 etf_price 获取聚合数据
            if latest_price_date:
                query_price = f"""
                SELECT
                    i.fund_manager as company_name, -- 使用 fund_manager
                    -- AVG(p.change_rate) as avg_price_change_rate, -- 需求3: 删除
                    SUM(p.amount) as total_amount,
                    AVG(p.turnover_rate) as avg_turnover_rate
                    -- SUM(p.net_inflow) as total_net_inflow -- 需求4: 删除 (原已移除)
                FROM etf_price p
                JOIN etf_info i ON p.code = i.code
                WHERE p.date = '{latest_price_date}' AND i.fund_manager IS NOT NULL AND i.fund_manager != ''
                GROUP BY i.fund_manager;
                """
                df_price = pd.read_sql_query(query_price, conn)
                if not df_price.empty:
                    df_price = df_price.set_index('company_name')
                    all_company_data = all_company_data.join(df_price, how='left')
                else:
                    print(f"在日期 {latest_price_date} 未从 etf_price 获取到聚合数据。")
            else:
                print("无法获取 etf_price 最新日期，相关指标将为空。")
                # avg_price_change_rate 已删除
                for col in ['total_amount', 'avg_turnover_rate']:
                    all_company_data[col] = None

            # 4. 从 etf_attention 获取聚合数据
            if latest_attention_date:
                query_attention = f"""
                SELECT
                    i.fund_manager as company_name, -- 使用 fund_manager
                    SUM(a.attention_count) as total_attention_count
                FROM etf_attention a
                JOIN etf_info i ON a.code = i.code
                WHERE a.date = '{latest_attention_date}' AND i.fund_manager IS NOT NULL AND i.fund_manager != ''
                GROUP BY i.fund_manager;
                """
                df_attention = pd.read_sql_query(query_attention, conn)
                if not df_attention.empty:
                    df_attention = df_attention.set_index('company_name')
                    all_company_data = all_company_data.join(df_attention, how='left')
                else:
                    print(f"在日期 {latest_attention_date} 未从 etf_attention 获取到聚合数据。")
            else:
                print("无法获取 etf_attention 最新日期，相关指标将为空。")
                all_company_data['total_attention_count'] = None
            
            # 5. 从 etf_holders 获取聚合数据
            if latest_holders_date:
                query_holders = f"""
                SELECT
                    i.fund_manager as company_name, -- 使用 fund_manager
                    SUM(h.holding_amount) as total_shares_holders, -- 改为 holding_amount
                    SUM(h.holder_count) as total_holder_count_holders,
                    SUM(h.holding_value) as total_holding_value -- 需求7: 新增持仓价值合计
                FROM etf_holders h
                JOIN etf_info i ON h.code = i.code
                WHERE h.date = '{latest_holders_date}' AND i.fund_manager IS NOT NULL AND i.fund_manager != ''
                GROUP BY i.fund_manager;
                """
                df_holders = pd.read_sql_query(query_holders, conn)
                if not df_holders.empty:
                    df_holders = df_holders.set_index('company_name')
                    all_company_data = all_company_data.join(df_holders, how='left')
                else:
                    print(f"在日期 {latest_holders_date} 未从 etf_holders 获取到聚合数据。")
            else:
                print("无法获取 etf_holders 最新日期，相关指标将为空。")
                for col in ['total_shares_holders', 'total_holder_count_holders', 'total_holding_value']:
                    all_company_data[col] = None

            # 6. 从 etf_business 获取聚合数据
            # 注意：etf_business 中的 fund_company_short 需要能映射到 manager_company_name
            # 这里假设 etf_business.code 可以关联到 etf_info.code, 从而得到 manager_company_name
            query_business = """
            SELECT
                i.fund_manager as company_name, -- 使用 fund_manager
                COUNT(b.code) as business_agreement_count,
                SUM(b.fund_size) as business_agreement_total_size,
                AVG(b.management_fee_rate) as business_agreement_avg_mgmt_fee,
                AVG(b.custody_fee_rate) as business_agreement_avg_cust_fee
            FROM etf_business b
            JOIN etf_info i ON b.code = i.code
            WHERE i.fund_manager IS NOT NULL AND i.fund_manager != ''
            GROUP BY i.fund_manager;
            """
            df_business = pd.read_sql_query(query_business, conn)
            if not df_business.empty:
                df_business = df_business.set_index('company_name')
                # 确保关键计数列是整数类型
                if 'business_agreement_count' in df_business.columns:
                    df_business['business_agreement_count'] = pd.to_numeric(df_business['business_agreement_count'], errors='coerce').fillna(0).astype(int)
                all_company_data = all_company_data.join(df_business, how='left')
            else:
                print("未从 etf_business 获取到聚合数据。")
                for col in ['business_agreement_count', 'business_agreement_total_size', 'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee']:
                    all_company_data[col] = None
            
            # 需求5: business_agreement_count，null 显示为 0
            if 'business_agreement_count' in all_company_data.columns:
                all_company_data['business_agreement_count'] = all_company_data['business_agreement_count'].fillna(0).astype(int)
            else: # 如果列因为没有数据源而未创建，则添加并填充0
                all_company_data['business_agreement_count'] = 0

            # 添加更新时间戳
            all_company_data['update_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 7. 计算商务品总持仓价值和商务品持仓价值占比
            if latest_holders_date:
                query_business_holders = f"""
                SELECT
                    i.fund_manager as company_name,
                    SUM(h.holding_value) as business_total_holding_value
                FROM etf_holders h
                JOIN etf_info i ON h.code = i.code
                JOIN etf_business b ON h.code = b.code  -- 只关联商务品
                WHERE h.date = '{latest_holders_date}' AND i.fund_manager IS NOT NULL AND i.fund_manager != ''
                GROUP BY i.fund_manager;
                """
                df_business_holders = pd.read_sql_query(query_business_holders, conn)
                if not df_business_holders.empty:
                    df_business_holders = df_business_holders.set_index('company_name')
                    all_company_data = all_company_data.join(df_business_holders, how='left')
                    
                    # 填充空值为0
                    all_company_data['business_total_holding_value'] = all_company_data['business_total_holding_value'].fillna(0.0)
                    
                    # 确保total_holding_value列存在且非空
                    if 'total_holding_value' in all_company_data.columns:
                        all_company_data['total_holding_value'] = all_company_data['total_holding_value'].fillna(0.0)
                        
                        # 计算商务品持仓价值占比 (%)
                        all_company_data['business_holding_value_ratio'] = all_company_data.apply(
                            lambda row: (row['business_total_holding_value'] * 100.0 / row['total_holding_value'])
                            if row['total_holding_value'] > 0 else 0.0,
                            axis=1
                        ).round(1)
                    else:
                        all_company_data['business_holding_value_ratio'] = 0.0
                else:
                    print(f"在日期 {latest_holders_date} 未从商务品ETF获取到持仓价值数据。")
                    all_company_data['business_total_holding_value'] = 0.0
                    all_company_data['business_holding_value_ratio'] = 0.0
            else:
                print("无法获取 etf_holders 最新日期，商务品持仓价值相关指标将为空。")
                all_company_data['business_total_holding_value'] = 0.0
                all_company_data['business_holding_value_ratio'] = 0.0
            
            # 重置索引，使 company_name 成为一列
            all_company_data = all_company_data.reset_index()
            # company_name 列已经存在且正确，不需要再 rename
            
            # 确保所有预期的列都存在，填充缺失的聚合列为 None 或 0
            # company_id 列暂时没有来源，会填充为None
            # 我们新增了 company_short_name，也加入 expected_cols
            expected_cols = [
                'company_name', 'company_short_name', # company_id 已删除
                'product_count', 'total_fund_size', 'avg_fund_size',
                'total_holder_count_info', 'latest_date', 
                # avg_price_change_rate 已删除
                'total_amount', 'avg_turnover_rate', 
                # total_net_inflow 已删除
                'total_attention_count', 'total_shares_holders',
                'total_holder_count_holders', 'holder_attention_ratio', # 新增持仓自选比
                'total_holding_value', 
                'business_agreement_count', 'business_agreement_ratio', # 新增商务品占比
                'business_agreement_total_size',
                'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'update_timestamp',
                'business_total_holding_value', 'business_holding_value_ratio' # 新增：允许按这两个新列排序
            ]
            for col in expected_cols:
                if col not in all_company_data.columns:
                    all_company_data[col] = None # 如果列不存在，添加并赋值为None
            
            # 将NaN替换为None，以便正确插入数据库 (特别是对于非数值型主键如company_id)
            all_company_data = all_company_data.astype(object).where(pd.notnull(all_company_data), None)

            # 插入数据到 etf_company_analytics
            # 调整列顺序以匹配表定义
            all_company_data = all_company_data[expected_cols]

            # 使用 'replace' 确保表总是被DataFrame的内容完全替换，避免UNIQUE constraint问题
            all_company_data.to_sql('etf_company_analytics', conn, if_exists='replace', index=False, dtype=self.get_company_analytics_table_sql_dtypes()) # 添加dtype确保类型正确
            
            print(f"成功更新基金公司层面聚合分析数据，共 {len(all_company_data)} 条记录。")

            # 计算商务品占比 (需求6)
            print("DEBUG: Before calculating business_agreement_ratio:")
            if 'company_short_name' not in all_company_data.columns and 'company_name' in all_company_data.columns:
                 # If company_short_name is not there yet (it's the index before reset_index)
                 temp_company_col = all_company_data.index.name if all_company_data.index.name == 'company_name' else 'company_name' # temp for company name
            elif 'company_short_name' in all_company_data.columns:
                 temp_company_col = 'company_short_name'
            else: # Fallback if no suitable company name column is found before reset_index
                 temp_company_col = None

            if 'product_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("product_count sample:", all_company_data[[temp_company_col, 'product_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col: # If it is the index
                    print("product_count sample (index as company name):", all_company_data[['product_count']].head())
                else:
                    print("product_count sample (company name col not found for debug):", all_company_data[['product_count']].head())
                print("product_count dtypes:", all_company_data['product_count'].dtype)
                print("product_count has NaN:", all_company_data['product_count'].isnull().any())
                print("product_count min, max, mean:", all_company_data['product_count'].min(), all_company_data['product_count'].max(), all_company_data['product_count'].mean())
            else:
                print("product_count column MISSING")

            if 'business_agreement_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("business_agreement_count sample:", all_company_data[[temp_company_col, 'business_agreement_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col:
                    print("business_agreement_count sample (index as company name):", all_company_data[['business_agreement_count']].head())
                else:
                    print("business_agreement_count sample (company name col not found for debug):", all_company_data[['business_agreement_count']].head())
                print("business_agreement_count dtypes:", all_company_data['business_agreement_count'].dtype)
                print("business_agreement_count has NaN:", all_company_data['business_agreement_count'].isnull().any())
                print("business_agreement_count min, max, mean:", all_company_data['business_agreement_count'].min(), all_company_data['business_agreement_count'].max(), all_company_data['business_agreement_count'].mean())
            else:
                print("business_agreement_count column MISSING")

            if 'product_count' in all_company_data.columns and 'business_agreement_count' in all_company_data.columns:
                #确保 product_count 和 business_agreement_count 是数值类型
                # all_company_data['product_count'] = pd.to_numeric(all_company_data['product_count'], errors='coerce') # 移除不必要的转换
                # all_company_data['business_agreement_count'] = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce') # 移除不必要的转换
                
                # 计算占比，处理分母为0的情况
                # 确保参与计算的列是数值类型，并且预先处理NaN为0，以避免计算中出现NaN或类型错误
                pc_col = pd.to_numeric(all_company_data['product_count'], errors='coerce').fillna(0)
                bc_col = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce').fillna(0)

                print(f"DEBUG: product_count for ratio calculation (after to_numeric, fillna(0)): min={pc_col.min()}, max={pc_col.max()}, mean={pc_col.mean()}")
                print(f"DEBUG: business_agreement_count for ratio calculation (after to_numeric, fillna(0)): min={bc_col.min()}, max={bc_col.max()}, mean={bc_col.mean()}")

                all_company_data['business_agreement_ratio'] = \
                    (bc_col * 100.0 / pc_col).where(pc_col != 0, 0)

                print(f"DEBUG: business_agreement_ratio after direct calculation: min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")

                # 在四舍五入前，确保列是数值类型并且填充NaN，以避免round的TypeError
                all_company_data['business_agreement_ratio'] = pd.to_numeric(all_company_data['business_agreement_ratio'], errors='coerce').fillna(0.0)
                all_company_data['business_agreement_ratio'] = all_company_data['business_agreement_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: business_agreement_ratio after round(2): min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")
            else:
                print("product_count or business_agreement_count column MISSING for business_agreement_ratio")
                all_company_data['business_agreement_ratio'] = 0.0 # 如果相关列不存在，则占比为0

            # 计算持仓自选比 (需求2 新)
            print("DEBUG: Before calculating holder_attention_ratio:")
            if 'total_holder_count_holders' in all_company_data.columns and 'total_attention_count' in all_company_data.columns:
                h_col = pd.to_numeric(all_company_data['total_holder_count_holders'], errors='coerce').fillna(0)
                a_col = pd.to_numeric(all_company_data['total_attention_count'], errors='coerce').fillna(0)
                
                print(f"DEBUG: total_holder_count_holders for ratio (after to_numeric, fillna(0)): min={h_col.min()}, max={h_col.max()}, mean={h_col.mean()}")
                print(f"DEBUG: total_attention_count for ratio (after to_numeric, fillna(0)): min={a_col.min()}, max={a_col.max()}, mean={a_col.mean()}")

                all_company_data['holder_attention_ratio'] = \
                    (h_col * 100.0 / a_col).where(a_col != 0, 0)
                
                all_company_data['holder_attention_ratio'] = pd.to_numeric(all_company_data['holder_attention_ratio'], errors='coerce').fillna(0.0)
                all_company_data['holder_attention_ratio'] = all_company_data['holder_attention_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: holder_attention_ratio after calculation and round(2): min={all_company_data['holder_attention_ratio'].min()}, max={all_company_data['holder_attention_ratio'].max()}, mean={all_company_data['holder_attention_ratio'].mean()}")
            else:
                print("total_holder_count_holders or total_attention_count column MISSING for holder_attention_ratio")
                all_company_data['holder_attention_ratio'] = 0.0

            # 重置索引，使 company_name 成为一列
            all_company_data = all_company_data.reset_index()
            
            # 在写入数据库前，对关键数值列进行最终的类型确认和 NaN 处理
            numeric_int_cols = ['product_count', 'total_holder_count_info', 'total_attention_count', 'total_holder_count_holders', 'business_agreement_count']
            numeric_float_cols = ['total_fund_size', 'avg_fund_size', 'total_amount', 'avg_turnover_rate', 
                                  'total_shares_holders', 'total_holding_value', 
                                  'business_agreement_ratio', 'business_agreement_total_size',
                                  'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'holder_attention_ratio',
                                  'business_total_holding_value', 'business_holding_value_ratio']  # 新增列

            for col in numeric_int_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0).astype(int)
                else:
                    all_company_data[col] = 0 # 如果列在聚合过程中未创建，则添加并设为0

            for col in numeric_float_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0.0).astype(float)
                else:
                    all_company_data[col] = 0.0 # 如果列在聚合过程中未创建，则添加并设为0.0

            print("DEBUG: Final dtypes before to_sql for key columns:")
            if 'business_agreement_ratio' in all_company_data.columns:
                print(f"  business_agreement_ratio dtype: {all_company_data['business_agreement_ratio'].dtype}, sample: {all_company_data['business_agreement_ratio'].head().tolist()[:3]}")
            if 'holder_attention_ratio' in all_company_data.columns:
                print(f"  holder_attention_ratio dtype: {all_company_data['holder_attention_ratio'].dtype}, sample: {all_company_data['holder_attention_ratio'].head().tolist()[:3]}")
            if 'product_count' in all_company_data.columns:
                print(f"  product_count dtype: {all_company_data['product_count'].dtype}")
            if 'business_agreement_count' in all_company_data.columns:
                print(f"  business_agreement_count dtype: {all_company_data['business_agreement_count'].dtype}")

            # 确保所有预期的列都存在，填充缺失的聚合列为 None 或 0
            expected_cols = [
                'company_name', 'company_short_name', # company_id 已删除
                'product_count', 'total_fund_size', 'avg_fund_size',
                'total_holder_count_info', 'latest_date', 
                # avg_price_change_rate 已删除
                'total_amount', 'avg_turnover_rate', 
                # total_net_inflow 已删除
                'total_attention_count', 'total_shares_holders',
                'total_holder_count_holders', 'holder_attention_ratio', # 新增持仓自选比
                'total_holding_value', 
                'business_agreement_count', 'business_agreement_ratio', # 新增商务品占比
                'business_agreement_total_size',
                'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'update_timestamp',
                'business_total_holding_value', 'business_holding_value_ratio' # 新增：允许按这两个新列排序
            ]
            for col in expected_cols:
                if col not in all_company_data.columns:
                    all_company_data[col] = None # 如果列不存在，添加并赋值为None
            
            # 将NaN替换为None，以便正确插入数据库 (特别是对于非数值型主键如company_id)
            all_company_data = all_company_data.astype(object).where(pd.notnull(all_company_data), None)

            # 插入数据到 etf_company_analytics
            # 调整列顺序以匹配表定义
            all_company_data = all_company_data[expected_cols]

            # 使用 'replace' 确保表总是被DataFrame的内容完全替换，避免UNIQUE constraint问题
            all_company_data.to_sql('etf_company_analytics', conn, if_exists='replace', index=False, dtype=self.get_company_analytics_table_sql_dtypes()) # 添加dtype确保类型正确
            
            print(f"成功更新基金公司层面聚合分析数据，共 {len(all_company_data)} 条记录。")

            # 计算商务品占比 (需求6)
            print("DEBUG: Before calculating business_agreement_ratio:")
            if 'company_short_name' not in all_company_data.columns and 'company_name' in all_company_data.columns:
                 # If company_short_name is not there yet (it's the index before reset_index)
                 temp_company_col = all_company_data.index.name if all_company_data.index.name == 'company_name' else 'company_name' # temp for company name
            elif 'company_short_name' in all_company_data.columns:
                 temp_company_col = 'company_short_name'
            else: # Fallback if no suitable company name column is found before reset_index
                 temp_company_col = None

            if 'product_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("product_count sample:", all_company_data[[temp_company_col, 'product_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col: # If it is the index
                    print("product_count sample (index as company name):", all_company_data[['product_count']].head())
                else:
                    print("product_count sample (company name col not found for debug):", all_company_data[['product_count']].head())
                print("product_count dtypes:", all_company_data['product_count'].dtype)
                print("product_count has NaN:", all_company_data['product_count'].isnull().any())
                print("product_count min, max, mean:", all_company_data['product_count'].min(), all_company_data['product_count'].max(), all_company_data['product_count'].mean())
            else:
                print("product_count column MISSING")

            if 'business_agreement_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("business_agreement_count sample:", all_company_data[[temp_company_col, 'business_agreement_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col:
                    print("business_agreement_count sample (index as company name):", all_company_data[['business_agreement_count']].head())
                else:
                    print("business_agreement_count sample (company name col not found for debug):", all_company_data[['business_agreement_count']].head())
                print("business_agreement_count dtypes:", all_company_data['business_agreement_count'].dtype)
                print("business_agreement_count has NaN:", all_company_data['business_agreement_count'].isnull().any())
                print("business_agreement_count min, max, mean:", all_company_data['business_agreement_count'].min(), all_company_data['business_agreement_count'].max(), all_company_data['business_agreement_count'].mean())
            else:
                print("business_agreement_count column MISSING")

            if 'product_count' in all_company_data.columns and 'business_agreement_count' in all_company_data.columns:
                #确保 product_count 和 business_agreement_count 是数值类型
                # all_company_data['product_count'] = pd.to_numeric(all_company_data['product_count'], errors='coerce') # 移除不必要的转换
                # all_company_data['business_agreement_count'] = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce') # 移除不必要的转换
                
                # 计算占比，处理分母为0的情况
                # 确保参与计算的列是数值类型，并且预先处理NaN为0，以避免计算中出现NaN或类型错误
                pc_col = pd.to_numeric(all_company_data['product_count'], errors='coerce').fillna(0)
                bc_col = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce').fillna(0)

                print(f"DEBUG: product_count for ratio calculation (after to_numeric, fillna(0)): min={pc_col.min()}, max={pc_col.max()}, mean={pc_col.mean()}")
                print(f"DEBUG: business_agreement_count for ratio calculation (after to_numeric, fillna(0)): min={bc_col.min()}, max={bc_col.max()}, mean={bc_col.mean()}")

                all_company_data['business_agreement_ratio'] = \
                    (bc_col * 100.0 / pc_col).where(pc_col != 0, 0)

                print(f"DEBUG: business_agreement_ratio after direct calculation: min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")

                # 在四舍五入前，确保列是数值类型并且填充NaN，以避免round的TypeError
                all_company_data['business_agreement_ratio'] = pd.to_numeric(all_company_data['business_agreement_ratio'], errors='coerce').fillna(0.0)
                all_company_data['business_agreement_ratio'] = all_company_data['business_agreement_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: business_agreement_ratio after round(2): min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")
            else:
                print("product_count or business_agreement_count column MISSING for business_agreement_ratio")
                all_company_data['business_agreement_ratio'] = 0.0 # 如果相关列不存在，则占比为0

            # 计算持仓自选比 (需求2 新)
            print("DEBUG: Before calculating holder_attention_ratio:")
            if 'total_holder_count_holders' in all_company_data.columns and 'total_attention_count' in all_company_data.columns:
                h_col = pd.to_numeric(all_company_data['total_holder_count_holders'], errors='coerce').fillna(0)
                a_col = pd.to_numeric(all_company_data['total_attention_count'], errors='coerce').fillna(0)
                
                print(f"DEBUG: total_holder_count_holders for ratio (after to_numeric, fillna(0)): min={h_col.min()}, max={h_col.max()}, mean={h_col.mean()}")
                print(f"DEBUG: total_attention_count for ratio (after to_numeric, fillna(0)): min={a_col.min()}, max={a_col.max()}, mean={a_col.mean()}")

                all_company_data['holder_attention_ratio'] = \
                    (h_col * 100.0 / a_col).where(a_col != 0, 0)
                
                all_company_data['holder_attention_ratio'] = pd.to_numeric(all_company_data['holder_attention_ratio'], errors='coerce').fillna(0.0)
                all_company_data['holder_attention_ratio'] = all_company_data['holder_attention_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: holder_attention_ratio after calculation and round(2): min={all_company_data['holder_attention_ratio'].min()}, max={all_company_data['holder_attention_ratio'].max()}, mean={all_company_data['holder_attention_ratio'].mean()}")
            else:
                print("total_holder_count_holders or total_attention_count column MISSING for holder_attention_ratio")
                all_company_data['holder_attention_ratio'] = 0.0

            # 重置索引，使 company_name 成为一列
            all_company_data = all_company_data.reset_index()
            
            # 在写入数据库前，对关键数值列进行最终的类型确认和 NaN 处理
            numeric_int_cols = ['product_count', 'total_holder_count_info', 'total_attention_count', 'total_holder_count_holders', 'business_agreement_count']
            numeric_float_cols = ['total_fund_size', 'avg_fund_size', 'total_amount', 'avg_turnover_rate', 
                                  'total_shares_holders', 'total_holding_value', 
                                  'business_agreement_ratio', 'business_agreement_total_size',
                                  'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'holder_attention_ratio',
                                  'business_total_holding_value', 'business_holding_value_ratio']  # 新增列

            for col in numeric_int_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0).astype(int)
                else:
                    all_company_data[col] = 0 # 如果列在聚合过程中未创建，则添加并设为0

            for col in numeric_float_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0.0).astype(float)
                else:
                    all_company_data[col] = 0.0 # 如果列在聚合过程中未创建，则添加并设为0.0

            print("DEBUG: Final dtypes before to_sql for key columns:")
            if 'business_agreement_ratio' in all_company_data.columns:
                print(f"  business_agreement_ratio dtype: {all_company_data['business_agreement_ratio'].dtype}, sample: {all_company_data['business_agreement_ratio'].head().tolist()[:3]}")
            if 'holder_attention_ratio' in all_company_data.columns:
                print(f"  holder_attention_ratio dtype: {all_company_data['holder_attention_ratio'].dtype}, sample: {all_company_data['holder_attention_ratio'].head().tolist()[:3]}")
            if 'product_count' in all_company_data.columns:
                print(f"  product_count dtype: {all_company_data['product_count'].dtype}")
            if 'business_agreement_count' in all_company_data.columns:
                print(f"  business_agreement_count dtype: {all_company_data['business_agreement_count'].dtype}")

            # 确保所有预期的列都存在，填充缺失的聚合列为 None 或 0
            expected_cols = [
                'company_name', 'company_short_name', # company_id 已删除
                'product_count', 'total_fund_size', 'avg_fund_size',
                'total_holder_count_info', 'latest_date', 
                # avg_price_change_rate 已删除
                'total_amount', 'avg_turnover_rate', 
                # total_net_inflow 已删除
                'total_attention_count', 'total_shares_holders',
                'total_holder_count_holders', 'holder_attention_ratio', # 新增持仓自选比
                'total_holding_value', 
                'business_agreement_count', 'business_agreement_ratio', # 新增商务品占比
                'business_agreement_total_size',
                'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'update_timestamp',
                'business_total_holding_value', 'business_holding_value_ratio' # 新增：允许按这两个新列排序
            ]
            for col in expected_cols:
                if col not in all_company_data.columns:
                    all_company_data[col] = None # 如果列不存在，添加并赋值为None
            
            # 将NaN替换为None，以便正确插入数据库 (特别是对于非数值型主键如company_id)
            all_company_data = all_company_data.astype(object).where(pd.notnull(all_company_data), None)

            # 插入数据到 etf_company_analytics
            # 调整列顺序以匹配表定义
            all_company_data = all_company_data[expected_cols]

            # 使用 'replace' 确保表总是被DataFrame的内容完全替换，避免UNIQUE constraint问题
            all_company_data.to_sql('etf_company_analytics', conn, if_exists='replace', index=False, dtype=self.get_company_analytics_table_sql_dtypes()) # 添加dtype确保类型正确
            
            print(f"成功更新基金公司层面聚合分析数据，共 {len(all_company_data)} 条记录。")

            # 计算商务品占比 (需求6)
            print("DEBUG: Before calculating business_agreement_ratio:")
            if 'company_short_name' not in all_company_data.columns and 'company_name' in all_company_data.columns:
                 # If company_short_name is not there yet (it's the index before reset_index)
                 temp_company_col = all_company_data.index.name if all_company_data.index.name == 'company_name' else 'company_name' # temp for company name
            elif 'company_short_name' in all_company_data.columns:
                 temp_company_col = 'company_short_name'
            else: # Fallback if no suitable company name column is found before reset_index
                 temp_company_col = None

            if 'product_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("product_count sample:", all_company_data[[temp_company_col, 'product_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col: # If it is the index
                    print("product_count sample (index as company name):", all_company_data[['product_count']].head())
                else:
                    print("product_count sample (company name col not found for debug):", all_company_data[['product_count']].head())
                print("product_count dtypes:", all_company_data['product_count'].dtype)
                print("product_count has NaN:", all_company_data['product_count'].isnull().any())
                print("product_count min, max, mean:", all_company_data['product_count'].min(), all_company_data['product_count'].max(), all_company_data['product_count'].mean())
            else:
                print("product_count column MISSING")

            if 'business_agreement_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("business_agreement_count sample:", all_company_data[[temp_company_col, 'business_agreement_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col:
                    print("business_agreement_count sample (index as company name):", all_company_data[['business_agreement_count']].head())
                else:
                    print("business_agreement_count sample (company name col not found for debug):", all_company_data[['business_agreement_count']].head())
                print("business_agreement_count dtypes:", all_company_data['business_agreement_count'].dtype)
                print("business_agreement_count has NaN:", all_company_data['business_agreement_count'].isnull().any())
                print("business_agreement_count min, max, mean:", all_company_data['business_agreement_count'].min(), all_company_data['business_agreement_count'].max(), all_company_data['business_agreement_count'].mean())
            else:
                print("business_agreement_count column MISSING")

            if 'product_count' in all_company_data.columns and 'business_agreement_count' in all_company_data.columns:
                #确保 product_count 和 business_agreement_count 是数值类型
                # all_company_data['product_count'] = pd.to_numeric(all_company_data['product_count'], errors='coerce') # 移除不必要的转换
                # all_company_data['business_agreement_count'] = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce') # 移除不必要的转换
                
                # 计算占比，处理分母为0的情况
                # 确保参与计算的列是数值类型，并且预先处理NaN为0，以避免计算中出现NaN或类型错误
                pc_col = pd.to_numeric(all_company_data['product_count'], errors='coerce').fillna(0)
                bc_col = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce').fillna(0)

                print(f"DEBUG: product_count for ratio calculation (after to_numeric, fillna(0)): min={pc_col.min()}, max={pc_col.max()}, mean={pc_col.mean()}")
                print(f"DEBUG: business_agreement_count for ratio calculation (after to_numeric, fillna(0)): min={bc_col.min()}, max={bc_col.max()}, mean={bc_col.mean()}")

                all_company_data['business_agreement_ratio'] = \
                    (bc_col * 100.0 / pc_col).where(pc_col != 0, 0)

                print(f"DEBUG: business_agreement_ratio after direct calculation: min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")

                # 在四舍五入前，确保列是数值类型并且填充NaN，以避免round的TypeError
                all_company_data['business_agreement_ratio'] = pd.to_numeric(all_company_data['business_agreement_ratio'], errors='coerce').fillna(0.0)
                all_company_data['business_agreement_ratio'] = all_company_data['business_agreement_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: business_agreement_ratio after round(2): min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")
            else:
                print("product_count or business_agreement_count column MISSING for business_agreement_ratio")
                all_company_data['business_agreement_ratio'] = 0.0 # 如果相关列不存在，则占比为0

            # 计算持仓自选比 (需求2 新)
            print("DEBUG: Before calculating holder_attention_ratio:")
            if 'total_holder_count_holders' in all_company_data.columns and 'total_attention_count' in all_company_data.columns:
                h_col = pd.to_numeric(all_company_data['total_holder_count_holders'], errors='coerce').fillna(0)
                a_col = pd.to_numeric(all_company_data['total_attention_count'], errors='coerce').fillna(0)
                
                print(f"DEBUG: total_holder_count_holders for ratio (after to_numeric, fillna(0)): min={h_col.min()}, max={h_col.max()}, mean={h_col.mean()}")
                print(f"DEBUG: total_attention_count for ratio (after to_numeric, fillna(0)): min={a_col.min()}, max={a_col.max()}, mean={a_col.mean()}")

                all_company_data['holder_attention_ratio'] = \
                    (h_col * 100.0 / a_col).where(a_col != 0, 0)
                
                all_company_data['holder_attention_ratio'] = pd.to_numeric(all_company_data['holder_attention_ratio'], errors='coerce').fillna(0.0)
                all_company_data['holder_attention_ratio'] = all_company_data['holder_attention_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: holder_attention_ratio after calculation and round(2): min={all_company_data['holder_attention_ratio'].min()}, max={all_company_data['holder_attention_ratio'].max()}, mean={all_company_data['holder_attention_ratio'].mean()}")
            else:
                print("total_holder_count_holders or total_attention_count column MISSING for holder_attention_ratio")
                all_company_data['holder_attention_ratio'] = 0.0

            # 重置索引，使 company_name 成为一列
            all_company_data = all_company_data.reset_index()
            
            # 在写入数据库前，对关键数值列进行最终的类型确认和 NaN 处理
            numeric_int_cols = ['product_count', 'total_holder_count_info', 'total_attention_count', 'total_holder_count_holders', 'business_agreement_count']
            numeric_float_cols = ['total_fund_size', 'avg_fund_size', 'total_amount', 'avg_turnover_rate', 
                                  'total_shares_holders', 'total_holding_value', 
                                  'business_agreement_ratio', 'business_agreement_total_size',
                                  'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'holder_attention_ratio',
                                  'business_total_holding_value', 'business_holding_value_ratio']  # 新增列

            for col in numeric_int_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0).astype(int)
                else:
                    all_company_data[col] = 0 # 如果列在聚合过程中未创建，则添加并设为0

            for col in numeric_float_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0.0).astype(float)
                else:
                    all_company_data[col] = 0.0 # 如果列在聚合过程中未创建，则添加并设为0.0

            print("DEBUG: Final dtypes before to_sql for key columns:")
            if 'business_agreement_ratio' in all_company_data.columns:
                print(f"  business_agreement_ratio dtype: {all_company_data['business_agreement_ratio'].dtype}, sample: {all_company_data['business_agreement_ratio'].head().tolist()[:3]}")
            if 'holder_attention_ratio' in all_company_data.columns:
                print(f"  holder_attention_ratio dtype: {all_company_data['holder_attention_ratio'].dtype}, sample: {all_company_data['holder_attention_ratio'].head().tolist()[:3]}")
            if 'product_count' in all_company_data.columns:
                print(f"  product_count dtype: {all_company_data['product_count'].dtype}")
            if 'business_agreement_count' in all_company_data.columns:
                print(f"  business_agreement_count dtype: {all_company_data['business_agreement_count'].dtype}")

            # 确保所有预期的列都存在，填充缺失的聚合列为 None 或 0
            expected_cols = [
                'company_name', 'company_short_name', # company_id 已删除
                'product_count', 'total_fund_size', 'avg_fund_size',
                'total_holder_count_info', 'latest_date', 
                # avg_price_change_rate 已删除
                'total_amount', 'avg_turnover_rate', 
                # total_net_inflow 已删除
                'total_attention_count', 'total_shares_holders',
                'total_holder_count_holders', 'holder_attention_ratio', # 新增持仓自选比
                'total_holding_value', 
                'business_agreement_count', 'business_agreement_ratio', # 新增商务品占比
                'business_agreement_total_size',
                'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'update_timestamp',
                'business_total_holding_value', 'business_holding_value_ratio' # 新增：允许按这两个新列排序
            ]
            for col in expected_cols:
                if col not in all_company_data.columns:
                    all_company_data[col] = None # 如果列不存在，添加并赋值为None
            
            # 将NaN替换为None，以便正确插入数据库 (特别是对于非数值型主键如company_id)
            all_company_data = all_company_data.astype(object).where(pd.notnull(all_company_data), None)

            # 插入数据到 etf_company_analytics
            # 调整列顺序以匹配表定义
            all_company_data = all_company_data[expected_cols]

            # 使用 'replace' 确保表总是被DataFrame的内容完全替换，避免UNIQUE constraint问题
            all_company_data.to_sql('etf_company_analytics', conn, if_exists='replace', index=False, dtype=self.get_company_analytics_table_sql_dtypes()) # 添加dtype确保类型正确
            
            print(f"成功更新基金公司层面聚合分析数据，共 {len(all_company_data)} 条记录。")

            # 计算商务品占比 (需求6)
            print("DEBUG: Before calculating business_agreement_ratio:")
            if 'company_short_name' not in all_company_data.columns and 'company_name' in all_company_data.columns:
                 # If company_short_name is not there yet (it's the index before reset_index)
                 temp_company_col = all_company_data.index.name if all_company_data.index.name == 'company_name' else 'company_name' # temp for company name
            elif 'company_short_name' in all_company_data.columns:
                 temp_company_col = 'company_short_name'
            else: # Fallback if no suitable company name column is found before reset_index
                 temp_company_col = None

            if 'product_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("product_count sample:", all_company_data[[temp_company_col, 'product_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col: # If it is the index
                    print("product_count sample (index as company name):", all_company_data[['product_count']].head())
                else:
                    print("product_count sample (company name col not found for debug):", all_company_data[['product_count']].head())
                print("product_count dtypes:", all_company_data['product_count'].dtype)
                print("product_count has NaN:", all_company_data['product_count'].isnull().any())
                print("product_count min, max, mean:", all_company_data['product_count'].min(), all_company_data['product_count'].max(), all_company_data['product_count'].mean())
            else:
                print("product_count column MISSING")

            if 'business_agreement_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("business_agreement_count sample:", all_company_data[[temp_company_col, 'business_agreement_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col:
                    print("business_agreement_count sample (index as company name):", all_company_data[['business_agreement_count']].head())
                else:
                    print("business_agreement_count sample (company name col not found for debug):", all_company_data[['business_agreement_count']].head())
                print("business_agreement_count dtypes:", all_company_data['business_agreement_count'].dtype)
                print("business_agreement_count has NaN:", all_company_data['business_agreement_count'].isnull().any())
                print("business_agreement_count min, max, mean:", all_company_data['business_agreement_count'].min(), all_company_data['business_agreement_count'].max(), all_company_data['business_agreement_count'].mean())
            else:
                print("business_agreement_count column MISSING")

            if 'product_count' in all_company_data.columns and 'business_agreement_count' in all_company_data.columns:
                #确保 product_count 和 business_agreement_count 是数值类型
                # all_company_data['product_count'] = pd.to_numeric(all_company_data['product_count'], errors='coerce') # 移除不必要的转换
                # all_company_data['business_agreement_count'] = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce') # 移除不必要的转换
                
                # 计算占比，处理分母为0的情况
                # 确保参与计算的列是数值类型，并且预先处理NaN为0，以避免计算中出现NaN或类型错误
                pc_col = pd.to_numeric(all_company_data['product_count'], errors='coerce').fillna(0)
                bc_col = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce').fillna(0)

                print(f"DEBUG: product_count for ratio calculation (after to_numeric, fillna(0)): min={pc_col.min()}, max={pc_col.max()}, mean={pc_col.mean()}")
                print(f"DEBUG: business_agreement_count for ratio calculation (after to_numeric, fillna(0)): min={bc_col.min()}, max={bc_col.max()}, mean={bc_col.mean()}")

                all_company_data['business_agreement_ratio'] = \
                    (bc_col * 100.0 / pc_col).where(pc_col != 0, 0)

                print(f"DEBUG: business_agreement_ratio after direct calculation: min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")

                # 在四舍五入前，确保列是数值类型并且填充NaN，以避免round的TypeError
                all_company_data['business_agreement_ratio'] = pd.to_numeric(all_company_data['business_agreement_ratio'], errors='coerce').fillna(0.0)
                all_company_data['business_agreement_ratio'] = all_company_data['business_agreement_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: business_agreement_ratio after round(2): min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")
            else:
                print("product_count or business_agreement_count column MISSING for business_agreement_ratio")
                all_company_data['business_agreement_ratio'] = 0.0 # 如果相关列不存在，则占比为0

            # 计算持仓自选比 (需求2 新)
            print("DEBUG: Before calculating holder_attention_ratio:")
            if 'total_holder_count_holders' in all_company_data.columns and 'total_attention_count' in all_company_data.columns:
                h_col = pd.to_numeric(all_company_data['total_holder_count_holders'], errors='coerce').fillna(0)
                a_col = pd.to_numeric(all_company_data['total_attention_count'], errors='coerce').fillna(0)
                
                print(f"DEBUG: total_holder_count_holders for ratio (after to_numeric, fillna(0)): min={h_col.min()}, max={h_col.max()}, mean={h_col.mean()}")
                print(f"DEBUG: total_attention_count for ratio (after to_numeric, fillna(0)): min={a_col.min()}, max={a_col.max()}, mean={a_col.mean()}")

                all_company_data['holder_attention_ratio'] = \
                    (h_col * 100.0 / a_col).where(a_col != 0, 0)
                
                all_company_data['holder_attention_ratio'] = pd.to_numeric(all_company_data['holder_attention_ratio'], errors='coerce').fillna(0.0)
                all_company_data['holder_attention_ratio'] = all_company_data['holder_attention_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: holder_attention_ratio after calculation and round(2): min={all_company_data['holder_attention_ratio'].min()}, max={all_company_data['holder_attention_ratio'].max()}, mean={all_company_data['holder_attention_ratio'].mean()}")
            else:
                print("total_holder_count_holders or total_attention_count column MISSING for holder_attention_ratio")
                all_company_data['holder_attention_ratio'] = 0.0

            # 重置索引，使 company_name 成为一列
            all_company_data = all_company_data.reset_index()
            
            # 在写入数据库前，对关键数值列进行最终的类型确认和 NaN 处理
            numeric_int_cols = ['product_count', 'total_holder_count_info', 'total_attention_count', 'total_holder_count_holders', 'business_agreement_count']
            numeric_float_cols = ['total_fund_size', 'avg_fund_size', 'total_amount', 'avg_turnover_rate', 
                                  'total_shares_holders', 'total_holding_value', 
                                  'business_agreement_ratio', 'business_agreement_total_size',
                                  'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'holder_attention_ratio',
                                  'business_total_holding_value', 'business_holding_value_ratio']  # 新增列

            for col in numeric_int_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0).astype(int)
                else:
                    all_company_data[col] = 0 # 如果列在聚合过程中未创建，则添加并设为0

            for col in numeric_float_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0.0).astype(float)
                else:
                    all_company_data[col] = 0.0 # 如果列在聚合过程中未创建，则添加并设为0.0

            print("DEBUG: Final dtypes before to_sql for key columns:")
            if 'business_agreement_ratio' in all_company_data.columns:
                print(f"  business_agreement_ratio dtype: {all_company_data['business_agreement_ratio'].dtype}, sample: {all_company_data['business_agreement_ratio'].head().tolist()[:3]}")
            if 'holder_attention_ratio' in all_company_data.columns:
                print(f"  holder_attention_ratio dtype: {all_company_data['holder_attention_ratio'].dtype}, sample: {all_company_data['holder_attention_ratio'].head().tolist()[:3]}")
            if 'product_count' in all_company_data.columns:
                print(f"  product_count dtype: {all_company_data['product_count'].dtype}")
            if 'business_agreement_count' in all_company_data.columns:
                print(f"  business_agreement_count dtype: {all_company_data['business_agreement_count'].dtype}")

            # 确保所有预期的列都存在，填充缺失的聚合列为 None 或 0
            expected_cols = [
                'company_name', 'company_short_name', # company_id 已删除
                'product_count', 'total_fund_size', 'avg_fund_size',
                'total_holder_count_info', 'latest_date', 
                # avg_price_change_rate 已删除
                'total_amount', 'avg_turnover_rate', 
                # total_net_inflow 已删除
                'total_attention_count', 'total_shares_holders',
                'total_holder_count_holders', 'holder_attention_ratio', # 新增持仓自选比
                'total_holding_value', 
                'business_agreement_count', 'business_agreement_ratio', # 新增商务品占比
                'business_agreement_total_size',
                'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'update_timestamp',
                'business_total_holding_value', 'business_holding_value_ratio' # 新增：允许按这两个新列排序
            ]
            for col in expected_cols:
                if col not in all_company_data.columns:
                    all_company_data[col] = None # 如果列不存在，添加并赋值为None
            
            # 将NaN替换为None，以便正确插入数据库 (特别是对于非数值型主键如company_id)
            all_company_data = all_company_data.astype(object).where(pd.notnull(all_company_data), None)

            # 插入数据到 etf_company_analytics
            # 调整列顺序以匹配表定义
            all_company_data = all_company_data[expected_cols]

            # 使用 'replace' 确保表总是被DataFrame的内容完全替换，避免UNIQUE constraint问题
            all_company_data.to_sql('etf_company_analytics', conn, if_exists='replace', index=False, dtype=self.get_company_analytics_table_sql_dtypes()) # 添加dtype确保类型正确
            
            print(f"成功更新基金公司层面聚合分析数据，共 {len(all_company_data)} 条记录。")

            # 计算商务品占比 (需求6)
            print("DEBUG: Before calculating business_agreement_ratio:")
            if 'company_short_name' not in all_company_data.columns and 'company_name' in all_company_data.columns:
                 # If company_short_name is not there yet (it's the index before reset_index)
                 temp_company_col = all_company_data.index.name if all_company_data.index.name == 'company_name' else 'company_name' # temp for company name
            elif 'company_short_name' in all_company_data.columns:
                 temp_company_col = 'company_short_name'
            else: # Fallback if no suitable company name column is found before reset_index
                 temp_company_col = None

            if 'product_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("product_count sample:", all_company_data[[temp_company_col, 'product_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col: # If it is the index
                    print("product_count sample (index as company name):", all_company_data[['product_count']].head())
                else:
                    print("product_count sample (company name col not found for debug):", all_company_data[['product_count']].head())
                print("product_count dtypes:", all_company_data['product_count'].dtype)
                print("product_count has NaN:", all_company_data['product_count'].isnull().any())
                print("product_count min, max, mean:", all_company_data['product_count'].min(), all_company_data['product_count'].max(), all_company_data['product_count'].mean())
            else:
                print("product_count column MISSING")

            if 'business_agreement_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("business_agreement_count sample:", all_company_data[[temp_company_col, 'business_agreement_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col:
                    print("business_agreement_count sample (index as company name):", all_company_data[['business_agreement_count']].head())
                else:
                    print("business_agreement_count sample (company name col not found for debug):", all_company_data[['business_agreement_count']].head())
                print("business_agreement_count dtypes:", all_company_data['business_agreement_count'].dtype)
                print("business_agreement_count has NaN:", all_company_data['business_agreement_count'].isnull().any())
                print("business_agreement_count min, max, mean:", all_company_data['business_agreement_count'].min(), all_company_data['business_agreement_count'].max(), all_company_data['business_agreement_count'].mean())
            else:
                print("business_agreement_count column MISSING")

            if 'product_count' in all_company_data.columns and 'business_agreement_count' in all_company_data.columns:
                #确保 product_count 和 business_agreement_count 是数值类型
                # all_company_data['product_count'] = pd.to_numeric(all_company_data['product_count'], errors='coerce') # 移除不必要的转换
                # all_company_data['business_agreement_count'] = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce') # 移除不必要的转换
                
                # 计算占比，处理分母为0的情况
                # 确保参与计算的列是数值类型，并且预先处理NaN为0，以避免计算中出现NaN或类型错误
                pc_col = pd.to_numeric(all_company_data['product_count'], errors='coerce').fillna(0)
                bc_col = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce').fillna(0)

                print(f"DEBUG: product_count for ratio calculation (after to_numeric, fillna(0)): min={pc_col.min()}, max={pc_col.max()}, mean={pc_col.mean()}")
                print(f"DEBUG: business_agreement_count for ratio calculation (after to_numeric, fillna(0)): min={bc_col.min()}, max={bc_col.max()}, mean={bc_col.mean()}")

                all_company_data['business_agreement_ratio'] = \
                    (bc_col * 100.0 / pc_col).where(pc_col != 0, 0)

                print(f"DEBUG: business_agreement_ratio after direct calculation: min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")

                # 在四舍五入前，确保列是数值类型并且填充NaN，以避免round的TypeError
                all_company_data['business_agreement_ratio'] = pd.to_numeric(all_company_data['business_agreement_ratio'], errors='coerce').fillna(0.0)
                all_company_data['business_agreement_ratio'] = all_company_data['business_agreement_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: business_agreement_ratio after round(2): min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")
            else:
                print("product_count or business_agreement_count column MISSING for business_agreement_ratio")
                all_company_data['business_agreement_ratio'] = 0.0 # 如果相关列不存在，则占比为0

            # 计算持仓自选比 (需求2 新)
            print("DEBUG: Before calculating holder_attention_ratio:")
            if 'total_holder_count_holders' in all_company_data.columns and 'total_attention_count' in all_company_data.columns:
                h_col = pd.to_numeric(all_company_data['total_holder_count_holders'], errors='coerce').fillna(0)
                a_col = pd.to_numeric(all_company_data['total_attention_count'], errors='coerce').fillna(0)
                
                print(f"DEBUG: total_holder_count_holders for ratio (after to_numeric, fillna(0)): min={h_col.min()}, max={h_col.max()}, mean={h_col.mean()}")
                print(f"DEBUG: total_attention_count for ratio (after to_numeric, fillna(0)): min={a_col.min()}, max={a_col.max()}, mean={a_col.mean()}")

                all_company_data['holder_attention_ratio'] = \
                    (h_col * 100.0 / a_col).where(a_col != 0, 0)
                
                all_company_data['holder_attention_ratio'] = pd.to_numeric(all_company_data['holder_attention_ratio'], errors='coerce').fillna(0.0)
                all_company_data['holder_attention_ratio'] = all_company_data['holder_attention_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: holder_attention_ratio after calculation and round(2): min={all_company_data['holder_attention_ratio'].min()}, max={all_company_data['holder_attention_ratio'].max()}, mean={all_company_data['holder_attention_ratio'].mean()}")
            else:
                print("total_holder_count_holders or total_attention_count column MISSING for holder_attention_ratio")
                all_company_data['holder_attention_ratio'] = 0.0

            # 重置索引，使 company_name 成为一列
            all_company_data = all_company_data.reset_index()
            
            # 在写入数据库前，对关键数值列进行最终的类型确认和 NaN 处理
            numeric_int_cols = ['product_count', 'total_holder_count_info', 'total_attention_count', 'total_holder_count_holders', 'business_agreement_count']
            numeric_float_cols = ['total_fund_size', 'avg_fund_size', 'total_amount', 'avg_turnover_rate', 
                                  'total_shares_holders', 'total_holding_value', 
                                  'business_agreement_ratio', 'business_agreement_total_size',
                                  'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'holder_attention_ratio',
                                  'business_total_holding_value', 'business_holding_value_ratio']  # 新增列

            for col in numeric_int_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0).astype(int)
                else:
                    all_company_data[col] = 0 # 如果列在聚合过程中未创建，则添加并设为0

            for col in numeric_float_cols:
                if col in all_company_data.columns:
                    all_company_data[col] = pd.to_numeric(all_company_data[col], errors='coerce').fillna(0.0).astype(float)
                else:
                    all_company_data[col] = 0.0 # 如果列在聚合过程中未创建，则添加并设为0.0

            print("DEBUG: Final dtypes before to_sql for key columns:")
            if 'business_agreement_ratio' in all_company_data.columns:
                print(f"  business_agreement_ratio dtype: {all_company_data['business_agreement_ratio'].dtype}, sample: {all_company_data['business_agreement_ratio'].head().tolist()[:3]}")
            if 'holder_attention_ratio' in all_company_data.columns:
                print(f"  holder_attention_ratio dtype: {all_company_data['holder_attention_ratio'].dtype}, sample: {all_company_data['holder_attention_ratio'].head().tolist()[:3]}")
            if 'product_count' in all_company_data.columns:
                print(f"  product_count dtype: {all_company_data['product_count'].dtype}")
            if 'business_agreement_count' in all_company_data.columns:
                print(f"  business_agreement_count dtype: {all_company_data['business_agreement_count'].dtype}")

            # 确保所有预期的列都存在，填充缺失的聚合列为 None 或 0
            expected_cols = [
                'company_name', 'company_short_name', # company_id 已删除
                'product_count', 'total_fund_size', 'avg_fund_size',
                'total_holder_count_info', 'latest_date', 
                # avg_price_change_rate 已删除
                'total_amount', 'avg_turnover_rate', 
                # total_net_inflow 已删除
                'total_attention_count', 'total_shares_holders',
                'total_holder_count_holders', 'holder_attention_ratio', # 新增持仓自选比
                'total_holding_value', 
                'business_agreement_count', 'business_agreement_ratio', # 新增商务品占比
                'business_agreement_total_size',
                'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'update_timestamp',
                'business_total_holding_value', 'business_holding_value_ratio' # 新增：允许按这两个新列排序
            ]
            for col in expected_cols:
                if col not in all_company_data.columns:
                    all_company_data[col] = None # 如果列不存在，添加并赋值为None
            
            # 将NaN替换为None，以便正确插入数据库 (特别是对于非数值型主键如company_id)
            all_company_data = all_company_data.astype(object).where(pd.notnull(all_company_data), None)

            # 插入数据到 etf_company_analytics
            # 调整列顺序以匹配表定义
            all_company_data = all_company_data[expected_cols]

            # 使用 'replace' 确保表总是被DataFrame的内容完全替换，避免UNIQUE constraint问题
            all_company_data.to_sql('etf_company_analytics', conn, if_exists='replace', index=False, dtype=self.get_company_analytics_table_sql_dtypes()) # 添加dtype确保类型正确
            
            print(f"成功更新基金公司层面聚合分析数据，共 {len(all_company_data)} 条记录。")

            # 计算商务品占比 (需求6)
            print("DEBUG: Before calculating business_agreement_ratio:")
            if 'company_short_name' not in all_company_data.columns and 'company_name' in all_company_data.columns:
                 # If company_short_name is not there yet (it's the index before reset_index)
                 temp_company_col = all_company_data.index.name if all_company_data.index.name == 'company_name' else 'company_name' # temp for company name
            elif 'company_short_name' in all_company_data.columns:
                 temp_company_col = 'company_short_name'
            else: # Fallback if no suitable company name column is found before reset_index
                 temp_company_col = None

            if 'product_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("product_count sample:", all_company_data[[temp_company_col, 'product_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col: # If it is the index
                    print("product_count sample (index as company name):", all_company_data[['product_count']].head())
                else:
                    print("product_count sample (company name col not found for debug):", all_company_data[['product_count']].head())
                print("product_count dtypes:", all_company_data['product_count'].dtype)
                print("product_count has NaN:", all_company_data['product_count'].isnull().any())
                print("product_count min, max, mean:", all_company_data['product_count'].min(), all_company_data['product_count'].max(), all_company_data['product_count'].mean())
            else:
                print("product_count column MISSING")

            if 'business_agreement_count' in all_company_data.columns:
                if temp_company_col and temp_company_col in all_company_data.columns:
                    print("business_agreement_count sample:", all_company_data[[temp_company_col, 'business_agreement_count']].head())
                elif temp_company_col and all_company_data.index.name == temp_company_col:
                    print("business_agreement_count sample (index as company name):", all_company_data[['business_agreement_count']].head())
                else:
                    print("business_agreement_count sample (company name col not found for debug):", all_company_data[['business_agreement_count']].head())
                print("business_agreement_count dtypes:", all_company_data['business_agreement_count'].dtype)
                print("business_agreement_count has NaN:", all_company_data['business_agreement_count'].isnull().any())
                print("business_agreement_count min, max, mean:", all_company_data['business_agreement_count'].min(), all_company_data['business_agreement_count'].max(), all_company_data['business_agreement_count'].mean())
            else:
                print("business_agreement_count column MISSING")

            if 'product_count' in all_company_data.columns and 'business_agreement_count' in all_company_data.columns:
                #确保 product_count 和 business_agreement_count 是数值类型
                # all_company_data['product_count'] = pd.to_numeric(all_company_data['product_count'], errors='coerce') # 移除不必要的转换
                # all_company_data['business_agreement_count'] = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce') # 移除不必要的转换
                
                # 计算占比，处理分母为0的情况
                # 确保参与计算的列是数值类型，并且预先处理NaN为0，以避免计算中出现NaN或类型错误
                pc_col = pd.to_numeric(all_company_data['product_count'], errors='coerce').fillna(0)
                bc_col = pd.to_numeric(all_company_data['business_agreement_count'], errors='coerce').fillna(0)

                print(f"DEBUG: product_count for ratio calculation (after to_numeric, fillna(0)): min={pc_col.min()}, max={pc_col.max()}, mean={pc_col.mean()}")
                print(f"DEBUG: business_agreement_count for ratio calculation (after to_numeric, fillna(0)): min={bc_col.min()}, max={bc_col.max()}, mean={bc_col.mean()}")

                all_company_data['business_agreement_ratio'] = \
                    (bc_col * 100.0 / pc_col).where(pc_col != 0, 0)

                print(f"DEBUG: business_agreement_ratio after direct calculation: min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")

                # 在四舍五入前，确保列是数值类型并且填充NaN，以避免round的TypeError
                all_company_data['business_agreement_ratio'] = pd.to_numeric(all_company_data['business_agreement_ratio'], errors='coerce').fillna(0.0)
                all_company_data['business_agreement_ratio'] = all_company_data['business_agreement_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: business_agreement_ratio after round(2): min={all_company_data['business_agreement_ratio'].min()}, max={all_company_data['business_agreement_ratio'].max()}, mean={all_company_data['business_agreement_ratio'].mean()}")
            else:
                print("product_count or business_agreement_count column MISSING for business_agreement_ratio")
                all_company_data['business_agreement_ratio'] = 0.0 # 如果相关列不存在，则占比为0

            # 计算持仓自选比 (需求2 新)
            print("DEBUG: Before calculating holder_attention_ratio:")
            if 'total_holder_count_holders' in all_company_data.columns and 'total_attention_count' in all_company_data.columns:
                h_col = pd.to_numeric(all_company_data['total_holder_count_holders'], errors='coerce').fillna(0)
                a_col = pd.to_numeric(all_company_data['total_attention_count'], errors='coerce').fillna(0)
                
                print(f"DEBUG: total_holder_count_holders for ratio (after to_numeric, fillna(0)): min={h_col.min()}, max={h_col.max()}, mean={h_col.mean()}")
                print(f"DEBUG: total_attention_count for ratio (after to_numeric, fillna(0)): min={a_col.min()}, max={a_col.max()}, mean={a_col.mean()}")

                all_company_data['holder_attention_ratio'] = \
                    (h_col * 100.0 / a_col).where(a_col != 0, 0)
                
                all_company_data['holder_attention_ratio'] = pd.to_numeric(all_company_data['holder_attention_ratio'], errors='coerce').fillna(0.0)
                all_company_data['holder_attention_ratio'] = all_company_data['holder_attention_ratio'].round(2) # 保留两位小数
                print(f"DEBUG: holder_attention_ratio after calculation and round(2): min={all_company_data['holder_attention_ratio'].min()}, max={all_company_data['holder_attention_ratio'].max()}, mean={all_company_data['holder_attention_ratio'].mean()}")
            else:
                print("total_holder_count_holders or total_attention_count column MISSING for holder_attention_ratio")
                all_company_data['holder_attention_ratio'] = 0.0

            # 重置索引，使 company_name 成为一列
            all_company_data = all_company_data.reset_index()
            
            return True

        except sqlite3.Error as e:
            print(f"数据库操作时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        except pd.io.sql.DatabaseError as e:
            print(f"Pandas SQL操作时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"更新基金公司聚合数据时发生未知错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # self.close() # 通常不在每个方法中关闭，由调用者管理或析构函数处理
            pass

    def get_company_analytics_table_sql_dtypes(self):
        """返回 etf_company_analytics 表的SQL列类型字典，供 to_sql 使用"""
        # 这有助于确保Pandas在创建/替换表时使用正确的SQLite数据类型
        return {
            'company_short_name': 'TEXT', 
            'product_count': 'INTEGER',
            'business_agreement_count': 'INTEGER',
            'business_agreement_ratio': 'REAL',
            'total_fund_size': 'REAL',
            'total_amount': 'REAL',
            'total_attention_count': 'INTEGER',
            'total_holder_count_holders': 'INTEGER',
            'holder_attention_ratio': 'REAL',
            'total_holding_value': 'REAL',
            'business_total_holding_value': 'REAL', # 新增
            'business_holding_value_ratio': 'REAL',  # 新增
            'latest_date': 'TEXT',
            'company_name': 'TEXT',
            'avg_fund_size': 'REAL',
            'total_holder_count_info': 'REAL',
            'avg_turnover_rate': 'REAL',
            'total_shares_holders': 'REAL',
            'business_agreement_total_size': 'REAL',
            'business_agreement_avg_mgmt_fee': 'REAL',
            'business_agreement_avg_cust_fee': 'REAL',
            'update_timestamp': 'TEXT'
        }
    
    def get_existing_dates(self, table_name, code=None):
        """获取指定表中已存在的日期"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            if code:
                cursor.execute(f"SELECT DISTINCT date FROM {table_name} WHERE code = ?", (code,))
            else:
                cursor.execute(f"SELECT DISTINCT date FROM {table_name}")
            dates = [row[0] for row in cursor.fetchall()]
            cursor.close()  # 只关闭游标
            return dates
        except Exception as e:
            print(f"获取日期时出错: {str(e)}")
            return []
    
    def save_etf_info(self, df: pd.DataFrame) -> bool:
        """保存ETF基本信息"""
        try:
            print("开始处理ETF基本信息数据...")
            
            # 显示原始数据信息
            print("原始列名：", df.columns.tolist())
            print("原始数据前5行：")
            print(df.head())
            
            # 标准化列名（去除多余的空格和换行符）
            df.columns = [col.strip().replace('\n', ' ').replace('[', '(').replace(']', ')') for col in df.columns]
            
            # 标准化ETF代码
            from utils.etf_code import normalize_etf_code
            
            if '证券代码' in df.columns:
                print("标准化ETF代码...")
                print("标准化前示例：", df['证券代码'].head(5).tolist())
                df['证券代码'] = df['证券代码'].apply(normalize_etf_code)
                print("标准化后示例：", df['证券代码'].head(5).tolist())
            
            # 检查列名是否包含指定的关键词
            column_keywords = {
                '基金规模': 'fund_size',
                '年化跟踪误差': 'tracking_error',
                '信息比率': 'information_ratio',
                '基金份额持有人户数': 'total_holder_count',
                '管理费率': 'management_fee_rate',
                '托管费率': 'custody_fee_rate',
                '月成交额': 'monthly_volume',
                '日均成交额': 'daily_avg_volume',
                '换手率': 'turnover_rate',
                '成交额': 'daily_volume',
                '成交笔数': 'transaction_count',
                '总市值': 'total_market_value'
            }
            
            # 重命名包含关键词的列
            for cn_keyword, en_name in column_keywords.items():
                matching_cols = [col for col in df.columns if cn_keyword in col]
                if matching_cols:
                    # 用第一个匹配的列名
                    print(f"列名映射: '{matching_cols[0]}' -> '{en_name}'")
                    df = df.rename(columns={matching_cols[0]: en_name})
            
            # 将业绩比较基准、成立年限、成立日期、场内简称和跟踪指数名称映射为英文字段名
            if '业绩比较基准' in df.columns:
                df = df.rename(columns={'业绩比较基准': 'benchmark'})
            
            if '成立年限' in df.columns or any('成立年限' in col for col in df.columns):
                matching_cols = [col for col in df.columns if '成立年限' in col]
                if matching_cols:
                    df = df.rename(columns={matching_cols[0]: 'years_since_establishment'})
            
            if '基金成立日' in df.columns:
                df = df.rename(columns={'基金成立日': 'establishment_date'})
            
            if '基金场内简称' in df.columns:
                df = df.rename(columns={'基金场内简称': 'fund_exchange_abbr'})
            
            if '跟踪指数名称' in df.columns:
                df = df.rename(columns={'跟踪指数名称': 'tracking_index_name'})
            
            # 基本的列名映射
            column_mapping = {
                '证券代码': 'code',
                '证券简称': 'name',
                '基金管理人': 'fund_manager',
                '基金上市地点': 'exchange',
                '指数使用费率': 'index_usage_fee',
                '跟踪指数代码': 'tracking_index_code'
            }
            
            # 重命名基本列
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df = df.rename(columns={old_name: new_name})
            
            print("重命名后的列名：", df.columns.tolist())
            
            # 标准化ETF代码（确保一致性）
            if 'code' in df.columns:
                print("标准化ETF代码...")
                print("标准化前示例：", df['code'].head(5).tolist())
                df['code'] = df['code'].apply(normalize_etf_code)
                print("标准化后示例：", df['code'].head(5).tolist())
                # 显示ETF代码的唯一数量
                print(f"标准化后唯一代码数量: {df['code'].nunique()}")
            
            # 定义所有我们需要的列
            required_columns = ['code', 'name', 'fund_manager']
            optional_columns = [
                'fund_size', 'exchange', 'tracking_index_code', 'tracking_index_name',
                'tracking_error', 'information_ratio', 'total_holder_count',
                'management_fee_rate', 'custody_fee_rate', 'index_usage_fee',
                'monthly_volume', 'daily_avg_volume', 'turnover_rate', 'daily_volume',
                'transaction_count', 'total_market_value', 'benchmark',
                'years_since_establishment', 'establishment_date', 'fund_exchange_abbr',
                'date'
            ]
            
            # 检查必需列是否存在
            missing_required = [col for col in required_columns if col not in df.columns]
            if missing_required:
                print(f"错误：缺少必需列 {missing_required}")
                return False
            
            # 创建最终的数据框，只包含我们定义的列
            final_columns = required_columns + [col for col in optional_columns if col in df.columns]
            
            # 选择存在的列，丢弃其他未映射列
            final_df = df[final_columns].copy()
            
            # 为所有可选列设置默认值（如果不存在）
            for col in optional_columns:
                if col not in final_df.columns:
                    final_df[col] = None
            
            # 处理基金规模数据
            if 'fund_size' in final_df.columns:
                print("\n处理基金规模数据...")
                print(f"基金规模列的数据类型： {final_df['fund_size'].dtype}")
                print(f"基金规模的唯一值： {final_df['fund_size'].unique()[:5]}")  # 只显示前5个唯一值
                
                # 将基金规模转换为浮点数
                final_df['fund_size'] = pd.to_numeric(final_df['fund_size'], errors='coerce')
                
                # 显示基金规模的统计信息
                print("\n处理后的基金规模统计：")
                print(final_df['fund_size'].describe())
            
            # 处理费率数据
            fee_columns = ['management_fee_rate', 'custody_fee_rate', 'index_usage_fee']
            
            # 定义处理费率的函数
            def process_fee_rate(value):
                if pd.isna(value):
                    return 0.0
                if isinstance(value, str):
                    # 尝试提取数字部分
                    value = value.replace('%', '').replace('％', '').strip()
                    try:
                        return float(value) / 100.0  # 转换为小数
                    except ValueError:
                        return 0.0
                try:
                    # 如果是%格式（例如 0.5%），则除以100
                    if value > 1.0:
                        return value / 100.0
                    return value
                except (ValueError, TypeError):
                    return 0.0
            
            # 处理费率列
            for col in fee_columns:
                if col in final_df.columns:
                    final_df[col] = final_df[col].apply(process_fee_rate)
            
            # 添加total_annual_fee_rate列
            fee_cols_exist = [col for col in fee_columns if col in final_df.columns]
            if fee_cols_exist:
                final_df['total_annual_fee_rate'] = final_df[fee_cols_exist].sum(axis=1)
            else:
                final_df['total_annual_fee_rate'] = 0.0
            
            # 处理数量和金额字段
            def process_numeric_value(value, unit_mult=1.0):
                if pd.isna(value):
                    return 0.0
                if isinstance(value, str):
                    # 移除非数字字符
                    value = value.replace(',', '').strip()
                    try:
                        return float(value) * unit_mult
                    except (ValueError, TypeError):
                        print(f"警告：无法转换数值 '{value}' 为数字")
                        return 0.0
                try:
                    return float(value) * unit_mult
                except (ValueError, TypeError):
                    print(f"警告：无法转换数值 '{value}' 为数字")
                    return 0.0
            
            # 处理月交易量数据（从百万元转为亿元）
            if 'monthly_volume' in final_df.columns:
                final_df['monthly_volume'] = final_df['monthly_volume'].apply(lambda x: process_numeric_value(x, 0.01))  # 百万到亿的转换
            
            # 处理交易量数据
            if 'daily_avg_volume' in final_df.columns:
                final_df['daily_avg_volume'] = final_df['daily_avg_volume'].apply(process_numeric_value)
            
            # 处理换手率
            if 'turnover_rate' in final_df.columns:
                final_df['turnover_rate'] = final_df['turnover_rate'].apply(process_numeric_value)
            
            # 处理日交易量
            if 'daily_volume' in final_df.columns:
                final_df['daily_volume'] = final_df['daily_volume'].apply(process_numeric_value)
            
            # 处理成交笔数
            if 'transaction_count' in final_df.columns:
                final_df['transaction_count'] = final_df['transaction_count'].apply(lambda x: int(process_numeric_value(x)) if pd.notna(x) else 0)
            
            # 处理总市值
            if 'total_market_value' in final_df.columns:
                final_df['total_market_value'] = final_df['total_market_value'].apply(process_numeric_value)
            
            # 添加更新时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            final_df['update_time'] = current_time
            
            # 添加或使用文件提供的日期列
            # 如果df中已经有date列（从文件名提取的日期），则使用该列
            # 否则使用当前日期
            if 'date' not in final_df.columns:
                current_date = datetime.now().strftime('%Y-%m-%d')
                final_df['date'] = current_date
                print(f"未发现日期字段，使用当前日期：{current_date}")
            else:
                print(f"使用文件中提供的日期：{final_df['date'].iloc[0]}")
                
            # 添加管理人简称
            print("\n处理基金管理人简称...")
            
            # 基金管理人简称提取函数
            def get_manager_short(full_name):
                """基金管理人简称提取"""
                if pd.isna(full_name) or not full_name:
                    return "未知"
                
                # 特定公司单独处理
                if "摩根基金管理" in full_name:
                    return "摩根"
                elif "浙江浙商证券资产管理" in full_name:
                    return "浙商资管"
                elif "华泰证券" in full_name and "资产管理" in full_name:
                    return "华泰资管"
                elif "中银国际证券" in full_name:
                    return "中银国际"
                
                # 通用后缀处理
                short_name = full_name
                # 移除常见后缀
                suffixes = [
                    "基金管理有限公司", "基金管理股份有限公司", "基金管理有限责任公司", 
                    "基金管理公司", "基金", "股份有限公司", "有限公司", "有限责任公司",
                    "证券资产管理有限公司", "证券资产管理", "资产管理有限公司", "资产管理"
                ]
                
                for suffix in suffixes:
                    short_name = short_name.replace(suffix, "")
                
                return short_name
            
            # 生成管理人简称
            if 'fund_manager' in final_df.columns:
                final_df['manager_short'] = final_df['fund_manager'].apply(get_manager_short)
                print("管理人简称示例：")
                print(final_df[['fund_manager', 'manager_short']].head())
            else:
                final_df['manager_short'] = "未知"
                print("警告: 没有fund_manager字段, 所有manager_short设为默认值'未知'")
            
            # 显示数据示例
            print("\n最终数据示例：")
            print(final_df[['code', 'name', 'fund_manager', 'manager_short', 'fund_size']].head())
            print("\n数据形状：", final_df.shape)
            
            # 删除现有表并重新创建
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS etf_info")
            cursor.execute("""
                CREATE TABLE etf_info (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    fund_manager TEXT,
                    manager_short TEXT,
                    fund_size REAL,
                    exchange TEXT,
                    tracking_index_code TEXT,
                    tracking_index_name TEXT,
                    tracking_error REAL,
                    information_ratio REAL,
                    total_holder_count INTEGER,
                    management_fee_rate REAL,
                    custody_fee_rate REAL,
                    index_usage_fee REAL,
                    total_annual_fee_rate REAL,
                    monthly_volume REAL,
                    daily_avg_volume REAL,
                    turnover_rate REAL,
                    daily_volume REAL,
                    transaction_count INTEGER,
                    total_market_value REAL,
                    benchmark TEXT,
                    years_since_establishment REAL,
                    establishment_date TEXT,
                    fund_exchange_abbr TEXT,
                    date TEXT,
                    update_time TIMESTAMP
                )
            """)
            
            # 保存到主表
            final_df.to_sql('etf_info', conn, if_exists='append', index=False)
            
            conn.commit()
            
            print(f"\n成功保存ETF基本信息，共{len(final_df)}条记录")
            return True
        
        except Exception as e:
            print(f"保存ETF基本信息失败: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.conn:
                self.conn.rollback()
            return False
    
    def save_etf_price(self, df: pd.DataFrame) -> bool:
        """保存ETF价格数据"""
        try:
            print("开始处理ETF价格数据...")
            
            # 导入normalize_etf_code函数用于标准化ETF代码
            from utils.etf_code import normalize_etf_code
            
            # 显示原始数据信息
            print("原始列名：", df.columns.tolist())
            print("原始数据形状：", df.shape)
            
            # 确保代码列正确
            if 'code' not in df.columns:
                print("缺少代码列，无法继续处理")
                return False
            
            # 确保数据日期和更新时间存在
            if 'date' not in df.columns:
                current_date = datetime.now().strftime('%Y-%m-%d')
                df['date'] = current_date
                print(f"未发现日期字段，使用当前日期：{current_date}")
            
            if 'update_time' not in df.columns:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df['update_time'] = current_time
                print(f"未发现更新时间字段，使用当前时间：{current_time}")
            
            # 转换数据类型 - 对所有可能的数值列进行处理
            numeric_columns = [
                'change_rate', 'turnover_rate', 'amount', 'transaction_count', 'total_market_value',
                'close_price', 'open_price', 'high_price', 'low_price', 'amplitude',
                'premium_discount', 'premium_discount_rate'
            ]
            
            # 仅处理存在的列
            numeric_columns = [col for col in numeric_columns if col in df.columns]
            
            # 转换数值类型
            for col in numeric_columns:
                try:
                    # 如果列是字符串类型，尝试清理和转换
                    if df[col].dtype == 'object':
                        # 移除非数字字符（如%、,等）
                        df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '').str.strip()
                    # 转换为浮点数
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    print(f"转换列 {col} 时出错: {str(e)}")
                    df[col] = 0.0  # 转换失败时设为默认值
            
            # 保存到数据库
            conn = self.connect()
            try:
                # 创建或替换现有表
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS etf_price")
                
                # 动态创建表字段列表
                fields = ["code TEXT", "date TEXT"]
                for col in numeric_columns:
                    fields.append(f"{col} REAL")
                fields.append("update_time TIMESTAMP")
                fields.append("PRIMARY KEY (code, date)")
                
                # 创建表
                create_table_sql = f"CREATE TABLE etf_price ({', '.join(fields)})"
                print(f"创建表SQL: {create_table_sql}")
                cursor.execute(create_table_sql)
                
                # 同时删除并重新创建历史表，确保结构一致
                cursor.execute("DROP TABLE IF EXISTS etf_price_history")
                
                # 创建历史表，结构与主表相同，但主键改为ID
                history_fields = ["id INTEGER PRIMARY KEY AUTOINCREMENT", "code TEXT", "date TEXT"]
                for col in numeric_columns:
                    history_fields.append(f"{col} REAL")
                history_fields.append("update_time TIMESTAMP")
                history_fields.append("UNIQUE(code, date)")
                
                create_history_sql = f"CREATE TABLE etf_price_history ({', '.join(history_fields)})"
                print(f"创建历史表SQL: {create_history_sql}")
                cursor.execute(create_history_sql)
                
                # 选择要保存的列 - 只保存表中定义的列
                save_columns = ['code', 'date'] + numeric_columns + ['update_time']
                # 确保所有列都存在于DataFrame中
                for col in save_columns:
                    if col not in df.columns:
                        print(f"添加缺失的列 {col}")
                        df[col] = None
                
                # 只保存定义的列
                save_df = df[save_columns].copy()
                print(f"保存到数据库的列: {save_df.columns.tolist()}")
                print(f"保存的数据样本:\n{save_df.head(2)}")
                
                # 保存数据到主表
                save_df.to_sql('etf_price', conn, if_exists='append', index=False)
                
                # 保存数据到历史表 - 使用与主表相同的列
                save_df.to_sql('etf_price_history', conn, if_exists='append', index=False)
                
                conn.commit()
                print(f"成功保存ETF价格数据，共{len(df)}条记录")
                print(f"同时保存了{len(df)}条价格历史记录到etf_price_history表")
                return True
            except Exception as e:
                print(f"保存ETF价格数据失败: {str(e)}")
                import traceback
                traceback.print_exc()
                conn.rollback()
                return False
        except Exception as e:
            print(f"处理ETF价格数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_etf_attention(self, df: pd.DataFrame) -> bool:
        """保存ETF自选数据"""
        try:
            print("开始处理ETF自选数据...")
            
            # 显示原始列名和数据
            print("原始列名：", df.columns.tolist())
            print("原始数据前5行：")
            print(df.head())
            
            # 重命名列
            column_mapping = {
                '标的代码': 'code',
                '加自选人数': 'attention_count'
            }
            df = df.rename(columns=column_mapping)
            
            # 处理代码列
            df['code'] = df['code'].astype(str).str.zfill(6)
            
            # 确保所需列存在
            required_columns = ['code', 'attention_count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF自选数据缺少必需字段: {missing_columns}")
                return False
            
            # 确保date字段存在，如果不存在使用当前日期
            if 'date' not in df.columns:
                # 添加日期列（仅取日期部分）
                current_date = datetime.now().strftime('%Y-%m-%d')
                df['date'] = current_date
                print(f"未发现日期字段，使用当前日期：{current_date}")
            else:
                print(f"使用文件中提供的日期：{df['date'].iloc[0]}")
            
            # 添加更新时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df['update_time'] = current_time
            
            # 确保数字类型正确
            try:
                df['attention_count'] = pd.to_numeric(df['attention_count'], errors='coerce').fillna(0).astype(int)
            except Exception as e:
                print(f"转换自选人数时出错: {str(e)}")
            
            # 选择需要的列
            df = df[['code', 'attention_count', 'date', 'update_time']]
            
            # 保存到数据库
            conn = self.connect()
            
            # 删除现有表并重新创建
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS etf_attention")
            cursor.execute("""
                CREATE TABLE etf_attention (
                    code TEXT PRIMARY KEY,
                    attention_count INTEGER,
                    date TEXT,
                    update_time TIMESTAMP
                )
            """)
            
            # 同时保存到历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etf_attention_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    attention_count INTEGER,
                    date TEXT,
                    update_time TIMESTAMP,
                    UNIQUE(code, date)
                )
            """)
            
            # 保存到主表
            df[['code', 'attention_count', 'date', 'update_time']].to_sql('etf_attention', conn, if_exists='append', index=False)
            
            # 获取当前数据的日期
            current_date = df['date'].iloc[0] if not df.empty else datetime.now().strftime('%Y-%m-%d')
            
            # 先删除历史表中同一天的记录
            cursor.execute("DELETE FROM etf_attention_history WHERE date = ?", (current_date,))
            print(f"已删除历史表中日期为 {current_date} 的记录")
            
            # 保存到历史表
            df[['code', 'attention_count', 'date', 'update_time']].to_sql('etf_attention_history', conn, if_exists='append', index=False)
            
            conn.commit()
            cursor.close()  # 只关闭游标，不关闭连接
            
            print(f"成功保存ETF自选数据，共{len(df)}条记录")
            print(f"同时保存了{len(df)}条历史记录到etf_attention_history表")
            return True
            
        except Exception as e:
            print(f"保存ETF自选数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.conn:
                self.conn.rollback()
            return False
    
    def save_etf_holders(self, df: pd.DataFrame) -> bool:
        """保存ETF持有人数据"""
        try:
            print("开始处理ETF持有人数据...")
            
            # 显示原始列名和数据
            print("原始列名：", df.columns.tolist())
            print("原始数据前5行：")
            print(df.head())
            
            # 检查DataFrame是否为空
            if df.empty:
                print("ETF持有人数据为空")
                return False
            
            # 确保所需列存在
            required_columns = ['code']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF持有人数据缺少必需字段: {missing_columns}")
                return False
            
            # 处理代码列
            df['code'] = df['code'].astype(str).str.strip()
            # 确保是6位数字代码
            df['code'] = df['code'].str.extract(r'(\d{6})').fillna('')
            # 移除空代码的行
            df = df[df['code'] != '']
            
            # 确保holder_count、holding_amount和holding_value列存在
            if 'holder_count' not in df.columns:
                df['holder_count'] = 0
            if 'holding_amount' not in df.columns:
                df['holding_amount'] = 0.0
            if 'holding_value' not in df.columns:
                df['holding_value'] = 0.0
            
            # 转换为数字类型
            try:
                df['holder_count'] = pd.to_numeric(df['holder_count'], errors='coerce').fillna(0).astype(int)
                df['holding_amount'] = pd.to_numeric(df['holding_amount'], errors='coerce').fillna(0).astype(float)
                df['holding_value'] = pd.to_numeric(df['holding_value'], errors='coerce').fillna(0).astype(float)
            except Exception as e:
                print(f"转换数值时出错: {str(e)}")
            
            # 添加更新时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df['update_time'] = current_time
            
            # 确保date字段存在，如果不存在使用当前日期
            if 'date' not in df.columns:
                # 添加日期列（仅取日期部分）
                current_date = datetime.now().strftime('%Y-%m-%d')
                df['date'] = current_date
                print(f"未发现日期字段，使用当前日期：{current_date}")
            else:
                print(f"使用文件中提供的日期：{df['date'].iloc[0]}")
            
            # 选择最终列
            final_columns = ['code', 'holder_count', 'holding_amount', 'holding_value', 'date', 'update_time']
            df = df[final_columns]
            
            # 保存到数据库
            conn = self.connect()
            
            # 删除现有表并重新创建
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS etf_holders")
            cursor.execute("""
                CREATE TABLE etf_holders (
                    code TEXT PRIMARY KEY,
                    holder_count INTEGER,
                    holding_amount REAL,
                    holding_value REAL,
                    date TEXT,
                    update_time TIMESTAMP,
                    FOREIGN KEY (code) REFERENCES etf_info(code)
                )
            """)
            
            # 同时创建历史表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etf_holders_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    holder_count INTEGER,
                    holding_amount REAL,
                    holding_value REAL,
                    date TEXT,
                    update_time TIMESTAMP,
                    UNIQUE(code, date)
                )
            """)
            
            # 保存到主表
            df[['code', 'holder_count', 'holding_amount', 'holding_value', 'date', 'update_time']].to_sql('etf_holders', conn, if_exists='append', index=False)
            
            # 获取当前数据的日期
            current_date = df['date'].iloc[0] if not df.empty else datetime.now().strftime('%Y-%m-%d')
            
            # 先删除历史表中同一天的记录
            cursor.execute("DELETE FROM etf_holders_history WHERE date = ?", (current_date,))
            print(f"已删除历史表中日期为 {current_date} 的记录")
            
            # 保存到历史表
            df[['code', 'holder_count', 'holding_amount', 'holding_value', 'date', 'update_time']].to_sql('etf_holders_history', conn, if_exists='append', index=False)
            
            conn.commit()
            cursor.close()  # 只关闭游标，不关闭连接
            
            print(f"成功保存ETF持有人数据，共{len(df)}条记录")
            print(f"同时保存了{len(df)}条历史记录到etf_holders_history表")
            return True
            
        except Exception as e:
            print(f"保存ETF持有人数据失败: {str(e)}")
            if self.conn:
                try:
                    self.conn.rollback()
                except:
                    pass
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
        except Exception as e:
            print(f"处理ETF指数分类数据失败: {str(e)}")
            return False
    
    def save_business_etf(self, df: pd.DataFrame) -> bool:
        """保存ETF商务协议数据"""
        try:
            print("开始处理ETF商务协议数据...")
            
            # 显示原始列名和数据
            print("原始列名：", df.columns.tolist())
            print("原始数据前5行：")
            print(df.head())
            
            # 重命名列
            column_mapping = {
                '证券代码': 'code',
                '产品名称': 'product_name',
                '基金公司简称': 'fund_company_short',
                '开始日期': 'start_date',
                '结束日期': 'end_date',
                '管理费率': 'management_fee_rate',
                '托管费率': 'custody_fee_rate',
                '指数使用费率（人工调整）': 'index_usage_fee',
                '规模': 'fund_size'  # 修改这里，将规模映射到fund_size
            }
            df = df.rename(columns=column_mapping)
            
            # 处理代码列
            df['code'] = df['code'].astype(str).str.zfill(6)
            
            # 确保所需列存在
            required_columns = ['code', 'product_name', 'fund_company_short', 'start_date', 'end_date',
                              'management_fee_rate', 'custody_fee_rate', 'fund_size']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF商务协议数据缺少必需字段: {missing_columns}")
                return False
            
            # 选择需要的列
            df = df[required_columns]
            
            # 添加更新时间
            df['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存到数据库
            conn = self.connect()
            
            # 创建游标执行DROP TABLE操作
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS etf_business")
            cursor.execute("""
                CREATE TABLE etf_business (
                    code TEXT PRIMARY KEY,
                    product_name TEXT,
                    fund_company_short TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    management_fee_rate REAL,
                    custody_fee_rate REAL,
                    fund_size REAL,
                    update_time TIMESTAMP
                )
            """)
            
            # 保存数据
            df.to_sql('etf_business', conn, if_exists='append', index=False)
            conn.commit()
            cursor.close()  # 只关闭游标，不关闭连接
            
            print(f"成功保存ETF商务协议数据，共{len(df)}条记录")
            return True
        
        except Exception as e:
            print(f"保存ETF商务协议数据失败: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def check_etf_code_exists(self, code):
        """检查ETF代码是否存在"""
        try:
            # 处理可能带有后缀的ETF代码
            base_code = code
            if '.' in code:
                base_code = code.split('.')[0]
            elif code.startswith('sh') or code.startswith('sz'):
                base_code = code[2:]
            
            # 确保是6位数字
            base_code = base_code.zfill(6)
            
            print(f"检查ETF代码是否存在: {code} -> {base_code}")
            
            # 使用两种模式匹配：精确匹配和带后缀匹配
            query = "SELECT COUNT(*) FROM etf_info WHERE code LIKE ? OR code LIKE ?"
            params = [f"%{base_code}%", f"%{base_code}.%"]
            
            print(f"执行查询: {query}")
            print(f"查询参数: {params}")
            
            result = self.execute_query(query, params)
            exists = result[0][0] > 0 if result else False
            
            print(f"ETF代码是否存在: {exists}")
            return exists
            
        except Exception as e:
            print(f"检查ETF代码是否存在时出错: {str(e)}")
            return False
    
    def check_company_exists(self, company_name):
        """检查基金公司是否存在"""
        try:
            query = "SELECT COUNT(*) FROM etf_info WHERE fund_manager LIKE ?"
            result = self.execute_query(query, (f"%{company_name}%",))
            return result[0][0] > 0 if result else False
        except Exception as e:
            print(f"检查基金公司是否存在时出错: {str(e)}")
            return False
    
    def check_index_name_exists(self, index_name):
        """检查指数名称是否存在"""
        try:
            query = "SELECT COUNT(*) FROM etf_info WHERE tracking_index_name LIKE ?"
            result = self.execute_query(query, (f"%{index_name}%",))
            return result[0][0] > 0 if result else False
        except Exception as e:
            print(f"检查指数名称是否存在时出错: {str(e)}")
            return False
    
    def get_attention_changes(self, code: str) -> dict:
        """获取ETF自选人数变化（当日和近5日）"""
        try:
            # 标准化ETF代码
            code = normalize_etf_code(code)
            
            # 连接数据库
            conn = self.connect()
            cursor = conn.cursor()
            
            # 查询最近日期的自选人数
            cursor.execute("""
                SELECT date, attention_count
                FROM etf_attention_history
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 1
            """, (code,))
            
            latest_data = cursor.fetchone()
            
            if not latest_data:
                return {'daily_change': 0, 'five_day_change': 0}
                
            latest_date, latest_count = latest_data
            
            # 查询前一天的自选人数
            cursor.execute("""
                SELECT date, attention_count
                FROM etf_attention_history
                WHERE code = ? AND date < ?
                ORDER BY date DESC
                LIMIT 1
            """, (code, latest_date))
            
            previous_data = cursor.fetchone()
            previous_count = previous_data[1] if previous_data else latest_count
            
            # 查询5天前的自选人数
            cursor.execute("""
                SELECT date, attention_count
                FROM etf_attention_history
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 6
            """, (code,))
            
            all_data = cursor.fetchall()
            # 安全获取五天前的数据
            five_day_before_count = latest_count  # 默认值
            if len(all_data) >= 6:
                five_day_before_count = all_data[5][1]
            
            # 计算变化
            daily_change = latest_count - previous_count
            five_day_change = latest_count - five_day_before_count
            
            return {
                'daily_change': daily_change,
                'five_day_change': five_day_change
            }
            
        except Exception as e:
            print(f"获取ETF自选人数变化出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'daily_change': 0, 'five_day_change': 0}
    
    def get_holder_changes(self, code: str) -> dict:
        """获取ETF持仓人数变化（当日和近5日）"""
        try:
            # 标准化ETF代码
            code = normalize_etf_code(code)
            
            # 连接数据库
            conn = self.connect()
            cursor = conn.cursor()
            
            # 查询最近日期的持仓人数
            cursor.execute("""
                SELECT date, holder_count
                FROM etf_holders_history
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 1
            """, (code,))
            
            latest_data = cursor.fetchone()
            
            if not latest_data:
                return {'daily_change': 0, 'five_day_change': 0}
                
            latest_date, latest_count = latest_data
            
            # 查询前一天的持仓人数
            cursor.execute("""
                SELECT date, holder_count
                FROM etf_holders_history
                WHERE code = ? AND date < ?
                ORDER BY date DESC
                LIMIT 1
            """, (code, latest_date))
            
            previous_data = cursor.fetchone()
            previous_count = previous_data[1] if previous_data else latest_count
            
            # 查询5天前的持仓人数
            cursor.execute("""
                SELECT date, holder_count
                FROM etf_holders_history
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 6
            """, (code,))
            
            all_data = cursor.fetchall()
            # 安全获取五天前的数据
            five_day_before_count = latest_count  # 默认值
            if len(all_data) >= 6:
                five_day_before_count = all_data[5][1]
            
            # 计算变化
            daily_change = latest_count - previous_count
            five_day_change = latest_count - five_day_before_count
            
            return {
                'daily_change': daily_change,
                'five_day_change': five_day_change
            }
            
        except Exception as e:
            print(f"获取ETF持仓人数变化出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'daily_change': 0, 'five_day_change': 0}
    
    def get_value_changes(self, code: str) -> dict:
        """获取ETF持仓市值变化（当日和近5日）"""
        try:
            # 标准化ETF代码
            code = normalize_etf_code(code)
            
            # 连接数据库
            conn = self.connect()
            cursor = conn.cursor()
            
            # 查询最近日期的持仓市值
            cursor.execute("""
                SELECT date, holding_value
                FROM etf_holders_history
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 1
            """, (code,))
            
            latest_data = cursor.fetchone()
            
            if not latest_data:
                return {'daily_change': 0, 'five_day_change': 0}
                
            latest_date, latest_value = latest_data
            
            # 查询前一天的持仓市值
            cursor.execute("""
                SELECT date, holding_value
                FROM etf_holders_history
                WHERE code = ? AND date < ?
                ORDER BY date DESC
                LIMIT 1
            """, (code, latest_date))
            
            previous_data = cursor.fetchone()
            previous_value = previous_data[1] if previous_data else latest_value
            
            # 查询5天前的持仓市值
            cursor.execute("""
                SELECT date, holding_value
                FROM etf_holders_history
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 6
            """, (code,))
            
            all_data = cursor.fetchall()
            # 安全获取五天前的数据
            five_day_before_value = latest_value  # 默认值
            if len(all_data) >= 6:
                five_day_before_value = all_data[5][1]
            
            # 计算变化
            daily_change = latest_value - previous_value
            five_day_change = latest_value - five_day_before_value
            
            return {
                'daily_change': daily_change,
                'five_day_change': five_day_change
            }
            
        except Exception as e:
            print(f"获取ETF持仓市值变化出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'daily_change': 0, 'five_day_change': 0}
    
    def get_amount_changes(self, code: str) -> dict:
        """获取ETF持仓份额变化（当日和近5日）"""
        try:
            # 标准化ETF代码
            code = normalize_etf_code(code)
            
            # 连接数据库
            conn = self.connect()
            cursor = conn.cursor()
            
            # 查询最近日期的持仓份额
            cursor.execute("""
                SELECT date, holding_amount
                FROM etf_holders_history
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 1
            """, (code,))
            
            latest_data = cursor.fetchone()
            
            if not latest_data:
                return {'daily_change': 0, 'five_day_change': 0}
                
            latest_date, latest_amount = latest_data
            
            # 查询前一天的持仓份额
            cursor.execute("""
                SELECT date, holding_amount
                FROM etf_holders_history
                WHERE code = ? AND date < ?
                ORDER BY date DESC
                LIMIT 1
            """, (code, latest_date))
            
            previous_data = cursor.fetchone()
            previous_amount = previous_data[1] if previous_data else latest_amount
            
            # 查询5天前的持仓份额
            cursor.execute("""
                SELECT date, holding_amount
                FROM etf_holders_history
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 6
            """, (code,))
            
            all_data = cursor.fetchall()
            # 安全获取五天前的数据
            five_day_before_amount = latest_amount  # 默认值
            if len(all_data) >= 6:
                five_day_before_amount = all_data[5][1]
            
            # 计算变化
            daily_change = latest_amount - previous_amount
            five_day_change = latest_amount - five_day_before_amount
            
            return {
                'daily_change': daily_change,
                'five_day_change': five_day_change
            }
            
        except Exception as e:
            print(f"获取ETF持仓份额变化出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'daily_change': 0, 'five_day_change': 0}
    
    def search_by_etf_code(self, code: str) -> List[Dict]:
        """根据ETF代码搜索"""
        try:
            # 标准化ETF代码
            code = code.strip().upper()
            # 移除可能的后缀
            if '.' in code:
                code = code.split('.')[0]
            elif code.startswith('sh') or code.startswith('sz'):
                code = code[2:]
            # 确保是6位数字
            code = code.zfill(6)
            
            print(f"搜索ETF代码: {code}")
            
            # 构建查询，获取所有必要字段，包括持仓人数和持仓价值
            # 使用 SUBSTR 来提取ETF代码的数字部分进行比较
            query = """
            SELECT 
                i.code,
                i.name,
                i.fund_manager,
                i.fund_size,
                i.exchange,
                i.tracking_index_code,
                i.tracking_index_name,
                i.tracking_error,
                i.information_ratio,
                i.total_holder_count,
                i.management_fee_rate,
                i.custody_fee_rate,
                i.index_usage_fee,
                i.total_annual_fee_rate,
                a.attention_count,
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business,
                h.holder_count,
                h.holding_amount,
                h.holding_value,
                i.daily_avg_volume,
                i.daily_volume
            FROM etf_info i
            LEFT JOIN etf_attention a ON SUBSTR(i.code, 1, 6) = SUBSTR(a.code, 1, 6)
            LEFT JOIN etf_business b ON SUBSTR(i.code, 1, 6) = SUBSTR(b.code, 1, 6)
            LEFT JOIN etf_holders h ON SUBSTR(i.code, 1, 6) = SUBSTR(h.code, 1, 6)
            WHERE i.code LIKE ? OR i.code LIKE ?
            ORDER BY i.fund_size DESC
            """
            
            # 执行查询
            results = self.execute_query(query, (f"%{code}%", f"%{code}.%"))
            
            if not results:
                return []
            
            # 处理结果
            processed_results = []
            for row in results:
                etf_code = row[0]
                
                # 获取变化数据
                attention_changes = self.get_attention_changes(etf_code)
                holder_changes = self.get_holder_changes(etf_code)
                value_changes = self.get_value_changes(etf_code)
                amount_changes = self.get_amount_changes(etf_code)
                
                result = {
                    'code': etf_code,
                    'name': row[1],
                    'manager': row[2],
                    'fund_size': float(row[3]) if row[3] is not None else 0.0,
                    'exchange': row[4],
                    'tracking_index_code': row[5],
                    'tracking_index_name': row[6],
                    'tracking_error': float(row[7]) if row[7] is not None else 0.0,
                    'information_ratio': float(row[8]) if row[8] is not None else 0.0,
                    'total_holder_count': int(row[9]) if row[9] is not None else 0,
                    'management_fee_rate': float(row[10]) if row[10] is not None else 0.0,
                    'custody_fee_rate': float(row[11]) if row[11] is not None else 0.0,
                    'index_usage_fee': float(row[12]) if row[12] is not None else 0.0,
                    'total_annual_fee_rate': float(row[13]) if row[13] is not None else 0.0,
                    'attention_count': self.get_latest_attention_count(etf_code) or (int(row[14]) if row[14] is not None else 0),  # 优先使用历史表中的最新数据
                    'is_business': bool(row[15]),
                    'business_text': '商务品' if row[15] else '非商务品',
                    'holder_count': int(row[16]) if row[16] is not None else 0,
                    'holding_amount': float(row[17]) if row[17] is not None else 0.0,
                    'holding_value': float(row[18]) if row[18] is not None else 0.0,
                    'daily_avg_volume': float(row[19]) if row[19] is not None else 0.0,
                    'daily_volume': float(row[20]) if row[20] is not None else 0.0,
                    # 添加变化数据
                    'attention_daily_change': attention_changes['daily_change'],
                    'attention_five_day_change': attention_changes['five_day_change'],
                    'holder_daily_change': holder_changes['daily_change'],
                    'holder_five_day_change': holder_changes['five_day_change'],
                    'holding_amount_daily_change': amount_changes['daily_change'],
                    'holding_amount_five_day_change': amount_changes['five_day_change'],
                    'holding_value_daily_change': value_changes['daily_change'],
                    'holding_value_five_day_change': value_changes['five_day_change']
                }
                processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            print(f"搜索ETF代码时出错: {str(e)}")
            return []
    
    def search_by_index_name(self, index_name):
        """搜索与指定指数名称相关的ETF"""
        try:
            # 构建查询SQL
            query = """
            SELECT 
                i.code, 
                i.name, 
                i.fund_manager,
                i.fund_size,
                i.management_fee_rate, 
                i.tracking_error,
                i.total_holder_count,
                i.tracking_index_code, 
                i.tracking_index_name,
                a.attention_count,
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business,
                h.holder_count,
                h.holding_amount,
                h.holding_value,
                i.daily_avg_volume,
                i.daily_volume
            FROM etf_info i
            LEFT JOIN etf_attention a ON SUBSTR(i.code, 1, 6) = SUBSTR(a.code, 1, 6)
            LEFT JOIN etf_business b ON SUBSTR(i.code, 1, 6) = SUBSTR(b.code, 1, 6) 
            LEFT JOIN etf_holders h ON SUBSTR(i.code, 1, 6) = SUBSTR(h.code, 1, 6)
            WHERE i.tracking_index_name LIKE ?
            ORDER BY i.fund_size DESC
            """
            
            # 执行查询
            params = [f'%{index_name}%']
            results = self.execute_query(query, params)
            
            # 如果没有结果，返回空列表
            if not results:
                return []
            
            # 按跟踪指数分组
            index_groups = {}
            etf_results = []
            
            for row in results:
                etf_code = row[0]
                index_code = row[7] or '未知指数'
                index_name = row[8] or '未知指数名称'
                
                # 获取变化数据
                attention_changes = self.get_attention_changes(etf_code)
                holder_changes = self.get_holder_changes(etf_code)
                value_changes = self.get_value_changes(etf_code)
                amount_changes = self.get_amount_changes(etf_code)
                
                result = {
                    'code': etf_code,
                    'name': row[1],
                    'manager': row[2],
                    'fund_size': float(row[3] or 0),
                    'management_fee_rate': float(row[4] or 0), 
                    'tracking_error': float(row[5] or 0),
                    'total_holder_count': int(row[6] or 0),
                    'tracking_index_code': index_code,
                    'tracking_index_name': index_name,
                    'attention_count': self.get_latest_attention_count(etf_code) or int(row[9] or 0),  # 优先使用历史表中的最新数据
                    'is_business': bool(row[10]),
                    'business_text': '商务品' if row[10] else '非商务品',
                    'holder_count': int(row[11] or 0),
                    'holding_amount': float(row[12] or 0),
                    'holding_value': float(row[13] or 0),
                    'daily_avg_volume': float(row[14] or 0),
                    'daily_volume': float(row[15] or 0),
                    # 添加变化数据
                    'attention_daily_change': attention_changes['daily_change'],
                    'attention_five_day_change': attention_changes['five_day_change'],
                    'holder_daily_change': holder_changes['daily_change'],
                    'holder_five_day_change': holder_changes['five_day_change'],
                    'holding_amount_daily_change': amount_changes['daily_change'],
                    'holding_amount_five_day_change': amount_changes['five_day_change'],
                    'holding_value_daily_change': value_changes['daily_change'],
                    'holding_value_five_day_change': value_changes['five_day_change']
                }
                
                # 添加到结果列表
                etf_results.append(result)
                
                # 初始化当前指数组
                if index_code not in index_groups:
                    index_groups[index_code] = {
                        'index_code': index_code,
                        'index_name': index_name,
                        'etfs': [],
                        'total_scale': 0
                    }
                    
                    # 添加指数简介
                    index_intro = get_index_intro(index_code)
                    if index_intro:
                        index_groups[index_code]['index_intro'] = index_intro
                
                # 添加到对应指数组
                index_groups[index_code]['etfs'].append(result)
                # 累加该指数的总规模
                index_groups[index_code]['total_scale'] += result['fund_size']
            
            # 将索引组转为列表并按总规模排序
            index_groups_list = list(index_groups.values())
            index_groups_list.sort(key=lambda x: x['total_scale'], reverse=True)
            
            # 对每个指数组内的ETF按规模排序
            for group in index_groups_list:
                group['etfs'].sort(key=lambda x: x['fund_size'], reverse=True)
                group['etf_count'] = len(group['etfs'])
            
            # 返回分组结果
            return {
                'is_grouped': True,
                'index_groups': index_groups_list,
                'index_count': len(index_groups_list),
                'count': len(etf_results),
                'results': etf_results  # 保留原始的扁平结果，以防需要
            }
            
        except Exception as e:
            print(f"按指数名称搜索时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def search_by_index_code(self, index_code):
        """根据指数代码搜索ETF"""
        try:
            index_code = index_code.strip()
            print(f"搜索指数代码: {index_code}")
            
            # 如果是带后缀的，去掉后缀
            if '.' in index_code:
                index_code = index_code.split('.')[0]
            
            query = """
            SELECT 
                i.code, 
                i.name, 
                i.fund_manager,
                i.fund_size,
                i.exchange,
                i.tracking_index_code,
                i.tracking_index_name,
                i.tracking_error,
                i.information_ratio,
                i.total_holder_count,
                i.management_fee_rate,
                i.custody_fee_rate,
                i.index_usage_fee,
                i.total_annual_fee_rate,
                a.attention_count,
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business,
                h.holder_count,
                h.holding_amount,
                h.holding_value,
                i.daily_avg_volume,
                i.daily_volume
            FROM etf_info i
            LEFT JOIN etf_attention a ON SUBSTR(i.code, 1, 6) = SUBSTR(a.code, 1, 6)
            LEFT JOIN etf_business b ON SUBSTR(i.code, 1, 6) = SUBSTR(b.code, 1, 6)
            LEFT JOIN etf_holders h ON SUBSTR(i.code, 1, 6) = SUBSTR(h.code, 1, 6)
            WHERE i.tracking_index_code LIKE ?
            ORDER BY i.fund_size DESC
            """
            
            pattern = f"%{index_code}%"
            results = self.execute_query(query, (pattern,))
            
            if not results:
                return []
            
            processed_results = []
            for row in results:
                result = {
                    'code': row[0],
                    'name': row[1],
                    'manager': row[2],
                    'fund_size': float(row[3]) if row[3] is not None else 0.0,
                    'exchange': row[4],
                    'tracking_index_code': row[5],
                    'tracking_index_name': row[6],
                    'tracking_error': float(row[7]) if row[7] is not None else 0.0,
                    'information_ratio': float(row[8]) if row[8] is not None else 0.0,
                    'total_holder_count': int(row[9]) if row[9] is not None else 0,
                    'management_fee_rate': float(row[10]) if row[10] is not None else 0.0,
                    'custody_fee_rate': float(row[11]) if row[11] is not None else 0.0,
                    'index_usage_fee': float(row[12]) if row[12] is not None else 0.0,
                    'total_annual_fee_rate': float(row[13]) if row[13] is not None else 0.0,
                    'attention_count': int(row[14]) if row[14] is not None else 0,
                    'is_business': bool(row[15]),
                    'business_text': '商务品' if row[15] else '非商务品',
                    'holder_count': int(row[16]) if row[16] is not None else 0,
                    'holding_amount': float(row[17]) if row[17] is not None else 0.0,
                    'holding_value': float(row[18]) if row[18] is not None else 0.0,
                    'daily_avg_volume': float(row[19]) if row[19] is not None else 0.0,
                    'daily_volume': float(row[20]) if row[20] is not None else 0.0,
                    # 添加变化数据
                    'attention_daily_change': self.get_attention_changes(row[0])['daily_change'],
                    'attention_five_day_change': self.get_attention_changes(row[0])['five_day_change'],
                    'holder_daily_change': self.get_holder_changes(row[0])['daily_change'],
                    'holder_five_day_change': self.get_holder_changes(row[0])['five_day_change'],
                    'holding_amount_daily_change': self.get_amount_changes(row[0])['daily_change'],
                    'holding_amount_five_day_change': self.get_amount_changes(row[0])['five_day_change'],
                    'holding_value_daily_change': self.get_value_changes(row[0])['daily_change'],
                    'holding_value_five_day_change': self.get_value_changes(row[0])['five_day_change']
                }
                processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            print(f"搜索指数代码时出错: {str(e)}")
            return []
    
    def search_by_company(self, company_name):
        """根据基金公司名称搜索ETF"""
        try:
            company_name = company_name.strip()
            print(f"搜索基金公司: {company_name}")
            
            query = """
            SELECT 
                i.code, 
                i.name, 
                i.fund_manager,
                i.fund_size,
                i.exchange,
                i.tracking_index_code, 
                i.tracking_index_name,
                i.tracking_error,
                i.information_ratio,
                i.total_holder_count,
                i.management_fee_rate, 
                i.custody_fee_rate,
                i.index_usage_fee,
                i.total_annual_fee_rate,
                a.attention_count,
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business,
                h.holder_count,
                h.holding_amount,
                h.holding_value,
                i.daily_avg_volume,
                i.daily_volume
            FROM etf_info i
            LEFT JOIN etf_attention a ON SUBSTR(i.code, 1, 6) = SUBSTR(a.code, 1, 6)
            LEFT JOIN etf_business b ON SUBSTR(i.code, 1, 6) = SUBSTR(b.code, 1, 6)
            LEFT JOIN etf_holders h ON SUBSTR(i.code, 1, 6) = SUBSTR(h.code, 1, 6)
            WHERE i.fund_manager LIKE ?
            ORDER BY i.fund_size DESC
            """
            
            pattern = f"%{company_name}%"
            results = self.execute_query(query, (pattern,))
            
            if not results:
                return []
            
            processed_results = []
            for row in results:
                result = {
                    'code': row[0],
                    'name': row[1],
                    'manager': row[2],
                    'fund_size': float(row[3]) if row[3] is not None else 0.0,
                    'exchange': row[4],
                    'tracking_index_code': row[5],
                    'tracking_index_name': row[6],
                    'tracking_error': float(row[7]) if row[7] is not None else 0.0,
                    'information_ratio': float(row[8]) if row[8] is not None else 0.0,
                    'total_holder_count': int(row[9]) if row[9] is not None else 0,
                    'management_fee_rate': float(row[10]) if row[10] is not None else 0.0,
                    'custody_fee_rate': float(row[11]) if row[11] is not None else 0.0,
                    'index_usage_fee': float(row[12]) if row[12] is not None else 0.0,
                    'total_annual_fee_rate': float(row[13]) if row[13] is not None else 0.0,
                    'attention_count': self.get_latest_attention_count(row[0]) or (int(row[14]) if row[14] is not None else 0),  # 优先使用历史表中的最新数据
                    'is_business': bool(row[15]),
                    'business_text': '商务品' if row[15] else '非商务品',
                    'holder_count': int(row[16]) if row[16] is not None else 0,
                    'holding_amount': float(row[17]) if row[17] is not None else 0.0,
                    'holding_value': float(row[18]) if row[18] is not None else 0.0,
                    'daily_avg_volume': float(row[19]) if row[19] is not None else 0.0,
                    'daily_volume': float(row[20]) if row[20] is not None else 0.0,
                    # 添加变化数据
                    'attention_daily_change': self.get_attention_changes(row[0])['daily_change'],
                    'attention_five_day_change': self.get_attention_changes(row[0])['five_day_change'],
                    'holder_daily_change': self.get_holder_changes(row[0])['daily_change'],
                    'holder_five_day_change': self.get_holder_changes(row[0])['five_day_change'],
                    'holding_amount_daily_change': self.get_amount_changes(row[0])['daily_change'],
                    'holding_amount_five_day_change': self.get_amount_changes(row[0])['five_day_change'],
                    'holding_value_daily_change': self.get_value_changes(row[0])['daily_change'],
                    'holding_value_five_day_change': self.get_value_changes(row[0])['five_day_change']
                }
                processed_results.append(result)
            
            # 明确返回扁平化的结果列表，不按指数分组
            return processed_results
            
        except Exception as e:
            print(f"搜索基金公司时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def general_search(self, keyword):
        """通用搜索，关键词可能是ETF代码、指数名称、基金公司名称等"""
        try:
            print(f"通用搜索关键词: '{keyword}'")
            
            # 先尝试单独用基金公司名称搜索，看是否有结果
            if '基金' in keyword or '资管' in keyword or '汇添富' in keyword or '华夏' in keyword or '易方达' in keyword:
                print(f"尝试先用公司名称搜索: '{keyword}'")
                company_results = self.search_by_company(keyword)
                if company_results:
                    print(f"基金公司名称搜索成功，找到{len(company_results)}条结果")
                    return {
                        'is_grouped': True,
                        'index_groups': [],
                        'index_count': 0,
                        'count': len(company_results),
                        'results': company_results,
                        'search_type': '基金公司名称'
                    }
                else:
                    print(f"基金公司名称搜索失败，继续尝试通用搜索")
            
            # 构建查询SQL
            query = """
            SELECT 
                i.code as etf_code, 
                i.name as etf_name, 
                i.fund_manager,
                i.fund_size,
                i.management_fee_rate, 
                i.tracking_error,
                i.total_holder_count,
                i.tracking_index_code, 
                i.tracking_index_name,
                a.attention_count,
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business,
                h.holder_count,
                h.holding_amount,
                h.holding_value,
                i.daily_avg_volume,
                i.daily_volume
            FROM etf_info i
            LEFT JOIN etf_attention a ON SUBSTR(i.code, 1, 6) = SUBSTR(a.code, 1, 6)
            LEFT JOIN etf_business b ON SUBSTR(i.code, 1, 6) = SUBSTR(b.code, 1, 6)
            LEFT JOIN etf_holders h ON SUBSTR(i.code, 1, 6) = SUBSTR(h.code, 1, 6)
            WHERE i.code LIKE ? OR i.name LIKE ? OR i.fund_manager LIKE ? OR i.tracking_index_name LIKE ? OR i.tracking_index_code LIKE ?
            ORDER BY i.fund_size DESC
            """
            
            # 执行查询
            params = [f'%{keyword}%'] * 5
            print(f"执行SQL查询: {query}")
            print(f"SQL参数: {params}")
            results = self.execute_query(query, params)
            
            # 如果没有结果，返回空列表
            if not results:
                print(f"SQL查询没有结果")
                return []
            
            print(f"SQL查询返回{len(results)}条结果")
            # 按跟踪指数分组
            index_groups = {}
            etf_results = []
            
            for row in results:
                etf_code = row[0]
                index_code = row[7] or '未知指数'
                index_name = row[8] or '未知指数名称'
                
                # 获取变化数据
                attention_changes = self.get_attention_changes(etf_code)
                holder_changes = self.get_holder_changes(etf_code)
                value_changes = self.get_value_changes(etf_code)
                amount_changes = self.get_amount_changes(etf_code)
                
                result = {
                    'code': etf_code,  # row[0]
                    'name': row[1],
                    'manager': row[2],
                    'fund_size': float(row[3]) if row[3] is not None else 0.0,
                    'management_fee_rate': float(row[4]) if row[4] is not None else 0.0,
                    'tracking_error': float(row[5]) if row[5] is not None else 0.0,
                    'total_holder_count': int(row[6]) if row[6] is not None else 0,
                    'tracking_index_code': row[7],
                    'tracking_index_name': row[8],
                    'attention_count': self.get_latest_attention_count(etf_code) or (int(row[9]) if row[9] is not None else 0),
                    'is_business': bool(row[10]),
                    'business_text': '商务品' if bool(row[10]) else '非商务品',
                    'holder_count': int(row[11]) if row[11] is not None else 0,
                    'holding_amount': float(row[12]) if row[12] is not None else 0.0,
                    'holding_value': float(row[13]) if row[13] is not None else 0.0,
                    'daily_avg_volume': float(row[14]) if row[14] is not None else 0.0,
                    'daily_volume': float(row[15]) if row[15] is not None else 0.0,
                    'attention_daily_change': attention_changes['daily_change'],
                    'attention_five_day_change': attention_changes['five_day_change'],
                    'holder_daily_change': holder_changes['daily_change'],
                    'holder_five_day_change': holder_changes['five_day_change'],
                    'holding_amount_daily_change': amount_changes['daily_change'],
                    'holding_amount_five_day_change': amount_changes['five_day_change'],
                    'holding_value_daily_change': value_changes['daily_change'],
                    'holding_value_five_day_change': value_changes['five_day_change']
                }
                
                # 添加到结果列表
                etf_results.append(result)
                
                # 初始化当前指数组
                if index_code not in index_groups:
                    index_groups[index_code] = {
                        'index_code': index_code,
                        'index_name': index_name,
                        'etfs': [],
                        'total_scale': 0
                    }
                    
                    # 添加指数简介
                    index_intro = get_index_intro(index_code)
                    if index_intro:
                        index_groups[index_code]['index_intro'] = index_intro
                
                # 添加到对应指数组
                index_groups[index_code]['etfs'].append(result)
                # 累加该指数的总规模
                index_groups[index_code]['total_scale'] += result['fund_size']
            
            # 将索引组转为列表并按总规模排序
            index_groups_list = list(index_groups.values())
            index_groups_list.sort(key=lambda x: x['total_scale'], reverse=True)
            
            # 对每个指数组内的ETF按规模排序
            for group in index_groups_list:
                group['etfs'].sort(key=lambda x: x['fund_size'], reverse=True)
                group['etf_count'] = len(group['etfs'])
            
            # 返回分组结果
            return {
                'is_grouped': True,
                'index_groups': index_groups_list,
                'index_count': len(index_groups_list),
                'count': len(etf_results),
                'results': etf_results  # 保留原始的扁平结果，以防需要
            }
        
        except Exception as e:
            print(f"通用搜索时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_etfs_by_index_code(self, index_code):
        """获取指定指数代码的所有ETF"""
        try:
            query = """
            SELECT code, name, fund_size, fund_manager, exchange, tracking_index_code,
                   tracking_error, information_ratio, total_holder_count
            FROM etf_info
            WHERE tracking_index_code = ?
            """
            result = self.execute_query(query, (index_code,))
            columns = ['code', 'name', 'fund_size', 'fund_manager', 'exchange', 'tracking_index_code',
                      'tracking_error', 'information_ratio', 'total_holder_count']
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            print(f"获取指定指数代码的ETF时出错: {str(e)}")
            return []
    
    def get_etf_attention_history(self, etf_code):
        """获取ETF自选人数历史数据"""
        try:
            # 标准化ETF代码
            etf_code = normalize_etf_code(etf_code)
            
            # 连接数据库
            conn = self.connect()
            cursor = conn.cursor()
            
            # 查询指定ETF的历史自选人数
            cursor.execute("""
                SELECT date, attention_count
                FROM etf_attention_history
                WHERE code LIKE ?
                ORDER BY date
            """, (f"%{etf_code}%",))
            
            history = cursor.fetchall()
            
            # 格式化结果
            result = [{"date": date, "attention_count": count} for date, count in history]
            
            return result
        
        except Exception as e:
            print(f"获取ETF自选人数历史数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
            
    def get_etf_holders_history(self, etf_code):
        """获取ETF持有人历史数据"""
        try:
            # 标准化ETF代码
            etf_code = normalize_etf_code(etf_code)
            
            # 连接数据库
            conn = self.connect()
            cursor = conn.cursor()
            
            # 查询指定ETF的历史持有人数据
            cursor.execute("""
                SELECT date, holder_count, holding_amount, holding_value
                FROM etf_holders_history
                WHERE code LIKE ?
                ORDER BY date
            """, (f"%{etf_code}%",))
            
            history = cursor.fetchall()
            
            # 格式化结果
            result = [
                {
                    "date": date, 
                    "holder_count": holder_count,
                    "holding_amount": holding_amount,
                    "holding_value": holding_value
                } 
                for date, holder_count, holding_amount, holding_value in history
            ]
            
            return result
        
        except Exception as e:
            print(f"获取ETF持有人历史数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
            
            
            # 如果存在历史规模表，查询历史规模数据
            cursor.execute("""
                SELECT count(*)
                FROM sqlite_master
                WHERE type='table' AND name='etf_fund_size_history'
            """)
            
            if cursor.fetchone()[0] > 0:
                cursor.execute("""
                    SELECT date, fund_size
                    FROM etf_fund_size_history
                    WHERE code LIKE ?
                    ORDER BY date
                """, (f"%{etf_code}%",))
                
                history = cursor.fetchall()
                
                # 格式化结果
                result = [{"date": date, "fund_size": fund_size} for date, fund_size in history]
                
                return result
            else:
                print("etf_fund_size_history表不存在")
                return []
        
        except Exception as e:
            print(f"获取ETF规模历史数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_latest_attention_count(self, etf_code):
        """获取ETF最新的自选数据（从历史表中）"""
        try:
            # 标准化ETF代码
            etf_code = normalize_etf_code(etf_code)
            
            # 连接数据库
            conn = self.connect()
            cursor = conn.cursor()
            
            # 查询最新日期的自选人数
            cursor.execute("""
                SELECT attention_count, date
                FROM etf_attention_history 
                WHERE code = ? 
                ORDER BY date DESC 
                LIMIT 1
            """, (etf_code,))
            
            latest_data = cursor.fetchone()
            if latest_data:
                attention_count = latest_data[0]
                date = latest_data[1]
                print(f"获取ETF {etf_code} 最新自选数据: {attention_count}，日期: {date}")
                return attention_count
            else:
                # 如果找不到历史数据，尝试从etf_attention表获取
                cursor.execute("""
                    SELECT attention_count
                    FROM etf_attention 
                    WHERE code = ? 
                    LIMIT 1
                """, (etf_code,))
                
                current_data = cursor.fetchone()
                if current_data and current_data[0]:
                    return current_data[0]
                else:
                    return 0
        except Exception as e:
            print(f"获取ETF最新自选数据出错: {str(e)}")
            return 0

    def get_fund_company_attention_history(self, company_name: str) -> List[Dict]:
        """获取基金公司自选历史汇总数据"""
        try:
            # 使用 LIKE 匹配基金公司名称
            # 这将汇总所有基金管理人名称包含所提供 company_name 字符串的ETF的自选数据
            query = """
            SELECT
                eah.date,
                SUM(eah.attention_count) as total_attention_count
            FROM etf_attention_history eah
            JOIN etf_info ei ON eah.code = ei.code
            WHERE ei.fund_manager LIKE ?
            GROUP BY eah.date
            ORDER BY eah.date ASC;
            """
            params = (f'%{company_name}%',)
            result = self.execute_query(query, params)
            return [
                {
                    'date': row[0],
                    'attention_count': row[1] if row[1] is not None else 0
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取基金公司 {company_name} 自选历史汇总数据失败: {str(e)}")
            return []

    def get_fund_company_holders_history(self, company_name: str) -> List[Dict]:
        """获取基金公司持有人和持仓价值历史汇总数据"""
        try:
            # 使用 LIKE 匹配基金公司名称
            query = """
            SELECT
                ehh.date,
                SUM(ehh.holder_count) as total_holder_count,
                SUM(ehh.holding_value) as total_holding_value
            FROM etf_holders_history ehh
            JOIN etf_info ei ON ehh.code = ei.code
            WHERE ei.fund_manager LIKE ?
            GROUP BY ehh.date
            ORDER BY ehh.date ASC;
            """
            params = (f'%{company_name}%',)
            result = self.execute_query(query, params)
            return [
                {
                    'date': row[0],
                    'holder_count': row[1] if row[1] is not None else 0,
                    'holding_value': row[2] if row[2] is not None else 0
                }
                for row in result
            ]
        except Exception as e:
            print(f"获取基金公司 {company_name} 持有人历史汇总数据失败: {str(e)}")
            return []

    def get_company_analytics_for_dashboard(self, sort_by: str = 'total_holding_value', ascending: bool = False, limit: int = None) -> List[Dict]:
        """获取用于仪表盘展示的基金公司分析数据，支持排序和限制数量"""
        # 需求1: 默认排序改为 total_holding_value, 移除 limit 的默认值
        print(f"开始获取基金公司分析数据用于仪表盘，排序依据: {sort_by}, 升序: {ascending}, 限制: {limit}")
        try:
            conn = self.connect()
            # 构建基础查询语句
            query = "SELECT * FROM etf_company_analytics"
            
            # 添加排序逻辑
            # 为防止SQL注入，sort_by应该是预定义的、安全的列名
            allowed_sort_columns = [
                'company_name', 'company_short_name', 'product_count', 'total_fund_size', 'avg_fund_size',
                'total_holder_count_info', 'latest_date', 'total_amount',
                'avg_turnover_rate', 'total_attention_count', 'total_shares_holders',
                'total_holder_count_holders', 'holder_attention_ratio', 'total_holding_value',
                'business_agreement_count', 'business_agreement_ratio', 'business_agreement_total_size',
                'business_agreement_avg_mgmt_fee', 'business_agreement_avg_cust_fee', 'update_timestamp',
                'business_total_holding_value', 'business_holding_value_ratio' # 新增：允许按这两个新列排序
            ]
            # 确保 sort_by 是安全的，如果不在允许列表中，则使用默认值
            if not sort_by or sort_by not in allowed_sort_columns: # This check will fail for new columns until allowed_sort_columns is updated.
                print(f"警告: 无效或未提供排序字段 '{sort_by}'，将默认按 total_holding_value 降序排序。")
                sort_by = 'total_holding_value' # 默认排序字段
                ascending = False # 默认排序方向
            
            order_direction = "ASC" if ascending else "DESC"
            query += f" ORDER BY {sort_by} {order_direction}"

            # 添加数量限制逻辑
            if limit and isinstance(limit, int) and limit > 0:
                query += f" LIMIT {limit}"
            
            print(f"执行查询: {query}")
            df = pd.read_sql_query(query, conn)
            
            if df.empty:
                print("未从 'etf_company_analytics' 获取到基金公司分析数据。")
                return []
            
            # 将DataFrame转换为字典列表
            results = df.to_dict(orient='records')
            print(f"成功获取 {len(results)} 条基金公司分析数据。")
            return results

        except sqlite3.Error as e:
            print(f"数据库操作时发生错误 (get_company_analytics_for_dashboard): {e}")
            return []
        except pd.io.sql.DatabaseError as e:
            print(f"Pandas SQL操作时发生错误 (get_company_analytics_for_dashboard): {e}")
            return []
        except Exception as e:
            print(f"获取基金公司分析数据时发生未知错误: {e}")
            return []
        # finally:
            # self.close() # 保持连接由调用者管理