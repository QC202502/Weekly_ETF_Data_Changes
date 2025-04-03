#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from database.models import Database

def create_test_holders_data():
    """创建测试用的ETF持有人数据"""
    print("开始创建测试ETF持有人数据...")
    
    # 创建数据库连接
    db = Database()
    
    # 创建一个包含示例数据的DataFrame
    data = {
        'code': [
            '159005', '159919', '510050', '510300', '510500',
            '510880', '512880', '512980', '515050', '518880'
        ],
        'holder_count': [
            13, 4921, 3046, 5230, 2715,
            1842, 895, 760, 523, 1250
        ],
        'holding_amount': [
            149998.5, 625487520.32, 515202640.51, 782450320.25, 425630150.75,
            315420680.45, 125840320.35, 115250480.25, 85640320.15, 225480620.55
        ]
    }
    
    df = pd.DataFrame(data)
    
    # 打印测试数据
    print("测试数据:")
    print(df)
    print(f"总行数: {len(df)}")
    
    # 清空现有的ETF持有人数据表
    try:
        db.execute_query("DELETE FROM etf_holders")
        print("已清空现有ETF持有人数据")
    except Exception as e:
        print(f"清空数据表失败: {str(e)}")
    
    # 保存到数据库
    success = db.save_etf_holders(df)
    if success:
        print(f"成功保存ETF持有人测试数据，共{len(df)}条记录")
        
        # 验证数据是否已保存
        result = db.execute_query("SELECT * FROM etf_holders")
        print(f"数据库中的ETF持有人数据记录数: {len(result)}")
        print("数据样例:")
        for i, row in enumerate(result[:5]):
            print(f"  {i+1}. {row}")
        
        return True
    else:
        print("保存ETF持有人测试数据失败")
        return False

if __name__ == "__main__":
    create_test_holders_data() 