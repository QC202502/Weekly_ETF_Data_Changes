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
            'manager': result.get('manager', ''),
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
            
            'holding_amount_daily_change': result.get('holding_amount_daily_change', 0),  # 持仓份额日变化
            'holding_amount_five_day_change': result.get('holding_amount_five_day_change', 0),  # 持仓份额五日变化
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
            
            print(f"关注度日变化: {first_result['attention_daily_change']}")
            print(f"关注度五日变化: {first_result['attention_five_day_change']}")
            print(f"持仓客户数日变化: {first_result['holder_daily_change']}")
            print(f"持仓客户数五日变化: {first_result['holder_five_day_change']}")
            print(f"持仓份额日变化: {first_result['holding_amount_daily_change']}")
            print(f"持仓份额五日变化: {first_result['holding_amount_five_day_change']}")
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
        
        from services.data_service import get_previous_date_str
        five_days_ago_str = get_previous_date_str(current_date_str, 5)
        previous_date_str = get_previous_date_str(current_date_str, 1)
        
        with get_db_connection() as conn:
            # 构建SQL查询并获取可能匹配的ETF
            results = []
            cursor = conn.cursor()
            
            # 尝试不同的匹配方式
            sql_query = """
            SELECT e.code, e.name, e.manager as fund_manager, e.scale, e.fee_rate, 
                  e.tracking_error, e.index_code, e.index_name, 
                  h.count as holder_count, a.count as attention_count,
                  (SELECT AVG(p.volume) FROM etf_price p 
                   WHERE p.code = e.code AND p.date >= ? AND p.date <= ?) as daily_avg_volume,
                  (SELECT volume FROM etf_price p2 
                   WHERE p2.code = e.code AND p2.date = ?) as daily_volume
            FROM etf_info e
            LEFT JOIN etf_holders h ON e.code = h.code AND h.date = ?
            LEFT JOIN etf_attention a ON e.code = a.code AND a.date = ?
            WHERE e.code LIKE ? OR e.code LIKE ?
            ORDER BY daily_volume DESC
            """
            cursor.execute(sql_query, (five_days_ago_str, current_date_str, current_date_str, 
                                      current_date_str, current_date_str, 
                                      f"{code}%", f"%{code}%"))
            
            for row in cursor.fetchall():
                etf_code = row['code']
                
                # 获取关注度变化数据
                attention_current = 0
                cursor.execute("SELECT attention_count FROM etf_attention_history WHERE code = ? AND date = ?", 
                              (etf_code, current_date_str))
                current_attention = cursor.fetchone()
                if current_attention:
                    attention_current = current_attention['attention_count'] or 0
                
                attention_previous = 0
                cursor.execute("SELECT attention_count FROM etf_attention_history WHERE code = ? AND date = ?", 
                              (etf_code, previous_date_str))
                prev_attention = cursor.fetchone()
                if prev_attention:
                    attention_previous = prev_attention['attention_count'] or 0
                
                attention_five_days_ago = 0
                cursor.execute("SELECT attention_count FROM etf_attention_history WHERE code = ? AND date = ?", 
                              (etf_code, five_days_ago_str))
                five_days_ago_attention = cursor.fetchone()
                if five_days_ago_attention:
                    attention_five_days_ago = five_days_ago_attention['attention_count'] or 0
                
                # 计算日变化和五日变化
                attention_daily_change = attention_current - attention_previous
                attention_five_day_change = attention_current - attention_five_days_ago
                
                # 获取持仓人数变化数据
                holder_current = row['holder_count'] or 0
                holder_previous = 0
                cursor.execute("SELECT holder_count FROM etf_holders_history WHERE code = ? AND date = ?", 
                              (etf_code, previous_date_str))
                prev_holder = cursor.fetchone()
                if prev_holder:
                    holder_previous = prev_holder['holder_count'] or 0
                
                holder_five_days_ago = 0
                cursor.execute("SELECT holder_count FROM etf_holders_history WHERE code = ? AND date = ?", 
                              (etf_code, five_days_ago_str))
                five_days_ago_holder = cursor.fetchone()
                if five_days_ago_holder:
                    holder_five_days_ago = five_days_ago_holder['holder_count'] or 0
                
                # 计算日变化和五日变化
                holder_daily_change = holder_current - holder_previous
                holder_five_day_change = holder_current - holder_five_days_ago
                
                # 获取持仓份额变化数据
                holding_amount_current = etf_data.get(etf_code, {}).get('holding_amount', 0)
                holding_amount_previous = 0
                cursor.execute("SELECT holding_amount FROM etf_holders_history WHERE code = ? AND date = ?", 
                              (etf_code, previous_date_str))
                prev_holding = cursor.fetchone()
                if prev_holding:
                    holding_amount_previous = prev_holding['holding_amount'] or 0
                
                holding_amount_five_days_ago = 0
                cursor.execute("SELECT holding_amount FROM etf_holders_history WHERE code = ? AND date = ?", 
                              (etf_code, five_days_ago_str))
                five_days_ago_holding = cursor.fetchone()
                if five_days_ago_holding:
                    holding_amount_five_days_ago = five_days_ago_holding['holding_amount'] or 0
                
                # 计算持仓份额的日变化和五日变化
                holding_amount_daily_change = holding_amount_current - holding_amount_previous
                holding_amount_five_day_change = holding_amount_current - holding_amount_five_days_ago
                
                # 获取持仓市值计算数据
                holding_value_current = etf_data.get(etf_code, {}).get('holding_value', 0)
                holding_value_previous = 0
                cursor.execute("SELECT holding_value FROM etf_holders_history WHERE code = ? AND date = ?", 
                              (etf_code, previous_date_str))
                prev_value = cursor.fetchone()
                if prev_value:
                    holding_value_previous = prev_value['holding_value'] or 0
                
                holding_value_five_days_ago = 0
                cursor.execute("SELECT holding_value FROM etf_holders_history WHERE code = ? AND date = ?", 
                              (etf_code, five_days_ago_str))
                five_days_ago_value = cursor.fetchone()
                if five_days_ago_value:
                    holding_value_five_days_ago = five_days_ago_value['holding_value'] or 0
                
                # 计算持仓市值的日变化和五日变化
                holding_value_daily_change = holding_value_current - holding_value_previous
                holding_value_five_day_change = holding_value_current - holding_value_five_days_ago
                
                # 添加一个ETF记录
                etf_record = {
                    'code': etf_code,
                    'name': row['name'],
                    'manager': row['fund_manager'],
                    'fund_size': row['scale'],
                    'management_fee_rate': row['fee_rate'],
                    'tracking_error': row['tracking_error'],
                    'total_holder_count': row['holder_count'],
                    'tracking_index_code': row['index_code'],
                    'tracking_index_name': row['index_name'],
                    'daily_avg_volume': row['daily_avg_volume'],
                    'daily_volume': row['daily_volume'],
                    'holder_count': row['holder_count'],
                    'holding_amount': holding_amount_current,  # 持仓份额
                    'holding_value': holding_value_current,  # 持仓市值
                    'attention_count': attention_current,  # 使用从history表获取的最新自选数据
                    'attention_daily_change': attention_daily_change,
                    'attention_five_day_change': attention_five_day_change,
                    'holder_daily_change': holder_daily_change,
                    'holder_five_day_change': holder_five_day_change,
                    'holding_amount_daily_change': holding_amount_daily_change,  # 持仓份额日变化
                    'holding_amount_five_day_change': holding_amount_five_day_change,  # 持仓份额五日变化
                    'holding_value_daily_change': holding_value_daily_change,  # 持仓市值日变化
                    'holding_value_five_day_change': holding_value_five_day_change,  # 持仓市值五日变化
                    'is_business': etf_code in business_etfs
                }
                
                results.append(etf_record)
        
        return results
    except Exception as e:
        print(f"search_by_etf_code错误: {e}")
        traceback.print_exc()
        return []

def search_by_index_name(keyword, etf_data, business_etfs, current_date_str):
    """按跟踪指数名称搜索"""
    # 查找包含关键词的指数
    matching_indices = etf_data[etf_data['跟踪指数名称'].str.contains(keyword, na=False)]
    
    if matching_indices.empty:
        return []
    
    # 按指数分组
    index_groups = {}
    
    # 获取唯一的指数代码和名称
    unique_indices = matching_indices[['跟踪指数代码', '跟踪指数名称']].drop_duplicates()
    
    # 计算每个指数的总规模
    index_scales = {}
    for index_code in unique_indices['跟踪指数代码']:
        index_etfs = etf_data[etf_data['跟踪指数代码'] == index_code]
        # 使用正确的规模列名
        total_scale = index_etfs['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'].sum()
        index_scales[index_code] = total_scale
    
    # 按指数总规模从大到小排序
    sorted_indices = sorted(unique_indices.to_dict('records'), 
                           key=lambda x: index_scales.get(x['跟踪指数代码'], 0), 
                           reverse=True)
    
    # 从data_service导入当前和上周日期
    from services.data_service import current_date_str, previous_date_str
    
    # 创建结果列表
    etf_results = []
    
    # 为每个指数创建一个组
    for index_info in sorted_indices:
        index_code = index_info['跟踪指数代码']
        index_name = index_info['跟踪指数名称']
        
        # 获取该指数下的所有ETF
        index_etfs = etf_data[etf_data['跟踪指数代码'] == index_code]
        
        # 按区间日均交易量字段从大到小排序
        volume_col = '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元'
        index_etfs = index_etfs.sort_values(by=volume_col, ascending=False)
        
        # 初始化当前指数组
        if index_code not in index_groups:
            index_groups[index_code] = {
                'index_code': index_code,
                'index_name': index_name,
                'etfs': [],
                'total_scale': 0
            }
            
            # 添加指数简介
            index_intro = get_index_intro(index_code)
            if index_intro:
                index_groups[index_code]['index_intro'] = index_intro
        
        # 格式化ETF结果
        for _, row in index_etfs.iterrows():
            etf_code = row['证券代码']
            is_business = etf_code in business_etfs
            
            # 使用带日期的列名
            name_col = f'证券名称（{current_date_str}）'
            
            # 添加新增字段
            attention_current = f'关注人数（{current_date_str}）'
            attention_previous = f'关注人数（{previous_date_str}）'
            holders_current = f'持仓客户数（{current_date_str}）'
            holders_previous = f'持仓客户数（{previous_date_str}）'
            amount_current = f'持仓份额（{current_date_str}）'  # 新增持仓份额字段
            amount_previous = f'持仓份额（{previous_date_str}）'  # 新增持仓份额字段
            value_current = f'持仓市值（{current_date_str}）'  # 修改为持仓市值
            value_previous = f'持仓市值（{previous_date_str}）'  # 修改为持仓市值
            
            # 创建ETF记录
            etf_record = {
                'code': etf_code,
                'name': row[name_col] if name_col in row else row['证券简称'],  # 如果列名不存在，使用证券简称作为备用
                'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
                'fund_size': row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'],
                'management_fee_rate': row['管理费率[单位]%'],
                'tracking_error': row['跟踪误差[单位]%'],
                'tracking_index_code': index_code,
                'tracking_index_name': index_name,
                'total_holder_count': row[holders_current] if holders_current in row else 0,
                'daily_avg_volume': row[volume_col] if volume_col in row else 0,
                'daily_volume': row[f'成交额（{current_date_str}）'] if f'成交额（{current_date_str}）' in row else 0,
                'holder_count': row[holders_current] if holders_current in row else 0,
                'holding_amount': row[amount_current] if amount_current in row else 0,  # 新增持仓份额
                'holding_value': row[value_current] if value_current in row else 0,  # 修改为持仓市值
                'attention_count': row[attention_current] if attention_current in row else 0,
                'attention_daily_change': (row[attention_current] if attention_current in row else 0) - 
                                        (row[attention_previous] if attention_previous in row else 0),
                'attention_five_day_change': 0,  # 需要从历史数据计算
                'holder_daily_change': (row[holders_current] if holders_current in row else 0) - 
                                     (row[holders_previous] if holders_previous in row else 0),
                'holder_five_day_change': 0,  # 需要从历史数据计算
                'holding_amount_daily_change': (row[amount_current] if amount_current in row else 0) - 
                                             (row[amount_previous] if amount_previous in row else 0),  # 新增持仓份额日变化
                'holding_amount_five_day_change': 0,  # 需要从历史数据计算
                'holding_value_daily_change': (row[value_current] if value_current in row else 0) - 
                                            (row[value_previous] if value_previous in row else 0),  # 修改为持仓市值日变化
                'holding_value_five_day_change': 0,  # 需要从历史数据计算
                'is_business': is_business
            }
            
            # 添加ETF到对应指数组
            index_groups[index_code]['etfs'].append(etf_record)
            # 累加该指数的总规模
            index_groups[index_code]['total_scale'] += etf_record['fund_size']
            
            # 添加到扁平结果列表
            etf_results.append(etf_record)
    
    # 更新各组的ETF数量
    for group in index_groups.values():
        group['etf_count'] = len(group['etfs'])
    
    # 将索引组转为列表并按总规模排序
    index_groups_list = list(index_groups.values())
    index_groups_list.sort(key=lambda x: x['total_scale'], reverse=True)
    
    # 返回分组结果
    return {
        'is_grouped': True,
        'index_groups': index_groups_list,
        'index_count': len(index_groups_list),
        'count': len(etf_results),  # 保留原始的扁平结果，以防需要
        'results': etf_results  # 保留原始的扁平结果，以防需要
    }

def search_by_index_code(keyword, etf_data, business_etfs, current_date_str):
    """按跟踪指数代码搜索"""
    # 查找匹配指数代码的ETF
    matching_etfs = etf_data[etf_data['跟踪指数代码'] == keyword]
    
    if matching_etfs.empty:
        # 尝试部分匹配
        matching_etfs = etf_data[etf_data['跟踪指数代码'].str.contains(keyword, na=False)]
    
    if matching_etfs.empty:
        return []
    
    # 使用新的交易量字段排序
    volume_col = '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元'
    matching_etfs = matching_etfs.sort_values(by=volume_col, ascending=False)
    
    # 从data_service导入当前和上周日期
    from services.data_service import current_date_str, previous_date_str
    
    # 格式化结果
    results = []
    for _, row in matching_etfs.iterrows():
        etf_code = row['证券代码']
        is_business = etf_code in business_etfs
        
        # 使用带日期的列名
        name_col = f'证券名称（{current_date_str}）'
        
        # 添加新增字段
        attention_current = f'关注人数（{current_date_str}）'
        attention_previous = f'关注人数（{previous_date_str}）'
        holders_current = f'持仓客户数（{current_date_str}）'
        holders_previous = f'持仓客户数（{previous_date_str}）'
        amount_current = f'持仓份额（{current_date_str}）'  # 新增持仓份额字段
        amount_previous = f'持仓份额（{previous_date_str}）'  # 新增持仓份额字段
        value_current = f'持仓市值（{current_date_str}）'  # 修改为持仓市值
        value_previous = f'持仓市值（{previous_date_str}）'  # 修改为持仓市值
        
        results.append({
            'code': etf_code,
            'name': row[name_col] if name_col in row else row['证券代码'],  # 如果列名不存在，使用证券代码作为备用
            'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
            'fund_size': row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'],
            'management_fee_rate': row['管理费率[单位]%'],
            'tracking_error': row['跟踪误差[单位]%'],
            'tracking_index_code': keyword,
            'tracking_index_name': row['跟踪指数名称'],
            'total_holder_count': row[holders_current] if holders_current in row else 0,
            'daily_avg_volume': row[volume_col] if volume_col in row else 0,
            'daily_volume': row[f'成交额（{current_date_str}）'] if f'成交额（{current_date_str}）' in row else 0,
            'holder_count': row[holders_current] if holders_current in row else 0,
            'holding_amount': row[amount_current] if amount_current in row else 0,  # 新增持仓份额
            'holding_value': row[value_current] if value_current in row else 0,  # 修改为持仓市值
            'attention_count': row[attention_current] if attention_current in row else 0,
            'attention_daily_change': (row[attention_current] if attention_current in row else 0) - 
                                    (row[attention_previous] if attention_previous in row else 0),
            'attention_five_day_change': 0,  # 需要从历史数据计算
            'holder_daily_change': (row[holders_current] if holders_current in row else 0) - 
                                 (row[holders_previous] if holders_previous in row else 0),
            'holder_five_day_change': 0,  # 需要从历史数据计算
            'holding_amount_daily_change': (row[amount_current] if amount_current in row else 0) - 
                                         (row[amount_previous] if amount_previous in row else 0),  # 新增持仓份额日变化
            'holding_amount_five_day_change': 0,  # 需要从历史数据计算
            'holding_value_daily_change': (row[value_current] if value_current in row else 0) - 
                                        (row[value_previous] if value_previous in row else 0),  # 修改为持仓市值日变化
            'holding_value_five_day_change': 0,  # 需要从历史数据计算
            'is_business': is_business
        })
    
    return results

def search_by_company(keyword, etf_data, business_etfs, current_date_str):
    """按基金公司名称搜索"""
    # 查找匹配基金公司的ETF
    matching_etfs = etf_data[etf_data['基金管理人'].str.contains(keyword, na=False)]
    
    if matching_etfs.empty:
        return []
    
    # 使用新的交易量字段排序
    volume_col = '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元'
    matching_etfs = matching_etfs.sort_values(by=volume_col, ascending=False)
    
    # 从data_service导入当前和上周日期
    from services.data_service import current_date_str, previous_date_str
    
    # 格式化结果
    results = []
    for _, row in matching_etfs.iterrows():
        etf_code = row['证券代码']
        is_business = etf_code in business_etfs
        
        # 使用带日期的列名
        name_col = f'证券名称（{current_date_str}）'
        
        # 添加新增字段
        attention_current = f'关注人数（{current_date_str}）'
        attention_previous = f'关注人数（{previous_date_str}）'
        holders_current = f'持仓客户数（{current_date_str}）'
        holders_previous = f'持仓客户数（{previous_date_str}）'
        amount_current = f'持仓份额（{current_date_str}）'  # 新增持仓份额字段
        amount_previous = f'持仓份额（{previous_date_str}）'  # 新增持仓份额字段
        value_current = f'持仓市值（{current_date_str}）'  # 修改为持仓市值
        value_previous = f'持仓市值（{previous_date_str}）'  # 修改为持仓市值
        
        results.append({
            'code': etf_code,
            'name': row[name_col] if name_col in row else row['证券代码'],  # 如果列名不存在，使用证券代码作为备用
            'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
            'fund_size': row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'],
            'management_fee_rate': row['管理费率[单位]%'],
            'tracking_error': row['跟踪误差[单位]%'],
            'tracking_index_code': row['跟踪指数代码'],
            'tracking_index_name': row['跟踪指数名称'],
            'total_holder_count': row[holders_current] if holders_current in row else 0,
            'daily_avg_volume': row[volume_col] if volume_col in row else 0,
            'daily_volume': row[f'成交额（{current_date_str}）'] if f'成交额（{current_date_str}）' in row else 0,
            'holder_count': row[holders_current] if holders_current in row else 0,
            'holding_amount': row[amount_current] if amount_current in row else 0,  # 新增持仓份额
            'holding_value': row[value_current] if value_current in row else 0,  # 修改为持仓市值
            'attention_count': row[attention_current] if attention_current in row else 0,
            'attention_daily_change': (row[attention_current] if attention_current in row else 0) - 
                                    (row[attention_previous] if attention_previous in row else 0),
            'attention_five_day_change': 0,  # 需要从历史数据计算
            'holder_daily_change': (row[holders_current] if holders_current in row else 0) - 
                                 (row[holders_previous] if holders_previous in row else 0),
            'holder_five_day_change': 0,  # 需要从历史数据计算
            'holding_amount_daily_change': (row[amount_current] if amount_current in row else 0) - 
                                         (row[amount_previous] if amount_previous in row else 0),  # 新增持仓份额日变化
            'holding_amount_five_day_change': 0,  # 需要从历史数据计算
            'holding_value_daily_change': (row[value_current] if value_current in row else 0) - 
                                        (row[value_previous] if value_previous in row else 0),  # 修改为持仓市值日变化
            'holding_value_five_day_change': 0,  # 需要从历史数据计算
            'is_business': is_business
        })
        
        # 按跟踪指数分组
        index_code = row['跟踪指数代码']
        index_name = row['跟踪指数名称']
        
        if index_code not in index_groups:
            index_groups[index_code] = {
                'index_code': index_code,
                'index_name': index_name,
                'etfs': [],
                'total_scale': 0
            }
        
        # 添加ETF到对应指数组
        index_groups[index_code]['etfs'].append(etf_record)
        # 累加该指数的总规模
        index_groups[index_code]['total_scale'] += etf_record['fund_size']
    
    # 将索引组转为列表并按总规模排序
    index_groups_list = list(index_groups.values())
    index_groups_list.sort(key=lambda x: x['total_scale'], reverse=True)
    
    # 对每个指数组内的ETF按交易量排序
    for group in index_groups_list:
        group['etfs'].sort(key=lambda x: x['daily_avg_volume'], reverse=True)
        group['etf_count'] = len(group['etfs'])
    
    return {
        'is_grouped': True,
        'index_groups': index_groups_list,
        'index_count': len(index_groups_list),
        'count': sum(len(group['etfs']) for group in index_groups_list)
    }

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
    
    try:
        # 准备推荐榜单数据
        recommendations = {
            "attention": [],  # 本周新增关注TOP20
            "holders": [],    # 本周新增持仓客户TOP20
            "value": [],     # 本周新增保有价值TOP20
            "price_return": [] # 最新交易日涨幅最大的ETF
        }
        
        # 初始化数据库连接
        db = Database()
        conn = None
        
        try:
            conn = db.connect()
            cursor = conn.cursor()
            
            # 使用当前日期作为交易日期
            current_date = datetime.now()
            recommendations["trade_date"] = f"{current_date.month}月{current_date.day}日"
            
            # 1. 获取涨幅最大的ETF (Top 20 Gainers)
            # 为每个指数只选取涨幅最大的一个ETF
            cursor.execute("""
                SELECT p.code, i.name, p.change_rate, i.tracking_index_code, i.fund_manager, 
                       CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business,
                       i.fund_size
                FROM etf_price p
                JOIN etf_info i ON p.code = i.code
                LEFT JOIN etf_business b ON p.code = b.code
                WHERE p.change_rate IS NOT NULL
                ORDER BY p.change_rate DESC
            """)
            
            results = cursor.fetchall()
            processed_indices = set()  # 记录已处理的指数代码
            count = 0
            
            for row in results:
                code, name, change_rate, tracking_index_code, manager, is_business, scale = row
                
                # 如果已经处理过该指数，则跳过
                if tracking_index_code in processed_indices:
                    continue
                
                # 添加到结果集
                recommendations["price_return"].append({
                    'code': code,
                    'name': name,
                    'change_rate': round(float(change_rate) * 100, 2) if change_rate else 0,
                    'manager': manager,
                    'is_business': bool(is_business),
                'business_text': "商务品" if is_business else "非商务品",
                    'index_code': tracking_index_code,
                    'scale': round(float(scale), 2) if scale else 0,
                    'type': 'gainers'
                })
                
                # 记录已处理的指数
                if tracking_index_code:
                    processed_indices.add(tracking_index_code)
                count += 1
                
                # 只取前20个
                if count >= 20:
                    break
            
            print(f"成功加载ETF价格推荐数据，共{len(recommendations['price_return'])}条记录，交易日期：{recommendations['trade_date']}")
            
            # 因为历史表中可能没有数据，以下部分暂时注释
            # 后续可以从etf_attention、etf_holders表中直接获取数据
            
            # 2. 尝试获取关注数据
            try:
                cursor.execute("""
                    SELECT a.code, i.name, a.attention_count, i.fund_manager, i.fund_size, i.tracking_index_code,
                           CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business
                    FROM etf_attention a
                    JOIN etf_info i ON a.code = i.code
                    LEFT JOIN etf_business b ON a.code = b.code
                    ORDER BY a.attention_count DESC
                    LIMIT 20
                """)
                
                for row in cursor.fetchall():
                    code, name, attention_count, manager, scale, tracking_index_code, is_business = row
                    
                    recommendations["attention"].append({
                        'code': code,
                        'name': name,
                        'attention_change': int(attention_count) if attention_count else 0,  # 使用总数而非变化
                        'manager': manager,
                        'scale': round(float(scale), 2) if scale else 0,
                        'is_business': bool(is_business),
                'business_text': "商务品" if is_business else "非商务品",
                        'index_code': tracking_index_code,
                        'type': 'attention'
                    })
                
                print(f"成功加载ETF关注推荐数据，共{len(recommendations['attention'])}条记录")
            except Exception as e:
                print(f"获取关注数据出错: {str(e)}")
            
            # 3. 尝试获取持有人数据
            try:
                cursor.execute("""
                    SELECT h.code, i.name, h.holder_count, i.fund_manager, i.fund_size, i.tracking_index_code,
                           CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business
                    FROM etf_holders h
                    JOIN etf_info i ON h.code = i.code
                    LEFT JOIN etf_business b ON h.code = b.code
                    ORDER BY h.holder_count DESC
                    LIMIT 20
                """)
                
                for row in cursor.fetchall():
                    code, name, holder_count, manager, scale, tracking_index_code, is_business = row
                    
                    recommendations["holders"].append({
                        'code': code,
                        'name': name,
                        'holders_change': int(holder_count) if holder_count else 0,  # 使用总数而非变化
                        'manager': manager,
                        'scale': round(float(scale), 2) if scale else 0,
                        'is_business': bool(is_business),
                        'business_text': "商务品" if is_business else "非商务品",
                        'index_code': tracking_index_code,
                        'type': 'holders'
                    })
                
                print(f"成功加载ETF持有人推荐数据，共{len(recommendations['holders'])}条记录")
            except Exception as e:
                print(f"获取持有人数据出错: {str(e)}")
            
            # 4. 尝试获取保有价值数据
            try:
                cursor.execute("""
                    SELECT h.code, i.name, h.holding_value, i.fund_manager, i.fund_size, i.tracking_index_code,
                           CASE WHEN b.code IS NOT NULL THEN 1 ELSE 0 END as is_business
                    FROM etf_holders h
                    JOIN etf_info i ON h.code = i.code
                    LEFT JOIN etf_business b ON h.code = b.code
                    WHERE h.holding_value IS NOT NULL
                    ORDER BY h.holding_value DESC
                    LIMIT 20
                """)
                
                for row in cursor.fetchall():
                    code, name, holding_value, manager, scale, tracking_index_code, is_business = row
                    
                    # 转换为亿元单位
                    holding_value_billion = round(float(holding_value) / 1e8, 2) if holding_value else 0
                    
                    recommendations["value"].append({
                        'code': code,
                        'name': name,
                        'holding_value_change': holding_value_billion,  # 使用总数而非变化
                        'manager': manager,
                        'scale': round(float(scale), 2) if scale else 0,
                        'is_business': bool(is_business),
                        'business_text': "商务品" if is_business else "非商务品",
                        'index_code': tracking_index_code,
                        'type': 'value'
                    })
                
                print(f"成功加载ETF保有价值推荐数据，共{len(recommendations['value'])}条记录")
            except Exception as e:
                print(f"获取保有价值数据出错: {str(e)}")
                
        except Exception as e:
            print(f"获取推荐数据出错: {str(e)}")
            traceback.print_exc()
        
        finally:
            # 关闭数据库连接
            if conn:
                conn.close()
        
        return jsonify({
            "success": True,
            "recommendations": recommendations
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"获取推荐数据出错：{str(e)}"})

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
            
            # 确保记录有效，含有必要字段
            if row and 'date' in row and 'holder_count' in row and 'holding_value' in row:
                records.append({
                    'date': row['date'],
                    'holder_count': row['holder_count'],
                    'holding_value': row['holding_value']
                })
            else:
                current_app.logger.warning(f"ETF持有人历史: 跳过无效记录 {row}")
        
        return jsonify(records)
    except Exception as e:
        current_app.logger.exception(f"ETF持有人历史API错误: {str(e)}")
        return jsonify({"error": f"获取数据失败: {str(e)}"}), 500

@search_bp.route('/etf_fund_size_history', methods=['GET'])
def etf_fund_size_history():
    """获取ETF规模历史数据"""
    try:
        # 获取ETF代码
        etf_code = request.args.get('code', '')
        if not etf_code:
            return jsonify({"error": "请提供ETF代码"})
        
        # 查询数据库
        db = Database()
        history_data = db.get_etf_fund_size_history(etf_code)
        
        return jsonify(history_data)
    except Exception as e:
        print(f"获取ETF规模历史数据出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"获取ETF规模历史数据出错: {str(e)}"})

def general_search(keyword, etf_data, business_etfs, current_date_str):
    """通用搜索，尝试多种匹配方式"""
    try:
        # 处理可能带有后缀的ETF代码
        etf_code = keyword
        if '.' in etf_code:
            etf_code = etf_code.split('.')[0]
        elif etf_code.startswith('sh') or etf_code.startswith('sz'):
            etf_code = etf_code[2:]
        
        # 从data_service导入当前和上周日期
        from services.data_service import current_date_str, previous_date_str
        
        # 尝试不同的匹配方式
        matching_etfs = pd.DataFrame()
        
        # 1. 尝试ETF代码匹配
        if etf_code.isdigit() and len(etf_code) == 6:
            code_matches = etf_data[etf_data['证券代码'].str.contains(etf_code, na=False)]
            if not code_matches.empty:
                matching_etfs = code_matches
        
        # 2. 尝试ETF名称匹配
        if matching_etfs.empty:
            name_matches = etf_data[etf_data['证券名称'].str.contains(keyword, na=False)]
            if not name_matches.empty:
                matching_etfs = name_matches
        
        # 3. 尝试指数名称匹配
        if matching_etfs.empty:
            index_matches = etf_data[etf_data['跟踪指数名称'].str.contains(keyword, na=False)]
            if not index_matches.empty:
                matching_etfs = index_matches
        
        # 4. 尝试基金公司名称匹配
        if matching_etfs.empty:
            company_matches = etf_data[etf_data['基金管理人'].str.contains(keyword, na=False)]
            if not company_matches.empty:
                matching_etfs = company_matches
        
        if matching_etfs.empty:
            return []
        
        # 使用新的交易量字段排序
        volume_col = '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元'
        matching_etfs = matching_etfs.sort_values(by=volume_col, ascending=False)
        
        # 格式化结果
        results = []
        for _, row in matching_etfs.iterrows():
            etf_code = row['证券代码']
            is_business = etf_code in business_etfs
            
            # 使用带日期的列名
            name_col = f'证券名称（{current_date_str}）'
            
            # 添加新增字段
            attention_current = f'关注人数（{current_date_str}）'
            attention_previous = f'关注人数（{previous_date_str}）'
            holders_current = f'持仓客户数（{current_date_str}）'
            holders_previous = f'持仓客户数（{previous_date_str}）'
            amount_current = f'持仓份额（{current_date_str}）'  # 新增持仓份额字段
            amount_previous = f'持仓份额（{previous_date_str}）'  # 新增持仓份额字段
            value_current = f'持仓市值（{current_date_str}）'  # 修改为持仓市值
            value_previous = f'持仓市值（{previous_date_str}）'  # 修改为持仓市值
            
            results.append({
                'code': etf_code,
                'name': row[name_col] if name_col in row else row['证券代码'],  # 如果列名不存在，使用证券代码作为备用
                'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
                'fund_size': row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'],
                'management_fee_rate': row['管理费率[单位]%'],
                'tracking_error': row['跟踪误差[单位]%'],
                'tracking_index_code': row['跟踪指数代码'],
                'tracking_index_name': row['跟踪指数名称'],
                'total_holder_count': row[holders_current] if holders_current in row else 0,
                'daily_avg_volume': row[volume_col] if volume_col in row else 0,
                'daily_volume': row[f'成交额（{current_date_str}）'] if f'成交额（{current_date_str}）' in row else 0,
                'holder_count': row[holders_current] if holders_current in row else 0,
                'holding_amount': row[amount_current] if amount_current in row else 0,  # 新增持仓份额
                'holding_value': row[value_current] if value_current in row else 0,  # 修改为持仓市值
                'attention_count': row[attention_current] if attention_current in row else 0,
                'attention_daily_change': (row[attention_current] if attention_current in row else 0) - 
                                        (row[attention_previous] if attention_previous in row else 0),
                'attention_five_day_change': 0,  # 需要从历史数据计算
                'holder_daily_change': (row[holders_current] if holders_current in row else 0) - 
                                     (row[holders_previous] if holders_previous in row else 0),
                'holder_five_day_change': 0,  # 需要从历史数据计算
                'holding_amount_daily_change': (row[amount_current] if amount_current in row else 0) - 
                                             (row[amount_previous] if amount_previous in row else 0),  # 新增持仓份额日变化
                'holding_amount_five_day_change': 0,  # 需要从历史数据计算
                'holding_value_daily_change': (row[value_current] if value_current in row else 0) - 
                                            (row[value_previous] if value_previous in row else 0),  # 修改为持仓市值日变化
                'holding_value_five_day_change': 0,  # 需要从历史数据计算
                'is_business': is_business
            })
        
        return results
    except Exception as e:
        print(f"general_search错误: {e}")
        traceback.print_exc()
        return []