from flask import Blueprint, jsonify, request
import pandas as pd
import traceback
from datetime import datetime

# 创建蓝图
search_bp = Blueprint('search', __name__)

# 获取当前日期格式化为"MM月DD日"
def get_current_date_format():
    """获取当前日期格式化为MM月DD日"""
    from services.data_service import current_date_str
    return current_date_str

@search_bp.route('/search', methods=['POST'])
def search():
    """搜索ETF"""
    # 从data_service导入数据
    from services.data_service import etf_data, business_etfs, current_date_str
    import pandas as pd
    
    if etf_data is None:
        return jsonify({"error": "数据未加载，请先加载数据"})
    
    try:
        # 获取搜索关键词
        keyword = request.form.get('code', '').strip()
        
        if not keyword:
            return jsonify({"error": "请输入搜索关键词"})
        
        print(f"搜索关键词: '{keyword}'")
        
        # 判断搜索类型
        search_type = determine_search_type(keyword, etf_data)
        print(f"搜索类型: {search_type}")
        
        # 根据不同搜索类型处理结果
        if search_type == "ETF基金代码":
            results = search_by_etf_code(keyword, etf_data, business_etfs, current_date_str)
            return jsonify({
                "success": True,
                "search_type": search_type,
                "count": len(results),
                "results": results,
                "keyword": keyword
            })
            
        elif search_type == "跟踪指数名称":
            index_groups = search_by_index_name(keyword, etf_data, business_etfs, current_date_str)
            return jsonify({
                "success": True,
                "search_type": search_type,
                "count": sum(len(group['etfs']) for group in index_groups),
                "index_groups": index_groups,
                "keyword": keyword
            })
            
        elif search_type == "跟踪指数代码":
            results = search_by_index_code(keyword, etf_data, business_etfs, current_date_str)
            return jsonify({
                "success": True,
                "search_type": search_type,
                "count": len(results),
                "results": results,
                "keyword": keyword
            })
            
        elif search_type == "基金公司名称":
            results = search_by_company(keyword, etf_data, business_etfs, current_date_str)
            return jsonify({
                "success": True,
                "search_type": search_type,
                "count": len(results),
                "results": results,
                "keyword": keyword
            })
        
        else:
            # 通用搜索，返回所有匹配结果
            results = general_search(keyword, etf_data, business_etfs, current_date_str)
            return jsonify({
                "success": True,
                "search_type": "通用搜索",
                "count": len(results),
                "results": results,
                "keyword": keyword
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"搜索出错：{str(e)}"})

def determine_search_type(keyword, etf_data):
    """判断搜索类型"""
    # 判断是否为ETF基金代码
    if keyword.isdigit() and len(keyword) == 6:
        if any(etf_data['证券代码'].str.contains(keyword, na=False)):
            return "ETF基金代码"
    
    # 判断是否为跟踪指数代码
    if '.' in keyword and any(etf_data['跟踪指数代码'].str.contains(keyword, na=False, regex=False)):
        return "跟踪指数代码"
    
    # 判断是否为基金公司名称
    company_keywords = ['基金', '资管', '投资', '证券']
    if any(kw in keyword for kw in company_keywords) or any(etf_data['基金管理人'].str.contains(keyword, na=False)):
        return "基金公司名称"
    
    # 判断是否为跟踪指数名称
    index_keywords = ['指数', '300', '500', '1000', '红利', '消费', '医药', '科技']
    if any(kw in keyword for kw in index_keywords) or any(etf_data['跟踪指数名称'].str.contains(keyword, na=False)):
        return "跟踪指数名称"
    
    # 默认为通用搜索
    return "通用搜索"

def search_by_etf_code(keyword, etf_data, business_etfs, current_date_str):
    """按ETF基金代码搜索"""
    # 精确匹配ETF代码
    target_etf = etf_data[etf_data['证券代码'] == keyword]
    
    if target_etf.empty:
        return []
    
    # 获取该ETF的跟踪指数代码
    index_code = target_etf.iloc[0]['跟踪指数代码']
    
    # 查找同一跟踪指数的所有ETF
    same_index_etfs = etf_data[etf_data['跟踪指数代码'] == index_code]
    
    # 使用新的交易量字段排序
    volume_col = '区间日均成交额[起始交易日期]S_cal_date(enddate,-1,M,0)[截止交易日期]最新收盘日[单位]亿元'
    same_index_etfs = same_index_etfs.sort_values(by=volume_col, ascending=False)
    
    # 从data_service导入当前和上周日期
    from services.data_service import current_date_str, previous_date_str
    
    # 格式化结果
    results = []
    for _, row in same_index_etfs.iterrows():
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
            'volume': round(float(row[volume_col]) if pd.notna(row[volume_col]) else 0, 2),  # 已经是亿元单位
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
                'volume': round(float(row['月成交额[交易日期]最新收盘日[单位]百万元']) / 100 if pd.notna(row['月成交额[交易日期]最新收盘日[单位]百万元']) else 0, 2),  # 百万转亿
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
        
        # 添加到指数组
        index_groups.append({
            'index_code': index_code,
            'index_name': index_name,
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
    
    # 尝试多种匹配方式
    matching_etfs = etf_data[
        etf_data['证券代码'].str.contains(keyword, na=False) |
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
            # 使用新的交易量字段
            'volume': round(float(row[volume_col]) if pd.notna(row[volume_col]) else 0, 2),  # 已经是亿元单位
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

# 安全转换数值的辅助函数
def safe_float(value, default=0.0):
    """安全地将值转换为浮点数"""
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default