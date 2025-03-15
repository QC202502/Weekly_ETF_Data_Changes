import pandas as pd
import glob
import os
from datetime import datetime, timedelta
import traceback

# 全局变量 - 需要导出这些变量
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
    """加载最新的ETF数据"""
    global etf_data, business_etfs, current_date_str, previous_date_str, date_range
    
    try:
        # 获取Flask应用配置
        from flask import current_app
        upload_folder = current_app.config['UPLOAD_FOLDER']
    except:
        # 如果不在Flask上下文中，使用默认路径
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    
    # 调用加载ETF数据函数
    success, message = load_etf_data()
    
    if success:
        return message, etf_data, business_etfs, current_date_str, previous_date_str, date_range
    else:
        return message, None, None, None, None, None

def load_etf_data():
    """加载ETF数据"""
    global etf_data, business_etfs, current_date_str, previous_date_str, date_range
    
    print("开始加载ETF数据...")
    
    # 动态获取最新数据文件
    files = glob.glob('ETF_基础数据合并_*.csv')
    if not files:
        # 尝试在其他目录查找
        alt_paths = [
            '/Users/admin/Downloads/ETF_基础数据合并_*.csv',
            '/Users/admin/PycharmProjects/Weekly_ETF_Data_Changes/data/ETF_基础数据合并_*.csv',
            './data/ETF_基础数据合并_*.csv'
        ]
        
        for path in alt_paths:
            alt_files = glob.glob(path)
            if alt_files:
                files = alt_files
                print(f"在备选路径找到数据文件: {files}")
                break
                
    if not files:
        print("警告: 未找到ETF基础数据文件!")
        return False, "未找到ETF基础数据文件，请确保文件存在于正确位置"
    
    # 提取最新文件日期
    filename = sorted(files)[-1]
    print(f"找到最新数据文件: {filename}")
    date_str = filename.split('_')[-1].split('.')[0]
    
    try:
        # 读取ETF基础数据
        print(f"正在读取CSV文件: {filename}")
        etf_data = pd.read_csv(filename, encoding='utf-8-sig')
        print(f"成功读取数据，共 {len(etf_data)} 行")
        
        # 确保证券代码为字符串
        etf_data['证券代码'] = etf_data['证券代码'].astype(str).str.strip()
        
        # 获取当前日期
        current_date = datetime.strptime(date_str, "%Y%m%d")
        current_date_str = current_date.strftime("%m月%d日")
        
        # 计算上周日期
        previous_date = current_date - timedelta(days=7)
        previous_date_str = previous_date.strftime("%m月%d日")
        
        # 设置日期范围
        date_range = f"{previous_date.strftime('%m%d')}-{current_date.strftime('%m%d')}"
        
        # 读取商务协议文件
        商务协议_paths = [
            f'/Users/admin/Downloads/ETF单产品商务协议{date_str}.xlsx',
            f'./ETF单产品商务协议{date_str}.xlsx',
            f'./data/ETF单产品商务协议{date_str}.xlsx',
            f'/Users/admin/PycharmProjects/Weekly_ETF_Data_Changes/ETF单产品商务协议{date_str}.xlsx'
        ]
        
        商务协议_loaded = False
        for 商务协议_path in 商务协议_paths:
            try:
                print(f"尝试读取商务协议文件: {商务协议_path}")
                # 修改这里：使用openpyxl引擎读取Excel文件
                商务协议 = pd.read_excel(商务协议_path, engine='openpyxl')
                商务协议_loaded = True
                print(f"成功读取商务协议文件，共 {len(商务协议)} 行")
                break
            except Exception as e:
                print(f"读取商务协议文件失败: {e}")
                continue
        
        # 如果成功加载商务协议文件
        if 商务协议_loaded:
            # 确保证券代码为字符串
            商务协议['证券代码'] = 商务协议['证券代码'].astype(str).str.strip()
            
            # 获取商务品代码集合
            business_etfs = set(商务协议['证券代码'].tolist())
            
            # 标记商务品
            etf_data['是否商务品'] = etf_data['证券代码'].apply(lambda x: '商务' if x in business_etfs else '非商务')
            
            print(f"商务品数据合并成功，共 {len(business_etfs)} 个商务品")
        else:
            # 如果没有商务协议文件，使用默认标记
            etf_data['是否商务品'] = '非商务'
            business_etfs = set()
            print("未找到商务协议文件，所有ETF标记为非商务品")
        
        # 处理管理人简称
        if '基金管理人' in etf_data.columns:
            etf_data['管理人'] = etf_data['基金管理人'].apply(get_manager_short)
        
        print("数据加载和处理完成")
        return True, f"数据已加载，日期：{current_date_str}，商务品数量：{len(business_etfs)}个"
        
    except Exception as e:
        traceback.print_exc()
        return False, f"加载数据出错：{str(e)}"

def format_etf_result(row):
    """格式化ETF搜索结果"""
    try:
        # 尝试获取证券名称，兼容不同的列名
        name = None
        for name_col in ['证券名称', '证券名称（03月07日）']:
            if name_col in row and not pd.isna(row[name_col]):
                name = row[name_col]
                break
        
        if name is None:
            name = '未知'
        
        # 尝试获取管理人，兼容不同的列名
        manager = None
        for manager_col in ['管理人', '基金管理人']:
            if manager_col in row and not pd.isna(row[manager_col]):
                manager = row[manager_col]
                break
        
        if manager is None:
            manager = '未知'
        
        # 尝试获取规模
        scale = 0
        scale_col = '基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'
        if scale_col in row and not pd.isna(row[scale_col]):
            try:
                scale = float(row[scale_col])
            except:
                scale = 0
        
        # 尝试获取管理费率
        fee_rate = 0
        fee_col = '管理费率[单位]%'
        if fee_col in row and not pd.isna(row[fee_col]):
            try:
                fee_rate = float(row[fee_col])
            except:
                fee_rate = 0
        
        # 尝试获取指数代码和名称
        index_code = ''
        index_name = ''
        if '跟踪指数代码' in row and not pd.isna(row['跟踪指数代码']):
            index_code = row['跟踪指数代码']
        if '跟踪指数名称' in row and not pd.isna(row['跟踪指数名称']):
            index_name = row['跟踪指数名称']
        
        # 构建结果字典
        result = {
            'code': row['证券代码'],
            'name': name,
            'is_business': '是否商务品' in row and row['是否商务品'] == '商务',
            'manager': manager,
            'scale': scale,
            'index_code': index_code,
            'index_name': index_name,
            'fee_rate': fee_rate,
        }
        return result
    except Exception as e:
        print(f"格式化ETF结果出错: {str(e)}")
        # 返回一个基本的结果，避免整个搜索失败
        return {
            'code': row.get('证券代码', '未知'),
            'name': '格式化错误',
            'is_business': False,
            'manager': '未知',
            'scale': 0,
            'index_code': '',
            'index_name': '',
            'fee_rate': 0,
        }