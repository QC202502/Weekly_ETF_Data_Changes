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

class Database:
    """
    数据库操作类
    """
    def __init__(self):
        """初始化数据库连接"""
        self.db_file = 'data/etf_data.db'
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        self.conn = None
        
        # 检查数据库文件是否存在
        if not os.path.exists(self.db_file):
            print(f"警告：数据库文件 {self.db_file} 不存在")
            print("请确保已经导入了ETF数据")
            return
        
        # 检查表是否存在
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='etf_info'")
            if not cursor.fetchone():
                print("警告：数据库表不存在")
                print("请确保已经导入了ETF数据")
        finally:
            cursor.close()
    
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
            return result
        except Exception as e:
            print(f"执行SQL查询失败: {str(e)}")
            return []
        finally:
            cursor.close()
    
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
                    holder_household_count INTEGER,
                    update_time TIMESTAMP,
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
            
            conn.commit()
            print("数据库表创建成功")
            return True
            
        except Exception as e:
            print(f"创建数据库表失败: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
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
            print("开始处理ETF基本信息数据...")
            
            # 显示原始列名和前几行数据
            print("原始列名：", df.columns.tolist())
            print("\n原始数据前5行：")
            print(df.head())
            
            # 定义列名映射
            column_mapping = {
                '证券代码': 'code',
                '证券简称': 'name',
                '基金管理人': 'fund_manager',
                '基金规模(合计)\n[交易日期] S_cal_date(now(),0,D,0)\n[单位] 亿元': 'fund_size',
                '基金上市地点': 'exchange',
                '跟踪指数代码': 'tracking_index_code',
                '跟踪指数名称': 'tracking_index_name',
                '年化跟踪误差阈值(业绩基准)\n[单位] %': 'tracking_error',
                '信息比率(年化)\n[起始交易日期] S_cal_date(enddate,-52,W,0)\n[截止交易日期] 最新收盘日\n[计算周期] 日\n[收益率计算方法] 普通收益率\n[无风险收益率] 一年定存利率（税前）\n[标的指数] 上证综合指数': 'information_ratio',
                '基金份额持有人户数\n[报告期] 20240630\n[单位] 户': 'total_holder_count',
                '管理费率\n[单位] %': 'management_fee_rate',
                '托管费率\n[单位] %': 'custody_fee_rate',
                '指数使用费率': 'index_usage_fee'
            }
            
            # 重命名列
            df = df.rename(columns=column_mapping)
            print("\n重命名后的列名：", df.columns.tolist())
            
            # 选择需要的列
            required_columns = ['code', 'name', 'fund_manager', 'fund_size', 'exchange', 
                              'tracking_index_code', 'tracking_index_name', 'tracking_error',
                              'information_ratio', 'total_holder_count', 'management_fee_rate',
                              'custody_fee_rate', 'index_usage_fee']
            
            # 确保所有必需的列都存在
            for col in required_columns:
                if col not in df.columns:
                    print(f"警告：缺少列 {col}，将使用空值填充")
                    df[col] = None
            
            # 选择并重排列顺序
            df = df[required_columns]
            
            # 处理规模数据
            def process_fund_size(value):
                if pd.isna(value):
                    return 0.0
                if isinstance(value, str):
                    # 移除可能的单位和其他字符
                    value = value.replace('亿元', '').replace('亿', '').strip()
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        print(f"警告：无法转换规模值 '{value}' 为数字")
                        return 0.0
                try:
                    return float(value)
                except (ValueError, TypeError):
                    print(f"警告：无法转换规模值 '{value}' 为数字")
                    return 0.0
            
            # 处理规模数据
            print("\n处理基金规模数据...")
            print("基金规模列的数据类型：", df['fund_size'].dtype)
            print("基金规模的唯一值：", df['fund_size'].unique())
            
            df['fund_size'] = df['fund_size'].apply(process_fund_size)
            
            # 检查处理后的规模数据
            print("\n处理后的基金规模统计：")
            print(df['fund_size'].describe())
            
            # 处理费率字段
            def process_fee_rate(value):
                if pd.isna(value):
                    return 0.0
                if isinstance(value, str):
                    # 移除"费率"前缀和"%"后缀
                    value = value.replace('费率', '').replace('%', '').strip()
                try:
                    return float(value)
                except (ValueError, TypeError):
                    print(f"警告：无法转换费率值 '{value}' 为数字")
                    return 0.0
            
            # 处理所有费率字段
            fee_columns = ['management_fee_rate', 'custody_fee_rate', 'index_usage_fee']
            for col in fee_columns:
                df[col] = df[col].apply(process_fee_rate)
            
            # 添加total_annual_fee_rate列
            df['total_annual_fee_rate'] = df[['management_fee_rate', 'custody_fee_rate', 'index_usage_fee']].sum(axis=1)
            
            # 显示数据示例
            print("\n最终数据示例：")
            print(df[['code', 'name', 'fund_size']].head())
            print("\n数据形状：", df.shape)
            
            # 删除现有表并重新创建
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS etf_info")
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
                    update_time TIMESTAMP
                )
            """)
            
            # 保存到数据库
            df.to_sql('etf_info', conn, if_exists='append', index=False)
            conn.commit()
            
            print(f"\n成功保存ETF基本信息，共{len(df)}条记录")
            return True
            
        except Exception as e:
            print(f"保存ETF基本信息失败: {str(e)}")
            if self.conn:
                self.conn.rollback()
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
            
            # 选择需要的列
            df = df[required_columns]
            
            # 添加更新时间
            df['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存到数据库
            conn = self.connect()
            df.to_sql('etf_attention', conn, if_exists='replace', index=False)
            conn.commit()
            
            print(f"成功保存ETF自选数据，共{len(df)}条记录")
            return True
            
        except Exception as e:
            print(f"保存ETF自选数据失败: {str(e)}")
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
            
            # 检查是否存在任何可用的列
            expected_cols = ['标的代码', '证券代码', '持有人数', '持仓户数', '持仓客户数']
            found_cols = [col for col in expected_cols if col in df.columns]
            
            if not found_cols:
                print(f"ETF持有人数据缺少必需的列，预期列：{expected_cols}，实际列：{df.columns.tolist()}")
                return False
            
            # 尝试从ETF基本信息表获取代码
            if 'code' not in df.columns and '标的代码' not in df.columns and '证券代码' not in df.columns:
                print("从ETF基本信息表获取代码...")
                
                try:
                    codes_query = "SELECT code FROM etf_info"
                    codes_result = self.execute_query(codes_query)
                    codes = [row[0] for row in codes_result]
                    
                    if codes:
                        # 创建临时DataFrame
                        holders_data = []
                        for code in codes:
                            holders_data.append({
                                'code': code,
                                'holder_count': 0,
                                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                        
                        df_new = pd.DataFrame(holders_data)
                        print(f"已创建默认持有人数据，共{len(df_new)}条记录")
                        
                        # 保存到数据库
                        conn = self.connect()
                        df_new.to_sql('etf_holders', conn, if_exists='replace', index=False)
                        conn.commit()
                        
                        print(f"成功保存ETF持有人数据，共{len(df_new)}条记录")
                        return True
                    else:
                        print("ETF基本信息表中没有代码数据")
                        return False
                    
                except Exception as e:
                    print(f"从ETF基本信息表获取代码时出错: {str(e)}")
                    return False
            
            # 重命名列
            column_mapping = {
                '数据截止日期': 'date',
                '标的代码': 'code',
                '证券代码': 'code',
                '持仓客户数': 'holder_count',
                '持仓户数': 'holder_count',
                '持有人数': 'holder_count',
                '家庭持仓户数': 'holder_household_count'
            }
            df = df.rename(columns={col: column_mapping[col] for col in df.columns if col in column_mapping})
            
            # 确保code列存在
            if 'code' not in df.columns:
                print("ETF持有人数据缺少必需字段: code")
                return False
            
            # 确保所需列存在
            required_columns = ['code', 'holder_count']
            if 'holder_count' not in df.columns and '持有人数' in df.columns:
                df = df.rename(columns={'持有人数': 'holder_count'})
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"ETF持有人数据缺少必需字段: {missing_columns}")
                # 如果缺少holder_count字段但有其他相关字段，可以创建一个默认值
                if 'holder_count' in missing_columns:
                    df['holder_count'] = 0
                    missing_columns.remove('holder_count')
                
                # 如果还有其他缺少的必需字段，则返回失败
                if missing_columns:
                    return False
            
            # 处理代码列
            df['code'] = df['code'].astype(str).str.strip()
            # 确保是6位数字代码
            df['code'] = df['code'].str.extract(r'(\d{6})').fillna('')
            # 移除空代码的行
            df = df[df['code'] != '']
            
            # 添加更新时间
            df['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存到数据库
            conn = self.connect()
            df.to_sql('etf_holders', conn, if_exists='replace', index=False)
            conn.commit()
            
            print(f"成功保存ETF持有人数据，共{len(df)}条记录")
            return True
            
        except Exception as e:
            print(f"保存ETF持有人数据失败: {str(e)}")
            if self.conn:
                self.conn.rollback()
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
            df.to_sql('etf_business', conn, if_exists='replace', index=False)
            conn.commit()
            
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
            
            # 构建查询，获取所有必要字段
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
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business
            FROM etf_info i
            LEFT JOIN etf_attention a ON i.code = a.code
            LEFT JOIN etf_business b ON i.code = b.code
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
                    'is_business': bool(row[15])
                }
                processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            print(f"搜索ETF代码时出错: {str(e)}")
            return []
    
    def search_by_index_name(self, index_name):
        """根据指数名称搜索ETF"""
        try:
            index_name = index_name.strip()
            print(f"搜索指数名称: {index_name}")
            
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
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business
            FROM etf_info i
            LEFT JOIN etf_attention a ON i.code = a.code
            LEFT JOIN etf_business b ON i.code = b.code
            WHERE i.tracking_index_name LIKE ? OR i.tracking_index_code LIKE ?
            ORDER BY i.fund_size DESC
            """
            
            pattern = f"%{index_name}%"
            results = self.execute_query(query, (pattern, pattern))
            
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
                    'is_business': bool(row[15])
                }
                processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            print(f"搜索指数名称时出错: {str(e)}")
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
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business
            FROM etf_info i
            LEFT JOIN etf_attention a ON i.code = a.code
            LEFT JOIN etf_business b ON i.code = b.code
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
                    'attention_count': int(row[14]) if row[14] is not None else 0,
                    'is_business': bool(row[15])
                }
                processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            print(f"搜索基金公司时出错: {str(e)}")
            return []
    
    def general_search(self, keyword):
        """通用搜索"""
        try:
            query = """
            SELECT i.*, p.amount as volume, b.code as business_code,
                   b.management_fee_rate, b.custody_fee_rate,
                   b.index_usage_fee, b.total_annual_fee_rate
            FROM etf_info i
            LEFT JOIN etf_price p ON i.code = p.code
            LEFT JOIN etf_business b ON i.code = b.code
            WHERE i.code LIKE ? 
               OR i.name LIKE ? 
               OR i.fund_manager LIKE ? 
               OR i.tracking_index_name LIKE ?
            ORDER BY i.fund_size DESC
            """
            pattern = f"%{keyword}%"
            result = self.execute_query(query, (pattern, pattern, pattern, pattern))
            
            if not result:
                return []
            
            return [{
                'code': str(row[0]),
                'name': str(row[1]),
                'manager': str(row[2]) if row[2] else '',
                'scale': float(row[3]) if row[3] and str(row[3]).replace('.','').isdigit() else 0.0,
                'exchange': str(row[4]) if row[4] else '',
                'tracking_index_code': str(row[5]) if row[5] else '',
                'tracking_index_name': str(row[6]) if row[6] else '',
                'tracking_error': float(row[7]) if row[7] and str(row[7]).replace('.','').isdigit() else 0.0,
                'information_ratio': float(row[8]) if row[8] and str(row[8]).replace('.','').isdigit() else 0.0,
                'holders_count': int(float(row[9])) if row[9] and str(row[9]).replace('.','').isdigit() else 0,
                'volume': float(row[10]) if row[10] and str(row[10]).replace('.','').isdigit() else 0.0,
                'is_business': bool(row[11]),
                'business_text': "商务品" if row[11] else "非商务品",
                'management_fee_rate': float(row[12]) if row[12] and str(row[12]).replace('.','').isdigit() else 0.0,
                'custody_fee_rate': float(row[13]) if row[13] and str(row[13]).replace('.','').isdigit() else 0.0,
                'index_usage_fee': float(row[14]) if row[14] and str(row[14]).replace('.','').isdigit() else 0.0,
                'total_annual_fee_rate': float(row[15]) if row[15] and str(row[15]).replace('.','').isdigit() else 0.0,
                'attention_count': 0,
                'attention_change': 0,
                'holders_change': 0,
                'amount': float(row[10]) if row[10] and str(row[10]).replace('.','').isdigit() else 0.0,
                'amount_change': 0.0
            } for row in result]
        except Exception as e:
            print(f"通用搜索时出错: {str(e)}")
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