#!/usr/bin/env python3
"""
导入市场可交易指数数据

此脚本用于将市场可交易指数Excel文件的数据导入到SQLite数据库
"""

import os
import sys
import pandas as pd
import sqlite3
from datetime import datetime
import glob
import re
import logging
import traceback

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='index_import.log'
)
logger = logging.getLogger('index_importer')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# 数据库路径
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DATABASE_PATH = os.path.join(DATA_DIR, 'etf_data.db')

def find_latest_file(pattern):
    """查找最新的文件"""
    try:
        files = glob.glob(os.path.join(DATA_DIR, pattern))
        if not files:
            logger.warning(f"未找到匹配 {pattern} 的文件")
            return None
        
        # 按文件修改时间排序，返回最新的
        return sorted(files, key=os.path.getmtime)[-1]
    except Exception as e:
        logger.error(f"查找文件时出错: {str(e)}")
        return None

def import_market_index():
    """导入市场可交易指数数据"""
    try:
        logger.info("开始导入市场可交易指数数据...")
        
        # 查找最新的市场可交易指数文件
        index_file = find_latest_file("市场可交易指数*.xlsx")
        if not index_file:
            logger.error("未找到市场可交易指数文件")
            return False
        
        logger.info(f"使用文件: {index_file}")
        
        # 读取Excel文件
        df = pd.read_excel(index_file, engine='openpyxl')
        logger.info(f"成功读取市场可交易指数数据，共 {len(df)} 行")
        
        # 检查必要的列
        required_columns = ['证券代码', '证券简称', '证券简介']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Excel文件中缺少必要的列: {col}")
                return False
        
        # 将列名映射到数据库字段
        column_mapping = {
            '证券代码': 'index_code',
            '证券简称': 'index_name',
            '证券简介': 'index_intro',
            '发布机构': 'publisher',
            '成份个数': 'components_count',
            '基期': 'base_date',
            '基点': 'base_point',
            '交易币种': 'currency'
        }
        
        # 重命名列
        renamed_columns = {}
        for excel_col, db_col in column_mapping.items():
            if excel_col in df.columns:
                renamed_columns[excel_col] = db_col
        
        df = df.rename(columns=renamed_columns)
        
        # 添加更新时间列
        df['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 连接数据库
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 创建市场可交易指数表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_index (
                index_code TEXT PRIMARY KEY,
                index_name TEXT,
                index_intro TEXT,
                publisher TEXT,
                components_count INTEGER,
                weight_method TEXT,
                base_date TEXT,
                base_point REAL,
                currency TEXT,
                update_time TIMESTAMP
            )
        """)
        
        # 保存数据 - 分两组处理：字母开头的指数代码和数字开头的指数代码
        letter_codes = df[~df['index_code'].str.match(r'^\d', na=False)]
        number_codes = df[df['index_code'].str.match(r'^\d', na=False)]
        
        logger.info(f"总记录数: {len(df)}, 字母开头记录: {len(letter_codes)}, 数字开头记录: {len(number_codes)}")
        
        # 处理字母开头的指数代码
        inserted_count, updated_count, error_count = process_index_data(conn, cursor, letter_codes, column_mapping)
        
        # 处理数字开头的指数代码
        inserted_count2, updated_count2, error_count2 = process_index_data(conn, cursor, number_codes, column_mapping)
        
        # 合计统计
        total_inserted = inserted_count + inserted_count2
        total_updated = updated_count + updated_count2
        total_errors = error_count + error_count2
        
        # 提交事务
        conn.commit()
        
        logger.info(f"市场可交易指数数据导入完成 - 新增: {total_inserted}, 更新: {total_updated}, 错误: {total_errors}")
        return True
        
    except Exception as e:
        logger.error(f"导入市场可交易指数数据时出错: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def process_index_data(conn, cursor, df, column_mapping):
    """处理指数数据的辅助函数"""
    inserted_count = 0
    updated_count = 0
    error_count = 0
    
    for _, row in df.iterrows():
        try:
            # 必须有指数代码
            if pd.isna(row.get('index_code')):
                continue
            
            # 检查这个指数代码是否已存在
            cursor.execute("SELECT 1 FROM market_index WHERE index_code = ?", (str(row['index_code']),))
            exists = cursor.fetchone()
            
            # 准备插入或更新的字段和值
            fields = []
            values = []
            
            # 处理每个列
            for db_col in column_mapping.values():
                if db_col in row:
                    fields.append(db_col)
                    value = row[db_col]
                    
                    # 确保特殊列的类型正确
                    if pd.isna(value):
                        value = None
                    elif db_col == 'index_code':
                        value = str(value)  # 确保指数代码是字符串
                    elif db_col == 'components_count':
                        try:
                            if value is not None:
                                value = int(float(value))
                        except (ValueError, TypeError):
                            value = None
                    elif db_col == 'base_point':
                        try:
                            if value is not None:
                                value = float(value)
                        except (ValueError, TypeError):
                            value = None
                    elif db_col == 'base_date':
                        # 将 Timestamp 转换为字符串
                        if isinstance(value, pd.Timestamp):
                            value = value.strftime('%Y-%m-%d')
                    
                    values.append(value)
            
            # 添加weight_method字段，设为NULL
            fields.append('weight_method')
            values.append(None)
            
            # 添加更新时间
            fields.append('update_time')
            values.append(row['update_time'])
            
            if exists:
                # 更新已存在的记录
                set_clause = ', '.join([f"{field} = ?" for field in fields])
                update_sql = f"UPDATE market_index SET {set_clause} WHERE index_code = ?"
                values.append(str(row['index_code']))  # 添加WHERE条件的值
                cursor.execute(update_sql, values)
                updated_count += 1
            else:
                # 插入新记录
                placeholders = ', '.join(['?'] * len(fields))
                fields_str = ', '.join(fields)
                insert_sql = f"INSERT INTO market_index ({fields_str}) VALUES ({placeholders})"
                cursor.execute(insert_sql, values)
                inserted_count += 1
                
        except Exception as e:
            error_count += 1
            logger.error(f"处理行 {_} (指数代码: {row.get('index_code', 'N/A')}) 时出错: {str(e)}")
            
            # 详细记录错误
            if 'index_code' in row:
                logger.error(f"出错的指数代码: {row['index_code']}, 数据类型: {type(row['index_code'])}")
                for i, (k, v) in enumerate(zip(fields, values)):
                    logger.error(f"字段 {k} (参数 {i+1}): {v} (类型: {type(v)})")
            
            traceback.print_exc()
    
    return inserted_count, updated_count, error_count

def main():
    """主函数"""
    try:
        # 导入市场可交易指数数据
        success = import_market_index()
        if success:
            logger.info("市场可交易指数数据导入成功")
        else:
            logger.error("市场可交易指数数据导入失败")
            
    except Exception as e:
        logger.error(f"运行中出错: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 