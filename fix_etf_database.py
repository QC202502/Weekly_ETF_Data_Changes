#!/usr/bin/env python3
"""
ETF数据库修复脚本

此脚本用于修复ETF数据库中的问题：
1. 修复etf_info表中由于证券代码格式不一致导致的重复数据
2. 导入商务协议Excel文件数据
3. 补充etf_attention表中缺失的历史数据

用法:
    python fix_etf_database.py
"""

import os
import sys
import glob
import pandas as pd
import sqlite3
from datetime import datetime

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import Database

def normalize_etf_code(code):
    """
    标准化ETF代码，去除.SH/.SZ后缀
    
    参数:
        code: ETF代码
    返回:
        标准化后的ETF代码
    """
    if not code:
        return code
    
    code = str(code).strip()
    # 去除.SH/.SZ后缀
    code = code.replace('.SH', '').replace('.SZ', '')
    # 确保是6位数字
    return code.zfill(6)

def fix_etf_info_duplicates():
    """
    修复etf_info表中由于证券代码格式不一致导致的重复数据
    """
    print("开始修复etf_info表中的重复数据...")
    
    # 连接数据库
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/etf_data.db')
    conn = sqlite3.connect(db_path)
    
    # 注册normalize_etf_code函数到SQLite
    conn.create_function("normalize_etf_code", 1, normalize_etf_code)
    
    try:
        # 获取所有ETF信息
        df = pd.read_sql("SELECT * FROM etf_info", conn)
        print(f"原始etf_info表中共有{len(df)}条记录")
        
        # 标准化证券代码
        df['normalized_code'] = df['code'].apply(normalize_etf_code)
        
        # 检查重复
        duplicates = df['normalized_code'].duplicated(keep=False)
        duplicate_codes = df[duplicates]['normalized_code'].unique()
        print(f"发现{len(duplicate_codes)}个重复的证券代码")
        
        if len(duplicate_codes) > 0:
            # 创建新表存储修复后的数据
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS etf_info_fixed (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                manager TEXT,
                index_code TEXT,
                index_name TEXT,
                fee_rate REAL,
                is_business INTEGER DEFAULT 0,
                business_share_ratio REAL DEFAULT 0.3,
                business_start_date TEXT,
                business_end_date TEXT,
                index_category_level1 TEXT,
                index_category_level2 TEXT,
                index_category_level3 TEXT,
                updated_at TEXT NOT NULL
            )
            ''')
            
            # 处理非重复记录
            non_duplicates = df[~df['normalized_code'].isin(duplicate_codes)]
            for _, row in non_duplicates.iterrows():
                cursor.execute('''
                INSERT INTO etf_info_fixed (
                    code, name, manager, index_code, index_name, fee_rate,
                    is_business, business_share_ratio, business_start_date, business_end_date,
                    index_category_level1, index_category_level2, index_category_level3, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['normalized_code'], row['name'], row['manager'], row['index_code'], row['index_name'], row['fee_rate'],
                    row['is_business'], row['business_share_ratio'], row['business_start_date'], row['business_end_date'],
                    row['index_category_level1'], row['index_category_level2'], row['index_category_level3'], row['updated_at']
                ))
            
            # 处理重复记录，保留最新的一条
            for code in duplicate_codes:
                duplicate_rows = df[df['normalized_code'] == code].sort_values('updated_at', ascending=False)
                latest_row = duplicate_rows.iloc[0]
                
                cursor.execute('''
                INSERT INTO etf_info_fixed (
                    code, name, manager, index_code, index_name, fee_rate,
                    is_business, business_share_ratio, business_start_date, business_end_date,
                    index_category_level1, index_category_level2, index_category_level3, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    code, latest_row['name'], latest_row['manager'], latest_row['index_code'], latest_row['index_name'], latest_row['fee_rate'],
                    latest_row['is_business'], latest_row['business_share_ratio'], latest_row['business_start_date'], latest_row['business_end_date'],
                    latest_row['index_category_level1'], latest_row['index_category_level2'], latest_row['index_category_level3'], latest_row['updated_at']
                ))
            
            # 更新外键约束的表
            # 更新etf_price表
            # 先检查etf_price表结构
            cursor.execute("PRAGMA table_info(etf_price)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 创建新表，确保包含所有必要的字段
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS etf_price_fixed (
                code TEXT,
                date TEXT,
                open_price REAL,
                close_price REAL,
                high_price REAL,
                low_price REAL,
                volume REAL,
                amount REAL,
                change_percent REAL,
                turnover_rate REAL,
                trade_count INTEGER,
                PRIMARY KEY (code, date),
                FOREIGN KEY (code) REFERENCES etf_info_fixed(code)
            )
            ''')
            
            cursor.execute('''
            INSERT INTO etf_price_fixed (code, date, open_price, close_price, high_price, low_price, volume, amount, change_percent, turnover_rate, trade_count)
            SELECT p.code, p.date, p.open_price, p.close_price, p.high_price, p.low_price, p.volume, p.amount, p.change_percent, p.turnover_rate, p.trade_count
            FROM etf_price p
            JOIN etf_info_fixed f ON normalize_etf_code(p.code) = f.code
            ''')
            
            # 更新etf_attention表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS etf_attention_fixed (
                code TEXT,
                date TEXT,
                attention_count INTEGER,
                PRIMARY KEY (code, date),
                FOREIGN KEY (code) REFERENCES etf_info_fixed(code)
            )
            ''')
            
            cursor.execute('''
            INSERT INTO etf_attention_fixed (code, date, attention_count)
            SELECT a.code, a.date, a.attention_count
            FROM etf_attention a
            JOIN etf_info_fixed f ON normalize_etf_code(a.code) = f.code
            ''')
            
            # 更新etf_holders表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS etf_holders_fixed (
                code TEXT,
                date TEXT,
                holder_count INTEGER,
                holding_amount REAL,
                holding_value REAL,
                PRIMARY KEY (code, date),
                FOREIGN KEY (code) REFERENCES etf_info_fixed(code)
            )
            ''')
            
            cursor.execute('''
            INSERT INTO etf_holders_fixed (code, date, holder_count, holding_amount, holding_value)
            SELECT h.code, h.date, h.holder_count, h.holding_amount, h.holding_value
            FROM etf_holders h
            JOIN etf_info_fixed f ON normalize_etf_code(h.code) = f.code
            ''')
            
            # 备份原表并替换
            cursor.execute("ALTER TABLE etf_info RENAME TO etf_info_backup")
            cursor.execute("ALTER TABLE etf_info_fixed RENAME TO etf_info")
            
            cursor.execute("ALTER TABLE etf_price RENAME TO etf_price_backup")
            cursor.execute("ALTER TABLE etf_price_fixed RENAME TO etf_price")
            
            cursor.execute("ALTER TABLE etf_attention RENAME TO etf_attention_backup")
            cursor.execute("ALTER TABLE etf_attention_fixed RENAME TO etf_attention")
            
            cursor.execute("ALTER TABLE etf_holders RENAME TO etf_holders_backup")
            cursor.execute("ALTER TABLE etf_holders_fixed RENAME TO etf_holders")
            
            conn.commit()
            
            # 验证修复结果
            fixed_count = pd.read_sql("SELECT COUNT(*) FROM etf_info", conn).iloc[0, 0]
            print(f"修复后etf_info表中共有{fixed_count}条记录")
            print("etf_info表中的重复数据已修复")
        else:
            print("未发现重复数据，无需修复")
    
    except Exception as e:
        conn.rollback()
        print(f"修复etf_info表出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def import_business_etf_data():
    """
    导入商务协议Excel文件数据
    """
    print("\n开始导入商务协议Excel文件数据...")
    
    # 查找商务协议Excel文件
    business_files = glob.glob('/Users/admin/Downloads/ETF单产品商务协议*.xlsx')
    
    if not business_files:
        print("未找到商务协议Excel文件，请确保文件存在于/Users/admin/Downloads/目录下")
        return
    
    # 连接数据库
    db = Database()
    
    try:
        with db.connect() as conn:
            # 获取当前商务品信息
            current_business = pd.read_sql("SELECT code, is_business FROM etf_info WHERE is_business = 1", conn)
            print(f"当前数据库中有{len(current_business)}个商务品")
            
            # 读取商务协议Excel文件
            all_business_codes = set()
            for file_path in business_files:
                print(f"处理商务协议文件: {file_path}")
                try:
                    df = pd.read_excel(file_path, engine='openpyxl')
                    
                    # 查找包含产品代码的列
                    code_columns = [col for col in df.columns if '产品代码' in col or '证券代码' in col]
                    if not code_columns:
                        print(f"文件 {file_path} 中未找到产品代码列")
                        continue
                    
                    code_column = code_columns[0]
                    
                    # 提取产品代码并标准化
                    business_codes = df[code_column].dropna().astype(str)
                    business_codes = business_codes.apply(normalize_etf_code)
                    
                    # 添加到商务品集合
                    all_business_codes.update(business_codes)
                    
                    print(f"从文件 {file_path} 中提取了 {len(business_codes)} 个商务品代码")
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {str(e)}")
            
            # 更新数据库中的商务品标记
            cursor = conn.cursor()
            
            # 先将所有ETF设为非商务品
            cursor.execute("UPDATE etf_info SET is_business = 0")
            
            # 更新商务品标记
            for code in all_business_codes:
                cursor.execute("UPDATE etf_info SET is_business = 1 WHERE code = ?", (code,))
            
            conn.commit()
            
            # 验证更新结果
            updated_business = pd.read_sql("SELECT code FROM etf_info WHERE is_business = 1", conn)
            print(f"更新后数据库中有{len(updated_business)}个商务品")
            print("商务品数据已更新")
    
    except Exception as e:
        print(f"导入商务协议数据出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def fill_etf_attention_data():
    """
    补充etf_attention表中缺失的历史数据
    """
    print("\n开始补充etf_attention表中缺失的历史数据...")
    
    # 查找ETF自选人数文件
    attention_files = glob.glob('/Users/admin/Downloads/etf自选人数*.csv')
    
    if not attention_files:
        print("未找到ETF自选人数文件，请确保文件存在于/Users/admin/Downloads/目录下")
        return
    
    # 连接数据库
    db = Database()
    
    try:
        with db.connect() as conn:
            # 获取当前关注人数数据的日期
            current_dates = pd.read_sql("SELECT DISTINCT date FROM etf_attention", conn)
            current_date_set = set(current_dates['date'])
            print(f"当前数据库中有{len(current_date_set)}个日期的关注人数数据")
            
            # 处理每个自选人数文件
            for file_path in attention_files:
                # 从文件名提取日期
                filename = os.path.basename(file_path)
                date_str = filename.replace('etf自选人数', '').replace('.csv', '')
                
                try:
                    # 格式化日期
                    date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
                    
                    # 检查该日期的数据是否已存在
                    if date in current_date_set:
                        print(f"日期 {date} 的关注人数数据已存在，跳过")
                        continue
                    
                    print(f"处理日期 {date} 的关注人数数据")
                    
                    # 读取CSV文件
                    # 尝试多种编码
                    encodings = ['utf-8', 'gbk', 'gb18030', 'latin1']
                    df = None
                    
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding)
                            break
                        except:
                            continue
                    
                    if df is None:
                        print(f"无法读取文件 {file_path}，跳过")
                        continue
                    
                    # 查找证券代码和关注人数列
                    code_columns = [col for col in df.columns if 'CODE' in col.upper() or '代码' in col]
                    attention_columns = [col for col in df.columns if 'CNT' in col.upper() or '人数' in col]
                    
                    if not code_columns or not attention_columns:
                        print(f"文件 {file_path} 中未找到证券代码或关注人数列")
                        continue
                    
                    code_column = code_columns[0]
                    attention_column = attention_columns[0]
                    
                    # 标准化证券代码
                    df['code'] = df[code_column].astype(str).apply(normalize_etf_code)
                    
                    # 获取有效的ETF代码列表
                    valid_codes = pd.read_sql("SELECT code FROM etf_info", conn)['code'].tolist()
                    
                    # 过滤有效的ETF
                    df = df[df['code'].isin(valid_codes)]
                    
                    # 插入数据
                    cursor = conn.cursor()
                    for _, row in df.iterrows():
                        try:
                            attention_count = int(row[attention_column])
                            cursor.execute('''
                            INSERT OR REPLACE INTO etf_attention (code, date, attention_count)
                            VALUES (?, ?, ?)
                            ''', (row['code'], date, attention_count))
                        except:
                            continue
                    
                    conn.commit()
                    print(f"已导入 {len(df)} 条 {date} 的关注人数数据")
                    
                    # 更新当前日期集合
                    current_date_set.add(date)
                
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {str(e)}")
            
            # 验证更新结果
            updated_dates = pd.read_sql("SELECT DISTINCT date FROM etf_attention", conn)
            print(f"更新后数据库中有{len(updated_dates)}个日期的关注人数数据")
            print("关注人数数据已补充")
    
    except Exception as e:
        print(f"补充关注人数数据出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def update_import_excel_data_script():
    """
    更新import_excel_data.py脚本，添加证券代码标准化处理
    """
    print("\n开始更新import_excel_data.py脚本...")
    
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'import_excel_data.py')
    
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        
        # 检查是否已包含normalize_etf_code函数
        if 'def normalize_etf_code' in content:
            print("import_excel_data.py脚本已包含证券代码标准化处理，无需更新")
            return
        
        # 添加normalize_etf_code函数
        normalize_func = '''

def normalize_etf_code(code):
    """标准化ETF代码，去除.SH/.SZ后缀"""
    if not code:
        return code
    
    code = str(code).strip()
    # 去除.SH/.SZ后缀
    code = code.replace('.SH', '').replace('.SZ', '')
    # 确保是6位数字
    return code.zfill(6)
'''
        
        # 在import语句后插入normalize_etf_code函数
        import_index = content.find('from database.models import Database')
        if import_index == -1:
            print("无法在import_excel_data.py中找到适当的插入位置")
            return
        
        insert_index = content.find('\n', import_index) + 1
        new_content = content[:insert_index] + normalize_func + content[insert_index:]
        
        # 修改save_etf_info调用前的代码，添加证券代码标准化处理
        save_etf_info_index = new_content.find('db.save_etf_info(df)')
        if save_etf_info_index == -1:
            print("无法在import_excel_data.py中找到save_etf_info调用")
            return
        
        # 查找save_etf_info调用前的行
        line_start = new_content.rfind('\n', 0, save_etf_info_index) + 1
        
        # 添加证券代码标准化处理代码
        normalize_code = '''
        # 标准化证券代码，去除.SH/.SZ后缀
        df['证券代码'] = df['证券代码'].apply(normalize_etf_code)
        '''
        
        new_content = new_content[:line_start] + normalize_code + new_content[line_start:]
        
        # 保存修改后的脚本
        with open(script_path, 'w') as f:
            f.write(new_content)
        
        print("import_excel_data.py脚本已更新，添加了证券代码标准化处理")
    
    except Exception as e:
        print(f"更新import_excel_data.py脚本出错: {str(e)}")
        import traceback
        traceback.print_exc()

def update_etf_price_data():
    """
    从ETF_DATA_*.xlsx文件中更新涨跌幅、换手率、成交额和成交笔数数据
    """
    print("\n开始更新ETF价格数据...")
    
    # 查找ETF_DATA_*.xlsx文件
    etf_data_files = glob.glob('/Users/admin/Downloads/ETF_DATA_*.xlsx')
    
    if not etf_data_files:
        print("未找到ETF_DATA_*.xlsx文件，请确保文件存在于/Users/admin/Downloads/目录下")
        return
    
    # 连接数据库
    db = Database()
    
    try:
        with db.connect() as conn:
            # 处理每个ETF_DATA文件
            for file_path in etf_data_files:
                print(f"处理ETF数据文件: {file_path}")
                
                try:
                    # 从文件名提取日期
                    filename = os.path.basename(file_path)
                    date_str = filename.replace('ETF_DATA_', '').replace('.xlsx', '')
                    
                    # 读取Excel文件
                    df = pd.read_excel(file_path, sheet_name='万得', engine='openpyxl')
                    
                    # 标准化证券代码
                    df['证券代码'] = df['证券代码'].astype(str).apply(normalize_etf_code)
                    
                    # 查找涨跌幅、换手率、成交额和成交笔数列
                    price_columns = []
                    for col in df.columns:
                        if '涨跌幅' in col and '最新收盘日' in col:
                            df['涨跌幅'] = df[col]
                            price_columns.append(col)
                        elif '换手率' in col and '最新收盘日' in col:
                            df['换手率'] = df[col]
                            price_columns.append(col)
                        elif '成交额' in col and '最新收盘日' in col and '亿元' in col:
                            df['成交额'] = df[col]
                            price_columns.append(col)
                        elif '成交笔数' in col and '最新收盘日' in col:
                            df['成交笔数'] = df[col]
                            price_columns.append(col)
                    
                    if price_columns:
                        print(f"找到价格相关列: {', '.join(price_columns)}")
                        
                        # 保存ETF价格数据
                        db.save_etf_price(df, date_str)
                        print(f"已更新 {len(df)} 条ETF价格数据，日期：{date_str}")
                    else:
                        print(f"文件 {file_path} 中未找到价格相关列")
                
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {str(e)}")
            
            print("ETF价格数据已更新")
    
    except Exception as e:
        print(f"更新ETF价格数据出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    print("ETF数据库修复工具")
    print("-" * 50)
    
    # 修复etf_info表中的重复数据
    fix_etf_info_duplicates()
    
    # 导入商务协议Excel文件数据
    import_business_etf_data()
    
    # 补充etf_attention表中缺失的历史数据
    fill_etf_attention_data()
    
    # 更新ETF价格数据
    update_etf_price_data()
    
    # 更新import_excel_data.py脚本
    update_import_excel_data_script()
    
    print("-" * 50)
    print("ETF数据库修复完成")

if __name__ == "__main__":
    main()