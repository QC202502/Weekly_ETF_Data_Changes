#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
from datetime import datetime, timedelta
from database.models import Database
from blueprints.feishu_routes import get_feishu_poster_data
import sqlite3

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fix_feishu_data.log')
    ]
)
logger = logging.getLogger(__name__)

def create_feishu_promo_table():
    """创建飞书推广数据表（如果不存在）"""
    try:
        db = Database()
        conn = db.connect()
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feishu_promo_data'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            logger.info("创建飞书推广数据表")
            cursor.execute("""
                CREATE TABLE feishu_promo_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    name TEXT,
                    publish_date TEXT,
                    offline_date TEXT,
                    publish_channel TEXT,
                    remarks TEXT,
                    banner_url TEXT,
                    long_image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("飞书推广数据表创建成功")
        else:
            logger.info("飞书推广数据表已存在")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"创建飞书推广数据表出错: {str(e)}")
        return False

def fix_feishu_data():
    """修复飞书数据中的日期问题"""
    try:
        # 获取飞书数据
        poster_data = get_feishu_poster_data()
        if not poster_data:
            logger.error("无法从飞书API获取数据")
            return False
        
        logger.info(f"从飞书API获取到 {len(poster_data)} 条记录")
        
        # 确保表存在
        create_feishu_promo_table()
        
        # 连接数据库
        db = Database()
        conn = db.connect()
        cursor = conn.cursor()
        
        # 获取当前日期作为默认值
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        fixed_count = 0
        saved_count = 0
        
        # 处理每条记录
        for item in poster_data:
            try:
                code = item.get('code', '')
                if not code:
                    logger.warning("跳过没有代码的记录")
                    continue
                
                # 检查并修复日期
                publish_date = item.get('publish_date', '')
                offline_date = item.get('offline_date', '')
                
                # 如果推广日期为空，设置为昨天
                if not publish_date:
                    publish_date = yesterday
                    item['publish_date'] = publish_date
                    fixed_count += 1
                    logger.info(f"为ETF {code} 设置默认推广日期: {publish_date}")
                
                # 如果下线日期为空，设置为今天
                if not offline_date:
                    offline_date = today
                    item['offline_date'] = offline_date
                    fixed_count += 1
                    logger.info(f"为ETF {code} 设置默认下线日期: {offline_date}")
                
                # 检查是否已存在相同记录
                cursor.execute("""
                    SELECT id FROM feishu_promo_data
                    WHERE code = ? AND publish_date = ?
                """, (code, publish_date))
                
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # 更新现有记录
                    cursor.execute("""
                        UPDATE feishu_promo_data
                        SET name = ?, offline_date = ?, publish_channel = ?, remarks = ?,
                            banner_url = ?, long_image_url = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        item.get('name', ''),
                        offline_date,
                        item.get('publish_channel', ''),
                        item.get('remarks', ''),
                        item.get('banner_url', ''),
                        item.get('long_image_url', ''),
                        existing_record[0]
                    ))
                else:
                    # 插入新记录
                    cursor.execute("""
                        INSERT INTO feishu_promo_data
                        (code, name, publish_date, offline_date, publish_channel, remarks, banner_url, long_image_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        code,
                        item.get('name', ''),
                        publish_date,
                        offline_date,
                        item.get('publish_channel', ''),
                        item.get('remarks', ''),
                        item.get('banner_url', ''),
                        item.get('long_image_url', '')
                    ))
                
                saved_count += 1
            except Exception as e:
                logger.error(f"处理记录时出错: {str(e)}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"成功修复 {fixed_count} 条日期问题，保存 {saved_count}/{len(poster_data)} 条记录到数据库")
        return True
    except Exception as e:
        logger.error(f"修复飞书数据出错: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始修复飞书数据")
    success = fix_feishu_data()
    if success:
        logger.info("飞书数据修复完成")
    else:
        logger.error("飞书数据修复失败") 