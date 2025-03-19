#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Tushare API权限

这个脚本用于测试Tushare API的权限级别，检查当前token是否有权限访问ETF相关接口。
使用方法：
python test_tushare_permission.py YOUR_TUSHARE_TOKEN
"""

import sys
import os
import tushare as ts
import pandas as pd

def test_api_permission(token):
    # 设置token
    ts.set_token(token)
    pro = ts.pro_api()
    
    print(f"\n正在测试Tushare API权限...\n")
    
    # 测试基本接口 - 股票列表
    print("1. 测试基本接口 - 股票列表")
    try:
        data = pro.stock_basic(exchange='', list_status='L')
        print(f"  结果: 成功 (获取到{len(data)}条记录)")
        print(f"  数据预览:\n{data.head(2)}\n")
    except Exception as e:
        print(f"  结果: 失败")
        print(f"  错误信息: {str(e)}\n")
    
    # 测试ETF基本信息接口
    print("2. 测试ETF基本信息接口 - fund_basic")
    try:
        data = pro.fund_basic(market='E')
        print(f"  结果: 成功 (获取到{len(data)}条记录)")
        print(f"  数据预览:\n{data.head(2)}\n")
    except Exception as e:
        print(f"  结果: 失败")
        print(f"  错误信息: {str(e)}\n")
    
    # 测试ETF日线行情接口
    print("3. 测试ETF日线行情接口 - fund_daily")
    try:
        # 尝试获取一个常见ETF的数据，如果没有ETF列表，使用上证50ETF
        ts_code = '510050.SH'  # 上证50ETF
        data = pro.fund_daily(ts_code=ts_code)
        print(f"  结果: 成功 (获取到{len(data)}条记录)")
        print(f"  数据预览:\n{data.head(2)}\n")
    except Exception as e:
        print(f"  结果: 失败")
        print(f"  错误信息: {str(e)}\n")
    
    print("\n权限测试总结:")
    print("---------------------------------------")
    print("如果上述接口测试失败，可能是因为:")
    print("1. 您的token没有相应的接口权限")
    print("2. 您需要在Tushare官网升级会员等级")
    print("3. 您需要在个人中心积分兑换相应接口权限")
    print("\n请访问 https://tushare.pro/document/1?doc_id=108 查看接口权限说明")
    print("请访问 https://tushare.pro/document/2?doc_id=187 查看积分获取和使用方法")
    print("---------------------------------------")

def main():
    # 获取命令行参数中的token
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        # 尝试从环境变量获取token
        token = os.environ.get('TUSHARE_TOKEN')
        if not token:
            print("错误: 未提供tushare API令牌")
            print("使用方法: python test_tushare_permission.py YOUR_TUSHARE_TOKEN")
            print("或者设置环境变量: export TUSHARE_TOKEN=YOUR_TUSHARE_TOKEN")
            return 1
    
    try:
        test_api_permission(token)
        return 0
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())