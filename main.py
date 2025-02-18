import pandas as pd
from datetime import datetime

# 加载 CSV 文件
jan24_etf_balance = pd.read_csv('/Users/admin/Downloads/etf保有量20250124.csv', encoding='GBK')
feb7_etf_balance = pd.read_csv('/Users/admin/Downloads/etf保有量20250207.csv', encoding='GBK')
jan24_etf_customers = pd.read_csv('/Users/admin/Downloads/etf自选人数20250124.csv', encoding='GBK')
feb7_etf_customers = pd.read_csv('/Users/admin/Downloads/etf自选人数20250207.csv', encoding='GBK')

# 假设这些是你要处理的文件名
jan24_file = '/Users/admin/Downloads/etf保有量20250124.csv'
feb7_file = '/Users/admin/Downloads/etf保有量20250207.csv'

# 从文件名提取年份和日期
jan24_year = jan24_file.split('保有量')[1][:4]  # 提取 2025
feb7_year = feb7_file.split('保有量')[1][:4]    # 提取 2025

jan24_date_str = jan24_file.split('2025')[1].split('.')[0]  # 提取 0124
feb7_date_str = feb7_file.split('2025')[1].split('.')[0]    # 提取 0207

# 确保日期是标准格式（动态使用年份）
jan24_date = datetime.strptime(f'{jan24_year}{jan24_date_str}', '%Y%m%d')
feb7_date = datetime.strptime(f'{feb7_year}{feb7_date_str}', '%Y%m%d')

# 比较两个日期，获取较晚的日期
latest_date = max(jan24_date, feb7_date)
latest_date_str = latest_date.strftime('%Y%m%d')

# 加载 Excel 文件，确保使用 openpyxl 引擎
excel_file_path = '/Users/admin/Downloads/ETF_DATA_20250214.xlsx'
excel_data = pd.read_excel(excel_file_path, sheet_name='万得', engine='openpyxl', header=0)

# 清理列名中的空格和不可见字符
jan24_etf_balance.columns = jan24_etf_balance.columns.str.replace(r'\s+', '', regex=True)
feb7_etf_balance.columns = feb7_etf_balance.columns.str.replace(r'\s+', '', regex=True)
jan24_etf_customers.columns = jan24_etf_customers.columns.str.replace(r'\s+', '', regex=True)
feb7_etf_customers.columns = feb7_etf_customers.columns.str.replace(r'\s+', '', regex=True)
excel_data.columns = excel_data.columns.str.replace(r'\s+', '', regex=True)

# 去除 ETF_DATA_20250213.xlsx 中证券代码的后缀（.SZ, .SH）
excel_data['证券代码'] = excel_data['证券代码'].str.replace(r'\.SH$', '', regex=True)
excel_data['证券代码'] = excel_data['证券代码'].str.replace(r'\.SZ$', '', regex=True)

# 重命名列，统一列名为中文
jan24_etf_balance.rename(columns={'SEC_CODE': '证券代码'}, inplace=True)
feb7_etf_balance.rename(columns={'SEC_CODE': '证券代码'}, inplace=True)
jan24_etf_customers.rename(columns={'SECURITY_CODE': '证券代码'}, inplace=True)
feb7_etf_customers.rename(columns={'SECURITY_CODE': '证券代码'}, inplace=True)

# 确保 sec_code 列的数据类型一致
jan24_etf_balance['证券代码'] = jan24_etf_balance['证券代码'].astype(str)
feb7_etf_balance['证券代码'] = feb7_etf_balance['证券代码'].astype(str)
jan24_etf_customers['证券代码'] = jan24_etf_customers['证券代码'].astype(str)
feb7_etf_customers['证券代码'] = feb7_etf_customers['证券代码'].astype(str)
excel_data['证券代码'] = excel_data['证券代码'].astype(str)

# 进一步清理 sec_code 格式，去掉 .0 后缀
jan24_etf_customers['证券代码'] = jan24_etf_customers['证券代码'].str.replace(r'\.0$', '', regex=True)
feb7_etf_customers['证券代码'] = feb7_etf_customers['证券代码'].str.replace(r'\.0$', '', regex=True)

# 进行数据清洗，确保 sec_code 格式一致
jan24_etf_customers['证券代码'] = jan24_etf_customers['证券代码'].str.strip()
feb7_etf_customers['证券代码'] = feb7_etf_customers['证券代码'].str.strip()

# 提取需要的字段，并重命名为中文
jan24_etf_customers = jan24_etf_customers[['证券代码', 'CNT']].rename(columns={'CNT': '关注人数（1月24日）'})
feb7_etf_customers = feb7_etf_customers[['证券代码', 'CNT']].rename(columns={'CNT': '关注人数（2月7日）'})

# 合并 ETF 保有量数据和自选人数数据
jan24_data = pd.merge(jan24_etf_balance, jan24_etf_customers, on='证券代码', how='outer')
feb7_data = pd.merge(feb7_etf_balance, feb7_etf_customers, on='证券代码', how='outer')

# 合并数据并检查列名
merged_data = pd.merge(feb7_data, jan24_data, on='证券代码', suffixes=('_feb7', '_jan24'), how='outer')

# 统一重命名合并后的列
rename_mapping = {
    'SEC_BAL_feb7': '保有份额（2月7日）',
    'SEC_BAL_jan24': '保有份额（1月24日）',
    'MKT_VALUE_feb7': '保有金额（2月7日）',
    'MKT_VALUE_jan24': '保有金额（1月24日）',
    'CUST_CNT_feb7': '持仓客户数（2月7日）',
    'CUST_CNT_jan24': '持仓客户数（1月24日）',
    'SEC_NAME_feb7': '证券名称（2月7日）',
    'SEC_NAME_jan24': '证券名称（1月24日）'
}
merged_data.rename(columns=rename_mapping, inplace=True)

# 计算各项变动
merged_data['持仓客户数变动'] = merged_data['持仓客户数（2月7日）'] - merged_data['持仓客户数（1月24日）']
merged_data['关注人数变动'] = merged_data['关注人数（2月7日）'] - merged_data['关注人数（1月24日）']
merged_data['保有份额变动'] = merged_data['保有份额（2月7日）'] - merged_data['保有份额（1月24日）']
merged_data['保有金额变动'] = merged_data['保有金额（2月7日）'] - merged_data['保有金额（1月24日）']

# 合并 Excel 数据
final_data = pd.merge(merged_data, excel_data, left_on='证券代码', right_on='证券代码', how='left')

# 检查并填充缺失值
final_data.fillna(0, inplace=True)

# ...（前面的代码保持不变）

# 添加证券代码格式化函数
def format_security_code(code):
    code = str(code).strip()
    code = code.zfill(6)  # 补零至6位
    return code

# 在合并 Excel 数据前应用格式化
merged_data['证券代码'] = merged_data['证券代码'].apply(format_security_code)
excel_data['证券代码'] = excel_data['证券代码'].apply(format_security_code)

# 检查 Excel 列名（临时调试）
print("Excel 列名:", excel_data.columns.tolist())

# 合并数据（使用正确列名）
final_data = pd.merge(
    merged_data,
    excel_data,
    on='证券代码',
    how='left'
)

# 检查合并结果（临时调试）
print("合并后总行数:", len(final_data))
print("Excel 数据非空示例:", final_data[excel_data.columns].notnull().sum())

# 选择并排列最终展示的列（包含所有 Excel 字段）
final_columns = [
    # 基础字段
    '证券代码',
    '证券名称（2月7日）',

    # 关注人数相关
    '关注人数（1月24日）',
    '关注人数（2月7日）',
    '关注人数变动',

    # 持仓客户数相关
    '持仓客户数（1月24日）',
    '持仓客户数（2月7日）',
    '持仓客户数变动',

    # 保有份额相关
    '保有份额（1月24日）',
    '保有份额（2月7日）',
    '保有份额变动',

    # 保有金额相关
    '保有金额（1月24日）',
    '保有金额（2月7日）',
    '保有金额变动',

    # 添加 Excel 文件中的所有字段（根据列名列表）
    '证券简称',
    '业绩比较基准',
    '成立年限[单位]年',
    '基金上市地点',
    '基金成立日',
    '基金管理人',
    '管理费率[单位]%',
    '托管费率[单位]%',
    '指数使用费率',
    '跟踪指数代码',
    '日均跟踪偏离度阈值(业绩基准)[单位]%',
    '年化跟踪误差阈值(业绩基准)[单位]%',
    '跟踪误差[起始交易日期]截止日52周前[截止交易日期]最新收盘日[计算周期]日[收益率计算方法]普通收益率[标的指数]上证综合指数[单位]%',
    '跟踪误差(跟踪指数)[起始交易日期]截止日52周前[截止交易日期]最新收盘日[计算周期]日[收益率计算方法]普通收益率[单位]%',
    '信息比率(年化)[起始交易日期]截止日52周前[截止交易日期]最新收盘日[计算周期]日[收益率计算方法]普通收益率[无风险收益率]一年定存利率（税前）[标的指数]上证综合指数',
    '跟踪误差(年化)[起始交易日期]截止日52周前[截止交易日期]最新收盘日[计算周期]日[收益率计算方法]普通收益率[标的指数]上证综合指数[单位]%',
    '月成交额[交易日期]最新收盘日[单位]百万元',
    '跟踪指数名称'
]

final_result = final_data[final_columns]

# 保存结果到 CSV
file_name = f'/Users/admin/Downloads/analysis_result_{latest_date_str}.csv'
final_result.to_csv(file_name, index=False, encoding='utf-8-sig')

print(f"文件已保存为 {file_name}")