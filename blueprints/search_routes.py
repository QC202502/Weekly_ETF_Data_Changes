from flask import Blueprint, jsonify, request
import pandas as pd
import traceback

# 创建蓝图
search_bp = Blueprint('search', __name__)

# 修复搜索功能中的关键词获取问题

@search_bp.route('/search', methods=['POST'])
def search():
    """搜索ETF"""
    # 从data_service导入数据
    from services.data_service import etf_data, format_etf_result
    import pandas as pd
    
    if etf_data is None:
        return jsonify({"error": "数据未加载，请先加载数据"})
    
    try:
        # 打印请求信息，帮助调试
        print(f"请求方法: {request.method}")
        print(f"请求内容类型: {request.content_type}")
        print(f"请求表单数据: {request.form}")
        
        # 获取搜索关键词 - 优先使用'code'参数
        keyword = ""
        
        # 从表单数据获取
        if request.form and 'code' in request.form:
            keyword = request.form.get('code', '').strip()
            print(f"从表单参数 'code' 获取搜索关键词: {keyword}")
        
        print(f"最终搜索关键词: '{keyword}'")
        
        if not keyword:
            print("错误: 未提供搜索关键词")
            return jsonify({"error": "请输入搜索关键词"})
        
        # 搜索结果
        results = []
        
        # 1. 精确匹配证券代码
        if keyword.isdigit() or (len(keyword) >= 6 and keyword.isalnum()):
            # 提取数字部分作为证券代码
            code_part = ''.join(c for c in keyword if c.isdigit())
            if len(code_part) >= 6:
                code_part = code_part[:6]  # 取前6位数字
                exact_match = etf_data[etf_data['证券代码'].str.contains(code_part, na=False)]
                if not exact_match.empty:
                    for _, row in exact_match.iterrows():
                        results.append(format_etf_result(row))
        
        # 2. 模糊匹配证券名称
        name_cols = ['证券名称', '证券名称（03月07日）']
        for name_col in name_cols:
            if name_col in etf_data.columns:
                name_matches = etf_data[etf_data[name_col].str.contains(keyword, na=False)]
                for _, row in name_matches.iterrows():
                    if not any(r['code'] == row['证券代码'] for r in results):  # 避免重复
                        results.append(format_etf_result(row))
        
        # 3. 模糊匹配跟踪指数名称
        if '跟踪指数名称' in etf_data.columns:
            index_matches = etf_data[etf_data['跟踪指数名称'].str.contains(keyword, na=False)]
            for _, row in index_matches.iterrows():
                if not any(r['code'] == row['证券代码'] for r in results):  # 避免重复
                    results.append(format_etf_result(row))
        
        # 4. 模糊匹配基金管理人
        if '基金管理人' in etf_data.columns:
            manager_matches = etf_data[etf_data['基金管理人'].str.contains(keyword, na=False)]
            for _, row in manager_matches.iterrows():
                if not any(r['code'] == row['证券代码'] for r in results):  # 避免重复
                    results.append(format_etf_result(row))
        
        # 5. 如果是指数代码，查找跟踪该指数的ETF
        if '跟踪指数代码' in etf_data.columns:
            index_etfs = etf_data[etf_data['跟踪指数代码'].str.contains(keyword, na=False)]
            if not index_etfs.empty:
                for _, row in index_etfs.iterrows():
                    if not any(r['code'] == row['证券代码'] for r in results):  # 避免重复
                        results.append(format_etf_result(row))
        
        print(f"搜索结果数量: {len(results)}")
        
        # 返回搜索结果
        return jsonify({
            "success": True,
            "count": len(results),
            "results": results,
            "keyword": keyword
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"搜索出错：{str(e)}"})