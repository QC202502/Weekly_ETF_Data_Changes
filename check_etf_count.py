import json

with open('search_result_159922.json') as f:
    data = json.load(f)
    print('主要ETF数量:', len(data['results']))
    print('相关ETF数量:', len(data['related_etfs']))