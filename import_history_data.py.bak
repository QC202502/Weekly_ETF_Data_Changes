#!/usr/bin/env python3
"""
从历史Excel文件导入ETF数据到历史表

此脚本会遍历data目录下的所有历史Excel文件，提取日期信息，并将数据导入到相应的历史表中
"""

import os
import pandas as pd
import re
from datetime import datetime
from database.models import Database
import logging
import sys
import openpyxl
from utils.etf_code import normalize_etf_code

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('etf_history_import.log')
    ]
)
logger = logging.getLogger(__name__)

def extract_date_from_filename(filename):
    """从文件名中提取日期"""
    # 尝试查找格式为YYYYMMDD的日期
    date_match = re.search(r'(\d{8})', filename)
    if date_match:
        date_str = date_match.group(1)
        try:
            # 将YYYYMMDD转换为YYYY-MM-DD
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None

def get_all_data_files():
    """获取所有数据文件及其日期"""
    data_dir = 'data'
    data_files = {
        'etf_info': [],      # ETF基本信息文件
        'etf_attention': [], # ETF自选数据文件
        'etf_holders': []    # ETF持有人数据文件
    }
    
    # 遍历data目录
    for filename in os.listdir(data_dir):
        # 提取日期
        date = extract_date_from_filename(filename)
        if not date:
            continue
        
        # 文件完整路径
        file_path = os.path.join(data_dir, filename)
        
        # 分类文件
        if filename.startswith('ETF_DATA_'):
            data_files['etf_info'].append((file_path, date))
        elif filename.startswith('客户ETF自选人数'):
            data_files['etf_attention'].append((file_path, date))
        elif filename.startswith('客户ETF保有量'):
            data_files['etf_holders'].append((file_path, date))
    
    # 按日期排序
    for key in data_files:
        data_files[key].sort(key=lambda x: x[1])
    
    return data_files

def read_excel_with_enhanced_logic(file_path, sheet_name=None):
    """使用增强的逻辑读取Excel文件，与import_excel_data.py保持一致"""
    try:
        # 尝试列出所有工作表
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        logger.info(f"文件中的工作表: {sheet_names}")
        
        # 如果指定了工作表名，尝试读取
        if sheet_name and sheet_name in sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        # 如果只有一个工作表，直接读取
        elif len(sheet_names) == 1:
            df = pd.read_excel(file_path, engine='openpyxl')
        # 尝试读取特定名称的工作表
        elif '数据表' in sheet_names:
            df = pd.read_excel(file_path, sheet_name='数据表', engine='openpyxl')
        elif 'Sheet1' in sheet_names:
            df = pd.read_excel(file_path, sheet_name='Sheet1', engine='openpyxl')
        elif '客户ETF自选人数' in sheet_names:
            df = pd.read_excel(file_path, sheet_name='客户ETF自选人数', engine='openpyxl')
        elif '客户ETF保有量' in sheet_names:
            df = pd.read_excel(file_path, sheet_name='客户ETF保有量', engine='openpyxl')
        else:
            # 尝试读取第一个工作表
            df = pd.read_excel(file_path, sheet_name=sheet_names[0], engine='openpyxl')
        
        # 打印列名和数据样本，帮助诊断
        logger.info(f"原始列名: {list(df.columns)}")
        logger.info(f"数据形状: {df.shape}")
        logger.info(f"数据前5行:\n{df.head()}")
        
        # 如果数据帧为空，尝试其他读取方式
        if df.empty or len(df.columns) <= 1:
            logger.warning("标准读取方式返回空数据或只有单列，尝试读取所有单元格...")
            # 使用更底层的方式读取
            wb = openpyxl.load_workbook(file_path)
            
            # 尝试所有工作表
            for sheet_name in wb.sheetnames:
                logger.info(f"尝试读取工作表: {sheet_name}")
                ws = wb[sheet_name]
                
                # 获取表格范围
                data = []
                # 从第一行开始，假设第一行是标题
                for row in ws.iter_rows(min_row=1, values_only=True):
                    if any(row):  # 只添加非空行
                        data.append(row)
                
                if data:
                    # 检查第一行是否包含我们需要的列标题
                    first_row = data[0]
                    logger.info(f"找到的标题行: {first_row}")
                    
                    # 检查是否包含必要的列（根据文件类型判断）
                    if ('标的代码' in first_row and '加自选人数' in first_row) or \
                       ('标的代码' in first_row and '持仓客户数' in first_row and '持仓市值' in first_row) or \
                       ('证券代码' in first_row):
                        df = pd.DataFrame(data[1:], columns=data[0])
                        logger.info(f"成功读取数据，形状: {df.shape}")
                        break
            
            if df.empty or len(df.columns) <= 1:
                logger.error("所有读取方式都失败，无法获取必要的数据")
                return None
        
        return df
    
    except Exception as e:
        logger.error(f"读取Excel文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def process_etf_info_file(file_path, date, db):
    """处理ETF基本信息文件并导入数据到历史表"""
    logger.info(f"处理ETF基本信息文件: {file_path}, 日期: {date}")
    try:
        # 检查该日期的数据是否已经存在
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM etf_fund_size_history WHERE date = ?", (date,))
        if cursor.fetchone()[0] > 0:
            logger.info(f"日期 {date} 的ETF规模历史数据已存在，跳过导入")
            return
        
        # 读取Excel文件
        df = read_excel_with_enhanced_logic(file_path)
        if df is None:
            return
        
        # 标准化列名
        df.columns = [str(col).strip() for col in df.columns]
        
        # 处理ETF代码（确保是6位字符串）
        if '证券代码' in df.columns:
            code_column = '证券代码'
        else:
            # 查找可能的代码列
            code_columns = [col for col in df.columns if '代码' in col]
            if not code_columns:
                logger.error(f"无法在文件 {file_path} 中找到代码列")
                return
            code_column = code_columns[0]
        
        # 处理规模列
        scale_columns = [col for col in df.columns if '规模' in col and '亿元' in col]
        if not scale_columns:
            logger.error(f"无法在文件 {file_path} 中找到规模列")
            return
        scale_column = scale_columns[0]
        
        # 准备数据
        df['code'] = df[code_column].apply(normalize_etf_code)
        df['fund_size'] = pd.to_numeric(df[scale_column], errors='coerce').fillna(0)
        
        # 添加日期和更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 过滤有效数据
        valid_data = df[['code', 'fund_size']].dropna(subset=['code'])
        valid_data = valid_data[valid_data['fund_size'] > 0]
        
        # 插入数据
        for _, row in valid_data.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO etf_fund_size_history (code, fund_size, date, update_time)
                    VALUES (?, ?, ?, ?)
                """, (row['code'], row['fund_size'], date, current_time))
            except Exception as e:
                logger.error(f"插入规模数据时出错: {str(e)}")
        
        db.conn.commit()
        logger.info(f"成功导入 {len(valid_data)} 条 {date} 的ETF规模历史数据")
    
    except Exception as e:
        logger.error(f"处理ETF基本信息文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def process_etf_attention_file(file_path, date, db):
    """处理ETF自选数据文件并导入数据到历史表"""
    logger.info(f"处理ETF自选数据文件: {file_path}, 日期: {date}")
    try:
        # 检查该日期的数据是否已经存在
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM etf_attention_history WHERE date = ?", (date,))
        if cursor.fetchone()[0] > 0:
            logger.info(f"日期 {date} 的ETF自选历史数据已存在，跳过导入")
            return
        
        # 读取Excel文件，优先尝试"客户ETF自选人数"工作表
        df = read_excel_with_enhanced_logic(file_path, sheet_name='客户ETF自选人数')
        if df is None:
            return
        
        # 标准化列名
        df.columns = [str(col).strip() for col in df.columns]
        
        # 检查所需列是否存在
        required_columns = ['标的代码', '加自选人数']
        
        # 检查实际列名中是否有与所需列名模糊匹配的
        actual_columns = list(df.columns)
        logger.info(f"标准化后列名: {actual_columns}")
        
        # 查找可能的代码列
        code_columns = [col for col in actual_columns if '代码' in col]
        logger.info(f"找到的代码列: {code_columns}")
        
        # 查找可能的自选列
        attention_columns = [col for col in actual_columns if '自选' in col or '加' in col or '人数' in col]
        logger.info(f"找到的自选列: {attention_columns}")
        
        # 如果找不到精确匹配的列名，尝试使用模糊匹配的列名
        if '标的代码' not in actual_columns and code_columns:
            logger.info(f"使用替代代码列: {code_columns[0]}")
            df = df.rename(columns={code_columns[0]: '标的代码'})
            actual_columns = list(df.columns)
        
        if '加自选人数' not in actual_columns and attention_columns:
            logger.info(f"使用替代自选人数列: {attention_columns[0]}")
            df = df.rename(columns={attention_columns[0]: '加自选人数'})
            actual_columns = list(df.columns)
        
        # 再次检查所需列是否存在
        missing_columns = [col for col in required_columns if col not in actual_columns]
        
        if missing_columns:
            logger.error(f"未找到必要的列: {missing_columns}")
            logger.error(f"文件中的所有列: {actual_columns}")
            return
        
        # 重命名列
        rename_map = {
            '标的代码': 'code',
            '加自选人数': 'attention_count'
        }
        df = df.rename(columns=rename_map)
        
        # 标准化ETF代码
        df['code'] = df['code'].apply(normalize_etf_code)
        
        # 转换数据类型
        df['attention_count'] = pd.to_numeric(df['attention_count'], errors='coerce').fillna(0).astype(int)
        
        # 添加日期字段
        df['date'] = date
        
        # 打印处理后的数据帮助诊断
        logger.info(f"处理后列名: {list(df.columns)}")
        logger.info(f"处理后数据前5行:\n{df.head()}")
        
        # 过滤有效数据
        valid_data = df[['code', 'attention_count', 'date']].dropna(subset=['code'])
        
        # 添加更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 插入数据
        for _, row in valid_data.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO etf_attention_history (code, attention_count, date, update_time)
                    VALUES (?, ?, ?, ?)
                """, (row['code'], row['attention_count'], date, current_time))
            except Exception as e:
                logger.error(f"插入自选数据时出错: {str(e)}")
        
        db.conn.commit()
        logger.info(f"成功导入 {len(valid_data)} 条 {date} 的ETF自选历史数据")
    
    except Exception as e:
        logger.error(f"处理ETF自选数据文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def process_etf_holders_file(file_path, date, db):
    """处理ETF持有人数据文件并导入数据到历史表"""
    logger.info(f"处理ETF持有人数据文件: {file_path}, 日期: {date}")
    try:
        # 检查该日期的数据是否已经存在
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM etf_holders_history WHERE date = ?", (date,))
        if cursor.fetchone()[0] > 0:
            logger.info(f"日期 {date} 的ETF持有人历史数据已存在，跳过导入")
            return
        
        # 读取Excel文件，优先尝试"客户ETF保有量"工作表
        df = read_excel_with_enhanced_logic(file_path, sheet_name='客户ETF保有量')
        if df is None:
            return
        
        # 确保所需列存在
        required_columns = ['标的代码', '持仓客户数', '持仓市值']
        if '持仓份额' in df.columns:
            required_columns.append('持仓份额')
            
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Excel文件缺少以下列: {missing_columns}")
            logger.error(f"实际列名: {list(df.columns)}")
            
            # 尝试查找替代列
            if '标的代码' in missing_columns:
                code_columns = [col for col in df.columns if '代码' in str(col)]
                if code_columns:
                    df = df.rename(columns={code_columns[0]: '标的代码'})
                    missing_columns.remove('标的代码')
            
            if '持仓客户数' in missing_columns:
                holder_columns = [col for col in df.columns if ('持' in str(col) and '客户' in str(col)) or '客户数' in str(col)]
                if holder_columns:
                    df = df.rename(columns={holder_columns[0]: '持仓客户数'})
                    missing_columns.remove('持仓客户数')
            
            if '持仓市值' in missing_columns:
                value_columns = [col for col in df.columns if '市值' in str(col) or '持仓市值' in str(col)]
                if value_columns:
                    df = df.rename(columns={value_columns[0]: '持仓市值'})
                    missing_columns.remove('持仓市值')
            
            # 如果仍然缺少必要列，则返回
            if '标的代码' in missing_columns or '持仓客户数' in missing_columns or '持仓市值' in missing_columns:
                logger.error(f"无法找到必要的替代列，放弃处理此文件")
                return
        
        # 重命名列
        rename_map = {
            '标的代码': 'code',
            '持仓客户数': 'holder_count',
            '持仓市值': 'holding_value'
        }
        
        if '持仓份额' in df.columns:
            rename_map['持仓份额'] = 'holding_amount'
            
        df = df.rename(columns=rename_map)
        
        # 标准化ETF代码
        df['code'] = df['code'].apply(normalize_etf_code)
        
        # 转换数据类型
        df['holder_count'] = pd.to_numeric(df['holder_count'], errors='coerce').fillna(0).astype(int)
        df['holding_value'] = pd.to_numeric(df['holding_value'], errors='coerce').fillna(0).astype(float)
        
        if 'holding_amount' in df.columns:
            df['holding_amount'] = pd.to_numeric(df['holding_amount'], errors='coerce').fillna(0).astype(float)
        else:
            # 如果没有持仓份额列，将字段设为0而不是使用持仓市值
            df['holding_amount'] = 0
        
        # 添加日期字段
        df['date'] = date
        
        # 打印处理后的数据帮助诊断
        logger.info(f"处理后列名: {list(df.columns)}")
        logger.info(f"处理后数据前5行:\n{df.head()}")
        
        # 过滤有效数据
        valid_data = df[['code', 'holder_count', 'holding_amount', 'holding_value', 'date']].dropna(subset=['code'])
        
        # 添加更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 插入数据
        for _, row in valid_data.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO etf_holders_history (code, holder_count, holding_amount, date, update_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['code'], row['holder_count'], row['holding_amount'], row['date'], current_time))
            except Exception as e:
                logger.error(f"插入持有人数据时出错: {str(e)}")
        
        db.conn.commit()
        logger.info(f"成功导入 {len(valid_data)} 条 {date} 的ETF持有人历史数据")
    
    except Exception as e:
        logger.error(f"处理ETF持有人数据文件 {file_path} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

def import_all_history_data():
    """导入所有历史数据"""
    logger.info("开始导入所有历史数据...")
    
    # 连接数据库
    db = Database()
    
    # 确保历史表存在
    cursor = db.conn.cursor()
    
    # 创建ETF自选历史表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf_attention_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            attention_count INTEGER,
            date TEXT,
            update_time TIMESTAMP
        )
    """)
    
    # 创建ETF持有人历史表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf_holders_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            holder_count INTEGER,
            holding_amount REAL,
            holding_value REAL,
            date TEXT,
            update_time TIMESTAMP
        )
    """)
    
    # 创建ETF规模历史表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf_fund_size_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            fund_size REAL,
            date TEXT,
            update_time TIMESTAMP
        )
    """)
    
    # 获取所有数据文件
    data_files = get_all_data_files()
    
    # 处理ETF基本信息文件
    for file_path, date in data_files['etf_info']:
        process_etf_info_file(file_path, date, db)
    
    # 处理ETF自选数据文件
    for file_path, date in data_files['etf_attention']:
        process_etf_attention_file(file_path, date, db)
    
    # 处理ETF持有人数据文件
    for file_path, date in data_files['etf_holders']:
        process_etf_holders_file(file_path, date, db)
    
    # 查询并显示导入结果
    cursor.execute("SELECT date, COUNT(*) FROM etf_fund_size_history GROUP BY date ORDER BY date")
    fund_size_dates = cursor.fetchall()
    logger.info("\nETF规模历史数据日期统计:")
    for date, count in fund_size_dates:
        logger.info(f"  - {date}: {count}条记录")
    
    cursor.execute("SELECT date, COUNT(*) FROM etf_attention_history GROUP BY date ORDER BY date")
    attention_dates = cursor.fetchall()
    logger.info("\nETF自选历史数据日期统计:")
    for date, count in attention_dates:
        logger.info(f"  - {date}: {count}条记录")
    
    cursor.execute("SELECT date, COUNT(*) FROM etf_holders_history GROUP BY date ORDER BY date")
    holders_dates = cursor.fetchall()
    logger.info("\nETF持有人历史数据日期统计:")
    for date, count in holders_dates:
        logger.info(f"  - {date}: {count}条记录")
    
    logger.info("\n所有历史数据导入完成")

if __name__ == "__main__":
    import_all_history_data() 