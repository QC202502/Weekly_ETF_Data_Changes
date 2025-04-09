#!/usr/bin/env python3
"""
从历史数据中更新ETF基本信息

此脚本从ETF历史数据表中提取所有ETF代码，并更新etf_info表
解决数据库中只有13条ETF基本信息记录的问题
"""

import os
import pandas as pd
from datetime import datetime
from database.models import Database

def extract_etf_codes_from_history(db):
    """从历史数据表中提取所有不同的ETF代码"""
    cursor = db.conn.cursor()
    
    # 查询不同的ETF代码
    cursor.execute("""
        SELECT DISTINCT code FROM (
            SELECT code FROM etf_attention_history
            UNION
            SELECT code FROM etf_holders_history
            UNION
            SELECT code FROM etf_fund_size_history
        )
    """)
    
    # 获取所有代码
    codes = [row[0] for row in cursor.fetchall()]
    print(f"从历史数据中提取了 {len(codes)} 个不同的ETF代码")
    
    return codes

def get_latest_etf_data(db, code):
    """获取ETF的最新数据"""
    cursor = db.conn.cursor()
    result = {}
    
    # 获取最新的自选人数
    cursor.execute("""
        SELECT attention_count, date FROM etf_attention_history
        WHERE code = ?
        ORDER BY date DESC LIMIT 1
    """, (code,))
    attention = cursor.fetchone()
    if attention:
        result['total_holder_count'] = attention[0]
    
    # 获取最新的规模数据
    cursor.execute("""
        SELECT fund_size, date FROM etf_fund_size_history
        WHERE code = ?
        ORDER BY date DESC LIMIT 1
    """, (code,))
    fund_size = cursor.fetchone()
    if fund_size:
        result['fund_size'] = fund_size[0]
    
    return result

def update_etf_info_table(db, codes):
    """更新etf_info表"""
    cursor = db.conn.cursor()
    
    # 获取当前的ETF信息
    cursor.execute("SELECT code FROM etf_info")
    existing_codes = [row[0] for row in cursor.fetchall()]
    print(f"当前etf_info表中有 {len(existing_codes)} 条记录")
    
    # 获取当前时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 插入或更新ETF信息
    new_count = 0
    update_count = 0
    
    for code in codes:
        # 从历史数据获取ETF的最新数据
        latest_data = get_latest_etf_data(db, code)
        
        if not latest_data:
            print(f"没有找到ETF {code} 的历史数据，跳过")
            continue
        
        # 构建数据
        etf_data = {
            'fund_size': latest_data.get('fund_size', 0),
            'total_holder_count': latest_data.get('total_holder_count', 0),
            'update_time': current_time
        }
        
        if code in existing_codes:
            # 更新现有记录
            try:
                cursor.execute("""
                    UPDATE etf_info SET
                    fund_size = ?,
                    total_holder_count = ?,
                    update_time = ?
                    WHERE code = ?
                """, (etf_data['fund_size'], etf_data['total_holder_count'], etf_data['update_time'], code))
                update_count += 1
            except Exception as e:
                print(f"更新ETF {code} 时出错: {str(e)}")
        else:
            # 插入新记录
            try:
                # 对于新记录，使用一些默认值
                name = f"ETF-{code}"  # 默认名称
                manager = "未知"  # 默认管理人
                management_fee_rate = 0.5  # 默认管理费率
                tracking_error = 1.0  # 默认跟踪误差
                tracking_index_code = ""  # 默认跟踪指数代码
                tracking_index_name = "未知指数"  # 默认跟踪指数名称
                
                cursor.execute("""
                    INSERT INTO etf_info (
                        code, name, manager, fund_size, management_fee_rate, tracking_error,
                        tracking_index_code, tracking_index_name, total_holder_count, update_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    code, name, manager, etf_data['fund_size'], 
                    management_fee_rate, tracking_error, 
                    tracking_index_code, tracking_index_name,
                    etf_data['total_holder_count'], etf_data['update_time']
                ))
                new_count += 1
            except Exception as e:
                print(f"插入ETF {code} 时出错: {str(e)}")
    
    # 提交事务
    db.conn.commit()
    print(f"更新了 {update_count} 条ETF记录，新增了 {new_count} 条ETF记录")
    
    return new_count + update_count

def update_etf_names_from_data_files(db):
    """从ETF_DATA文件中更新ETF名称和基金公司信息"""
    print("\n开始从数据文件更新ETF名称和基金公司信息...")
    
    # 查找所有ETF_DATA文件
    data_dir = 'data'
    etf_data_files = [f for f in os.listdir(data_dir) if 'ETF_DATA' in f and f.endswith('.xlsx')]
    etf_data_files.sort(reverse=True)  # 按文件名倒序排列，使用最新的文件
    
    if not etf_data_files:
        print("未找到ETF_DATA文件，无法更新ETF名称")
        return 0
    
    # 使用最新的文件
    latest_file = etf_data_files[0]
    file_path = os.path.join(data_dir, latest_file)
    print(f"使用文件 {latest_file} 更新ETF名称和基金公司信息")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path, engine='xlrd')
        print(f"读取了 {len(df)} 行数据")
        print(f"列名: {df.columns.tolist()}")
        
        # 设置已知的列名
        code_col = '证券代码'
        name_col = '证券简称'
        company_col = '基金管理人'
        
        if code_col not in df.columns:
            print(f"列 '{code_col}' 不存在")
            return 0
            
        if name_col not in df.columns:
            print(f"列 '{name_col}' 不存在")
            name_col = None
            
        if company_col not in df.columns:
            print(f"列 '{company_col}' 不存在")
            # 尝试使用备用列名
            if '基金管理人简称' in df.columns:
                company_col = '基金管理人简称'
                print(f"使用备用公司列: {company_col}")
            else:
                company_col = None
        
        print(f"使用列: 代码={code_col}, 名称={name_col}, 公司={company_col}")
        
        # 确保代码列是字符串并去除空白
        df['code'] = df[code_col].astype(str).str.strip()
        
        # 提取6位数字代码
        df['code'] = df['code'].str.extract(r'(\d{6})').fillna('')
        
        # 过滤掉无效代码
        df = df[df['code'] != '']
        print(f"有效ETF代码数量: {len(df)}")
        
        # 更新ETF信息
        cursor = db.conn.cursor()
        update_count = 0
        
        for _, row in df.iterrows():
            code = row['code']
            
            # 构建更新参数和SQL
            update_params = []
            update_sql_parts = []
            
            # 如果有名称列，添加名称更新
            if name_col and pd.notna(row[name_col]):
                name = str(row[name_col]).strip()
                update_sql_parts.append("name = ?")
                update_params.append(name)
            
            # 如果有公司列，添加公司更新
            if company_col and pd.notna(row[company_col]):
                manager = str(row[company_col]).strip()
                update_sql_parts.append("manager = ?")
                update_params.append(manager)
            
            # 如果没有要更新的内容，跳过
            if not update_sql_parts:
                continue
            
            # 构建SQL语句
            update_sql = f"UPDATE etf_info SET {', '.join(update_sql_parts)} WHERE code = ?"
            update_params.append(code)
            
            try:
                cursor.execute(update_sql, update_params)
                if cursor.rowcount > 0:
                    update_count += 1
            except Exception as e:
                print(f"更新ETF {code} 的信息时出错: {str(e)}")
        
        # 提交事务
        db.conn.commit()
        print(f"从数据文件更新了 {update_count} 条ETF的名称和基金公司信息")
        
        return update_count
    
    except Exception as e:
        print(f"处理ETF_DATA文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """主函数"""
    # 创建数据库连接
    db = Database()
    
    # 从历史数据中提取ETF代码
    codes = extract_etf_codes_from_history(db)
    
    # 更新etf_info表
    updated_count = update_etf_info_table(db, codes)
    
    # 从数据文件更新ETF名称和基金公司信息
    name_update_count = update_etf_names_from_data_files(db)
    
    # 检查更新结果
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM etf_info")
    total_count = cursor.fetchone()[0]
    
    print(f"\n更新完成！")
    print(f"etf_info表中现在有 {total_count} 条记录")
    
    # 关闭数据库连接
    db.close()

if __name__ == "__main__":
    main() 