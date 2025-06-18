from flask import Blueprint, jsonify, request, current_app
import pandas as pd
import traceback
from datetime import datetime
from services.index_service import get_index_intro, get_index_info
from database.models import Database
import re
import json
import traceback  # 确保导入traceback模块
import sqlite3

# 创建蓝图
search_bp = Blueprint('search', __name__)

# 调试辅助函数
def debug_print(obj, title="调试信息"):
    """打印调试信息"""
    print(f"\n=== {title} ===")
    if isinstance(obj, dict):
        for k, v in obj.items():
            print(f"{k}: {v}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if i < 5:  # 只打印前5个
                print(f"[{i}] {item}")
            else:
                print(f"... 还有 {len(obj) - 5} 项未显示")
                break
    else:
        print(obj)
    print("=" * (len(title) + 8))

# 获取当前日期格式化为"MM月DD日"
def get_current_date_format():
    """获取当前日期格式化为MM月DD日"""
    from services.data_service import current_date_str
    return current_date_str

@search_bp.route('/search', methods=['POST'])
def search():
    """搜索ETF"""
    try:
        # 在返回的jsonify结果中查看CORS头
        def add_cors_headers(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            return response
            
        # 调试输出完整的请求信息
        print("\n======= 收到搜索请求 =======")
        print(f"请求方法: {request.method}")
        print(f"请求Content-Type: {request.content_type}")
        print(f"请求头: {dict(request.headers)}")
        print(f"表单数据: {request.form}")
        print(f"JSON数据: {request.get_json(silent=True)}")
        print(f"URL参数: {request.args}")
        print("===========================\n")
        
        # 获取搜索关键词，尝试多种方式
        keyword = None
        
        # 尝试从表单数据获取
        if request.form and 'code' in request.form:
            keyword = request.form.get('code', '').strip()
            print(f"从表单获取关键词: {keyword}")
        
        # 如果表单数据不存在，尝试从JSON数据获取
        if not keyword and request.is_json:
            data = request.get_json(silent=True)
            if data and 'code' in data:
                keyword = data.get('code', '').strip()
                print(f"从JSON获取关键词: {keyword}")
        
        # 如果JSON数据不存在，尝试从URL参数获取
        if not keyword and 'code' in request.args:
            keyword = request.args.get('code', '').strip()
            print(f"从URL参数获取关键词: {keyword}")
        
        # 如果仍然没有关键词，返回错误
        if not keyword:
            print("未提供搜索关键词")
            response = jsonify({"error": "请输入搜索关键词"})
            return add_cors_headers(response)
        
        print(f"最终使用的搜索关键词: '{keyword}'")
        
        print(f"开始处理搜索请求...")
        print(f"搜索关键词: '{keyword}'")
        
        db = Database()
        
        # 获取数据截止日期
        data_date = get_data_cutoff_date()
        
        # 检查是否是ETF代码
        if re.match(r'^\d{6}$', keyword) or re.match(r'^\d{6}\.[A-Z]{2}$', keyword):
            code = keyword.split('.')[0] if '.' in keyword else keyword
            print(f"检查ETF代码是否存在: {keyword} -> {code}")
            
            if db.check_etf_code_exists(code):
                print("搜索类型: ETF基金代码")
                print(f"搜索ETF代码: {code}")
                
                # 1. 首先获取主要ETF信息
                results = db.search_by_etf_code(code)
                
                if results:
                    # 确保所有必要字段都存在并格式化
                    results = normalize_etf_results(results)
                    
                    # 获取第一条结果的信息，用于查找同指数产品
                    main_etf = results[0]
                    
                    # 2. 然后查找同指数的其他ETF
                    tracking_index_code = main_etf.get('tracking_index_code', '')
                    tracking_index_name = main_etf.get('tracking_index_name', '')
                    
                    print(f"查找跟踪同一指数的ETF: 指数代码={tracking_index_code}, 指数名称={tracking_index_name}")
                    
                    related_etfs = []
                    if tracking_index_code or tracking_index_name:
                        # 根据跟踪指数查找相关ETF
                        if tracking_index_code:
                            related_etfs = db.search_by_index_code(tracking_index_code)
                        else:
                            related_etfs = db.search_by_index_name(tracking_index_name)
                            
                        # 标准化结果
                        related_etfs = normalize_etf_results(related_etfs)
                        
                        # 移除重复项
                        seen_codes = set(item['code'] for item in results)
                        related_etfs = [etf for etf in related_etfs if etf['code'] not in seen_codes]
                        
                        print(f"找到 {len(related_etfs)} 个相关ETF (同指数)")
                    
                    # 打印一条结果用于调试
                    if results:
                        print(f"主ETF搜索结果示例：")
                        for key, value in results[0].items():
                            print(f"  {key}: {value}")
                    
                    # 构建返回数据
                    response_data = {
                        'search_type': 'ETF基金代码',
                        'results': results,
                        'count': len(results),
                        'related_etfs': related_etfs,
                        'related_count': len(related_etfs),
                        'index_code': tracking_index_code,
                        'index_name': tracking_index_name,
                        'data_date': data_date  # 添加数据截止日期
                    }
                    
                    # 添加ETF数量和总规模字段
                    total_etf_count = len(results) + len(related_etfs)
                    response_data['etf_count'] = total_etf_count
                    
                    # 计算总规模
                    total_scale = 0
                    for etf in results:
                        total_scale += float(etf.get('fund_size', 0) or 0)
                    for etf in related_etfs:
                        total_scale += float(etf.get('fund_size', 0) or 0)
                    response_data['total_scale'] = total_scale
                    
                    # 调试信息
                    print(f"ETF基金代码搜索 - 添加总计字段:")
                    print(f"- etf_count: {total_etf_count}")
                    print(f"- total_scale: {total_scale}")
                    
                    # 尝试获取指数介绍
                    if tracking_index_code:
                        index_intro = get_index_intro(tracking_index_code)
                        if index_intro:
                            response_data['index_intro'] = index_intro
                    
                    # 增加调试日志，确保返回格式正确
                    print(f"返回数据结构：{type(response_data)}")
                    print(f"results类型：{type(response_data['results'])}")
                    print(f"results长度：{len(response_data['results'])}")
                    print(f"related_etfs长度：{len(response_data['related_etfs'])}")
                    
                    response = jsonify(response_data)
                    return add_cors_headers(response)
                else:
                    response = jsonify({
                        'results': [],
                        'count': 0,
                        'message': '未找到相关ETF'
                    })
                    return add_cors_headers(response)
        
        # 检查是否是基金公司名称
        fund_company_keywords = ['基金', '资管', '华夏', '汇添富', '易方达', '南方', '广发', '嘉实', '博时']
        is_fund_company = any(kw in keyword for kw in fund_company_keywords)
        if is_fund_company:
            print("搜索类型: 基金公司名称")
            print(f"搜索基金公司: {keyword}")
            results = db.search_by_company(keyword)
            
            if results:
                # 确保所有必要字段都存在并格式化
                results = normalize_etf_results(results)
                
                response = jsonify({
                    'search_type': '基金公司名称',
                    'results': results,
                    'count': len(results),
                    'company_name': keyword,
                    'is_grouped': False,
                    'data_date': data_date  # 添加数据截止日期
                })
                return add_cors_headers(response)
            else:
                response = jsonify({
                    'results': [],
                    'count': 0,
                    'message': '未找到相关ETF',
                    'data_date': data_date  # 添加数据截止日期
                })
                return add_cors_headers(response)
        
        # 默认按指数名称搜索
        print("搜索类型: 跟踪指数名称")
        print(f"搜索指数名称: {keyword}")
        results = db.search_by_index_name(keyword)
        
        if results:
            # 检查结果是否已分组
            if isinstance(results, dict) and results.get('is_grouped'):
                # 已分组的结果格式不同
                response = jsonify({
                    'search_type': '跟踪指数名称(按指数分组)',
                    'index_groups': results['index_groups'],
                    'index_count': results['index_count'],
                    'count': results['count'],
                    'is_grouped': True,
                    'keyword': keyword
                })
                return add_cors_headers(response)
            else:
                # 确保所有必要字段都存在并格式化
                results = normalize_etf_results(results)
                
                # 获取指数代码和名称
                tracking_index_code = results[0].get('tracking_index_code', '') if results else ''
                tracking_index_name = results[0].get('tracking_index_name', '') if results else ''
                
                response_data = {
                    'search_type': '跟踪指数名称',
                    'results': results,
                    'count': len(results),
                    'index_code': tracking_index_code,
                    'index_name': tracking_index_name or keyword,
                    'is_grouped': False,
                    'data_date': data_date  # 添加数据截止日期
                }
                
                # 尝试获取指数介绍
                if tracking_index_code:
                    index_intro = get_index_intro(tracking_index_code)
                    if index_intro:
                        response_data['index_intro'] = index_intro
                
                response = jsonify(response_data)
                return add_cors_headers(response)
        else:
            # 尝试通用搜索
            print("指数名称搜索无结果，尝试通用搜索")
            results = db.general_search(keyword)
            
            if results:
                # 检查结果是否已分组
                if isinstance(results, dict) and results.get('is_grouped'):
                    # 已分组的结果格式不同
                    response = jsonify({
                        'search_type': '通用搜索(按指数分组)',
                        'index_groups': results['index_groups'],
                        'index_count': results['index_count'],
                        'count': results['count'],
                        'is_grouped': True,
                        'keyword': keyword
                    })
                    return add_cors_headers(response)
                else:
                    # 标准化普通结果
                    results = normalize_etf_results(results)
                    
                    response = jsonify({
                        'search_type': '通用搜索',
                        'results': results,
                        'count': len(results),
                        'keyword': keyword,
                        'is_grouped': False,
                        'data_date': data_date  # 添加数据截止日期
                    })
                    return add_cors_headers(response)
            else:
                response = jsonify({
                    'results': [],
                    'count': 0,
                    'message': '未找到相关ETF',
                    'data_date': data_date  # 添加数据截止日期
                })
                return add_cors_headers(response)
        
    except Exception as e:
        print(f"搜索出错: {str(e)}")
        traceback.print_exc()
        response = jsonify({'error': f'搜索出错: {str(e)}'})
        return add_cors_headers(response)

def normalize_etf_results(results):
    """标准化ETF搜索结果，确保所有必要字段存在"""
    normalized_results = []
    
    # 创建数据库连接，用于从历史表获取最新数据
    db = Database()
    
    for result in results:
        # 从历史表获取最新自选数据
        etf_code = result.get('code', '')
        attention_count = result.get('attention_count', 0)
        
        if etf_code:
            # 尝试从历史表获取最新自选数据
            latest_attention = db.get_latest_attention_count(etf_code)
            if latest_attention > 0:
                attention_count = latest_attention
        
        # 将持仓价值从元转为万元
        holding_value = float(result.get('holding_value', 0)) / 10000
        holding_value_daily_change = float(result.get('holding_value_daily_change', 0)) / 10000
        holding_value_five_day_change = float(result.get('holding_value_five_day_change', 0)) / 10000
        
        # 创建标准化的ETF数据对象
        etf_data = {
            'code': etf_code,
            'name': result.get('name', ''),
            'manager': result.get('manager', result.get('fund_manager', '')),
            'manager_short': result.get('manager_short', ''),  # 优先使用数据库中的管理人简称字段
            'fund_size': result.get('fund_size', 0),
            'management_fee_rate': result.get('management_fee_rate', 0),
            'tracking_error': result.get('tracking_error', 0),
            'tracking_index_code': result.get('tracking_index_code', ''),
            'tracking_index_name': result.get('tracking_index_name', ''),
            'total_holder_count': result.get('total_holder_count', 0),
            'daily_avg_volume': result.get('daily_avg_volume', 0),
            'daily_volume': result.get('daily_volume', 0),
            'is_business': result.get('is_business', False),
            
            # 持仓相关字段
            'holder_count': result.get('holder_count', 0),  # 持仓客户数
            'holding_amount': result.get('holding_amount', 0),  # 持仓份额
            'holding_value': round(holding_value, 2),  # 持仓价值（万元）
            'attention_count': attention_count,  # 使用历史表中的最新数据
            
            # 变化相关字段 - 同时保留原字段名和前端期望的字段名
            'attention_daily_change': result.get('attention_daily_change', 0),
            'attention_five_day_change': result.get('attention_five_day_change', 0),
            'attention_day_change': result.get('attention_daily_change', 0),  # 前端期望的字段名
            'attention_5day_change': result.get('attention_five_day_change', 0),  # 前端期望的字段名
            
            'holder_daily_change': result.get('holder_daily_change', 0),
            'holder_five_day_change': result.get('holder_five_day_change', 0),
            'holders_day_change': result.get('holder_daily_change', 0),  # 前端期望的字段名
            'holders_5day_change': result.get('holder_five_day_change', 0),  # 前端期望的字段名
            
            'holding_value_daily_change': round(holding_value_daily_change, 2),  # 持仓价值日变化（万元）
            'holding_value_five_day_change': round(holding_value_five_day_change, 2),  # 持仓价值五日变化（万元）
            
            # 添加前端期望的持仓价值变化字段名
            'holding_day_change': round(holding_value_daily_change, 2),  # 持仓价值日变化（万元）（前端期望的字段名）
            'holding_5day_change': round(holding_value_five_day_change, 2),  # 持仓价值五日变化（万元）（前端期望的字段名）
        }
        
        normalized_results.append(etf_data)
    
    # 打印第一个结果的详细信息，用于调试
    if normalized_results:
        first_result = normalized_results[0]
        try:
            print(f"第一个结果: {first_result['code']}")
            print(f"持仓客户数: {first_result['holder_count']}")
            print(f"持仓份额: {first_result['holding_amount']}")
            print(f"持仓价值(万元): {first_result['holding_value']}")
            print(f"关注度: {first_result['attention_count']}")
            print(f"日均成交量: {first_result['daily_avg_volume']}")
            print(f"管理人: {first_result['manager']}")
            print(f"管理人简称: {first_result['manager_short']}")
            
            print(f"关注度日变化: {first_result['attention_daily_change']}")
            print(f"关注度五日变化: {first_result['attention_five_day_change']}")
            print(f"持仓客户数日变化: {first_result['holder_daily_change']}")
            print(f"持仓客户数五日变化: {first_result['holder_five_day_change']}")
            print(f"持仓价值日变化(万元): {first_result['holding_value_daily_change']}")
            print(f"持仓价值五日变化(万元): {first_result['holding_value_five_day_change']}")
        except Exception as e:
            print(f"打印结果详情出错: {e}")
    
    return normalized_results

def determine_search_type(keyword):
    """判断搜索类型"""
    # 创建数据库连接
    db = Database()
    
    # 处理可能带有后缀的ETF代码
    etf_code = keyword
    if '.' in etf_code:
        etf_code = etf_code.split('.')[0]
    elif etf_code.startswith('sh') or etf_code.startswith('sz'):
        etf_code = etf_code[2:]
    
    # 判断是否为ETF基金代码
    if etf_code.isdigit() and len(etf_code) == 6:
        # 检查所有可能的格式
        possible_codes = [
            etf_code,
            f"{etf_code}.SZ",
            f"{etf_code}.SH"
        ]
        for code in possible_codes:
            if db.check_etf_code_exists(code):
                return "ETF基金代码"
    
    # 判断是否为基金公司名称
    company_keywords = ['基金', '资管', '投资', '证券']
    if any(kw in keyword for kw in company_keywords) or db.check_company_exists(keyword):
        return "基金公司名称"
    
    # 判断是否为跟踪指数名称
    index_keywords = ['指数', '300', '500', '1000', '红利', '消费', '医药', '科技']
    if any(kw in keyword for kw in index_keywords) or db.check_index_name_exists(keyword):
        return "跟踪指数名称"
    
    # 默认为通用搜索
    return "通用搜索"

def search_by_etf_code(code, etf_data, business_etfs, current_date_str):
    """根据ETF代码搜索"""
    try:
        # 处理可能的前缀
        if code.startswith(('SH', 'sh')):
            code = code[2:]
        elif code.startswith(('SZ', 'sz')):
            code = code[2:]
            
        # 创建数据库连接
        db = Database()
        # 直接调用数据库模型中的search_by_etf_code方法
        results = db.search_by_etf_code(code)
        
        # 处理业务ETF标记
        for result in results:
            result['is_business'] = result['code'] in business_etfs
            
            # 获取跟踪指数代码
            index_code = result.get('tracking_index_code', '')
            if index_code:
                # 获取指数简介
                index_intro = get_index_intro(index_code)
                result['index_intro'] = index_intro
    
        return results
    except Exception as e:
        print(f"search_by_etf_code错误: {e}")
        traceback.print_exc()
        return []

def search_by_index_name(keyword, etf_data, business_etfs, current_date_str):
    """按跟踪指数名称搜索"""
    # 创建数据库连接
    db = Database()
    # 直接调用数据库模型中的search_by_index_name方法
    results = db.search_by_index_name(keyword)
    
    # 处理业务ETF标记和指数简介
    if isinstance(results, dict) and 'results' in results:
        # 如果有索引信息，添加索引简介
        if 'index_info' in results and 'index_code' in results['index_info']:
            index_code = results['index_info']['index_code']
            results['index_info']['index_intro'] = get_index_intro(index_code)
            
        # 为每个ETF添加业务标记
        for etf in results['results']:
            etf['is_business'] = etf['code'] in business_etfs
    
    return results

def search_by_index_code(keyword, etf_data, business_etfs, current_date_str):
    """按指数代码搜索"""
    # 创建数据库连接
    db = Database()
    # 直接调用数据库模型中的search_by_index_code方法
    results = db.search_by_index_code(keyword)
    
    # 处理业务ETF标记和指数简介
    if isinstance(results, dict) and 'results' in results:
        # 如果有索引信息，添加索引简介
        if 'index_info' in results and 'index_code' in results['index_info']:
            index_code = results['index_info']['index_code']
            results['index_info']['index_intro'] = get_index_intro(index_code)
            
        # 为每个ETF添加业务标记
        for etf in results['results']:
            etf['is_business'] = etf['code'] in business_etfs
    
    return results

def search_by_company(keyword, etf_data, business_etfs, current_date_str):
    """按基金公司名称搜索"""
    # 创建数据库连接
    db = Database()
    # 直接调用数据库模型中的search_by_company方法
    results = db.search_by_company(keyword)
    
    # 处理业务ETF标记
    if isinstance(results, dict) and 'results' in results:
        for etf in results['results']:
            etf['is_business'] = etf['code'] in business_etfs
    elif isinstance(results, list):
        for result in results:
            result['is_business'] = result['code'] in business_etfs
    
    return results

# 安全转换数值的辅助函数
def safe_float(value, default=0.0):
    """安全地将值转换为浮点数"""
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

@search_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """获取ETF推荐数据"""
    # 导入所需模块
    from database.models import Database
    import traceback
    from datetime import datetime
    from flask import jsonify
    
    try:
        # 创建数据库连接
        db = Database()
        conn = db.connect()
        cursor = conn.cursor()
        
        # 准备推荐榜单数据
        recommendations = {
            "attention": [],  # 关注TOP20
            "holders": [],    # 持仓人数TOP20
            "price_return": [], # 涨幅TOP20
            "favorites": [],  # 新增：加自选排行榜
            "trade_date": "",
            "date_for_title": ""
        }
        
        # 获取最新的交易日期
        cursor.execute("SELECT MAX(date) FROM etf_price")
        latest_date = cursor.fetchone()[0]
        
        if latest_date:
            # 直接使用最新数据的日期，而不是当前日期
            date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
            # 格式化为"MM月DD日"
            recommendations["trade_date"] = f"{date_obj.month}月{date_obj.day}日"
            # 给页面标题使用的日期，格式为"04月16日"，补零
            recommendations["date_for_title"] = f"{date_obj.month:02d}月{date_obj.day:02d}日"
            print(f"最新数据日期: {latest_date}, 格式化为: {recommendations['date_for_title']}")
        else:
            # 如果没有最新日期，使用默认值
            recommendations["trade_date"] = "最新"
            recommendations["date_for_title"] = "最新"
            
        # 1. 尝试获取涨幅数据
        try:
            query = """
            WITH grouped_etfs AS (
                SELECT 
                    p.code, 
                    i.name, 
                    p.change_rate, 
                    i.fund_manager, 
                    i.manager_short,
                    ROUND(i.fund_size / 1, 2) as fund_size, 
                    i.tracking_index_code,
                    i.tracking_index_name,
                    CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business,
                    CASE WHEN b.code IS NOT NULL THEN '商务品' ELSE '非商务品' END as business_text,
                    i.management_fee_rate
                FROM etf_price p
                JOIN etf_info i ON p.code = i.code
                LEFT JOIN etf_business b ON p.code = b.code
                WHERE p.date = (SELECT MAX(date) FROM etf_price)
                ORDER BY i.tracking_index_code, p.change_rate DESC
            ),
            business_etfs AS (
                -- 筛选出所有商务品
                SELECT 
                    g.code, 
                    g.name, 
                    g.fund_manager,
                    g.manager_short,
                    g.tracking_index_code,
                    g.tracking_index_name,
                    g.management_fee_rate,
                    p.amount
                FROM grouped_etfs g
                JOIN etf_price p ON g.code = p.code
                WHERE g.is_business = 1
                AND p.date = (SELECT MAX(date) FROM etf_price)
            ),
            best_volume_business AS (
                -- 对每个指数，找出交易量最大的"商务品"
                WITH all_etfs AS (
                    -- 所有ETF按指数分组
                    SELECT 
                        g.tracking_index_code,
                        g.code,
                        g.manager_short,
                        p.amount,
                        CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END AS is_business
                    FROM grouped_etfs g
                    JOIN etf_price p ON g.code = p.code
                    LEFT JOIN etf_business b ON g.code = b.code
                    WHERE p.date = (SELECT MAX(date) FROM etf_price)
                ),
                business_etfs_by_index AS (
                    -- 仅商务品
                    SELECT *
                    FROM all_etfs
                    WHERE is_business = 1
                ),
                max_volume_business AS (
                    -- 每个指数下交易量最大的"商务品"
                    SELECT 
                        be1.tracking_index_code,
                        be1.code,
                        be1.manager_short,
                        be1.amount
                    FROM business_etfs_by_index be1
                    WHERE NOT EXISTS (
                        SELECT 1 FROM business_etfs_by_index be2
                        WHERE be2.tracking_index_code = be1.tracking_index_code
                        AND be2.amount > be1.amount
                    )
                ),
                current_etf_rank AS (
                    -- 每个指数下涨幅排名第一的ETF
                    SELECT 
                        g1.tracking_index_code,
                        g1.code AS rank_one_code,
                        p1.amount AS rank_one_amount
                    FROM grouped_etfs g1
                    JOIN etf_price p1 ON g1.code = p1.code
                    WHERE p1.date = (SELECT MAX(date) FROM etf_price)
                    AND NOT EXISTS (
                        SELECT 1 FROM grouped_etfs g2
                        JOIN etf_price p2 ON g2.code = p2.code
                        WHERE g2.tracking_index_code = g1.tracking_index_code
                        AND p2.date = p1.date
                        AND g2.change_rate > g1.change_rate
                    )
                )
                -- 最终结果
                SELECT
                    mvb.tracking_index_code,
                    mvb.code AS best_volume_code,
                    mvb.manager_short AS best_volume_manager,
                    1 AS is_business_product, -- 始终为1，因为只选择商务品
                    CASE 
                        WHEN mvb.amount > cer.rank_one_amount THEN 0 -- 有商务品交易量大于排行榜中的ETF，显示红色
                        ELSE 1 -- 没有商务品交易量大于排行榜中的ETF，显示绿色
                    END AS is_max_volume
                FROM max_volume_business mvb
                JOIN current_etf_rank cer ON mvb.tracking_index_code = cer.tracking_index_code
            ),
            lowest_fee_business AS (
                -- 对每个指数和每个ETF，找出费率严格低于该ETF的同指数商务品中费率最低的
                SELECT DISTINCT
                    g.tracking_index_code,
                    g.code AS etf_code,
                    b_min.code AS lowest_fee_code,
                    b_min.manager_short AS lowest_fee_manager,
                    b_min.management_fee_rate
                FROM grouped_etfs g
                JOIN business_etfs b_min ON g.tracking_index_code = b_min.tracking_index_code
                WHERE NOT EXISTS (
                    -- 确保没有其他同指数商务品的费率更低
                    SELECT 1 FROM business_etfs b2
                    WHERE b2.tracking_index_code = g.tracking_index_code
                    AND b2.management_fee_rate < b_min.management_fee_rate
                    AND b2.code != g.code
                )
                AND b_min.management_fee_rate < g.management_fee_rate  -- 严格小于当前ETF的费率
                AND b_min.code != g.code  -- 不是当前ETF自身
            )
            SELECT 
                g1.code, g1.name, g1.change_rate, g1.fund_manager, g1.manager_short,
                g1.fund_size, g1.tracking_index_code, g1.tracking_index_name, 
                g1.is_business, g1.business_text, g1.management_fee_rate,
                bvb.best_volume_code,
                bvb.best_volume_manager,
                bvb.is_business_product,
                bvb.is_max_volume,
                lfb.lowest_fee_code,
                lfb.lowest_fee_manager,
                lfb.management_fee_rate AS lowest_fee_rate
            FROM grouped_etfs g1
            LEFT JOIN best_volume_business bvb ON g1.tracking_index_code = bvb.tracking_index_code
            LEFT JOIN lowest_fee_business lfb ON g1.tracking_index_code = lfb.tracking_index_code AND g1.code = lfb.etf_code
            WHERE NOT EXISTS (
                SELECT 1 FROM grouped_etfs g2
                WHERE g2.tracking_index_code = g1.tracking_index_code
                AND g2.change_rate > g1.change_rate
            )
            ORDER BY g1.change_rate DESC
            LIMIT 20
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # 使用字段名创建结果字典
            field_names = [
                'code', 'name', 'change_rate', 'fund_manager', 'manager_short',
                'fund_size', 'tracking_index_code', 'tracking_index_name',
                'is_business', 'business_text', 'management_fee_rate',
                'best_volume_code', 'best_volume_manager', 'is_business_product', 'is_max_volume',
                'lowest_fee_code', 'lowest_fee_manager', 'lowest_fee_rate'
            ]
            
            for row in results:
                item = dict(zip(field_names, row))
                # 处理is_business字段，确保是布尔值
                item['is_business'] = bool(item['is_business'])
                recommendations["price_return"].append(item)
            
            print(f"成功加载ETF价格推荐数据，共{len(recommendations['price_return'])}条记录，交易日期：{recommendations['trade_date']}")
            
        except Exception as e:
            print(f"获取涨幅数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 2. 尝试获取关注数据
        try:
            query = """
            SELECT 
                a.code, 
                i.name, 
                a.attention_count as attention_change, 
                i.fund_manager, 
                ROUND(i.fund_size / 1, 2) as fund_size, 
                i.tracking_index_code,
                i.tracking_index_name,
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business,
                CASE WHEN b.code IS NOT NULL THEN '商务品' ELSE '非商务品' END as business_text
            FROM etf_attention a
            JOIN etf_info i ON a.code = i.code
            LEFT JOIN etf_business b ON a.code = b.code
            ORDER BY a.attention_count DESC
            LIMIT 20
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # 使用字段名创建结果字典
            field_names = [
                'code', 'name', 'attention_change', 'fund_manager', 
                'fund_size', 'tracking_index_code', 'tracking_index_name',
                'is_business', 'business_text'
            ]
            
            for row in results:
                item = dict(zip(field_names, row))
                # 确保数值类型正确
                item['attention_change'] = int(item['attention_change']) if item['attention_change'] else 0
                item['is_business'] = bool(item['is_business'])
                recommendations["attention"].append(item)
            
            print(f"成功加载ETF关注推荐数据，共{len(recommendations['attention'])}条记录")
        except Exception as e:
            print(f"获取关注数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 3. 尝试获取持有人数据
        try:
            query = """
            SELECT 
                h.code, 
                i.name, 
                h.holder_count as holders_change, 
                i.fund_manager, 
                ROUND(i.fund_size / 1, 2) as fund_size, 
                i.tracking_index_code,
                i.tracking_index_name,
                CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business,
                CASE WHEN b.code IS NOT NULL THEN '商务品' ELSE '非商务品' END as business_text
            FROM etf_holders h
            JOIN etf_info i ON h.code = i.code
            LEFT JOIN etf_business b ON h.code = b.code
            ORDER BY h.holder_count DESC
            LIMIT 20
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # 使用字段名创建结果字典
            field_names = [
                'code', 'name', 'holders_change', 'fund_manager', 
                'fund_size', 'tracking_index_code', 'tracking_index_name',
                'is_business', 'business_text'
            ]
            
            for row in results:
                item = dict(zip(field_names, row))
                # 确保数值类型正确
                item['holders_change'] = int(item['holders_change']) if item['holders_change'] else 0
                item['is_business'] = bool(item['is_business'])
                recommendations["holders"].append(item)
            
            print(f"成功加载ETF持有人推荐数据，共{len(recommendations['holders'])}条记录")
        except Exception as e:
            print(f"获取持有人数据出错: {str(e)}")
            import traceback
            traceback.print_exc()

        # 4. 新增：尝试获取加自选排行榜数据
        try:
            # 使用Database类的方法获取加自选排行榜数据
            favorites_data = db.get_etf_favorites_recommendations()
            
            if favorites_data:
                # 收集所有的跟踪指数代码，以便后续查询替补商务品和低费率商务品
                tracking_index_codes = [item['tracking_index_code'] for item in favorites_data if item.get('tracking_index_code')]
                
                # 查询为每个跟踪指数找出交易量最大的商务品
                best_volume_business = {}
                lowest_fee_business = {}
                
                if tracking_index_codes:
                    # 查询交易量最大的商务品
                    try:
                        index_codes_str = ', '.join([f"'{code}'" for code in tracking_index_codes])
                        query_best_volume = f"""
                        WITH ranked_business AS (
                            SELECT 
                                i.code,
                                i.tracking_index_code,
                                i.fund_manager,
                                i.manager_short,
                                i.market_volume,
                                i.management_fee_rate,
                                ROW_NUMBER() OVER (PARTITION BY i.tracking_index_code ORDER BY i.market_volume DESC) as volume_rank
                            FROM etf_info i
                            JOIN etf_business b ON i.code = b.code
                            WHERE i.tracking_index_code IN ({index_codes_str})
                        )
                        SELECT 
                            code,
                            tracking_index_code,
                            fund_manager,
                            manager_short,
                            market_volume,
                            management_fee_rate
                        FROM ranked_business
                        WHERE volume_rank = 1
                        """
                        cursor.execute(query_best_volume)
                        for row in cursor.fetchall():
                            code, tracking_index_code, fund_manager, manager_short, volume, fee_rate = row
                            best_volume_business[tracking_index_code] = {
                                'code': code,
                                'manager': manager_short or fund_manager,
                                'volume': volume
                            }
                        
                        # 查询每个指数下费率最低的商务品
                        query_lowest_fee = f"""
                        WITH ranked_fee AS (
                            SELECT 
                                i.code,
                                i.tracking_index_code,
                                i.fund_manager,
                                i.manager_short,
                                i.management_fee_rate,
                                ROW_NUMBER() OVER (PARTITION BY i.tracking_index_code ORDER BY i.management_fee_rate ASC) as fee_rank
                            FROM etf_info i
                            JOIN etf_business b ON i.code = b.code
                            WHERE i.tracking_index_code IN ({index_codes_str})
                        )
                        SELECT 
                            code,
                            tracking_index_code,
                            fund_manager,
                            manager_short,
                            management_fee_rate
                        FROM ranked_fee
                        WHERE fee_rank = 1
                        """
                        cursor.execute(query_lowest_fee)
                        for row in cursor.fetchall():
                            code, tracking_index_code, fund_manager, manager_short, fee_rate = row
                            lowest_fee_business[tracking_index_code] = {
                                'code': code,
                                'manager': manager_short or fund_manager,
                                'fee_rate': fee_rate
                            }
                    except Exception as e:
                        print(f"查询替补商务品或低费率商务品时出错: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                for item in favorites_data:
                    # 获取该ETF的交易量
                    etf_volume = 0
                    try:
                        volume_query = "SELECT market_volume FROM etf_info WHERE code = ?"
                        cursor.execute(volume_query, (item['code'],))
                        volume_result = cursor.fetchone()
                        if volume_result and volume_result[0]:
                            etf_volume = float(volume_result[0])
                    except Exception as e:
                        print(f"获取ETF交易量时出错 ({item['code']}): {str(e)}")
                    
                    # 添加替补商务品数据
                    tracking_index_code = item.get('tracking_index_code', '')
                    best_volume_data = best_volume_business.get(tracking_index_code, {})
                    
                    is_max_volume = 0
                    if tracking_index_code and best_volume_data:
                        best_volume_code = best_volume_data.get('code')
                        if best_volume_code != item['code']:  # 如果不是当前ETF
                            best_volume_volume = best_volume_data.get('volume', 0) or 0
                            # 判断商务品交易量是否大于当前ETF
                            if best_volume_volume > etf_volume:
                                is_max_volume = 1
                    
                    # 添加低费率商务品数据
                    lowest_fee_data = lowest_fee_business.get(tracking_index_code, {})
                    lowest_fee_code = lowest_fee_data.get('code')
                    
                    # 转换为前端需要的格式
                    recommendations["favorites"].append({
                        'code': item['code'],
                        'name': item['name'],
                        'attention_count': item['attention_count'],
                        'price_change_rate': item.get('price_change_rate', 0.0),
                        'fund_manager': item['fund_manager'],
                        'manager_short': item.get('manager_short', ''),
                        'fund_size': item.get('fund_size', 0),
                        'tracking_index_code': item.get('tracking_index_code', ''),
                        'tracking_index_name': item.get('tracking_index_name', ''),
                        'tracking_index': item.get('tracking_index_name', ''),
                        'is_business': item.get('is_business', False),
                        'business_text': item.get('business_text', '非商务品'),
                        'management_fee_rate': item.get('management_fee_rate', 0),
                        # 替补商务品信息
                        'best_volume_code': best_volume_data.get('code', ''),
                        'best_volume_manager': best_volume_data.get('manager', ''),
                        'is_business_product': item.get('is_business', False),
                        'is_max_volume': is_max_volume,
                        # 低费率商务品信息
                        'lowest_fee_code': lowest_fee_data.get('code', ''),
                        'lowest_fee_manager': lowest_fee_data.get('manager', ''),
                        'lowest_fee_rate': lowest_fee_data.get('fee_rate', 0)
                    })
                
                print(f"成功加载ETF加自选排行榜数据，共{len(recommendations['favorites'])}条记录")
            else:
                print("没有获取到ETF加自选排行榜数据")
        except Exception as e:
            print(f"获取加自选排行榜数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
        return jsonify({"recommendations": recommendations})
        
    except Exception as e:
        print(f"获取ETF推荐数据出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)})

# 添加一个新函数来获取数据截止日期
def get_data_cutoff_date():
    """从ETF数据文件名获取最新的数据截止日期"""
    try:
        import os
        import re
        import datetime
        
        # 定义可能的数据文件路径模式
        data_file_patterns = [
            'data/ETF_DATA_*.xlsx',
            'data/客户ETF自选人数*.xlsx',
            'data/客户ETF保有量*.xlsx',
            'data/ETF单产品商务协议*.xlsx'
        ]
        
        latest_date = None
        
        # 遍历所有可能的文件模式
        for pattern in data_file_patterns:
            # 使用glob查找匹配的文件
            import glob
            files = glob.glob(pattern)
            
            for file_path in files:
                # 从文件名中提取日期
                date_match = re.search(r'(\d{8})', file_path)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        file_date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
                        if latest_date is None or file_date > latest_date:
                            latest_date = file_date
                    except ValueError:
                        # 日期格式不正确，忽略
                        continue
        
        # 如果找到有效日期，格式化为YYYY.MM.DD
        if latest_date:
            return latest_date.strftime('%Y.%m.%d')
        else:
            # 如果没有找到有效日期，返回当前日期
            return datetime.datetime.now().strftime('%Y.%m.%d')
    except Exception as e:
        print(f"获取数据截止日期出错: {str(e)}")
        # 出错时返回当前日期
        import datetime
        return datetime.datetime.now().strftime('%Y.%m.%d')

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('data/etf_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@search_bp.route('/api/search', methods=['GET'])
def api_search():
    """API搜索ETF（GET方法）"""
    try:
        # 在返回的jsonify结果中查看CORS头
        def add_cors_headers(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            return response
            
        # 调试输出请求信息
        print("\n======= 收到API搜索请求 =======")
        print(f"请求方法: {request.method}")
        print(f"URL参数: {request.args}")
        print("============================\n")
        
        # 获取搜索关键词
        keyword = ''
        
        # 尝试从URL查询参数获取，API使用的是'query'参数
        if request.args and 'query' in request.args:
            keyword = request.args.get('query', '').strip()
            print(f"从URL参数获取关键词: {keyword}")
            
            # 尝试解码URL编码
            try:
                import urllib.parse
                decoded_keyword = urllib.parse.unquote(keyword)
                print(f"原始关键词: '{keyword}'")
                print(f"解码后关键词: '{decoded_keyword}'")
                keyword = decoded_keyword
            except Exception as e:
                print(f"解码关键词时出错: {str(e)}")
        
        # 如果没有关键词，返回错误
        if not keyword:
            print("未提供搜索关键词")
            response = jsonify({"error": "请输入搜索关键词"})
            return add_cors_headers(response)
        
        print(f"最终使用的搜索关键词: '{keyword}'")
        
        # 尝试直接运行公司搜索
        if keyword in ['汇添富', '华夏', '易方达', '南方', '广发', '嘉实', '博时'] or '基金' in keyword or '资管' in keyword:
            print(f"尝试直接进行公司搜索: '{keyword}'")
            db = Database()
            company_results = db.search_by_company(keyword)
            
            if company_results:
                print(f"公司搜索成功，找到{len(company_results)}条结果")
                response = jsonify({
                    'results': normalize_etf_results(company_results),
                    'count': len(company_results),
                    'data_date': get_data_cutoff_date(),
                    'search_type': '基金公司名称',
                    'company_name': keyword
                })
                return add_cors_headers(response)
        
        # 如果公司搜索无结果或不是公司名称，则继续进行其他类型的搜索
        db = Database()
        
        # 获取数据截止日期
        data_date = get_data_cutoff_date()
        
        # 确定搜索类型
        search_type = determine_search_type(keyword)
        print(f"搜索类型: {search_type}")
        
        # 根据搜索类型执行不同的搜索
        if search_type == "ETF基金代码":
            # 处理ETF代码，去掉可能的后缀
            etf_code = keyword
            if '.' in etf_code:
                etf_code = etf_code.split('.')[0]
            elif etf_code.startswith('sh') or etf_code.startswith('sz'):
                etf_code = etf_code[2:]
            print(f"搜索ETF代码: {etf_code}")
            results = db.search_by_etf_code(etf_code)
        elif search_type == "基金公司名称":
            print(f"搜索基金公司: {keyword}")
            results = db.search_by_company(keyword)
        elif search_type == "跟踪指数名称":
            print(f"搜索指数名称: {keyword}")
            results = db.search_by_index_name(keyword)
        else:
            # 通用搜索
            print(f"执行通用搜索: {keyword}")
            results = db.general_search(keyword)
        
        if results:
            # 添加数据截止日期
            if isinstance(results, dict) and 'results' in results:
                results['data_date'] = data_date
            else:
                # 如果结果是列表，则构建新的字典返回
                results = {
                    'results': normalize_etf_results(results),
                    'count': len(results),
                    'data_date': data_date
                }
            
            print(f"搜索成功，返回{results.get('count', len(results.get('results', [])))}条结果")
            response = jsonify(results)
            return add_cors_headers(response)
        else:
            print("搜索无结果")
            response = jsonify({
                'results': [],
                'count': 0,
                'message': '未找到相关ETF',
                'data_date': data_date
            })
            return add_cors_headers(response)
            
    except Exception as e:
        print(f"API搜索处理错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': f'搜索处理错误: {str(e)}',
            'trace': traceback.format_exc()
        }), 500

@search_bp.route('/api/company', methods=['GET'])
def api_company_search():
    """按基金公司搜索ETF（GET方法）"""
    try:
        # 在返回的jsonify结果中查看CORS头
        def add_cors_headers(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            return response
            
        # 调试输出请求信息
        print("\n======= 收到基金公司搜索请求 =======")
        print(f"请求方法: {request.method}")
        print(f"URL参数: {request.args}")
        print("=================================\n")
        
        # 获取搜索关键词
        company = ''
        
        # 尝试从URL查询参数获取
        if request.args and 'name' in request.args:
            company = request.args.get('name', '').strip()
            print(f"从URL参数获取公司名称: {company}")
            
            # 尝试解码URL编码
            try:
                import urllib.parse
                decoded_company = urllib.parse.unquote(company)
                print(f"原始公司名称: '{company}'")
                print(f"解码后公司名称: '{decoded_company}'")
                company = decoded_company
            except Exception as e:
                print(f"解码公司名称时出错: {str(e)}")
        
        # 如果没有关键词，返回错误
        if not company:
            print("未提供基金公司名称")
            response = jsonify({"error": "请输入基金公司名称"})
            return add_cors_headers(response)
        
        print(f"最终使用的基金公司名称: '{company}'")
        
        # 查询数据库
        db = Database()
        company_results = db.search_by_company(company)
        
        # 获取数据截止日期
        data_date = get_data_cutoff_date()
        
        if company_results:
            print(f"公司搜索成功，找到{len(company_results)}条结果")
            response = jsonify({
                'results': normalize_etf_results(company_results),
                'count': len(company_results),
                'data_date': data_date,
                'search_type': '基金公司名称',
                'company_name': company
            })
            return add_cors_headers(response)
        else:
            print("基金公司搜索无结果")
            response = jsonify({
                'results': [],
                'count': 0,
                'message': '未找到该基金公司的ETF产品',
                'data_date': data_date
            })
            return add_cors_headers(response)
            
    except Exception as e:
        print(f"基金公司搜索处理错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': f'搜索处理错误: {str(e)}',
            'trace': traceback.format_exc()
        }), 500

@search_bp.route('/etf_attention_history', methods=['GET'])
def etf_attention_history():
    """返回ETF自选历史数据"""
    code = request.args.get('code', '')
    
    if not code:
        current_app.logger.error("ETF自选历史API: 未提供代码参数")
        return jsonify({"error": "请提供ETF代码"}), 400
    
    try:
        # 记录查询参数
        current_app.logger.info(f"ETF自选历史查询: 代码={code}")
        
        # 获取历史数据
        db = Database()
        results = db.get_etf_attention_history(code)
        
        # 记录结果信息
        current_app.logger.info(f"ETF自选历史查询结果: 代码={code}, 记录数={len(results) if results else 0}")
        
        # 格式化为API响应
        records = []
        for row in results:
            # 记录详细日志以便调试
            current_app.logger.debug(f"处理ETF自选历史记录: {row}")
            
            # 确保记录有效，含有date和attention_count字段
            if row and 'date' in row and 'attention_count' in row:
                records.append({
                    'date': row['date'],
                    'attention_count': row['attention_count']
                })
            else:
                current_app.logger.warning(f"ETF自选历史: 跳过无效记录 {row}")
        
        return jsonify(records)
    except Exception as e:
        current_app.logger.exception(f"ETF自选历史API错误: {str(e)}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500

@search_bp.route('/etf_holders_history', methods=['GET'])
def etf_holders_history():
    """返回ETF持有人历史数据"""
    code = request.args.get('code', '')
    
    if not code:
        current_app.logger.error("ETF持有人历史API: 未提供代码参数")
        return jsonify({"error": "请提供ETF代码"}), 400
    
    try:
        # 记录查询参数
        current_app.logger.info(f"ETF持有人历史查询: 代码={code}")
        
        # 获取历史数据
        db = Database()
        results = db.get_etf_holders_history(code)
        
        # 记录结果信息
        current_app.logger.info(f"ETF持有人历史查询结果: 代码={code}, 记录数={len(results) if results else 0}")
        
        # 格式化为API响应
        records = []
        for row in results:
            # 记录详细日志以便调试
            current_app.logger.debug(f"处理ETF持有人历史记录: {row}")
            
            # 确保记录有效，含有必要字段，直接返回原始数据
            if row and 'date' in row and 'holder_count' in row and 'holding_value' in row:
                records.append({
                    'date': row['date'],
                    'holder_count': row['holder_count'],
                    'holding_value': row['holding_value']  # 直接返回原始值，不做转换
                })
            else:
                current_app.logger.warning(f"ETF持有人历史: 跳过无效记录 {row}")
        
        return jsonify(records)
    except Exception as e:
        current_app.logger.exception(f"ETF持有人历史API错误: {str(e)}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500

