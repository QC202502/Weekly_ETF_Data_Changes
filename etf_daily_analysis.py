#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ETF日度分析模块

根据最新交易日的涨幅数据，提取涨幅最高的ETF，并按照跟踪指数分组，
从每组中选取涨幅最大的一只ETF，最后取前20个展示在推荐模块中。
同时整合客户关注数据和持仓数据，提供完整的日度分析视图。

使用方法：
python etf_daily_analysis.py
"""

import pandas as pd
import os
import sys
import json
import glob
from datetime import datetime, timedelta
import traceback

def load_etf_price_data():
    """
    加载ETF价格数据
    
    返回:
        pandas.DataFrame: 包含ETF价格数据的DataFrame
    """
    try:
        # 查找最新的ETF_DATA文件
        etf_data_files = glob.glob('/Users/admin/Downloads/ETF_DATA_*.xlsx')
        if not etf_data_files:
            print("错误: 未找到ETF_DATA文件")
            return pd.DataFrame()
        
        # 获取最新的文件
        latest_file = max(etf_data_files, key=os.path.getctime)
        print(f"使用最新的ETF数据文件: {latest_file}")
        
        # 读取Excel文件
        df = pd.read_excel(latest_file, sheet_name='万得', engine='openpyxl')
        print(f"成功读取ETF价格数据，共{len(df)}条记录")
        
        # 提取文件日期
        file_date = os.path.basename(latest_file).replace('ETF_DATA_', '').replace('.xlsx', '')
        try:
            file_date = datetime.strptime(file_date, "%Y%m%d").strftime("%Y-%m-%d")
        except:
            file_date = datetime.now().strftime("%Y-%m-%d")
        
        # 添加交易日期列
        df['交易日期'] = file_date
        
        return df
    except Exception as e:
        print(f"读取ETF价格数据失败: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame()

def load_customer_attention_data():
    """
    加载客户ETF自选人数数据
    
    返回:
        tuple: (当天数据DataFrame, 前一天数据DataFrame, 当天日期字符串)
    """
    try:
        # 查找客户ETF自选人数文件
        attention_files = glob.glob('/Users/admin/Downloads/客户ETF自选人数*.xlsx')
        if not attention_files:
            print("错误: 未找到客户ETF自选人数文件")
            return pd.DataFrame(), pd.DataFrame(), ""
        
        # 按创建时间排序
        sorted_files = sorted(attention_files, key=os.path.getctime, reverse=True)
        
        if len(sorted_files) < 2:
            print("警告: 只找到一个客户ETF自选人数文件，无法计算日度变化")
            latest_file = sorted_files[0]
            latest_df = pd.read_excel(latest_file, engine='openpyxl')
            return latest_df, pd.DataFrame(), extract_date_from_attention_file(latest_df)
        
        # 获取最新的两个文件
        latest_file = sorted_files[0]
        previous_file = sorted_files[1]
        
        print(f"使用最新的客户ETF自选人数文件: {latest_file}")
        print(f"使用前一天的客户ETF自选人数文件: {previous_file}")
        
        # 读取Excel文件
        latest_df = pd.read_excel(latest_file, engine='openpyxl')
        previous_df = pd.read_excel(previous_file, engine='openpyxl')
        
        # 提取日期
        latest_date = extract_date_from_attention_file(latest_df)
        
        return latest_df, previous_df, latest_date
    except Exception as e:
        print(f"读取客户ETF自选人数数据失败: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame(), pd.DataFrame(), ""

def extract_date_from_attention_file(df):
    """
    从客户ETF自选人数文件中提取日期
    
    参数:
        df: 客户ETF自选人数DataFrame
        
    返回:
        str: 日期字符串 (YYYY-MM-DD)
    """
    try:
        # 尝试从第一行第一列获取日期信息
        date_cell = df.iloc[0, 0]
        if isinstance(date_cell, str) and '数据截止日期' in date_cell:
            date_str = date_cell.replace('数据截止日期：', '').strip()
            # 尝试解析日期
            try:
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                elif '-' in date_str:
                    return date_str
                elif len(date_str) == 8:  # 格式如20250320
                    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except:
                pass
    except:
        pass
    
    # 如果无法提取，返回当前日期
    return datetime.now().strftime("%Y-%m-%d")

def load_customer_holding_data():
    """
    加载客户ETF保有量数据
    
    返回:
        tuple: (当天数据DataFrame, 前一天数据DataFrame, 当天日期字符串)
    """
    try:
        # 查找客户ETF保有量文件
        holding_files = glob.glob('/Users/admin/Downloads/客户ETF保有量*.xlsx')
        if not holding_files:
            print("错误: 未找到客户ETF保有量文件")
            return pd.DataFrame(), pd.DataFrame(), ""
        
        # 按创建时间排序
        sorted_files = sorted(holding_files, key=os.path.getctime, reverse=True)
        
        if len(sorted_files) < 2:
            print("警告: 只找到一个客户ETF保有量文件，无法计算日度变化")
            latest_file = sorted_files[0]
            latest_df = pd.read_excel(latest_file, engine='openpyxl')
            return latest_df, pd.DataFrame(), extract_date_from_holding_file(latest_df)
        
        # 获取最新的两个文件
        latest_file = sorted_files[0]
        previous_file = sorted_files[1]
        
        print(f"使用最新的客户ETF保有量文件: {latest_file}")
        print(f"使用前一天的客户ETF保有量文件: {previous_file}")
        
        # 读取Excel文件
        latest_df = pd.read_excel(latest_file, engine='openpyxl')
        previous_df = pd.read_excel(previous_file, engine='openpyxl')
        
        # 提取日期
        latest_date = extract_date_from_holding_file(latest_df)
        
        return latest_df, previous_df, latest_date
    except Exception as e:
        print(f"读取客户ETF保有量数据失败: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame(), pd.DataFrame(), ""

def extract_date_from_holding_file(df):
    """
    从客户ETF保有量文件中提取日期
    
    参数:
        df: 客户ETF保有量DataFrame
        
    返回:
        str: 日期字符串 (YYYY-MM-DD)
    """
    try:
        # 尝试从第一行第一列获取日期信息
        date_cell = df.iloc[0, 0]
        if isinstance(date_cell, str) and '数据截止日期' in date_cell:
            date_str = date_cell.replace('数据截止日期：', '').strip()
            # 尝试解析日期
            try:
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                elif '-' in date_str:
                    return date_str
                elif len(date_str) == 8:  # 格式如20250320
                    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except:
                pass
    except:
        pass
    
    # 如果无法提取，返回当前日期
    return datetime.now().strftime("%Y-%m-%d")

def get_top_etfs_by_return(df, top_n=20):
    """
    获取涨幅最高的ETF，按照跟踪指数分组，每组取涨幅最大的一只
    
    参数:
        df: 包含ETF价格数据的DataFrame
        top_n: 返回的ETF数量
        
    返回:
        pandas.DataFrame: 包含涨幅最高的ETF数据
    """
    try:
        # 确保必要的列存在
        # 处理可能包含换行符的列名
        required_columns = ['证券代码', '证券简称', '交易日期']
        # 查找涨跌幅列（可能包含换行符）
        return_column = None
        for col in df.columns:
            if '涨跌幅' in col and '%' in col:
                return_column = col
                break
        
        if return_column is None:
            print("警告：未找到涨跌幅列")
            return pd.DataFrame()
            
        # 检查其他必要列
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"警告：缺少以下列：{missing_columns}")
            return pd.DataFrame()
        
        # 重命名列以便处理
        df_copy = df.copy()
        
        # 查找涨跌幅列（可能包含换行符）
        return_column = None
        for col in df.columns:
            if '涨跌幅' in col and '%' in col:
                return_column = col
                break
        
        # 创建重命名字典
        rename_dict = {
            '证券简称': '场内简称',
            '证券代码': '代码'
        }
        
        # 如果找到涨跌幅列，添加到重命名字典中
        if return_column:
            rename_dict[return_column] = '当日涨跌幅(%)'
        
        # 应用重命名
        df_copy.rename(columns=rename_dict, inplace=True)
        
        # 处理ETF代码格式，移除可能存在的交易所后缀（如.SH或.SZ）
        df_copy['代码'] = df_copy['代码'].astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
        print("已处理ETF代码格式，移除交易所后缀")
        
        # 确保跟踪指数代码格式正确
        if '跟踪指数代码' in df_copy.columns:
            df_copy['跟踪指数代码'] = df_copy['跟踪指数代码'].astype(str).apply(
                lambda x: x.split('.')[0] if '.' in x else x
            )
        
        # 按跟踪指数分组，每组取涨幅最大的一只ETF
        top_etfs_by_index = df_copy.sort_values('当日涨跌幅(%)', ascending=False).groupby('跟踪指数代码').first().reset_index()
        
        # 按涨幅排序，取前N个
        top_etfs = top_etfs_by_index.sort_values('当日涨跌幅(%)', ascending=False).head(top_n)
        
        print(f"成功获取{len(top_etfs)}只涨幅最高的ETF")
        return top_etfs
    except Exception as e:
        print(f"获取涨幅最高的ETF失败: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame()

def merge_data(top_etfs, etf_data, attention_latest, attention_previous, holding_latest, holding_previous, business_etfs=None):
    """
    合并所有数据源
    
    参数:
        top_etfs: 涨幅最高的ETF DataFrame
        etf_data: ETF基础数据 DataFrame
        attention_latest: 最新客户ETF自选人数 DataFrame
        attention_previous: 前一天客户ETF自选人数 DataFrame
        holding_latest: 最新客户ETF保有量 DataFrame
        holding_previous: 前一天客户ETF保有量 DataFrame
        business_etfs: 商务品ETF代码集合
        
    返回:
        pandas.DataFrame: 合并后的数据
    """
    try:
        # 创建结果DataFrame
        result_df = top_etfs.copy()
        
        # 添加ETF基础数据
        if not etf_data.empty:
            # 确保代码列格式一致
            etf_data['代码'] = etf_data['证券代码'].astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
            
            # 要合并的列
            columns_to_merge = [
                '基金管理人简称',
                '管理费率[单位] %',
                '基金规模(合计)[交易日期] S_cal_date(now(),0,D,0)[单位] 亿元',
                '区间日均成交额[起始交易日期] S_cal_date(enddate,-1,M,0)[截止交易日期] 最新收盘日[单位] 亿元'
            ]
            
            # 检查列是否存在
            existing_columns = [col for col in columns_to_merge if col in etf_data.columns]
            
            # 合并数据
            if existing_columns:
                etf_data_subset = etf_data[['代码'] + existing_columns].copy()
                result_df = pd.merge(result_df, etf_data_subset, on='代码', how='left')
        
        # 添加客户ETF自选人数数据
        if not attention_latest.empty:
            # 处理最新数据
            attention_latest_clean = process_attention_data(attention_latest)
            if not attention_latest_clean.empty:
                result_df = pd.merge(result_df, attention_latest_clean[['标的代码', '加自选人数']], 
                                    left_on='代码', right_on='标的代码', how='left')
                result_df.rename(columns={'加自选人数': '关注人数'}, inplace=True)
                result_df.drop('标的代码', axis=1, errors='ignore', inplace=True)
            
            # 处理前一天数据并计算变动
            if not attention_previous.empty:
                attention_previous_clean = process_attention_data(attention_previous)
                if not attention_previous_clean.empty:
                    result_df = pd.merge(result_df, attention_previous_clean[['标的代码', '加自选人数']], 
                                        left_on='代码', right_on='标的代码', how='left')
                    result_df.rename(columns={'加自选人数': '前日关注人数'}, inplace=True)
                    result_df.drop('标的代码', axis=1, errors='ignore', inplace=True)
                    
                    # 计算日度变动
                    result_df['当日新增关注'] = result_df['关注人数'].fillna(0) - result_df['前日关注人数'].fillna(0)
        
        # 添加客户ETF保有量数据
        if not holding_latest.empty:
            # 处理最新数据
            holding_latest_clean = process_holding_data(holding_latest)
            if not holding_latest_clean.empty:
                result_df = pd.merge(result_df, holding_latest_clean[['标的代码', '持仓客户数', '持仓市值']], 
                                    left_on='代码', right_on='标的代码', how='left')
                result_df.rename(columns={'持仓市值': '保有规模(元)'}, inplace=True)
                result_df.drop('标的代码', axis=1, errors='ignore', inplace=True)
                
                # 转换保有规模为亿元
                result_df['保有规模(亿元)'] = result_df['保有规模(元)'].fillna(0) / 1e8
                result_df.drop('保有规模(元)', axis=1, errors='ignore', inplace=True)
            
            # 处理前一天数据并计算变动
            if not holding_previous.empty:
                holding_previous_clean = process_holding_data(holding_previous)
                if not holding_previous_clean.empty:
                    result_df = pd.merge(result_df, holding_previous_clean[['标的代码', '持仓客户数', '持仓市值']], 
                                        left_on='代码', right_on='标的代码', how='left')
                    result_df.rename(columns={
                        '持仓客户数': '前日持仓客户数',
                        '持仓市值': '前日保有规模(元)'
                    }, inplace=True)
                    result_df.drop('标的代码', axis=1, errors='ignore', inplace=True)
                    
                    # 计算日度变动
                    result_df['当日新增持仓'] = result_df['持仓客户数'].fillna(0) - result_df['前日持仓客户数'].fillna(0)
                    
                    # 计算保有规模变动（亿元）
                    result_df['当日新增保有(亿元)'] = (result_df['保有规模(亿元)'].fillna(0) - 
                                            result_df['前日保有规模(元)'].fillna(0) / 1e8)
        
        # 添加商务品标记
        if business_etfs is not None:
            result_df['是否商务品'] = result_df['代码'].apply(lambda x: '商务' if x in business_etfs else '非商务')
        else:
            result_df['是否商务品'] = '非商务'
        
        # 重命名和整理列
        column_mapping = {
            '基金管理人简称': '管理人简称',
            '管理费率[单位] %': '管理费率(%)',
            '基金规模(合计)[交易日期] S_cal_date(now(),0,D,0)[单位] 亿元': '规模(亿元)',
            '区间日均成交额[起始交易日期] S_cal_date(enddate,-1,M,0)[截止交易日期] 最新收盘日[单位] 亿元': '月日均交易量(亿元)'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in result_df.columns:
                result_df.rename(columns={old_col: new_col}, inplace=True)
        
        # 填充缺失值
        numeric_columns = [
            '管理费率(%)', '规模(亿元)', '月日均交易量(亿元)',
            '关注人数', '当日新增关注', '持仓客户数', '当日新增持仓',
            '保有规模(亿元)', '当日新增保有(亿元)'
        ]
        
        for col in numeric_columns:
            if col in result_df.columns:
                result_df[col] = result_df[col].fillna(0)
        
        return result_df
    
    except Exception as e:
        print(f"合并数据失败: {str(e)}")
        traceback.print_exc()
        return top_etfs

def process_attention_data(df):
    """
    处理客户ETF自选人数数据
    
    参数:
        df: 客户ETF自选人数DataFrame
        
    返回:
        pandas.DataFrame: 处理后的数据
    """
    try:
        # 跳过标题行，找到真正的数据开始行
        start_row = 0
        for i, row in df.iterrows():
            if '标的代码' in str(row.iloc[0]) or '标的代码' in df.columns:
                start_row = i
                break
        
        # 提取数据部分
        if start_row > 0:
            data_df = df.iloc[start_row+1:].copy()
            data_df.columns = df.iloc[start_row].values
        else:
            data_df = df.copy()
        
        # 确保必要的列存在
        if '标的代码' not in data_df.columns or '加自选人数' not in data_df.columns:
            print("警告: 客户ETF自选人数数据缺少必要的列")
            return pd.DataFrame()
        
        # 清理数据
        data_df['标的代码'] = data_df['标的代码'].astype(str).str.strip()
        data_df['加自选人数'] = pd.to_numeric(data_df['加自选人数'], errors='coerce').fillna(0)
        
        return data_df
    except Exception as e:
        print(f"处理客户ETF自选人数数据失败: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame()

def process_holding_data(df):
    """
    处理客户ETF保有量数据
    
    参数:
        df: 客户ETF保有量DataFrame
        
    返回:
        pandas.DataFrame: 处理后的数据
    """
    try:
        # 跳过标题行，找到真正的数据开始行
        start_row = 0
        for i, row in df.iterrows():
            if '标的代码' in str(row.iloc[0]) or '标的代码' in df.columns:
                start_row = i
                break
        
        # 提取数据部分
        if start_row > 0:
            data_df = df.iloc[start_row+1:].copy()
            data_df.columns = df.iloc[start_row].values
        else:
            data_df = df.copy()
        
        # 确保必要的列存在
        required_columns = ['标的代码', '持仓客户数', '持仓市值']
        missing_columns = [col for col in required_columns if col not in data_df.columns]
        if missing_columns:
            print(f"警告: 客户ETF保有量数据缺少以下列：{missing_columns}")
            return pd.DataFrame()
        
        # 清理数据
        data_df['标的代码'] = data_df['标的代码'].astype(str).str.strip()
        data_df['持仓客户数'] = pd.to_numeric(data_df['持仓客户数'], errors='coerce').fillna(0)
        data_df['持仓市值'] = pd.to_numeric(data_df['持仓市值'], errors='coerce').fillna(0)
        
        return data_df
    except Exception as e:
        print(f"处理客户ETF保有量数据失败: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame()

def format_recommendations(merged_data, trade_date):
    """
    格式化推荐数据，用于前端展示
    
    参数:
        merged_data: 合并后的数据DataFrame
        trade_date: 交易日期
        
    返回:
        dict: 包含推荐数据的字典
    """
    recommendations = {
        "price_return": [],  # 按涨幅排序的ETF
        "trade_date": ""    # 交易日期
    }
    
    try:
        # 格式化日期为"M月D日"格式
        try:
            if isinstance(trade_date, str):
                # 尝试解析日期字符串
                if '-' in trade_date:
                    # 格式如 "2025-03-19"
                    year, month, day = trade_date.split('-')
                    recommendations["trade_date"] = f"{int(month)}月{int(day)}日"
                elif '/' in trade_date:
                    # 格式如 "2025/03/19"
                    year, month, day = trade_date.split('/')
                    recommendations["trade_date"] = f"{int(month)}月{int(day)}日"
                else:
                    # 格式如 "20250319"
                    if len(trade_date) == 8:
                        month = trade_date[4:6]
                        day = trade_date[6:8]
                        recommendations["trade_date"] = f"{int(month)}月{int(day)}日"
        except Exception as date_e:
            print(f"格式化交易日期出错: {str(date_e)}")
            # 使用当前日期
            now = datetime.now()
            recommendations["trade_date"] = f"{now.month}月{now.day}日"
        
        # 遍历合并数据，格式化为推荐列表
        for _, row in merged_data.iterrows():
            try:
                # 确保ETF代码格式正确，添加sh/sz前缀
                etf_code = str(row['代码']).strip()
                
                # 添加交易所前缀（如果没有）
                if not (etf_code.startswith('sh') or etf_code.startswith('sz')):
                    # 根据代码规则添加前缀：5开头或6开头的是上交所，其他是深交所
                    if etf_code.startswith('5') or etf_code.startswith('6'):
                        etf_code = 'sh' + etf_code
                    else:
                        etf_code = 'sz' + etf_code
                
                # 获取基本信息
                etf_name = row['场内简称'] if '场内简称' in row else row.get('证券简称', f"ETF{etf_code}")
                daily_return = row['当日涨跌幅(%)'] if '当日涨跌幅(%)' in row else 0
                
                # 获取管理人信息
                manager = row.get('管理人简称', '未知')
                
                # 获取规模信息
                scale = row.get('规模(亿元)', 0)
                
                # 获取指数信息
                index_code = row.get('跟踪指数代码', '')
                index_name = row.get('跟踪指数名称', '')
                
                # 获取是否为商务品
                is_business = row.get('是否商务品', '非商务') == '商务'
                
                # 获取客户数据
                attention = row.get('关注人数', 0)
                attention_change = row.get('当日新增关注', 0)
                holders = row.get('持仓客户数', 0)
                holders_change = row.get('当日新增持仓', 0)
                amount = row.get('保有规模(亿元)', 0)
                amount_change = row.get('当日新增保有(亿元)', 0)
                
                # 获取交易量和费率
                volume = row.get('月日均交易量(亿元)', 0)
                fee_rate = row.get('管理费率(%)', 0)
                
                # 添加到推荐列表
                recommendations["price_return"].append({
                    'code': etf_code,
                    'name': etf_name,
                    'manager': manager,
                    'is_business': is_business,
                    'business_text': "商务品" if is_business else "非商务品",
                    'index_code': index_code,
                    'index_name': index_name,
                    'scale': round(float(scale), 2) if pd.notna(scale) else 0,
                    'daily_return': round(float(daily_return), 2) if pd.notna(daily_return) else 0,
                    'attention': int(attention) if pd.notna(attention) else 0,
                    'attention_change': int(attention_change) if pd.notna(attention_change) else 0,
                    'holders': int(holders) if pd.notna(holders) else 0,
                    'holders_change': int(holders_change) if pd.notna(holders_change) else 0,
                    'amount': round(float(amount), 2) if pd.notna(amount) else 0,
                    'amount_change': round(float(amount_change), 2) if pd.notna(amount_change) else 0,
                    'volume': round(float(volume), 2) if pd.notna(volume) else 0,
                    'fee_rate': round(float(fee_rate), 4) if pd.notna(fee_rate) else 0
                })
            except Exception as row_e:
                print(f"处理ETF记录时出错: {str(row_e)}")
                continue
        
        print(f"成功格式化{len(recommendations['price_return'])}条ETF推荐数据")
    except Exception as e:
        print(f"格式化推荐数据出错: {str(e)}")
        traceback.print_exc()
    
    return recommendations

def save_recommendations(recommendations, output_file=None):
    """
    保存推荐数据到JSON文件
    
    参数:
        recommendations: 包含推荐数据的字典
        output_file: 输出文件路径，如果为None，则使用默认路径
        
    返回:
        str: 保存的文件路径
    """
    if not output_file:
        # 创建数据目录
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 使用当前日期生成文件名
        today = datetime.now().strftime('%Y%m%d')
        output_file = os.path.join(data_dir, f"etf_price_recommendations_{today}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, ensure_ascii=False, indent=2)
    
    print(f"推荐数据已保存至: {output_file}")
    return output_file

def load_business_etfs():
    """
    加载商务品ETF代码集合
    
    返回:
        set: 商务品ETF代码集合
    """
    try:
        # 查找商务协议文件
        date_str = datetime.now().strftime('%Y%m%d')
        商务协议_paths = [
            f'/Users/admin/Downloads/ETF单产品商务协议{date_str}.xlsx',
            f'./ETF单产品商务协议{date_str}.xlsx',
            f'./data/ETF单产品商务协议{date_str}.xlsx',
            f'/Users/admin/PycharmProjects/Weekly_ETF_Data_Changes/ETF单产品商务协议{date_str}.xlsx'
        ]
        
        # 尝试查找其他日期的文件
        if not any(os.path.exists(path) for path in 商务协议_paths):
            # 查找任何日期的商务协议文件
            商务协议_files = glob.glob('/Users/admin/Downloads/ETF单产品商务协议*.xlsx')
            if 商务协议_files:
                商务协议_paths.append(max(商务协议_files, key=os.path.getctime))
        
        商务协议_loaded = False
        business_etfs = set()
        
        for 商务协议_path in 商务协议_paths:
            try:
                if os.path.exists(商务协议_path):
                    print(f"读取商务协议文件: {商务协议_path}")
                    # 使用openpyxl引擎读取Excel文件
                    商务协议 = pd.read_excel(商务协议_path, engine='openpyxl')
                    商务协议_loaded = True
                    print(f"成功读取商务协议文件，共 {len(商务协议)} 行")
                    
                    # 确保证券代码为字符串
                    商务协议['证券代码'] = 商务协议['证券代码'].astype(str).str.strip()
                    
                    # 获取商务品代码集合
                    business_etfs = set(商务协议['证券代码'].tolist())
                    print(f"获取到 {len(business_etfs)} 个商务品ETF代码")
                    break
            except Exception as e:
                print(f"读取商务协议文件失败: {e}")
                continue
        
        if not 商务协议_loaded:
            print("未找到商务协议文件，无法获取商务品ETF代码")
        
        return business_etfs
    
    except Exception as e:
        print(f"加载商务品ETF代码失败: {str(e)}")
        traceback.print_exc()
        return set()

def main():
    """
    主函数
    """
    try:
        print("开始ETF日度分析...")
        
        # 加载ETF价格数据
        etf_data = load_etf_price_data()
        if etf_data.empty:
            print("错误: 无法加载ETF价格数据")
            return 1
        
        # 加载客户ETF自选人数数据
        attention_latest, attention_previous, attention_date = load_customer_attention_data()
        
        # 加载客户ETF保有量数据
        holding_latest, holding_previous, holding_date = load_customer_holding_data()
        
        # 加载商务品ETF代码
        business_etfs = load_business_etfs()
        
        # 获取涨幅最高的ETF
        top_etfs = get_top_etfs_by_return(etf_data)
        if top_etfs.empty:
            print("错误: 无法获取涨幅最高的ETF")
            return 1
        
        # 合并数据
        merged_data = merge_data(
            top_etfs, 
            etf_data, 
            attention_latest, 
            attention_previous, 
            holding_latest, 
            holding_previous, 
            business_etfs
        )
        
        # 获取交易日期
        trade_date = ""
        if '交易日期' in top_etfs.columns and not top_etfs.empty:
            trade_date = top_etfs['交易日期'].iloc[0]
        
        # 格式化推荐数据
        recommendations = format_recommendations(merged_data, trade_date)
        
        # 保存推荐数据
        save_recommendations(recommendations)
        
        # 打印推荐数据预览
        print("\n推荐数据预览:")
        for i, item in enumerate(recommendations["price_return"][:5]):
            print(f"{i+1}. {item['name']} ({item['code']}): 涨幅 {item['daily_return']}%, 关注人数: {item['attention']}, 当日新增关注: {item['attention_change']}")
        
        print(f"\n日度分析完成，交易日期: {recommendations['trade_date']}")
        return 0
    
    except Exception as e:
        print(f"错误: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())