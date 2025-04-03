import json

with open('search_result_semiconductor_new.json') as f:
    data = json.load(f)
    print('搜索类型:', data['search_type'])
    print('是否分组:', data['is_grouped'])
    print('ETF数量:', data['count'])
    if 'index_groups' in data:
        print('索引组数量:', data['index_count'])
        print('
前3个指数组:')
        for i, group in enumerate(data['index_groups'][:3]):
            print(f"{i+1}. {group['index_name']} - {group['total_scale']}亿元 ({len(group['etfs'])}个ETF)")
    else:
        print('扁平列表，无索引组')