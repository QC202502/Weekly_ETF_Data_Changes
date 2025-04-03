#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试公司搜索功能
"""

import sys
import json
from database.models import Database

def test_company_search(company_name):
    """测试基金公司搜索功能"""
    print(f"测试搜索基金公司: '{company_name}'")
    
    # 1. 直接测试Database类的search_by_company方法
    db = Database()
    results = db.search_by_company(company_name)
    
    if results:
        print(f"数据库搜索成功，找到{len(results)}条记录")
        # 打印一些结果示例
        for i, result in enumerate(results[:3]):
            print(f"结果 {i+1}:")
            print(f"  代码: {result['code']}")
            print(f"  名称: {result['name']}")
            print(f"  管理公司: {result['manager']}")
            print(f"  规模: {result['fund_size']}")
    else:
        print(f"数据库搜索失败，未找到相关记录")
    
    # 2. 测试general_search方法
    general_results = db.general_search(company_name)
    
    if general_results:
        if isinstance(general_results, dict):
            print(f"通用搜索成功，找到{general_results.get('count', 0)}条记录")
            
            # 如果为特定类型，打印更具体的信息
            if general_results.get('search_type') == '基金公司名称':
                print(f"通用搜索识别为基金公司名称")
                
            # 如果结果是分组的，打印组数
            if general_results.get('is_grouped'):
                print(f"结果被分成{len(general_results.get('index_groups', []))}个组")
        else:
            print(f"通用搜索成功，找到{len(general_results)}条记录")
    else:
        print(f"通用搜索失败，未找到相关记录")
    
    return (results, general_results)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
    else:
        company_name = "汇添富"
    
    test_company_search(company_name) 