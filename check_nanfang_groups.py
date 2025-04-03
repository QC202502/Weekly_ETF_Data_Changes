import json

with open("search_result_nanfang_new.json") as f:
    data = json.load(f)
    print("索引数量:", data["index_count"])
    print("ETF总数:", data["count"])
    print("\n前3个指数组按规模排序:")
    for i, g in enumerate(data["index_groups"][:3]):
        print("%d. %s (%s) - %.2f亿元, %d个ETF" % (i+1, g["index_name"], g["index_code"], g["total_scale"], g["etf_count"]))
