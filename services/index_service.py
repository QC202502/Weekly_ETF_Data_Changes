import pandas as pd
import os
import glob
from datetime import datetime
import traceback

# 全局变量
index_info_map = {}

def load_index_info():
    """加载最新的市场可交易指数数据"""
    global index_info_map
    
    print("开始加载市场可交易指数数据...")
    
    # 动态获取最新数据文件
    files = glob.glob('/Users/admin/Downloads/市场可交易指数 *.xlsx')
    if not files:
        # 尝试在其他目录查找
        alt_paths = [
            '/Users/admin/PycharmProjects/Weekly_ETF_Data_Changes/data/市场可交易指数 *.xlsx',
            './data/市场可交易指数 *.xlsx'
        ]
        
        for path in alt_paths:
            alt_files = glob.glob(path)
            if alt_files:
                files = alt_files
                print(f"在备选路径找到指数数据文件: {files}")
                break
                
    if not files:
        print("警告: 未找到市场可交易指数数据文件!")
        return False, "未找到市场可交易指数数据文件，请确保文件存在于正确位置"
    
    # 提取最新文件
    filename = sorted(files)[-1]
    print(f"找到最新指数数据文件: {filename}")
    
    try:
        # 读取指数数据
        print(f"正在读取Excel文件: {filename}")
        index_data = pd.read_excel(filename, engine='openpyxl')
        print(f"成功读取指数数据，共 {len(index_data)} 行")
        
        # 创建指数代码到指数简介的映射
        index_info_map = {}
        for _, row in index_data.iterrows():
            if pd.notna(row['证券代码']) and pd.notna(row['证券简介']):
                index_code = str(row['证券代码']).strip()
                index_info_map[index_code] = {
                    'name': row['证券简称'] if pd.notna(row['证券简称']) else '',
                    'intro': row['证券简介'],
                    'publisher': row['发布机构'] if pd.notna(row['发布机构']) else '',
                    'components': row['成份个数'] if pd.notna(row['成份个数']) else '',
                    'weight_method': row['加权方式'] if pd.notna(row['加权方式']) else ''
                }
        
        print(f"成功创建指数信息映射，共 {len(index_info_map)} 个指数")
        return True, index_info_map
        
    except Exception as e:
        traceback.print_exc()
        return False, f"加载指数数据出错：{str(e)}"

def get_index_intro(index_code):
    """获取指数简介"""
    global index_info_map
    
    # 如果映射为空，尝试加载数据
    if not index_info_map:
        success, result = load_index_info()
        if success:
            index_info_map = result
        else:
            print(f"警告: {result}")
            return ""
    
    # 返回指数简介
    if index_code in index_info_map:
        return index_info_map[index_code]['intro']
    return ""

def get_index_info(index_code):
    """获取指数完整信息"""
    global index_info_map
    
    # 如果映射为空，尝试加载数据
    if not index_info_map:
        success, result = load_index_info()
        if success:
            index_info_map = result
        else:
            print(f"警告: {result}")
            return {}
    
    # 返回指数信息
    if index_code in index_info_map:
        return index_info_map[index_code]
    return {}