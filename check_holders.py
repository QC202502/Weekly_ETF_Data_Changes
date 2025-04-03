from database.models import Database
db = Database()
result = db.execute_query("SELECT * FROM etf_holders LIMIT 20")
print("ETF持仓数据前20条：")
for r in result:
    print(r)