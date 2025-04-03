import json

with open("search_result_consumer_new.json") as f:
    data = json.load(f)
    groups = data["index_groups"][-3:]
    print("规模最小的3个指数组：")
    for i, g in enumerate(groups):
        print("%d. %s - %.2f亿元, %d个ETF" % (i+1, g["index_name"], g["total_scale"], g["etf_count"]))
