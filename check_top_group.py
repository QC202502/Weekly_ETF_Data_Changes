import json

with open("search_result_consumer_new.json") as f:
    data = json.load(f)
    first_group = data["index_groups"][0]
    print("规模最大的指数组详情：")
    print("指数名称:", first_group["index_name"])
    print("指数代码:", first_group["index_code"])
    print("总规模:", first_group["total_scale"], "亿元")
    print("ETF数量:", first_group["etf_count"])
    print("\n前3个ETF:")
    for i, etf in enumerate(first_group["etfs"][:3]):
        print("%d. %s (%s) - %.2f亿元" % (i+1, etf["name"], etf["code"], etf["fund_size"]))
