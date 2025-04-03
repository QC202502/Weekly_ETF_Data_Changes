#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import json
import pandas as pd
from datetime import datetime
from database.models import Database
import re
from utils.etf_code import normalize_etf_code
import xlwings as xw

def extract_date_from_filename(filename):
    """从文件名中提取日期"""
    try:
        # 使用正则表达式匹配文件名中的日期
        match = re.search(r'(\d{8})', filename)
        if match:
            date_str = match.group(1)
            return datetime.strptime(date_str, '%Y%m%d').date()
        return None
    except Exception as e:
        print(f"从文件名提取日期时出错: {str(e)}")
        return None

def save_column_mapping():
    """保存列名映射"""
    column_mapping = {
        'etf_info': {
            '证券代码': 'code',
            '证券简称': 'name',
            '业绩比较基准': 'benchmark',
            '成立年限\n[单位] 年': 'years_since_establishment',
            '基金上市地点': 'listing_location',
            '基金成立日': 'establishment_date',
            '基金管理人': 'fund_manager',
            '管理费率\n[单位] %': 'management_fee_rate',
            '托管费率\n[单位] %': 'custodian_fee_rate',
            '指数使用费率': 'index_usage_fee_rate',
            '跟踪指数代码': 'tracking_index_code',
            '日均跟踪偏离度阈值(业绩基准)\n[单位] %': 'tracking_deviation_threshold',
            '年化跟踪误差阈值(业绩基准)\n[单位] %': 'tracking_error_threshold',
            '跟踪误差\n[起始交易日期] S_cal_date(enddate,-52,W,0)\n[ 截止交易日期] 最新收盘日\n[计算周期] 日\n[收益率计算方法] 普通收益率\n[标的指数] 上证综合指数\n[单位] %': 'tracking_error',
            ' 跟踪误差(跟踪指数)\n[起始交易日期] S_cal_date(enddate,-52,W,0)\n[截止交易日期] 最新收盘日\n[计算周期] 日\n[ 收益率计算方法] 普通收益率\n[单位] %': 'tracking_error_index',
            '信息比率(年化)\n[起始交易日期] S_cal_date(enddate,-52,W,0)\n[截止交 易日期] 最新收盘日\n[计算周期] 日\n[收益率计算方法] 普通收益率\n[无风险收益率] 一年定存利率（税前）\n[标的指数] 上证综合指数': 'information_ratio',
            '跟踪误差(年化)\n[起始交易日期] S_cal_date(enddate,-52,W,0)\n[截止交易日期] 最新收盘日\n[计算周期] 日\n[收益率计算方法] 普通收益率\n[标的指数] 上证综合指数\n[单位] %': 'tracking_error_annualized',
            '基金规模(合计)\n[交易日期] S_cal_date(now(),0,D,0)\n[单位] 亿元': 'fund_size',
            '基金份额持有人户数\n[报告期] 20240630\n[单位] 户': 'holder_count',
            '基金份额持有人户 数(合计)\n[报告期] 20240630\n[单位] 户': 'total_holder_count',
            '区间日均成交额\n[起始交易日期] S_cal_date(enddate,-1,M,0)\n[截止交易日期] 最新收盘日\n[单位] 亿元': 'avg_daily_volume',
            '基金管理人简称': 'fund_manager_abbr',
            '基金场内简称': 'fund_exchange_abbr',
            '跟踪指数名称': 'tracking_index_name',
            '月成交额\n[交易日期] 最新收盘日\n[单位] 百万元': 'monthly_volume',
            '涨跌幅\n[交易日期] 最新收盘日\n[单位] %': 'price_change_rate',
            '换手率\n[交易日期] 最新收盘日\n[单位] %': 'turnover_rate',
            '成交额\n[交易日期] 最新收盘日\n[单位] 亿元': 'daily_volume',
            '成交笔数\n[交易日期] 最新收盘日\n[单位] 笔': 'transaction_count',
            '总市值\n[交易日期] 最新收盘日\n[单位] 亿元': 'market_value'
        },
        'etf_price': {
            '证券代码': 'code',
            '涨跌幅\n[交易日期] 最新收盘日\n[单位] %': 'price_change_rate',
            '换手率\n[交易日期] 最新收盘日\n[单位] %': 'turnover_rate',
            '成交额\n[交易日期] 最新收盘日\n[单位] 亿元': 'daily_volume',
            '成交笔数\n[交易日期] 最新收盘日\n[单位] 笔': 'transaction_count',
            '总市值\n[交易日期] 最新收盘日\n[单位] 亿元': 'market_value'
        },
        'etf_attention': {
            '证券代码': 'code',
            '自选人数': 'attention_count'
        },
        'etf_holders': {
            '证券代码': 'code',
            '持有人数': 'holder_count',
            '持有份额': 'holding_amount',
            '持有市值': 'holding_value'
        }
    }
    
    # 确保data目录存在
    os.makedirs('data', exist_ok=True)
    
    # 保存列名映射到JSON文件
    with open('data/etf_column_names.json', 'w', encoding='utf-8') as f:
        json.dump(column_mapping, f, ensure_ascii=False, indent=4)
    
def import_etf_data():
    """导入ETF数据"""
    # 创建数据库连接
    db = Database()
    
    # 创建数据库表
    try:
        db.create_tables()
        print("数据库表创建成功")
    except Exception as e:
        print(f"创建数据库表失败: {str(e)}")
        return
    
    # 导入ETF市场数据
    try:
        print("开始导入ETF市场数据...")
        df = pd.read_excel('data/ETF_DATA_20250328.xlsx', engine='openpyxl')
        if db.save_etf_info(df):
            print("ETF市场数据导入成功")
        else:
            print("ETF市场数据导入失败")
    except Exception as e:
        print(f"导入ETF市场数据时出错: {str(e)}")
    
    # 导入ETF价格数据
    try:
        print("开始导入ETF价格数据...")
        df = pd.read_excel('data/ETF_DATA_20250328.xlsx', engine='openpyxl')
        if db.save_etf_price(df):
            print("ETF价格数据导入成功")
        else:
            print("ETF价格数据导入失败")
    except Exception as e:
        print(f"导入ETF价格数据时出错: {str(e)}")
    
    # 导入ETF自选数据
    try:
        print("开始导入ETF自选数据...")
        df = pd.read_excel('data/客户ETF自选人数20250331.xlsx', engine='openpyxl')
        if db.save_etf_attention(df):
            print("ETF自选数据导入成功")
        else:
            print("ETF自选数据导入失败")
    except Exception as e:
        print(f"导入ETF自选数据时出错: {str(e)}")
    
    # 导入ETF持有人数据
    try:
        print("开始导入ETF持有人数据...")
        df = pd.read_excel('data/客户ETF保有量20250331.xlsx', engine='openpyxl')
        
        # 标准化列名
        df.columns = [str(col).strip().replace('\n', '') for col in df.columns]
        
        print("原始列名：", list(df.columns))
        print("原始数据前5行：")
        print(df.head())
        
        # 准备列名映射
        columns_mapping = {
            '标的代码': 'code',
            '标的名称': 'name',
            '持仓客户数': 'holder_count',
            '持仓份额': 'holder_household_count',
            '持仓市值': 'holding_value'
        }
        
        # 重命名列
        df = df.rename(columns=columns_mapping)
        
        print("重命名后的列名：", list(df.columns))
        
        # 检查必需字段
        required_fields = ['code', 'name', 'holder_count', 'holder_household_count']
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            print(f"ETF持有人数据缺少必需字段: {missing_fields}")
            print("可用的列名：", list(df.columns))
            return False
        
        # 选择需要的列
        df = df[required_fields]
        
        print("选择需要的列后的数据前5行：")
        print(df.head())
        
        # 标准化ETF代码
        df['code'] = df['code'].apply(normalize_etf_code)
        
        # 转换数据类型
        numeric_fields = ['holder_count', 'holder_household_count']
        for field in numeric_fields:
            df[field] = pd.to_numeric(df[field], errors='coerce')
        
        print("数据类型转换后的数据前5行：")
        print(df.head())
        
        # 保存到数据库
        if not db.save_etf_holders(df):
            print("保存ETF持有人数据失败")
            return False
        
        print(f"成功保存ETF持有人数据，共{len(df)}条记录")
        return True
    
    except Exception as e:
        print(f"导入ETF持有人数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 导入ETF指数分类数据
    try:
        print("开始导入ETF指数分类数据...")
        df = pd.read_excel('data/ETF-Index-Classification_20250328.xlsx', engine='openpyxl')
        if db.save_etf_index_classification(df):
            print("ETF指数分类数据导入成功")
            return True
        else:
            print("ETF指数分类数据导入失败")
            return False
    except Exception as e:
        print(f"导入ETF指数分类数据时出错: {str(e)}")
        return False
    
    # 导入ETF商务协议数据
    try:
        print("开始导入ETF商务协议数据...")
        df = pd.read_excel('data/ETF单产品商务协议20250328.xlsx', engine='openpyxl')
        if db.save_business_etf(df):
            print("ETF商务协议数据导入成功")
            return True
        else:
            print("ETF商务协议数据导入失败")
            return False
    except Exception as e:
        print(f"导入ETF商务协议数据时出错: {str(e)}")
        return False

def main():
    """主函数"""
    # 创建数据库连接
    db = Database()
    
    # 创建数据库表
    try:
        db.create_tables()
        print("数据库表创建成功")
    except Exception as e:
        print(f"创建数据库表失败: {str(e)}")
        return
    
    # 导入ETF市场数据 - 这必须第一个执行
    if not import_etf_market_data(db):
        print("导入ETF市场数据失败 - 终止流程")
        return
    else:
        print("ETF市场数据导入成功")
    
    # 导入ETF指数分类数据
    if not import_etf_index_classification_data(db):
        print("导入ETF指数分类数据失败")
        # 继续执行，不要中断
    
    # 导入ETF商务协议数据
    if not import_etf_business_data(db):
        print("导入ETF商务协议数据失败")
        # 继续执行，不要中断
    
    # 导入ETF自选数据
    if not import_etf_attention_data(db):
        print("导入ETF自选数据失败")
        # 继续执行，不要中断
    
    # 导入ETF持有人数据
    if not import_etf_holders_data(db):
        print("导入ETF持有人数据失败")
        # 继续执行，不要中断
    
    # 导入ETF价格数据
    if not import_etf_price_data(db):
        print("导入ETF价格数据失败")
        # 继续执行，不要中断
    
    # 打印导入结果
    count_etf_info = db.execute_query("SELECT COUNT(*) FROM etf_info")[0][0]
    count_etf_business = db.execute_query("SELECT COUNT(*) FROM etf_business")[0][0]
    count_etf_attention = db.execute_query("SELECT COUNT(*) FROM etf_attention")[0][0]
    count_etf_holders = db.execute_query("SELECT COUNT(*) FROM etf_holders")[0][0]
    
    print(f"当前数据库中的ETF数据：{count_etf_info}条记录")
    print(f"当前数据库中的商务ETF数据：{count_etf_business}条记录")
    print(f"当前数据库中的ETF自选数据：{count_etf_attention}条记录")
    print(f"当前数据库中的ETF持有人数据：{count_etf_holders}条记录")
    
    # 关闭数据库连接
    db.close()
    
    print("ETF数据导入完成")

def import_etf_attention_data(db):
    """导入ETF自选数据"""
    try:
        # 读取Excel文件
        df = pd.read_excel('data/客户ETF自选人数20250331.xlsx', engine='openpyxl')
        
        # 标准化列名
        df.columns = [col.strip().replace('\n', '') for col in df.columns]
        
        # 准备列名映射
        columns_mapping = {
            '标的代码': 'code',
            '加自选人数': 'attention_count'
        }
        
        # 重命名列
        df = df.rename(columns=columns_mapping)
        
        # 检查必需字段
        required_fields = ['code', 'attention_count']
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            print(f"ETF自选数据缺少必需字段: {missing_fields}")
            return False
        
        # 选择需要的列
        df = df[required_fields]
        
        # 转换数据类型
        df['attention_count'] = pd.to_numeric(df['attention_count'], errors='coerce')
        
        # 保存到数据库
        if not db.save_etf_attention(df):
            print("保存ETF自选数据失败")
            return False
        
        print(f"成功保存ETF自选数据 {len(df)} 条记录")
        return True
    
    except Exception as e:
        print(f"导入ETF自选数据失败: {str(e)}")
        return False

def import_etf_market_data(db):
    """导入ETF市场数据"""
    try:
            # 读取Excel文件
        df = pd.read_excel('data/ETF_DATA_20250328.xlsx', engine='openpyxl')
        
        # 标准化列名
        df.columns = [col.strip().replace('\n', '') for col in df.columns]
        
        # 保存到数据库
        if not db.save_etf_info(df):
            print("保存ETF市场数据失败")
            return False
        
        print(f"成功保存ETF市场数据 {len(df)} 条记录")
        return True
        
    except Exception as e:
        print(f"导入ETF市场数据失败: {str(e)}")
        return False

def import_etf_price_data(db):
    """导入ETF价格数据"""
    try:
        # 读取Excel文件
        df = pd.read_excel('data/ETF_DATA_20250328.xlsx', engine='openpyxl')
        
        # 标准化列名
        df.columns = [col.strip().replace('\n', '') for col in df.columns]
        
        # 保存到数据库
        if not db.save_etf_price(df):
            print("保存ETF价格数据失败")
            return False
        
        print(f"成功保存ETF价格数据 {len(df)} 条记录")
        return True
    
    except Exception as e:
        print(f"导入ETF价格数据失败: {str(e)}")
        return False

def import_etf_index_classification_data(db):
    """导入ETF指数分类数据"""
    try:
        print("开始导入ETF指数分类数据...")
        df = pd.read_excel('data/ETF-Index-Classification_20250328.xlsx', engine='openpyxl')
        if db.save_etf_index_classification(df):
            print("ETF指数分类数据导入成功")
            return True
        else:
            print("ETF指数分类数据导入失败")
            return False
    except Exception as e:
        print(f"导入ETF指数分类数据时出错: {str(e)}")
        return False

def import_etf_business_data(db):
    """导入ETF商务协议数据"""
    try:
        print("开始导入ETF商务协议数据...")
        df = pd.read_excel('data/ETF单产品商务协议20250328.xlsx', engine='openpyxl')
        if db.save_business_etf(df):
            print("ETF商务协议数据导入成功")
            return True
        else:
            print("ETF商务协议数据导入失败")
            return False
    except Exception as e:
        print(f"导入ETF商务协议数据时出错: {str(e)}")
        return False

def import_etf_holders_data(db):
    """导入ETF持有人数据"""
    try:
        print("开始导入ETF持有人数据...")
        
        # 查找最新的持有人数据文件
        files = sorted(glob.glob("data/客户ETF保有量*.xlsx"), reverse=True)
        if not files:
            print("未找到ETF持有人数据文件")
            return False
        
        latest_file = files[0]
        print(f"正在处理文件: {latest_file}")
        
        try:
            # 尝试使用pandas读取
            df = pd.read_excel(latest_file, engine='openpyxl')
            if df.empty:
                raise ValueError("Pandas读取的文件为空")
        except Exception as e:
            print(f"Pandas读取Excel失败: {str(e)}，尝试使用xlwings...")
            # 尝试使用xlwings读取
            app = xw.App(visible=False)
            wb = app.books.open(latest_file)
            sheet = wb.sheets[0]
            
            # 获取数据范围
            data_range = sheet.used_range
            print(f"数据范围：{data_range.address}")
            
            # 读取所有数据
            data = data_range.value
            
            # 转换为DataFrame
            if data and len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                print(f"成功读取文件，数据形状：{df.shape}")
            else:
                print("读取的数据为空或无效")
                wb.close()
                app.quit()
                return False
            
            # 关闭Excel文件
            wb.close()
            app.quit()
        
        # 标准化列名
        df.columns = [str(col).strip().replace('\n', '') for col in df.columns]
        
        print("原始列名：", list(df.columns))
        print("原始数据前5行：")
        print(df.head())
        
        # 查找包含关键词的列
        code_cols = [col for col in df.columns if any(key in col.lower() for key in ['代码', 'code'])]
        name_cols = [col for col in df.columns if any(key in col.lower() for key in ['名称', 'name'])]
        holder_cols = [col for col in df.columns if any(key in col.lower() for key in ['客户数', '持有人', 'holder'])]
        amount_cols = [col for col in df.columns if any(key in col.lower() for key in ['保有金额', '持有金额', '市值', 'amount', 'value'])]
        
        print(f"找到的代码列: {code_cols}")
        print(f"找到的名称列: {name_cols}")
        print(f"找到的持有人列: {holder_cols}")
        print(f"找到的金额列: {amount_cols}")
        
        # 如果找不到必要的列，尝试解析列名
        if not code_cols or not holder_cols:
            # 尝试通过位置推断列
            if len(df.columns) >= 3:
                print("通过位置推断列...")
                code_cols = [df.columns[0]]
                name_cols = [df.columns[1]] if len(df.columns) > 1 else []
                holder_cols = [df.columns[2]] if len(df.columns) > 2 else []
                if len(df.columns) > 3:
                    amount_cols = [df.columns[3]]
        
        # 准备列名映射
        columns_mapping = {}
        if code_cols:
            columns_mapping[code_cols[0]] = 'code'
        if name_cols:
            columns_mapping[name_cols[0]] = 'name'
        if holder_cols:
            columns_mapping[holder_cols[0]] = 'holder_count'
        if amount_cols:
            columns_mapping[amount_cols[0]] = 'holding_amount'
        
        print("列名映射:", columns_mapping)
        
        # 如果没有找到足够的列，使用默认映射
        if len(columns_mapping) < 2:
            print("未找到足够的列，使用默认映射...")
            # 创建一个新的DataFrame，包含所有ETF代码
            etfs = db.get_all_etf_info()
            if not etfs:
                print("无法获取ETF代码列表")
                return False
            
            print(f"创建默认持有人数据，基于{len(etfs)}个ETF代码")
            default_data = []
            for etf in etfs:
                default_data.append({
                    'code': etf['code'],
                    'name': etf['name'],
                    'holder_count': 0,
                    'holding_amount': 0.0
                })
            
            df = pd.DataFrame(default_data)
        else:
            # 重命名列
            df = df.rename(columns=columns_mapping)
            
            # 确保所需列存在
            required_fields = ['code']
            for field in required_fields:
                if field not in df.columns:
                    print(f"错误: 缺少必要字段 {field}")
                    return False
            
            # 选择有映射的列
            mapped_columns = list(columns_mapping.values())
            df = df[mapped_columns]
            
            # 为缺失的列添加默认值
            if 'holder_count' not in df.columns:
                df['holder_count'] = 0
            if 'holding_amount' not in df.columns:
                df['holding_amount'] = 0.0
        
        print("处理后的数据前5行：")
        print(df.head())
        
        # 标准化ETF代码
        df['code'] = df['code'].astype(str).apply(normalize_etf_code)
        
        # 确保数字列是数字类型
        try:
            if 'holder_count' in df.columns:
                df['holder_count'] = pd.to_numeric(df['holder_count'], errors='coerce').fillna(0).astype(int)
            if 'holding_amount' in df.columns:
                df['holding_amount'] = pd.to_numeric(df['holding_amount'], errors='coerce').fillna(0).astype(float)
        except Exception as e:
            print(f"转换数值时出错: {str(e)}")
        
        # 添加更新时间
        df['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存到数据库
        if not db.save_etf_holders(df):
            print("保存ETF持有人数据失败")
            return False
        
        print(f"成功保存ETF持有人数据，共{len(df)}条记录")
        return True
        
    except Exception as e:
        print(f"导入ETF持有人数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()