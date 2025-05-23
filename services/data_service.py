import pandas as pd
import os
from datetime import datetime, timedelta
import traceback
from database.models import Database
import numpy as np

# 全局变量
etf_data = None
business_etfs = set()
current_date_str = ""
previous_date_str = ""
date_range = ""

def get_manager_short(full_name):
    """基金管理人简称提取"""
    if pd.isna(full_name):
        return "未知"
    
    # 移除常见后缀
    short_name = full_name.replace("基金管理有限公司", "")
    short_name = short_name.replace("基金管理股份有限公司", "")
    short_name = short_name.replace("基金管理有限责任公司", "")
    short_name = short_name.replace("基金管理公司", "")
    short_name = short_name.replace("基金", "")
    short_name = short_name.replace("股份有限公司", "")
    short_name = short_name.replace("有限公司", "")
    short_name = short_name.replace("有限责任公司", "")
    
    return short_name

def load_latest_data():
    """加载最新ETF数据"""
    try:
        print("开始从数据库加载ETF数据...")
        db = Database()
        
        etf_data_from_db = db.get_all_etf_info()
        if not etf_data_from_db:
            return {'status': 'error', 'message': '加载ETF数据失败'}
            
        business_etfs_set = db.get_all_business_etf()
        if business_etfs_set is None:
            business_etfs_set = set()
            print("警告: 加载商务品数据失败，将使用空列表。")

        etf_df = pd.DataFrame(etf_data_from_db)
        
        if etf_df.empty:
            print("警告: 从数据库获取的ETF数据为空DataFrame。")

        # 清理NaN值：遍历所有列，如果是数值类型，则用0填充NaN
        for col in etf_df.columns:
            if pd.api.types.is_numeric_dtype(etf_df[col]):
                etf_df[col].fillna(0, inplace=True)

        # 添加是否商务品标记 (确保 business_etfs_set 是最新的)
        etf_df['is_business'] = etf_df['code'].apply(lambda x: '商务' if x in business_etfs_set else '非商务')
        
        print(f"成功从数据库加载ETF数据，共 {len(etf_df)} 条记录")
        print(f"成功从数据库加载商务品数据，共 {len(business_etfs_set)} 个商务品")
        
        return {
            'status': 'success',
            'message': {
                'etf_data': etf_df.to_dict('records'),
                'business_etfs': list(business_etfs_set)
            }
        }
    except Exception as e:
        print(f"加载数据时出错: {str(e)}")
        traceback.print_exc()
        return {'status': 'error', 'message': f'加载数据时出错: {str(e)}'}

def format_etf_result(row):
    """格式化ETF搜索结果"""
    try:
        # 尝试获取证券名称
        name = row.get('name', '未知')
        
        # 尝试获取管理人
        manager = row.get('fund_manager', '未知')
        
        # 尝试获取规模
        scale = float(row.get('fund_size', 0))
        
        # 尝试获取管理费率
        fee_rate = float(row.get('management_fee_rate', 0))
        
        # 获取指数代码和名称
        index_code = row.get('tracking_index_code', '')
        index_name = row.get('tracking_index_name', '')
        
        # 构建结果字典
        result = {
            'code': row.get('code', '未知'),
            'name': name,
            'is_business': row.get('code') in business_etfs,
            'manager': manager,
            'scale': scale,
            'index_code': index_code,
            'index_name': index_name,
            'fee_rate': fee_rate,
            'tracking_error': float(row.get('tracking_error', 0)),
            'information_ratio': float(row.get('information_ratio', 0)),
            'total_holder_count': int(row.get('total_holder_count', 0))
        }
        return result
    except Exception as e:
        print(f"格式化ETF结果出错: {str(e)}")
        # 返回一个基本的结果，避免整个搜索失败
        return {
            'code': row.get('code', '未知'),
            'name': '格式化错误',
            'is_business': False,
            'manager': '未知',
            'scale': 0,
            'index_code': '',
            'index_name': '',
            'fee_rate': 0,
            'tracking_error': 0,
            'information_ratio': 0,
            'total_holder_count': 0
        }