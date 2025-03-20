#!/usr/bin/env python
# -*- coding: utf-8 -*-

import akshare as ak
import pandas as pd
import sys

def test_etf_hist():
    """测试fund_etf_hist_sina函数"""
    try:
        symbol = '159998'
        print(f"获取ETF {symbol}的历史数据...")
        df = ak.fund_etf_hist_sina(symbol=symbol)
        
        print("\n返回数据的列名:")
        print(df.columns.tolist())
        
        print("\n数据预览:")
        print(df.head())
        
        print("\n数据类型:")
        print(df.dtypes)
        
        return True
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_etf_hist()