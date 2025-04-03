from flask import Blueprint, jsonify, request
import pandas as pd
import traceback
from datetime import datetime
from services.index_service import get_index_intro, get_index_info
from database.models import Database
import re
import json
import traceback  # 确保导入traceback模块

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
    """标准化ETF搜索结果，确保所有必要字段都存在"""
    normalized_results = []
    
    print("\n===== normalize_etf_results被调用 =====")
    print(f"接收到{len(results)}条原始结果")
    
    for result in results:
        # 创建一个标准化的ETF数据对象
        normalized_etf = {
            'code': result.get('code', ''),
            'name': result.get('name', ''),
            'manager': result.get('manager', result.get('fund_manager', '')),
            'fund_size': float(result.get('fund_size', result.get('scale', 0))),
            'management_fee_rate': float(result.get('management_fee_rate', result.get('fee_rate', 0))),
            'tracking_error': float(result.get('tracking_error', 0)),
            'total_holder_count': int(result.get('total_holder_count', result.get('holders_count', 0))),
            'attention_count': int(result.get('attention_count', 0)),
            'is_business': bool(result.get('is_business')),
            'business_text': result.get('business_text', '商务品' if result.get('is_business') else '非商务品'),
            'tracking_index_code': result.get('tracking_index_code', result.get('index_code', '')),
            'tracking_index_name': result.get('tracking_index_name', result.get('index_name', '')),
            'holder_count': int(result.get('holder_count', 0)),
            'holding_amount': float(result.get('holding_amount', 0)),
            'daily_avg_volume': float(result.get('daily_avg_volume', 0)),
            'daily_volume': float(result.get('daily_volume', 0))
        }
        
        # 打印第一个结果的持仓人数和持仓金额
        if len(normalized_results) == 0:
            print(f"第一个结果的代码: {normalized_etf['code']}")
            print(f"持仓人数: {normalized_etf['holder_count']}")
            print(f"持仓金额: {normalized_etf['holding_amount']}")
            print(f"区间日均成交额: {normalized_etf['daily_avg_volume']}")
            print(f"最近交易日成交额: {normalized_etf['daily_volume']}")
        
        normalized_results.append(normalized_etf)
    
    print(f"返回{len(normalized_results)}条标准化结果")
    print("====================================\n")
    
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

def search_by_etf_code(keyword, etf_data, business_etfs, current_date_str):
    """按ETF基金代码搜索"""
    # 处理可能带有sh/sz前缀的ETF代码
    etf_code = keyword
    if keyword.startswith('sh') or keyword.startswith('sz'):
        etf_code = keyword[2:]
        print(f"处理带前缀的ETF代码: {keyword} -> {etf_code}")
    
    # 精确匹配ETF代码
    target_etf = etf_data[etf_data['证券代码'] == etf_code]
    
    if target_etf.empty:
        return []
    
    # 使用新的交易量字段排序
    volume_col = '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元'
    target_etf = target_etf.sort_values(by=volume_col, ascending=False)
    
    # 从data_service导入当前和上周日期
    from services.data_service import current_date_str, previous_date_str
    
    # 格式化结果
    results = []
    for _, row in target_etf.iterrows():
        etf_code = row['证券代码']
        is_business = etf_code in business_etfs
        
        # 使用带日期的列名
        name_col = f'证券名称（{current_date_str}）'
        
        # 添加新增字段
        attention_current = f'关注人数（{current_date_str}）'
        attention_previous = f'关注人数（{previous_date_str}）'
        holders_current = f'持仓客户数（{current_date_str}）'
        holders_previous = f'持仓客户数（{previous_date_str}）'
        amount_current = f'保有金额（{current_date_str}）'
        amount_previous = f'保有金额（{previous_date_str}）'
        
        results.append({
            'code': etf_code,
            'name': row[name_col] if name_col in row else row['证券代码'],  # 如果列名不存在，使用证券代码作为备用
            'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
            'volume': round(float(row[volume_col]) if pd.notna(row[volume_col]) else 0, 2),  # 已经是亿元单位
            'fee_rate': round(float(row['管理费率[单位]%']) if pd.notna(row['管理费率[单位]%']) else 0, 2),
            'scale': round(float(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) if pd.notna(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) else 0, 2),
            'is_business': is_business,
            'business_text': "商务品" if is_business else "非商务品",
            'index_code': row['跟踪指数代码'],
            'index_name': row['跟踪指数名称'],
            'attention_count': int(row[attention_current]) if pd.notna(row[attention_current]) else 0,
            'attention_change': int(row[attention_current] - row[attention_previous]) if pd.notna(row[attention_current]) and pd.notna(row[attention_previous]) else 0,
            'holders_count': int(row[holders_current]) if pd.notna(row[holders_current]) else 0,
            'holders_change': int(row[holders_current] - row[holders_previous]) if pd.notna(row[holders_current]) and pd.notna(row[holders_previous]) else 0,
            'amount': round(float(row[amount_current]) / 1e8 if pd.notna(row[amount_current]) else 0, 2),  # 转换为亿元
            'amount_change': round(float(row[amount_current] - row[amount_previous]) / 1e8 if pd.notna(row[amount_current]) and pd.notna(row[amount_previous]) else 0, 2)  # 转换为亿元
        })
    
    return results

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
            amount_current = f'保有金额（{current_date_str}）'
            amount_previous = f'保有金额（{previous_date_str}）'
            
            # 创建ETF记录
            etf_record = {
                'code': etf_code,
                'name': row[name_col] if name_col in row else row['证券简称'],  # 如果列名不存在，使用证券简称作为备用
                'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
                'fund_size': round(float(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) if pd.notna(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) else 0, 2),
                'management_fee_rate': round(float(row['管理费率[单位]%']) if pd.notna(row['管理费率[单位]%']) else 0, 2),
                'tracking_error': round(float(row['年化跟踪误差阈值(业绩基准)[单位]%']) if pd.notna(row['年化跟踪误差阈值(业绩基准)[单位]%']) else 0, 2),
                'total_holder_count': int(row['基金份额持有人户数[报告期]20240630[单位]户']) if pd.notna(row['基金份额持有人户数[报告期]20240630[单位]户']) else 0,
                'tracking_index_code': index_code,
                'tracking_index_name': index_name,
                'is_business': is_business,
                'business_text': "商务品" if is_business else "非商务品",
                'attention_count': int(row[attention_current]) if pd.notna(row[attention_current]) else 0,
                'attention_change': int(row[attention_current] - row[attention_previous]) if pd.notna(row[attention_current]) and pd.notna(row[attention_previous]) else 0,
                'holder_count': int(row[holders_current]) if pd.notna(row[holders_current]) else 0,
                'holders_change': int(row[holders_current] - row[holders_previous]) if pd.notna(row[holders_current]) and pd.notna(row[holders_previous]) else 0,
                'amount': round(float(row[amount_current]) / 1e8 if pd.notna(row[amount_current]) else 0, 2),
                'amount_change': round(float(row[amount_current] - row[amount_previous]) / 1e8 if pd.notna(row[amount_current]) and pd.notna(row[amount_previous]) else 0, 2),
                'daily_avg_volume': round(float(row[volume_col]) if pd.notna(row[volume_col]) else 0, 2),
                'daily_volume': round(float(row['成交额[交易日期]最新收盘日[单位]亿元']) if pd.notna(row['成交额[交易日期]最新收盘日[单位]亿元']) else 0, 2)
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
        'count': len(etf_results),
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
        amount_current = f'保有金额（{current_date_str}）'
        amount_previous = f'保有金额（{previous_date_str}）'
        
        results.append({
            'code': etf_code,
            'name': row[name_col] if name_col in row else row['证券代码'],  # 如果列名不存在，使用证券代码作为备用
            'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
            # 使用新的交易量字段
            'volume': round(float(row[volume_col]) if pd.notna(row[volume_col]) else 0, 2),  # 是已经是亿元单位
            'fee_rate': round(float(row['管理费率[单位]%']) if pd.notna(row['管理费率[单位]%']) else 0, 2),
            'scale': round(float(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) if pd.notna(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) else 0, 2),
            'is_business': is_business,
            'business_text': "商务品" if is_business else "非商务品",
            'index_code': row['跟踪指数代码'],
            'index_name': row['跟踪指数名称'],
            # 新增字段
            'attention_count': int(row[attention_current]) if pd.notna(row[attention_current]) else 0,
            'attention_change': int(row[attention_current] - row[attention_previous]) if pd.notna(row[attention_current]) and pd.notna(row[attention_previous]) else 0,
            'holders_count': int(row[holders_current]) if pd.notna(row[holders_current]) else 0,
            'holders_change': int(row[holders_current] - row[holders_previous]) if pd.notna(row[holders_current]) and pd.notna(row[holders_previous]) else 0,
            'amount': round(float(row[amount_current]) / 1e8 if pd.notna(row[amount_current]) else 0, 2),  # 转换为亿元
            'amount_change': round(float(row[amount_current] - row[amount_previous]) / 1e8 if pd.notna(row[amount_current]) and pd.notna(row[amount_previous]) else 0, 2)  # 转换为亿元
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
        amount_current = f'保有金额（{current_date_str}）'
        amount_previous = f'保有金额（{previous_date_str}）'
        
        results.append({
            'code': etf_code,
            'name': row[name_col] if name_col in row else row['证券代码'],  # 如果列名不存在，使用证券代码作为备用
            'index_code': row['跟踪指数代码'],
            'index_name': row['跟踪指数名称'],
            # 使用新的交易量字段
            'volume': round(float(row[volume_col]) if pd.notna(row[volume_col]) else 0, 2),  # 已经是亿元单位
            'fee_rate': round(float(row['管理费率[单位]%']) if pd.notna(row['管理费率[单位]%']) else 0, 2),
            'scale': round(float(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) if pd.notna(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) else 0, 2),
            'is_business': is_business,
            'business_text': "商务品" if is_business else "非商务品",
            # 新增字段
            'attention_count': int(row[attention_current]) if pd.notna(row[attention_current]) else 0,
            'attention_change': int(row[attention_current] - row[attention_previous]) if pd.notna(row[attention_current]) and pd.notna(row[attention_previous]) else 0,
            'holders_count': int(row[holders_current]) if pd.notna(row[holders_current]) else 0,
            'holders_change': int(row[holders_current] - row[holders_previous]) if pd.notna(row[holders_current]) and pd.notna(row[holders_previous]) else 0,
            'amount': round(float(row[amount_current]) / 1e8 if pd.notna(row[amount_current]) else 0, 2),  # 转换为亿元
            'amount_change': round(float(row[amount_current] - row[amount_previous]) / 1e8 if pd.notna(row[amount_current]) and pd.notna(row[amount_previous]) else 0, 2)  # 转换为亿元
        })
    
    return results

def general_search(keyword, etf_data, business_etfs, current_date_str):
    """通用搜索"""
    # 处理可能带有sh/sz前缀的ETF代码
    search_keyword = keyword
    if keyword.startswith('sh') or keyword.startswith('sz'):
        search_keyword = keyword[2:]
        print(f"通用搜索处理带前缀的ETF代码: {keyword} -> {search_keyword}")
    
    # 尝试多种匹配方式
    matching_etfs = etf_data[
        etf_data['证券代码'].str.contains(search_keyword, na=False) |
        etf_data['跟踪指数名称'].str.contains(keyword, na=False) |
        etf_data['跟踪指数代码'].str.contains(keyword, na=False) |
        etf_data['基金管理人'].str.contains(keyword, na=False)
    ]
    
    if matching_etfs.empty:
        return []
    
    # 获取匹配的ETF的指数信息并分组
    index_groups = {}
    
    # 从data_service导入当前和上周日期
    from services.data_service import current_date_str, previous_date_str
    
    # 为每个ETF创建记录
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
        amount_current = f'保有金额（{current_date_str}）'
        amount_previous = f'保有金额（{previous_date_str}）'
        
        # 获取交易量字段
        volume_col = '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元'
        
        # 创建ETF记录
        etf_record = {
            'code': etf_code,
            'name': row[name_col] if name_col in row else row['证券代码'],
            'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
            'volume': round(float(row[volume_col]) if pd.notna(row[volume_col]) else 0, 2),
            'fee_rate': round(float(row['管理费率[单位]%']) if pd.notna(row['管理费率[单位]%']) else 0, 2),
            'scale': round(float(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) if pd.notna(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) else 0, 2),
            'is_business': is_business,
            'business_text': "商务品" if is_business else "非商务品",
            'index_code': row['跟踪指数代码'],
            'index_name': row['跟踪指数名称'],
            'attention_count': int(row[attention_current]) if pd.notna(row[attention_current]) else 0,
            'attention_change': int(row[attention_current] - row[attention_previous]) if pd.notna(row[attention_current]) and pd.notna(row[attention_previous]) else 0,
            'holders_count': int(row[holders_current]) if pd.notna(row[holders_current]) else 0,
            'holders_change': int(row[holders_current] - row[holders_previous]) if pd.notna(row[holders_current]) and pd.notna(row[holders_previous]) else 0,
            'amount': round(float(row[amount_current]) / 1e8 if pd.notna(row[amount_current]) else 0, 2),
            'amount_change': round(float(row[amount_current] - row[amount_previous]) / 1e8 if pd.notna(row[amount_current]) and pd.notna(row[amount_previous]) else 0, 2),
            'daily_avg_volume': round(float(row[volume_col]) if pd.notna(row[volume_col]) else 0, 2),
            'daily_volume': round(float(row['最近一天成交额[交易日期]最新收盘日[单位]亿元']) if pd.notna(row['最近一天成交额[交易日期]最新收盘日[单位]亿元']) else 0, 2),
            'tracking_error': round(float(row['跟踪误差[单位]%']) if pd.notna(row['跟踪误差[单位]%']) else 0, 2),
        }
        
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
        index_groups[index_code]['total_scale'] += etf_record['scale']
    
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
    # 从data_service导入数据
    from services.data_service import etf_data, business_etfs, current_date_str, previous_date_str
    import os
    import json
    from datetime import datetime
    
    if etf_data is None:
        return jsonify({"error": "数据未加载，请先加载数据"})
    
    try:
        # 准备推荐榜单数据
        recommendations = {
            "attention": [],  # 本周新增关注TOP20
            "holders": [],   # 本周新增持仓客户TOP20
            "amount": [],    # 本周新增保有金额TOP20
            "price_return": [] # 最新交易日涨幅最大的ETF
        }
        
        # 获取列名
        attention_current = f'关注人数（{current_date_str}）'
        attention_previous = f'关注人数（{previous_date_str}）'
        holders_current = f'持仓客户数（{current_date_str}）'
        holders_previous = f'持仓客户数（{previous_date_str}）'
        amount_current = f'保有金额（{current_date_str}）'
        amount_previous = f'保有金额（{previous_date_str}）'
        name_col = f'证券名称（{current_date_str}）'
        
        # 确保所有必要的列都存在
        required_columns = [attention_current, attention_previous, holders_current, 
                          holders_previous, amount_current, amount_previous]
        
        # 检查列是否存在
        missing_columns = [col for col in required_columns if col not in etf_data.columns]
        if missing_columns:
            print(f"警告：缺少以下列：{missing_columns}")
            return jsonify({"error": "数据列不完整，无法生成推荐"})
        
        # 计算变化值
        etf_data['attention_change'] = etf_data[attention_current] - etf_data[attention_previous]
        etf_data['holders_change'] = etf_data[holders_current] - etf_data[holders_previous]
        etf_data['amount_change'] = (etf_data[amount_current] - etf_data[amount_previous]) / 1e8  # 转换为亿元
        
        # 获取本周新增关注TOP20
        attention_top = etf_data.sort_values(by='attention_change', ascending=False).head(20)
        for _, row in attention_top.iterrows():
            etf_code = row['证券代码']
            is_business = etf_code in business_etfs
            recommendations["attention"].append({
                'code': etf_code,
                'name': row[name_col] if name_col in row else row['证券代码'],
                'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
                'is_business': is_business,
                'business_text': "商务品" if is_business else "非商务品",
                'index_code': row['跟踪指数代码'],
                'scale': round(float(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) if pd.notna(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) else 0, 2),
                'attention_change': int(row['attention_change']) if pd.notna(row['attention_change']) else 0
            })
        
        # 获取本周新增持仓客户TOP20
        holders_top = etf_data.sort_values(by='holders_change', ascending=False).head(20)
        for _, row in holders_top.iterrows():
            etf_code = row['证券代码']
            is_business = etf_code in business_etfs
            recommendations["holders"].append({
                'code': etf_code,
                'name': row[name_col] if name_col in row else row['证券代码'],
                'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
                'is_business': is_business,
                'business_text': "商务品" if is_business else "非商务品",
                'index_code': row['跟踪指数代码'],
                'scale': round(float(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) if pd.notna(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) else 0, 2),
                'holders_change': int(row['holders_change']) if pd.notna(row['holders_change']) else 0
            })
        
        # 获取本周新增保有金额TOP20
        amount_top = etf_data.sort_values(by='amount_change', ascending=False).head(20)
        for _, row in amount_top.iterrows():
            etf_code = row['证券代码']
            is_business = etf_code in business_etfs
            recommendations["amount"].append({
                'code': etf_code,
                'name': row[name_col] if name_col in row else row['证券代码'],
                'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
                'is_business': is_business,
                'business_text': "商务品" if is_business else "非商务品",
                'index_code': row['跟踪指数代码'],
                'scale': round(float(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) if pd.notna(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元']) else 0, 2),
                'amount_change': round(float(row['amount_change']) if pd.notna(row['amount_change']) else 0, 2)
            })
        
        # 尝试加载ETF价格推荐数据
        try:
            # 查找最新的ETF价格推荐数据文件
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
            today = datetime.now().strftime('%Y%m%d')
            price_recommendation_file = os.path.join(data_dir, f"etf_price_recommendations_{today}.json")
            
            # 如果当天的文件不存在，尝试查找最新的推荐数据文件
            if not os.path.exists(price_recommendation_file):
                print(f"当天的ETF价格推荐数据文件不存在: {price_recommendation_file}")
                # 查找匹配模式的最新文件
                latest_file = None
                latest_date = None
                
                for file in os.listdir(data_dir):
                    if file.startswith("etf_price_recommendations_") and file.endswith(".json"):
                        try:
                            # 从文件名中提取日期
                            date_str = file.replace("etf_price_recommendations_", "").replace(".json", "")
                            file_date = datetime.strptime(date_str, "%Y%m%d")
                            if latest_date is None or file_date > latest_date:
                                latest_date = file_date
                                latest_file = os.path.join(data_dir, file)
                        except Exception as e:
                            print(f"解析文件日期出错: {file}, {str(e)}")
                
                # 如果找到了最新文件，使用它
                if latest_file:
                    price_recommendation_file = latest_file
                    print(f"使用最新的ETF价格推荐数据文件: {price_recommendation_file}")
                else:
                    # 如果没找到任何匹配的文件，尝试先获取最新ETF数据，然后生成新的推荐数据
                    print("未找到任何ETF价格推荐数据文件，尝试获取最新数据并生成...")
                    try:
                        # 先尝试获取最新ETF数据
                        from get_latest_etf_data import main as get_latest_data
                        get_latest_result = get_latest_data()
                        if get_latest_result != 0:
                            print("获取最新ETF数据失败，尝试直接生成推荐数据")
                        
                        # 无论获取数据是否成功，都尝试生成推荐
                        from etf_price_recommendation import main as generate_price_recommendations
                        generate_price_recommendations()
                        # 重新检查当天生成的文件
                        price_recommendation_file = os.path.join(data_dir, f"etf_price_recommendations_{today}.json")
                    except Exception as gen_e:
                        print(f"获取最新数据或生成推荐时出错: {str(gen_e)}")
                        import traceback
                        traceback.print_exc()
            
            # 读取ETF价格推荐数据
            if os.path.exists(price_recommendation_file):
                with open(price_recommendation_file, 'r', encoding='utf-8') as f:
                    price_data = json.load(f)
                    recommendations["price_return"] = price_data.get("price_return", [])
                    # 获取交易日期信息
                    recommendations["trade_date"] = price_data.get("trade_date", "3月19日")
                    print(f"成功加载ETF价格推荐数据，共{len(recommendations['price_return'])}条记录，交易日期：{recommendations['trade_date']}")
            else:
                print(f"警告：无法找到或生成ETF价格推荐数据文件")

        except Exception as e:
            print(f"加载ETF价格推荐数据出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
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