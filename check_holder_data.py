#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

# 从JSON文件加载数据
with open('search_result_semiconductor.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 查看第一个ETF的持仓人数和持仓价值
if data.get('etfs'):
    print("指数数量:", len(data['indices']))
    print("ETF总数:", len(data['etfs']))
    print("搜索类型:", data.get('search_type', '未知'))
    print("是否分组:", data.get('grouped', False))
    
    etf = data['etfs'][0]
    print("ETF代码:", etf["code"])
    print("持仓人数:", etf["holder_count"])
    print("持仓价值:", etf["holding_amount"])
    print("关注度:", etf["attention_count"])
else:
    print("未找到ETF数据")
