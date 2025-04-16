#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
在ETF信息表中添加管理人简称字段
将从fund_manager生成简称并存储在manager_short字段中
"""

import sqlite3
import os
import sys
import pandas as pd
from datetime import datetime

# 数据库路径
DB_PATH = 'data/etf_data.db'

def get_manager_short(full_name):
    """基金管理人简称提取"""
    if pd.isna(full_name) or not full_name:
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

def add_manager_short_field():
    """添加manager_short字段到etf_info表"""
    print("开始添加管理人简称字段...")
    
    # 检查数据库是否存在
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库文件 {DB_PATH} 不存在!")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='etf_info'")
        if not cursor.fetchone():
            print("错误: etf_info表不存在!")
            conn.close()
            return False
        
        # 检查manager_short字段是否已存在
        cursor.execute("PRAGMA table_info(etf_info)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'manager_short' in columns:
            print("manager_short字段已存在，将更新现有数据")
        else:
            # 添加manager_short字段
            print("添加manager_short字段到etf_info表")
            cursor.execute("ALTER TABLE etf_info ADD COLUMN manager_short TEXT")
        
        # 获取所有ETF管理人数据
        cursor.execute("SELECT code, fund_manager FROM etf_info")
        etf_managers = cursor.fetchall()
        
        update_count = 0
        error_count = 0
        
        # 更新每条记录
        for code, manager in etf_managers:
            try:
                if manager:
                    short_name = get_manager_short(manager)
                    cursor.execute(
                        "UPDATE etf_info SET manager_short = ? WHERE code = ?",
                        (short_name, code)
                    )
                    update_count += 1
                else:
                    cursor.execute(
                        "UPDATE etf_info SET manager_short = '未知' WHERE code = ?",
                        (code,)
                    )
                    update_count += 1
            except Exception as e:
                print(f"更新ETF {code} 的管理人简称时出错: {str(e)}")
                error_count += 1
        
        # 提交事务
        conn.commit()
        
        print(f"成功更新 {update_count} 条ETF管理人简称记录")
        if error_count > 0:
            print(f"有 {error_count} 条记录更新失败")
        
        # 显示几条示例数据进行验证
        cursor.execute("""
            SELECT code, name, fund_manager, manager_short 
            FROM etf_info 
            LIMIT 10
        """)
        
        print("\n示例数据:")
        print("代码\t名称\t管理人\t管理人简称")
        for row in cursor.fetchall():
            print(f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}")
        
        # 关闭连接
        conn.close()
        return True
        
    except Exception as e:
        print(f"执行过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def modify_database_models():
    """修改Database类，确保创建表时包含manager_short字段"""
    print("开始修改数据库模型文件，更新表结构定义...")
    
    model_file = 'database/models.py'
    if not os.path.exists(model_file):
        print(f"错误: 数据库模型文件 {model_file} 不存在!")
        return False
    
    try:
        # 读取文件内容
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找创建etf_info表的SQL语句
        create_table_stmt = "CREATE TABLE etf_info"
        fund_manager_field = "fund_manager TEXT,"
        manager_short_field = "    manager_short TEXT,"
        
        # 检查是否已包含manager_short字段
        if "manager_short TEXT" in content:
            print("数据库模型已包含manager_short字段，无需修改")
            return True
        
        # 在fund_manager字段后添加manager_short字段
        new_content = content.replace(
            fund_manager_field, 
            fund_manager_field + "\n" + manager_short_field
        )
        
        # 写回文件
        with open(model_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"成功修改数据库模型文件 {model_file}")
        return True
        
    except Exception as e:
        print(f"修改数据库模型文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("==== ETF管理人简称字段添加工具 ====")
    print(f"数据库路径: {DB_PATH}")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)
    
    # 先修改模型文件，确保后续创建的表包含新字段
    if modify_database_models():
        print("数据库模型更新成功")
    else:
        print("数据库模型更新失败")
    
    # 添加字段并更新数据
    if add_manager_short_field():
        print("成功添加并更新管理人简称字段")
    else:
        print("添加管理人简称字段失败") 