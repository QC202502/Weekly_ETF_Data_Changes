import json

with open('search_result_fund_company.json') as f:
    data = json.load(f)
    print('搜索类型:', data['search_type'])
    print('是否分组:', data['is_grouped'])
    print('ETF数量:', data['count'])
    if 'index_groups' in data:
        print('索引组数量:', data['index_count'])
    else:
        print('扁平列表，无索引组')