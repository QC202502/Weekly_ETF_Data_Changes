#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ETF价格推荐模块

根据最新交易日的涨幅数据，提取涨幅最高的ETF，并按照跟踪指数分组，
从每组中选取涨幅最大的一只ETF，最后取前20个展示在推荐模块中。

使用方法：
python etf_price_recommendation.py [csv文件路径]
"""

import pandas as pd
import os
import sys
import json
from datetime import datetime

def load_etf_price_data(file_path):
    """
    加载ETF价格数据
    
    参数:
        file_path: CSV文件路径
        
    返回:
        pandas.DataFrame: 包含ETF价格数据的DataFrame
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        print(f"成功读取ETF价格数据，共{len(df)}条记录")
        return df
    except Exception as e:
        print(f"读取ETF价格数据失败: {str(e)}")
        return pd.DataFrame()

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
        required_columns = ['TS代码', '代码', '场内简称', '当日涨跌幅(%)', '交易日期']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"警告：缺少以下列：{missing_columns}")
            return pd.DataFrame()
        
        # 获取最新交易日期
        latest_date = df['交易日期'].max()
        print(f"最新交易日期: {latest_date}")
        
        # 筛选最新交易日的数据
        latest_data = df[df['交易日期'] == latest_date].copy()
        
        # 处理ETF代码格式，移除可能存在的交易所后缀（如.SH或.SZ）
        if '代码' in latest_data.columns:
            # 检查代码格式，如果包含点号，则只保留点号前的部分（6位数字代码）
            latest_data['代码'] = latest_data['代码'].astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
            print("已处理ETF代码格式，移除交易所后缀")
        
        # 添加跟踪指数列（如果不存在）
        if '跟踪指数代码' not in latest_data.columns:
            # 从TS代码中提取跟踪指数信息，确保只获取数字部分
            latest_data['跟踪指数代码'] = latest_data['TS代码'].astype(str).apply(
                lambda x: x.split('.')[0] if '.' in x else x
            )
            print("警告：数据中缺少'跟踪指数代码'列，已根据TS代码生成临时列")
        else:
            # 确保跟踪指数代码格式正确（只保留数字部分）
            latest_data['跟踪指数代码'] = latest_data['跟踪指数代码'].astype(str).apply(
                lambda x: x.split('.')[0] if '.' in x else x
            )
        
        # 按跟踪指数分组，每组取涨幅最大的一只ETF
        top_etfs_by_index = latest_data.sort_values('当日涨跌幅(%)', ascending=False).groupby('跟踪指数代码').first().reset_index()
        
        # 按涨幅排序，取前N个
        top_etfs = top_etfs_by_index.sort_values('当日涨跌幅(%)', ascending=False).head(top_n)
        
        print(f"成功获取{len(top_etfs)}只涨幅最高的ETF（每个跟踪指数只取最高涨幅的一只）")
        return top_etfs
    except Exception as e:
        print(f"获取涨幅最高的ETF失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def format_recommendations(top_etfs, etf_base_data=None):
    """
    格式化推荐数据，用于前端展示
    
    参数:
        top_etfs: 包含涨幅最高的ETF数据的DataFrame
        etf_base_data: 包含ETF基础数据的DataFrame，用于匹配ETF信息
        
    返回:
        dict: 包含推荐数据的字典
    """
    recommendations = {
        "price_return": [],  # 按涨幅排序的ETF
        "trade_date": ""    # 交易日期
    }
    
    try:
        print(f"开始格式化推荐数据，共{len(top_etfs)}条记录")
        print(f"数据列名: {top_etfs.columns.tolist()}")
        
        # 获取交易日期
        if '交易日期' in top_etfs.columns and not top_etfs.empty:
            trade_date = top_etfs['交易日期'].iloc[0]
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
                # 使用默认日期
                recommendations["trade_date"] = "3月19日"
        else:
            # 使用默认日期
            recommendations["trade_date"] = "3月19日"
            
        for _, row in top_etfs.iterrows():
            try:
                # 确保ETF代码格式正确，添加sh/sz前缀
                etf_code = str(row['代码']).split('.')[0] if '.' in str(row['代码']) else str(row['代码'])
                
                # 添加交易所前缀（如果没有）
                if not (etf_code.startswith('sh') or etf_code.startswith('sz')):
                    # 根据代码规则添加前缀：5开头或6开头的是上交所，其他是深交所
                    if etf_code.startswith('5') or etf_code.startswith('6'):
                        etf_code = 'sh' + etf_code
                    else:
                        etf_code = 'sz' + etf_code
                
                # 保存不带前缀的ETF代码，用于匹配基础数据
                etf_code_no_prefix = etf_code[2:] if etf_code.startswith('sh') or etf_code.startswith('sz') else etf_code
                
                etf_name = row['场内简称'] if '场内简称' in row else row.get('名称', f"ETF{etf_code}")
                daily_return = row['当日涨跌幅(%)']
                
                # 获取跟踪指数代码，确保格式正确
                index_code = ''
                if '跟踪指数代码' in row and pd.notna(row['跟踪指数代码']):
                    index_code = str(row['跟踪指数代码']).split('.')[0] if '.' in str(row['跟踪指数代码']) else str(row['跟踪指数代码'])
                    
                    # 添加交易所前缀（如果没有）
                    if not (index_code.startswith('sh') or index_code.startswith('sz')):
                        # 根据代码规则添加前缀：5开头或6开头的是上交所，其他是深交所
                        if index_code.startswith('5') or index_code.startswith('6'):
                            index_code = 'sh' + index_code
                        else:
                            index_code = 'sz' + index_code
                
                # 获取基金管理人信息
                manager = '未知'
                for manager_col in ['基金管理人', '基金管理人简称', '管理人']:
                    if manager_col in row and pd.notna(row[manager_col]):
                        manager = row[manager_col]
                        break
                
                # 尝试从基础数据中获取更多信息
                scale = 0
                index_name = row.get('跟踪指数名称', '')
                index_code_display = index_code
                
                if etf_base_data is not None and not etf_base_data.empty:
                    # 在基础数据中查找匹配的ETF - 尝试多种匹配方式
                    matched_etf = etf_base_data[etf_base_data['证券代码'] == etf_code_no_prefix]
                    
                    # 如果没找到，尝试不同格式的代码匹配
                    if matched_etf.empty and len(etf_code_no_prefix) == 6:
                        # 尝试不同格式的代码
                        for code_format in [etf_code_no_prefix, f"{etf_code_no_prefix}.SH", f"{etf_code_no_prefix}.SZ"]:
                            temp_match = etf_base_data[etf_base_data['证券代码'].str.contains(code_format, na=False)]
                            if not temp_match.empty:
                                matched_etf = temp_match
                                print(f"找到ETF匹配: {code_format}")
                                break
                    
                    if not matched_etf.empty:
                        # 优先使用基金管理人简称
                        if '基金管理人简称' in matched_etf.columns and pd.notna(matched_etf['基金管理人简称'].iloc[0]):
                            manager = matched_etf['基金管理人简称'].iloc[0]
                        elif '基金管理人' in matched_etf.columns and pd.notna(matched_etf['基金管理人'].iloc[0]):
                            # 如果没有简称，尝试从完整名称提取简称
                            full_name = matched_etf['基金管理人'].iloc[0]
                            # 移除常见后缀
                            short_name = full_name.replace("基金管理有限公司", "")
                            short_name = short_name.replace("基金管理股份有限公司", "")
                            short_name = short_name.replace("基金管理有限责任公司", "")
                            short_name = short_name.replace("基金管理公司", "")
                            short_name = short_name.replace("基金", "")
                            short_name = short_name.replace("股份有限公司", "")
                            short_name = short_name.replace("有限公司", "")
                            short_name = short_name.replace("有限责任公司", "")
                            manager = short_name
                        
                        # 获取基金规模 - 确保正确匹配列名
                        scale_col = '基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'
                        if scale_col in matched_etf.columns and pd.notna(matched_etf[scale_col].iloc[0]):
                            scale_value = matched_etf[scale_col].iloc[0]
                            if pd.notna(scale_value):
                                scale = round(float(scale_value), 2)
                        
                        # 获取跟踪指数信息 - 优先使用基础数据中的信息
                        if '跟踪指数名称' in matched_etf.columns and pd.notna(matched_etf['跟踪指数名称'].iloc[0]):
                            index_name = matched_etf['跟踪指数名称'].iloc[0]
                        
                        if '跟踪指数代码' in matched_etf.columns and pd.notna(matched_etf['跟踪指数代码'].iloc[0]):
                            index_code_display = matched_etf['跟踪指数代码'].iloc[0]
                
                # 添加到推荐列表
                recommendations["price_return"].append({
                    'code': etf_code,
                    'name': etf_name,
                    'manager': manager,
                    'is_business': False,  # 默认为非商务品，实际应用中可能需要从其他数据源获取
                    'business_text': "非商务品",
                    'index_code': index_code_display,  # 使用正确的指数代码
                    'index_name': index_name,
                    'scale': scale,
                    'daily_return': round(float(daily_return), 2) if pd.notna(daily_return) else 0
                })
            except Exception as row_e:
                print(f"处理ETF记录时出错: {str(row_e)}")
                continue
        
        print(f"成功格式化{len(recommendations['price_return'])}条ETF推荐数据")
    except Exception as e:
        print(f"格式化推荐数据出错: {str(e)}")
        import traceback
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

def load_etf_base_data(file_path=None):
    """
    加载ETF基础数据
    
    参数:
        file_path: CSV文件路径，如果为None，则尝试查找默认文件
        
    返回:
        pandas.DataFrame: 包含ETF基础数据的DataFrame
    """
    try:
        if file_path is None:
            # 尝试查找默认文件
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # 查找最新的ETF基础数据文件
            for file in os.listdir(base_dir):
                if file.startswith('ETF_基础数据合并_') and file.endswith('.csv'):
                    file_path = os.path.join(base_dir, file)
                    break
        
        if file_path and os.path.exists(file_path):
            # 读取CSV文件
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            print(f"成功读取ETF基础数据，共{len(df)}条记录")
            return df
        else:
            print("未找到ETF基础数据文件")
            return pd.DataFrame()
    except Exception as e:
        print(f"读取ETF基础数据失败: {str(e)}")
        return pd.DataFrame()

def main():
    """
    主函数
    """
    # 获取命令行参数中的CSV文件路径
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # 尝试查找最新的ETF价格数据文件
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        # 查找匹配模式的最新文件
        latest_file = None
        latest_date = None
        
        # 首先在data目录中查找
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.startswith("etf_prices_") and file.endswith(".csv"):
                    try:
                        # 从文件名中提取日期
                        date_str = file.replace("etf_prices_", "").replace(".csv", "")
                        file_date = datetime.strptime(date_str, "%Y%m%d")
                        if latest_date is None or file_date > latest_date:
                            latest_date = file_date
                            latest_file = os.path.join(data_dir, file)
                    except Exception as e:
                        print(f"解析文件日期出错: {file}, {str(e)}")
        
        # 如果data目录中没找到，在根目录中查找
        if latest_file is None:
            root_dir = os.path.dirname(os.path.abspath(__file__))
            for file in os.listdir(root_dir):
                if file.startswith("etf_prices_") and file.endswith(".csv"):
                    try:
                        # 从文件名中提取日期
                        date_str = file.replace("etf_prices_", "").replace(".csv", "")
                        file_date = datetime.strptime(date_str, "%Y%m%d")
                        if latest_date is None or file_date > latest_date:
                            latest_date = file_date
                            latest_file = os.path.join(root_dir, file)
                    except Exception as e:
                        print(f"解析文件日期出错: {file}, {str(e)}")
        
        # 如果找到了最新文件，使用它
        if latest_file:
            file_path = latest_file
            print(f"使用最新的ETF价格数据文件: {file_path}")
        else:
            # 如果没找到任何匹配的文件，返回错误
            print("错误: 未找到任何ETF价格数据文件")
            print("请先运行 get_latest_etf_data.py 获取最新ETF价格数据")
            return 1
        
        if not os.path.exists(file_path):
            print(f"错误: 未找到ETF价格数据文件 {file_path}")
            print("使用方法: python etf_price_recommendation.py [csv文件路径]")
            return 1
    
    try:
        # 加载ETF价格数据
        df = load_etf_price_data(file_path)
        if df.empty:
            return 1
        
        # 加载ETF基础数据
        etf_base_data = load_etf_base_data()
        
        # 获取涨幅最高的ETF
        top_etfs = get_top_etfs_by_return(df)
        if top_etfs.empty:
            return 1
        
        # 格式化推荐数据
        recommendations = format_recommendations(top_etfs, etf_base_data)
        
        # 保存推荐数据
        save_recommendations(recommendations)
        
        # 打印推荐数据预览
        print("\n推荐数据预览:")
        for i, item in enumerate(recommendations["price_return"][:5]):
            print(f"{i+1}. {item['name']} ({item['code']}): 涨幅 {item['daily_return']}%")
        
        return 0
    
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())