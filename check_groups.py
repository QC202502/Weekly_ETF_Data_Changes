import json

with open("search_result_consumer_new.json") as f:
    data = json.load(f)
    groups = data["index_groups"]
    print("前3个指数组按规模排序：")
    for i, g in enumerate(groups[:3]):
        print("%d. %s - %.2f亿元, %d个ETF" % (i+1, g["index_name"], g["total_scale"], g["etf_count"]))
