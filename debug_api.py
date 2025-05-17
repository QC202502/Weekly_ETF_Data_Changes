import requests
import json
from pprint import pprint

def test_promotion_stats_api():
    """测试获取推广效果统计API"""
    try:
        url = "http://localhost:5007/api/feishu/promotion-stats"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"API返回状态: {data.get('success')}")
            print(f"数据条数: {data.get('total', 0)}")
            
            if data.get('data'):
                print("\n前3条数据示例:")
                for i, item in enumerate(data['data'][:3]):
                    print(f"\n数据项 {i+1}:")
                    print(f"  代码: {item.get('code')}")
                    print(f"  名称: {item.get('name')}")
                    print(f"  推广时间: {item.get('publish_date')}")
                    print(f"  下线时间: {item.get('offline_date')}")
                    print(f"  推广天数: {item.get('promo_days')}")
                    print(f"  自选人数(前): {item.get('pub_attention')}")
                    print(f"  自选人数(后): {item.get('off_attention')}")
                    print(f"  变化: {item.get('attention_change')} ({item.get('attention_pct_change')}%)")
                    print(f"  持有人数(前): {item.get('pub_holders')}")
                    print(f"  持有人数(后): {item.get('off_holders')}")
                    print(f"  变化: {item.get('holders_change')} ({item.get('holders_pct_change')}%)")
                    print(f"  持仓价值(前): {item.get('pub_value')}")
                    print(f"  持仓价值(后): {item.get('off_value')}")
                    print(f"  变化: {item.get('value_change')} ({item.get('value_pct_change')}%)")
            else:
                print("API未返回数据")
                
            if data.get('message'):
                print(f"\n消息: {data.get('message')}")
        else:
            print(f"API请求失败，状态码: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"测试API时出错: {str(e)}")

if __name__ == "__main__":
    print("开始测试推广效果统计API...")
    test_promotion_stats_api() 