import json

with open("search_result_semiconductor.json") as f:
    data = json.load(f)
    print("索引数量:", data["index_count"])
    print("ETF总数:", data["count"])
    print("\n所有指数组按规模排序:")
    for i, g in enumerate(data["index_groups"]):
        print("%d. %s (%s) - %.2f亿元, %d个ETF" % (i+1, g["index_name"], g["index_code"], g["total_scale"], g["etf_count"]))
