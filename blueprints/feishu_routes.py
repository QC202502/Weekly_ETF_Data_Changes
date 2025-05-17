from flask import Blueprint, request, jsonify
import json
import logging
from database.models import Database
import pandas as pd
from datetime import datetime
import requests

# 创建蓝图
feishu_bp = Blueprint('feishu', __name__)
logger = logging.getLogger(__name__)

# 飞书API配置 (从 app.py 移动过来)
FEISHU_APP_ID = "cli_a8af2342507bd00b" 
FEISHU_APP_SECRET = "gEVOCnDI5h5auLCGF8UrJepPsVWzwZ1V"
FEISHU_BITABLE_APP_TOKEN = "LCg4bOezDayVWbs3XZoctg7PnYc" # 多维表格 App Token
FEISHU_BITABLE_TABLE_ID = "tblFJwYk8uIM9cBu" # 多维表格 Table ID (从用户URL提取)

# 直接使用requests库调用飞书API (从 app.py 移动过来)
def get_tenant_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    # 禁用任何代理设置，直接连接
    proxies = {"http": None, "https": None}
    response = requests.post(url, json=payload, proxies=proxies, timeout=15)
    response_data = response.json()
    if "tenant_access_token" not in response_data:
        logger.error(f"获取 tenant_access_token 失败: {response_data}")
        return None
    return response_data.get("tenant_access_token")

# 创建一个函数用于获取飞书表格数据 (从 app.py 移动过来)
def get_feishu_poster_data():
    """从飞书多维表格获取海报库数据"""
    try:
        access_token = get_tenant_token()
        if not access_token:
            logger.error("无法获取 tenant_access_token，无法继续获取飞书多维表格数据。")
            return None
        
        headers = {"Authorization": f"Bearer {access_token}"}
        # 使用飞书多维表格API V1
        # API端点：GET /open-apis/bitable/v1/apps/:app_token/tables/:table_id/records
        # 支持参数 page_size (max 500), page_token
        # 为简单起见，我们先尝试获取第一页，最多500条记录
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_BITABLE_APP_TOKEN}/tables/{FEISHU_BITABLE_TABLE_ID}/records?page_size=500"
        
        # 禁用任何代理设置，直接连接
        proxies = {"http": None, "https": None}
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        response.raise_for_status() 
        api_response = response.json()

        if api_response.get("code") == 0 and "data" in api_response and "items" in api_response["data"]:
            records = api_response["data"]["items"]
            
            if not records:
                logger.warning("飞书多维表格数据为空。")
                return []

            processed_data = []
            for record in records:
                fields = record.get("fields", {})
                if not fields: # 如果这条记录没有字段信息，则跳过
                    logger.warning(f"跳过一条没有字段的记录: {record.get('record_id')}")
                    continue

                # 确保关键字段存在，避免因缺少字段导致后续处理错误
                code = str(fields.get('证券代码', ''))
                company_name = fields.get('基金公司简称', '')

                # 注意：多维表格中的 "是否可用" 字段可能直接是布尔值，或者需要特定处理
                # 假设CSV中的 "可用" 字符串对应多维表格中的 true (布尔类型) 或特定文本。
                # 如果是文本，比如 "是"/"否"，需要相应调整 item.get('是否可用') == "是"
                # 如果直接是布尔值，那么 fields.get('是否可用', False) 就可以
                # 假设 "是否可用" 列在多维表格中是文本 "可用" 或其他值
                is_available_text = fields.get('是否可用', '')
                is_available = True if isinstance(is_available_text, str) and is_available_text == "可用" else bool(is_available_text)

                # 处理推广渠道 (publish_channel)，转换为逗号分隔的字符串
                publish_channel_list = fields.get('推送渠道', [])
                publish_channel_str = ", ".join(publish_channel_list) if isinstance(publish_channel_list, list) else publish_channel_list

                # 提取附件URL的辅助函数
                def get_first_attachment_url(field_value):
                    if isinstance(field_value, list) and field_value:
                        # 优先尝试 tmp_url，如果无效或不存在，则用 url
                        # 实际应用中可能需要更复杂的逻辑来确认URL的有效性或进行下载代理
                        return field_value[0].get('tmp_url') or field_value[0].get('url', '')
                    return '' # 如果不是列表或列表为空，返回空字符串

                banner_url_to_use = get_first_attachment_url(fields.get('BANNER'))
                long_image_url_to_use = get_first_attachment_url(fields.get('长图'))
                cut_image_url_to_use = get_first_attachment_url(fields.get('切图'))

                # 日期字段直接使用从飞书获取的原始值 (字符串或时间戳)
                # 如果是时间戳，前端需要自行格式化
                compliance_date_raw = fields.get('合规通过日期', '') # 可能是时间戳
                expiry_date_raw = fields.get('有效性过期预估', '') # 可能是时间戳

                processed_item = {
                    "code": code,
                    "company_name": company_name,
                    "name": fields.get('证券简称', ''),
                    "banner_url": banner_url_to_use,
                    "banner_compliance": fields.get('BANNER 是否过合规', ''),
                    "long_image_url": long_image_url_to_use,
                    "long_image_compliance": fields.get('长图是否过合规', ''),
                    "cut_image_url": cut_image_url_to_use,
                    "compliance_date": compliance_date_raw, # 保留原始值
                    "is_available": is_available,
                    "expiry_period": fields.get('海报时效性', ''),
                    "expiry_date": expiry_date_raw, # 保留原始值
                    "publish_date": fields.get('推送时间', ''),
                    "publish_channel": publish_channel_str, # 使用逗号分隔的字符串
                    "offline_date": fields.get('下线时间', ''),
                    "remarks": fields.get('主题', '')
                }
                processed_data.append(processed_item)
            
            logger.info(f"成功从飞书多维表格获取并处理 {len(processed_data)} 条记录。")
            if api_response["data"].get("has_more"):
                logger.warning("飞书多维表格数据超过500条，目前仅获取了第一页。如需完整数据，需要实现分页逻辑。")
            return processed_data
        else:
            logger.error(f"从飞书多维表格获取数据失败或格式不符合预期: Code: {api_response.get('code')}, Msg: {api_response.get('msg')}, Response: {api_response}")
            return None # API调用本身可能成功(200)，但业务逻辑失败
    
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"请求飞书API时发生HTTP错误: {http_err} - {response.text if 'response' in locals() else ''}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"请求飞书API时发生错误: {req_err}")
        return None
    except Exception as e:
        logger.error(f"处理飞书海报数据时发生未知错误: {str(e)}", exc_info=True)
        return None

@feishu_bp.route('/api/template/feishu', methods=['GET'])
def get_feishu_template():
    """获取飞书数据模板"""
    try:
        db = Database()
        template = db.get_feishu_data_template()
        return jsonify(template)
    except Exception as e:
        logger.error(f"获取飞书数据模板时出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@feishu_bp.route('/api/feishu/data', methods=['POST'])
def receive_feishu_data():
    """接收来自飞书的数据"""
    try:
        # 获取请求数据
        data = request.json
        logger.info(f"收到飞书数据: {data.keys() if data else None}")
        
        if not data:
            return jsonify({"success": False, "message": "未接收到数据"}), 400
            
        # 验证数据格式
        required_fields = ["company_data", "token"]
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "message": f"缺少必要字段: {field}"}), 400
        
        # 测试模式，不写入数据
        if data["token"] == "test_mode":
            logger.info("测试模式，不写入数据")
            company_data = data["company_data"]
            return jsonify({
                "success": True, 
                "message": f"测试成功，有 {len(company_data)} 条公司数据将被处理（测试模式，未写入数据库）",
                "processed_count": len(company_data),
                "test_mode": True
            })
        
        # 简单的Token验证，实际应用中应使用更安全的认证方式
        if data["token"] != "your_secret_token":  # 请替换为实际使用的安全令牌
            return jsonify({"success": False, "message": "验证失败"}), 401
            
        # 处理数据
        company_data = data["company_data"]
        
        # 连接数据库
        db = Database()
        conn = db.connect()
        
        # 保存数据到数据库
        # 这里假设数据是基金公司分析的数据
        processed_count = 0
        for company in company_data:
            # 处理单个公司数据
            try:
                # 这里根据实际表结构进行插入或更新操作
                # 示例:
                db.update_company_analytics(
                    company_name=company.get("company_name"),
                    total_fund_size=company.get("total_fund_size"),
                    product_count=company.get("product_count"),
                    business_agreement_count=company.get("business_agreement_count"),
                    total_holding_value=company.get("total_holding_value"),
                    business_total_holding_value=company.get("business_total_holding_value")
                )
                processed_count += 1
            except Exception as e:
                logger.error(f"处理公司数据时出错: {e}")
                
        # 关闭数据库连接
        conn.close()
        
        # 记录操作日志
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('logs/feishu_data_sync.log', 'a') as f:
            f.write(f"{current_time} - 成功处理 {processed_count}/{len(company_data)} 条公司数据\n")
            
        return jsonify({
            "success": True, 
            "message": f"成功处理 {processed_count}/{len(company_data)} 条公司数据",
            "processed_count": processed_count
        })
        
    except Exception as e:
        logger.error(f"处理飞书数据时出错: {str(e)}")
        return jsonify({"success": False, "message": f"处理数据时出错: {str(e)}"}), 500

@feishu_bp.route('/api/feishu/posters', methods=['GET'])
def show_feishu_posters():
    """获取并显示飞书海报数据"""
    try:
        poster_data = get_feishu_poster_data()
        if poster_data is not None:
            return jsonify({"success": True, "data": poster_data})
        else:
            # 返回空数据，而不是错误码，防止前端界面崩溃
            logger.warning("无法获取飞书海报数据，返回空数据列表")
            return jsonify({"success": True, "data": [], "message": "暂时无法获取飞书海报数据，请稍后重试"})
    except Exception as e:
        logger.error(f"获取飞书海报数据时出错: {str(e)}")
        # 同样返回空数据而不是错误状态码
        return jsonify({"success": True, "data": [], "message": f"获取数据时发生错误: {str(e)}"}) 