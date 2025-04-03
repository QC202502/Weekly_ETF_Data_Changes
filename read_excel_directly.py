#!/usr/bin/env python3
"""
使用pyexcel-xls和pyexcel-xlsx直接读取Excel文件
"""

import os
import sys
import pandas as pd
from datetime import datetime
import subprocess

def install_package(package):
    """安装依赖包"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 尝试导入pyexcel包，如果不存在则安装
try:
    import pyexcel
except ImportError:
    print("正在安装pyexcel...")
    install_package("pyexcel")
    import pyexcel

# 尝试导入pyexcel-xlsx包，如果不存在则安装
try:
    import pyexcel_xlsx
except ImportError:
    print("正在安装pyexcel-xlsx...")
    install_package("pyexcel-xlsx")
    import pyexcel_xlsx

# 尝试导入pyexcel-xls包，如果不存在则安装
try:
    import pyexcel_xls
except ImportError:
    print("正在安装pyexcel-xls...")
    install_package("pyexcel-xls")
    import pyexcel_xls

try:
    import pyexcel_io
except ImportError:
    print("正在安装pyexcel-io...")
    install_package("pyexcel-io")
    import pyexcel_io

# 尝试导入压缩文件处理库
try:
    import zipfile
except ImportError:
    print("正在安装zipfile...")
    install_package("zipfile")
    import zipfile

def is_valid_xlsx(file_path):
    """检查文件是否是有效的XLSX格式"""
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            # XLSX文件必须包含这些文件
            required_files = ['[Content_Types].xml', '_rels/.rels', 'xl/workbook.xml']
            if not all(item in zf.namelist() for item in required_files):
                print(f"XLSX缺少必要的文件结构")
                return False
            
            # 检查工作表
            if 'xl/worksheets/sheet1.xml' not in zf.namelist():
                print(f"XLSX中找不到sheet1.xml")
                return False
            
            return True
    except zipfile.BadZipFile:
        print(f"文件不是有效的ZIP/XLSX格式")
        return False
    except Exception as e:
        print(f"验证XLSX文件时出错: {str(e)}")
        return False

def read_with_pyexcel(file_path):
    """使用pyexcel读取Excel文件"""
    print(f"使用pyexcel读取: {file_path}")
    try:
        # 使用pyexcel读取Excel文件
        data = pyexcel.get_array(file_name=file_path)
        
        if len(data) > 0:
            print(f"总行数: {len(data)}")
            print(f"第一行: {data[0]}")
            
            # 获取列名（第一行）
            headers = data[0] if data else []
            
            # 创建数据列表（跳过第一行）
            rows = []
            for row in data[1:]:
                # 创建行数据字典
                row_data = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_data[headers[i]] = value
                    else:
                        row_data[f"Column_{i}"] = value
                rows.append(row_data)
            
            # 创建DataFrame
            df = pd.DataFrame(rows)
            
            print(f"读取到 {len(df)} 行数据")
            return df
        else:
            print("文件内容为空")
            return None
    except Exception as e:
        print(f"使用pyexcel读取Excel文件时出错: {str(e)}")
        return None

def read_with_binary_parsing(file_path):
    """尝试直接读取XLSX文件二进制内容"""
    print(f"尝试二进制直接解析: {file_path}")
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # 打印所有文件
            print("ZIP中的文件列表:")
            for file in zip_ref.namelist():
                print(f"  - {file}")
            
            # 读取工作表列表
            if 'xl/workbook.xml' in zip_ref.namelist():
                with zip_ref.open('xl/workbook.xml') as f:
                    wb_content = f.read().decode('utf-8')
                    print("工作簿内容片段:")
                    print(wb_content[:200])
            
            # 读取第一个工作表
            sheet_files = [f for f in zip_ref.namelist() if f.startswith('xl/worksheets/sheet')]
            if sheet_files:
                with zip_ref.open(sheet_files[0]) as f:
                    sheet_content = f.read().decode('utf-8')
                    print(f"工作表内容片段 ({sheet_files[0]}):")
                    print(sheet_content[:200])
            
            # 读取共享字符串
            if 'xl/sharedStrings.xml' in zip_ref.namelist():
                with zip_ref.open('xl/sharedStrings.xml') as f:
                    strings_content = f.read().decode('utf-8')
                    print("共享字符串内容片段:")
                    print(strings_content[:200])
        
        return None
    except Exception as e:
        print(f"二进制解析XLSX文件时出错: {str(e)}")
        return None

def process_excel_files():
    """处理所有Excel文件"""
    # 查找所有自选人数和持有人数据文件
    data_dir = 'data'
    excel_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) 
                  if (f.endswith('.xlsx') or f.endswith('.xls'))]
    
    # 按名称排序
    excel_files.sort()
    
    for file_path in excel_files:
        print(f"\n=== 处理文件: {file_path} ===")
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        print(f"文件大小: {file_size / 1024:.2f} KB")
        
        # 检查文件格式是否有效
        if file_path.endswith('.xlsx'):
            if not is_valid_xlsx(file_path):
                print(f"文件 {file_path} 不是有效的XLSX格式")
                # 尝试二进制直接解析
                read_with_binary_parsing(file_path)
                continue
        
        # 尝试使用pyexcel读取
        df = read_with_pyexcel(file_path)
        
        if df is not None and len(df) > 0:
            # 打印列名
            print(f"列名: {df.columns.tolist()}")
            
            # 打印前5行数据
            print("数据预览:")
            print(df.head())
        else:
            print(f"无法读取 {file_path} 中的数据")

if __name__ == "__main__":
    process_excel_files() 