import pandas as pd
from datetime import datetime
import glob
from pathlib import Path

def format_security_code(code):
    """格式化证券代码为6位字符串"""
    return str(code).strip().zfill(6)

# 获取所有ETF保有量文件并按日期排序
balance_files = glob.glob('/Users/admin/Downloads/etf保有量*.csv')

def extract_date(file_path):
    """从文件路径提取日期"""
    filename = file_path.split('/')[-1]
    date_str = filename.replace('etf保有量', '').replace('.csv', '')
    return datetime.strptime(date_str, '%Y%m%d')

# 创建带日期的文件列表并排序
file_date_pairs = sorted([(f, extract_date(f)) for f in balance_files], key=lambda x: x[1])

if len(file_date_pairs) < 2:
    raise ValueError("需要至少两个周期的ETF保有量文件进行分析")

# 获取最近两个文件路径和日期
previous_balance = file_date_pairs[-2]
current_balance = file_date_pairs[-1]

def get_customer_file(date_obj):
    """构造自选人数文件路径"""
    return f'/Users/admin/Downloads/etf自选人数{date_obj.strftime("%Y%m%d")}.csv'

# 加载四个核心数据文件
previous_date_str = previous_balance[1].strftime("%Y%m%d")
current_date_str = current_balance[1].strftime("%Y%m%d")

# 加载数据
previous_etf_balance = pd.read_csv(previous_balance[0], encoding='GBK')
current_etf_balance = pd.read_csv(current_balance[0], encoding='GBK')
previous_etf_customers = pd.read_csv(get_customer_file(previous_balance[1]), encoding='GBK')
current_etf_customers = pd.read_csv(get_customer_file(current_balance[1]), encoding='GBK')

# 加载最新Excel文件
excel_path = f'/Users/admin/Downloads/ETF_DATA_{current_date_str}.xlsx'
excel_data = pd.read_excel(excel_path, sheet_name='万得', engine='openpyxl', header=0)

# 统一列名处理
def clean_columns(df):
    df.columns = df.columns.str.replace(r'\s+', '', regex=True)
    return df

for df in [previous_etf_balance, current_etf_balance,
          previous_etf_customers, current_etf_customers, excel_data]:
    df = clean_columns(df)

# 证券代码标准化处理
def process_security_code(df, column='证券代码'):
    df[column] = df[column].astype(str)
    df[column] = df[column].str.replace(r'\.SH|\.SZ|\.0', '', regex=True)
    df[column] = df[column].apply(format_security_code)
    return df

previous_etf_balance = process_security_code(previous_etf_balance.rename(columns={'SEC_CODE':'证券代码'}))
current_etf_balance = process_security_code(current_etf_balance.rename(columns={'SEC_CODE':'证券代码'}))
previous_etf_customers = process_security_code(previous_etf_customers.rename(columns={'SECURITY_CODE':'证券代码'}))
current_etf_customers = process_security_code(current_etf_customers.rename(columns={'SECURITY_CODE':'证券代码'}))
excel_data = process_security_code(excel_data)

# 合并基础数据
def prepare_dataset(balance_df, customer_df, date_label):
    """合并保有量和关注人数数据"""
    customer_renamed = customer_df[['证券代码', 'CNT']].rename(columns={'CNT': f'关注人数（{date_label}）'})
    merged = pd.merge(balance_df, customer_renamed, on='证券代码', how='outer')
    return merged.rename(columns={
        'SEC_BAL': f'保有份额（{date_label}）',
        'MKT_VALUE': f'保有金额（{date_label}）',
        'CUST_CNT': f'持仓客户数（{date_label}）',
        'SEC_NAME': f'证券名称（{date_label}）'
    })

# 准备日期标签
prev_date_label = previous_balance[1].strftime("%m月%d日")
curr_date_label = current_balance[1].strftime("%m月%d日")

previous_data = prepare_dataset(previous_etf_balance, previous_etf_customers, prev_date_label)
current_data = prepare_dataset(current_etf_balance, current_etf_customers, curr_date_label)

# 合并历史数据计算变化
merged = pd.merge(current_data, previous_data, on='证券代码', how='outer')

# 计算各项指标变化
change_metrics = {
    '持仓客户数': '持仓客户数变动',
    '关注人数': '关注人数变动',
    '保有份额': '保有份额变动',
    '保有金额': '保有金额变动'
}

for metric, change_name in change_metrics.items():
    current_col = f'{metric}（{curr_date_label}）'
    prev_col = f'{metric}（{prev_date_label}）'
    merged[change_name] = merged[current_col] - merged[prev_col]

# 合并Excel数据
final_df = pd.merge(merged, excel_data, on='证券代码', how='left').fillna(0)

# 列排序（保持核心指标在前）
core_columns = [
    '证券代码', f'证券名称（{curr_date_label}）',
    f'关注人数（{prev_date_label}）', f'关注人数（{curr_date_label}）', '关注人数变动',
    f'持仓客户数（{prev_date_label}）', f'持仓客户数（{curr_date_label}）', '持仓客户数变动',
    f'保有份额（{prev_date_label}）', f'保有份额（{curr_date_label}）', '保有份额变动',
    f'保有金额（{prev_date_label}）', f'保有金额（{curr_date_label}）', '保有金额变动'
]

other_columns = [col for col in final_df.columns if col not in core_columns]
final_columns = core_columns + other_columns

# 生成结果文件
output_filename = f'ETF_基础数据合并_{current_date_str}.csv'
final_df[final_columns].to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"基础数据合并成功，文件已保存至：{output_filename}")