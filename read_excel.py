import pandas as pd
import os

try:
    file_path = 'data/客户ETF保有量20250331.xlsx'
    print(f"文件路径: {file_path}")
    print(f"文件存在: {os.path.exists(file_path)}")
    print(f"文件大小: {os.path.getsize(file_path)} 字节")
    
    # 尝试读取文件
    df = pd.read_excel(file_path, engine='openpyxl')
    
    # 显示文件信息
    print(f"数据形状: {df.shape}")
    print(f"列名: {df.columns.tolist()}")
    print("前5行数据:")
    print(df.head(5))
    
except Exception as e:
    print(f"读取错误: {e}")
    
    # 尝试使用另一个引擎
    try:
        print("\n尝试使用xlrd引擎:")
        df = pd.read_excel(file_path, engine='xlrd')
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        print("前5行数据:")
        print(df.head(5))
    except Exception as e2:
        print(f"xlrd读取错误: {e2}") 