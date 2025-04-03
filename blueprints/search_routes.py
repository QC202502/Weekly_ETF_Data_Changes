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
        if request.form:
            keyword = request.form.get('code', '').strip()
            print(f"从表单获取关键词: {keyword}")
        
        # 如果表单数据不存在，尝试从JSON数据获取
        if not keyword and request.is_json:
            data = request.get_json()
            if data and 'code' in data:
                keyword = data.get('code', '').strip()
                print(f"从JSON获取关键词: {keyword}")
        
        # 如果JSON数据不存在，尝试从URL参数获取
        if not keyword:
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
        
        # 检查是否是ETF代码
        if re.match(r'^\d{6}$', keyword) or re.match(r'^\d{6}\.[A-Z]{2}$', keyword):
            code = keyword.split('.')[0] if '.' in keyword else keyword
            print(f"检查ETF代码是否存在: {keyword} -> {code}")
            
            if db.check_etf_code_exists(code):
                print("搜索类型: ETF基金代码")
                print(f"搜索ETF代码: {code}")
                results = db.search_by_etf_code(code)
                
                if results:
                    # 确保所有必要字段都存在并格式化
                    results = normalize_etf_results(results)
                    
                    # 打印一条结果用于调试
                    if results:
                        print(f"搜索结果示例：")
                        for key, value in results[0].items():
                            print(f"  {key}: {value}")
                    
                    # 增加调试日志，确保返回格式正确
                    response_data = {
                        'results': results,
                        'count': len(results)
                    }
                    print(f"返回数据结构：{type(response_data)}")
                    print(f"results类型：{type(response_data['results'])}")
                    print(f"results长度：{len(response_data['results'])}")
                    print(f"count值：{response_data['count']}")
                    
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
        if '基金' in keyword or '资管' in keyword:
            print("搜索类型: 基金公司名称")
            print(f"搜索基金公司: {keyword}")
            results = db.search_by_company(keyword)
            
            if results:
                # 确保所有必要字段都存在并格式化
                results = normalize_etf_results(results)
                
                response = jsonify({
                    'results': results,
                    'count': len(results)
                })
                return add_cors_headers(response)
            else:
                response = jsonify({
                    'results': [],
                    'count': 0,
                    'message': '未找到相关ETF'
                })
                return add_cors_headers(response)
        
        # 默认按指数名称搜索
        print("搜索类型: 跟踪指数名称")
        print(f"搜索指数名称: {keyword}")
        results = db.search_by_index_name(keyword)
        
        if results:
            # 确保所有必要字段都存在并格式化
            results = normalize_etf_results(results)
            
            response = jsonify({
                'results': results,
                'count': len(results)
            })
            return add_cors_headers(response)
        else:
            # 尝试通用搜索
            print("指数名称搜索无结果，尝试通用搜索")
            results = db.general_search(keyword)
            
            if results:
                # 确保所有必要字段都存在并格式化
                results = normalize_etf_results(results)
                
                response = jsonify({
                    'results': results,
                    'count': len(results)
                })
                return add_cors_headers(response)
            else:
                response = jsonify({
                    'results': [],
                    'count': 0,
                    'message': '未找到相关ETF'
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
            'tracking_index_name': result.get('tracking_index_name', result.get('index_name', ''))
        }
        
        normalized_results.append(normalized_etf)
    
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
    index_groups = []
    
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
    
    # 为每个指数创建一个组
    for index_info in sorted_indices:
        index_code = index_info['跟踪指数代码']
        index_name = index_info['跟踪指数名称']
        
        # 获取该指数下的所有ETF
        index_etfs = etf_data[etf_data['跟踪指数代码'] == index_code]
        
        # 按月日均交易量从大到小排序 - 修正列名
        index_etfs = index_etfs.sort_values(by='月成交额[交易日期]最新收盘日[单位]百万元', ascending=False)
        
        # 按新的交易量字段从大到小排序
        volume_col = '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元'
        index_etfs = index_etfs.sort_values(by=volume_col, ascending=False)
        
        # 格式化ETF结果
        etf_results = []
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
            
            etf_results.append({
                'code': etf_code,
                'name': row[name_col] if name_col in row else row['证券代码'],  # 如果列名不存在，使用证券代码作为备用
                'manager': row['基金管理人简称'] if '基金管理人简称' in row else row['基金管理人'],
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
        
        # 获取指数简介信息
        index_intro = get_index_intro(index_code)
        index_info = get_index_info(index_code)
        
        # 添加到指数组
        index_groups.append({
            'index_code': index_code,
            'index_name': index_name,
            'index_intro': index_intro,
            'index_info': index_info,
            'total_scale': round(index_scales.get(index_code, 0), 2),
            'etf_count': len(etf_results),
            'etfs': etf_results
        })
    
    return index_groups

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
    results = []
    
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
    
    # 使用新的交易量字段排序
    volume_col = '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元'
    matching_etfs = matching_etfs.sort_values(by=volume_col, ascending=False)
    
    # 从data_service导入当前和上周日期
    from services.data_service import current_date_str, previous_date_str
    
    # 格式化结果
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