#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动更新ETF数据脚本

本脚本用于自动获取最新的ETF价格数据并生成推荐。
可以设置为定时任务，确保系统始终使用最新的ETF价格数据。

使用方法：
python auto_update_etf_data.py

定时任务设置示例（每个工作日下午4点执行）：
0 16 * * 1-5 cd /path/to/Weekly_ETF_Data_Changes && python auto_update_etf_data.py
"""

import os
import sys
import logging
import datetime
from pathlib import Path

# 设置日志
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'etf_update_{datetime.datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('etf_updater')

def main():
    """主函数"""
    try:
        logger.info("开始自动更新ETF数据")
        
        # 导入获取最新ETF数据的函数
        from get_latest_etf_data import main as get_latest_data
        
        # 获取最新ETF数据
        logger.info("正在获取最新ETF价格数据...")
        result = get_latest_data()
        
        if result != 0:
            logger.error("获取ETF价格数据失败")
            return 1
        
        logger.info("ETF数据更新完成")
        return 0
        
    except Exception as e:
        logger.exception(f"自动更新ETF数据出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())