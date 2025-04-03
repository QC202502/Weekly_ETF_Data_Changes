import json

with open("search_result_semiconductor.json") as f:
    data = json.load(f)
    index_group = data["index_groups"][2]
    print("\n半导体材料设备指数组详情:")
    print("指数名称:", index_group["index_name"])
    print("指数代码:", index_group["index_code"])
    print("总规模:", "%.2f亿元" % index_group["total_scale"])
    print("ETF数量:", index_group["etf_count"])
    print("\n包含的ETF:")
    for i, etf in enumerate(index_group["etfs"]):
        print(f"{i+1}. {etf}")
