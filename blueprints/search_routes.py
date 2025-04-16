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
    
    # 处理业务ETF标记
    if isinstance(results, dict) and 'results' in results:
        for etf in results['results']:
            etf['is_business'] = etf['code'] in business_etfs
    
    return results

def search_by_index_code(keyword, etf_data, business_etfs, current_date_str):
    """按指数代码搜索"""
    # 创建数据库连接
    db = Database()
    # 直接调用数据库模型中的search_by_index_code方法
    results = db.search_by_index_code(keyword)
    
    # 处理业务ETF标记
    if isinstance(results, dict) and 'results' in results:
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
            try:
                # 获取最新的交易日期
                cursor.execute("SELECT MAX(date) FROM etf_price")
                latest_date = cursor.fetchone()[0]
                
                if latest_date:
                    recommendations["trade_date"] = f"{datetime.strptime(latest_date, '%Y-%m-%d').month}月{datetime.strptime(latest_date, '%Y-%m-%d').day}日"
                
                # 使用子查询先按跟踪指数分组选出每组涨幅最高的ETF
                query = """
                SELECT i1.code, i1.name, p1.change_rate, i1.tracking_index_code, i1.tracking_index_name, 
                       i1.fund_manager, i1.fund_size,
                       CASE WHEN b1.code IS NOT NULL THEN 1 ELSE 0 END as is_business
                FROM etf_price p1
                JOIN etf_info i1 ON p1.code = i1.code
                LEFT JOIN etf_business b1 ON p1.code = b1.code
                JOIN (
                    SELECT i.tracking_index_code, MAX(p.change_rate) as max_change_rate
                    FROM etf_price p
                    JOIN etf_info i ON p.code = i.code
                    WHERE p.date = ? AND i.tracking_index_code IS NOT NULL AND i.tracking_index_code != ''
                    GROUP BY i.tracking_index_code
                ) sub ON i1.tracking_index_code = sub.tracking_index_code AND p1.change_rate = sub.max_change_rate
                WHERE p1.date = ?
                ORDER BY p1.change_rate DESC
                LIMIT 20
                """
                
                cursor.execute(query, (latest_date, latest_date))
                results = cursor.fetchall()
                
                for row in results:
                    code, name, change_rate, tracking_index_code, tracking_index_name, manager, scale, is_business = row
                    
                    # 添加到结果集
                    recommendations["price_return"].append({
                        'code': code,
                        'name': name,
                        'change_rate': round(float(change_rate) * 100, 2) if change_rate else 0,
                        'manager': manager,
                        'is_business': bool(is_business),
                        'business_text': "商务品" if is_business else "非商务品",
                        'index_code': tracking_index_code,
                        'index_name': tracking_index_name or tracking_index_code,
                        'scale': round(float(scale), 2) if scale else 0,
                        'type': 'price_return'
                    })
                
                print(f"成功加载ETF价格推荐数据，共{len(recommendations['price_return'])}条记录，交易日期：{recommendations['trade_date']}")
                
            except Exception as e:
                print(f"获取涨幅数据出错: {str(e)}")
                traceback.print_exc()
            
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

