import json

with open("search_result_semiconductor.json") as f:
    data = json.load(f)
    print("索引数量:", data["index_count"])
    print("ETF总数:", data["count"])
    print("搜索类型:", data["search_type"])
    print("是否分组:", data["is_grouped"])
    
    # 查看第一个ETF的持仓人数和持仓金额
    if data["index_groups"] and data["index_groups"][0]["etfs"]:
        etf = data["index_groups"][0]["etfs"][0]
        print("\n第一个ETF持仓信息:")
        print("代码:", etf["code"])
        print("名称:", etf["name"])
        print("持仓人数:", etf["holder_count"])
        print("持仓金额:", etf["holding_amount"])
