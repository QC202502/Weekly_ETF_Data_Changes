from database.models import Database
from blueprints.feishu_routes import get_feishu_poster_data
import json

# 初始化数据库
db = Database()

# 获取飞书API数据
poster_data = get_feishu_poster_data()
print('飞书API获取的示例推广记录:')
for item in poster_data[:3]:
    print(f"代码: {item.get('code', '')}, 推广时间: {item.get('publish_date', '')}, 下线时间: {item.get('offline_date', '')}")

# 检查数据库中的历史数据
print('\n检查ETF自选历史数据:')
codes = ['513970', '159770', '512670']
for code in codes:
    print(f"\n代码 {code} 的自选历史数据:")
    data = db.execute_query('SELECT date, attention_count FROM etf_attention_history WHERE code = ? ORDER BY date DESC LIMIT 3', (code,))
    for row in data:
        print(row)
    
    print(f"\n代码 {code} 的持有人历史数据:")
    data = db.execute_query('SELECT date, holder_count, holding_value FROM etf_holders_history WHERE code = ? ORDER BY date DESC LIMIT 3', (code,))
    for row in data:
        print(row)

# 测试get_attention_on_date和get_holders_on_date方法
print('\n测试数据获取方法:')
test_date = '2025-05-12'
for code in codes:
    print(f"\n代码 {code} 在 {test_date} 的数据:")
    attention = db.get_attention_on_date(code, test_date)
    holders = db.get_holders_on_date(code, test_date)
    value = db.get_value_on_date(code, test_date)
    print(f"自选人数: {attention}")
    print(f"持有人数: {holders}")
    print(f"持仓价值: {value}")

# 检查API数据中的推广时间格式
print('\n检查API数据中的推广时间格式:')
date_formats = set()
for item in poster_data:
    pub_date = item.get('publish_date', '')
    off_date = item.get('offline_date', '')
    if pub_date:
        date_formats.add(pub_date)
    if off_date:
        date_formats.add(off_date)

print(f"所有日期格式示例: {list(date_formats)[:10]}") 