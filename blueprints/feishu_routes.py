from flask import Blueprint, request, jsonify
import json
import logging
from database.models import Database
import pandas as pd
from datetime import datetime, timedelta
import requests

# 创建蓝图
feishu_bp = Blueprint('feishu', __name__)
logger = logging.getLogger(__name__)

# 飞书API配置 (从 app.py 移动过来)
FEISHU_APP_ID = "cli_a8af2342507bd00b"
FEISHU_APP_SECRET = "gEVOCnDI5h5auLCGF8UrJepPsVWzwZ1V"
FEISHU_BITABLE_APP_TOKEN = "LCg4bOezDayVWbs3XZoctg7PnYc"  # 多维表格 App Token
FEISHU_BITABLE_TABLE_ID = "tblFJwYk8uIM9cBu"  # 多维表格 Table ID (从用户URL提取)

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
        response = requests.get(url, headers=headers,
                                proxies=proxies, timeout=15)
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
                if not fields:  # 如果这条记录没有字段信息，则跳过
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
                is_available = True if isinstance(
                    is_available_text, str) and is_available_text == "可用" else bool(is_available_text)

                # 处理推广渠道 (publish_channel)，转换为逗号分隔的字符串
                publish_channel_list = fields.get('推送渠道', [])
                publish_channel_str = ", ".join(publish_channel_list) if isinstance(
                    publish_channel_list, list) else publish_channel_list

                # 提取附件URL的辅助函数
                def get_first_attachment_url(field_value):
                    if isinstance(field_value, list) and field_value:
                        # 优先尝试 tmp_url，如果无效或不存在，则用 url
                        # 实际应用中可能需要更复杂的逻辑来确认URL的有效性或进行下载代理
                        return field_value[0].get('tmp_url') or field_value[0].get('url', '')
                    return ''  # 如果不是列表或列表为空，返回空字符串

                banner_url_to_use = get_first_attachment_url(
                    fields.get('BANNER'))
                long_image_url_to_use = get_first_attachment_url(
                    fields.get('长图'))
                cut_image_url_to_use = get_first_attachment_url(
                    fields.get('切图'))

                # 日期字段直接使用从飞书获取的原始值 (字符串或时间戳)
                # 如果是时间戳，前端需要自行格式化
                compliance_date_raw = fields.get('合规通过日期', '')  # 可能是时间戳
                expiry_date_raw = fields.get('有效性过期预估', '')  # 可能是时间戳

                processed_item = {
                    "code": code,
                    "company_name": company_name,
                    "name": fields.get('证券简称', ''),
                    "banner_url": banner_url_to_use,
                    "banner_compliance": fields.get('BANNER 是否过合规', ''),
                    "long_image_url": long_image_url_to_use,
                    "long_image_compliance": fields.get('长图是否过合规', ''),
                    "cut_image_url": cut_image_url_to_use,
                    "compliance_date": compliance_date_raw,  # 保留原始值
                    "is_available": is_available,
                    "expiry_period": fields.get('海报时效性', ''),
                    "expiry_date": expiry_date_raw,  # 保留原始值
                    "publish_date": fields.get('推送时间', ''),
                    "publish_channel": publish_channel_str,  # 使用逗号分隔的字符串
                    "offline_date": fields.get('下线时间', ''),
                    "remarks": fields.get('主题', '')
                }
                processed_data.append(processed_item)

            logger.info(f"成功从飞书多维表格获取并处理 {len(processed_data)} 条记录。")
            if api_response["data"].get("has_more"):
                logger.warning("飞书多维表格数据超过500条，目前仅获取了第一页。如需完整数据，需要实现分页逻辑。")
            return processed_data
        else:
            logger.error(
                f"从飞书多维表格获取数据失败或格式不符合预期: Code: {api_response.get('code')}, Msg: {api_response.get('msg')}, Response: {api_response}")
            return None  # API调用本身可能成功(200)，但业务逻辑失败

    except requests.exceptions.HTTPError as http_err:
        logger.error(
            f"请求飞书API时发生HTTP错误: {http_err} - {response.text if 'response' in locals() else ''}")
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
                    business_agreement_count=company.get(
                        "business_agreement_count"),
                    total_holding_value=company.get("total_holding_value"),
                    business_total_holding_value=company.get(
                        "business_total_holding_value")
                )
                processed_count += 1
            except Exception as e:
                logger.error(f"处理公司数据时出错: {e}")

        # 关闭数据库连接
        conn.close()

        # 记录操作日志
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('logs/feishu_data_sync.log', 'a') as f:
            f.write(
                f"{current_time} - 成功处理 {processed_count}/{len(company_data)} 条公司数据\n")

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
        # 首先尝试从数据库获取数据
        db = Database()
        conn = db.connect()
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='feishu_promo_data'")
        table_exists = cursor.fetchone() is not None

        if table_exists:
            # 如果表存在，尝试从数据库获取数据
            try:
                cursor.execute("""
                    SELECT code, name, publish_date, offline_date, publish_channel, remarks, 
                           banner_url, long_image_url
                    FROM feishu_promo_data
                """)

                records = cursor.fetchall()
                logger.info(f"从数据库获取到 {len(records)} 条海报数据")

                if records and len(records) > 0:
                    poster_data = []
                    for record in records:
                        poster_data.append({
                            "code": record[0],
                            "name": record[1],
                            "publish_date": record[2],
                            "offline_date": record[3],
                            "publish_channel": record[4],
                            "remarks": record[5],
                            "banner_url": record[6],
                            "long_image_url": record[7]
                        })
                    return jsonify({"success": True, "data": poster_data})
            except Exception as db_err:
                logger.error(f"从数据库获取海报数据时出错: {str(db_err)}")

        # 如果数据库没有数据，尝试使用API获取
        logger.info("数据库中没有海报数据，尝试使用API获取")
        poster_data = get_feishu_poster_data()
        if poster_data is not None and len(poster_data) > 0:
            return jsonify({"success": True, "data": poster_data})
        else:
            # 返回空数据，而不是错误码，防止前端界面崩溃
            logger.warning("无法获取飞书海报数据，返回空数据列表")
            return jsonify({"success": True, "data": [], "message": "暂时无法获取飞书海报数据，请稍后重试"})
    except Exception as e:
        logger.error(f"获取飞书海报数据时出错: {str(e)}")
        # 同样返回空数据而不是错误状态码
        return jsonify({"success": True, "data": [], "message": f"获取数据时发生错误: {str(e)}"})


@feishu_bp.route('/api/feishu/promotion-stats', methods=['GET'])
def get_promotion_stats():
    """获取推广效果统计数据"""
    try:
        # 获取查询参数
        code = request.args.get('code')
        logger.info(f"获取推广效果统计数据: code={code}")

        # 创建数据库连接
        db = Database()
        conn = db.connect()
        cursor = conn.cursor()

        # 首先尝试检查feishu_promo_data表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='feishu_promo_data'")
        table_exists = cursor.fetchone() is not None

        stats_data = []

        if table_exists:
            # 如果表存在，尝试从数据库获取数据
            try:
                if code:
                    cursor.execute("""
                        SELECT code, name, publish_date, offline_date, publish_channel, remarks, expiry_date
                        FROM feishu_promo_data 
                        WHERE code = ?
                    """, (code,))
                else:
                    cursor.execute("""
                        SELECT code, name, publish_date, offline_date, publish_channel, remarks, expiry_date
                        FROM feishu_promo_data
                    """)

                promo_records = cursor.fetchall()
                logger.info(f"从数据库获取到 {len(promo_records)} 条推广记录")

                # 处理数据库获取的记录
                for record in promo_records:
                    etf_code, etf_name, publish_date, offline_date, publish_channel, remarks, expiry_date = record

                    # 处理空字段情况
                    # 推送时间为空，说明还没有推送，跳过这条记录
                    if not publish_date:
                        logger.info(f"跳过代码 {etf_code} 的记录，因为推送时间为空（尚未推送）")
                        continue

                    # 获取基金公司简称
                    cursor.execute("SELECT manager_short FROM etf_info WHERE code = ?", (etf_code,))
                    company_result = cursor.fetchone()
                    company_name = company_result[0] if company_result else ""
                    
                    # 下线时间为空，说明还在推送中，使用当前日期作为临时下线日期进行统计
                    if not offline_date:
                        offline_date = datetime.now().strftime('%Y-%m-%d')
                        logger.info(
                            f"代码 {etf_code} 的下线时间为空（推送中），使用当前日期 {offline_date} 进行统计")

                    # 获取推广效果数据（自选人数、持有人数、持仓价值等）
                    # 推广前的数据应该取推广日期前一天的数据
                    try:
                        # 解析推广日期并计算前一天的日期
                        if '/' in publish_date:
                            pub_date = datetime.strptime(
                                publish_date, '%Y/%m/%d')
                        else:
                            pub_date = datetime.strptime(
                                publish_date, '%Y-%m-%d')

                        # 计算前一天的日期
                        prev_day = pub_date - timedelta(days=1)
                        prev_day_str = prev_day.strftime('%Y-%m-%d')
                        logger.info(
                            f"代码 {etf_code} 的推广日期为 {publish_date}，使用前一天 {prev_day_str} 的数据作为推广前数据")

                        # 获取前一天的数据
                        pub_attention = db.get_attention_on_date(
                            etf_code, prev_day_str)
                        pub_holders = db.get_holders_on_date(
                            etf_code, prev_day_str)
                        pub_value = db.get_value_on_date(
                            etf_code, prev_day_str)
                    except (ValueError, TypeError):
                        # 如果日期格式有问题，回退到使用推广日期本身
                        logger.warning(
                            f"无法解析推广日期 {publish_date}，使用当天数据作为推广前数据")
                        pub_attention = db.get_attention_on_date(
                            etf_code, publish_date)
                        pub_holders = db.get_holders_on_date(
                            etf_code, publish_date)
                        pub_value = db.get_value_on_date(
                            etf_code, publish_date)

                    off_attention = db.get_attention_on_date(
                        etf_code, offline_date)
                    off_holders = db.get_holders_on_date(
                        etf_code, offline_date)
                    off_value = db.get_value_on_date(etf_code, offline_date)

                    # 处理可能的None值
                    pub_attention = pub_attention or 0
                    pub_holders = pub_holders or 0
                    pub_value = pub_value or 0
                    off_attention = off_attention or 0
                    off_holders = off_holders or 0
                    off_value = off_value or 0

                    # 将持仓价值取整（不显示小数点）
                    pub_value = int(round(pub_value))
                    off_value = int(round(off_value))

                    # 计算变化值
                    attention_change = off_attention - pub_attention
                    holders_change = off_holders - pub_holders
                    value_change = off_value - pub_value

                    # 计算百分比变化
                    attention_pct_change = (
                        attention_change / pub_attention * 100) if pub_attention > 0 else 0
                    holders_pct_change = (
                        holders_change / pub_holders * 100) if pub_holders > 0 else 0
                    value_pct_change = (
                        value_change / pub_value * 100) if pub_value > 0 else 0

                    # 计算推广天数
                    try:
                        if publish_date and offline_date:
                            if '/' in publish_date:
                                pub_date = datetime.strptime(
                                    publish_date, '%Y/%m/%d')
                            else:
                                pub_date = datetime.strptime(
                                    publish_date, '%Y-%m-%d')

                            if '/' in offline_date:
                                off_date = datetime.strptime(
                                    offline_date, '%Y/%m/%d')
                            else:
                                off_date = datetime.strptime(
                                    offline_date, '%Y-%m-%d')

                            promo_days = (off_date - pub_date).days + 1
                        else:
                            promo_days = 0
                    except ValueError:
                        promo_days = 0

                    stats_data.append({
                        'code': etf_code,
                        'name': etf_name,
                        'company_name': company_name,  # 添加基金公司简称
                        'publish_date': publish_date,
                        'offline_date': offline_date,
                        'publish_channel': publish_channel,
                        'promo_days': promo_days,
                        'theme': remarks,
                        'expiry_date': expiry_date,  # 添加过期时间字段
                        'pub_attention': pub_attention,
                        'pub_holders': pub_holders,
                        'pub_value': pub_value,
                        'off_attention': off_attention,
                        'off_holders': off_holders,
                        'off_value': off_value,
                        'attention_change': attention_change,
                        'holders_change': holders_change,
                        'value_change': value_change,
                        'attention_pct_change': round(attention_pct_change, 2),
                        'holders_pct_change': round(holders_pct_change, 2),
                        'value_pct_change': round(value_pct_change, 2)
                    })
            except Exception as db_err:
                logger.error(f"从数据库获取推广数据时出错: {str(db_err)}")

        # 如果数据库没有数据，尝试使用API获取
        if not stats_data:
            logger.info("数据库中没有推广数据，尝试使用API获取")
            stats_data = db.get_promotion_effect_stats(code)
            logger.info(f"从API获取到推广效果统计数据: {len(stats_data)} 条记录")

        # 记录一些数据示例以便调试
        if stats_data and len(stats_data) > 0:
            sample = stats_data[0]
            logger.info(
                f"数据示例: code={sample.get('code')}, 自选变化={sample.get('attention_change')}, 持有人变化={sample.get('holders_change')}")
        else:
            logger.warning("未获取到任何推广效果统计数据")

            # 检查飞书API是否可以获取原始数据
            poster_data = get_feishu_poster_data()
            if poster_data:
                logger.info(f"API能获取到 {len(poster_data)} 条推广数据，但无法生成统计")
                if len(poster_data) > 0:
                    sample = poster_data[0]
                    logger.info(
                        f"API原始数据示例: code={sample.get('code')}, 推广时间={sample.get('publish_date')}, 推广渠道={sample.get('publish_channel')}")
            else:
                logger.warning("API无法获取任何推广数据")

        return jsonify({
            "success": True,
            "data": stats_data,
            "total": len(stats_data)
        })
    except Exception as e:
        logger.error(f"获取推广效果统计数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"获取推广效果统计数据时出错: {str(e)}",
            "data": []
        })


@feishu_bp.route('/api/feishu/save-promo-data', methods=['POST'])
def save_promo_data():
    """将飞书推广数据保存到数据库"""
    try:
        # 获取请求数据
        if request.is_json:
            data = request.json
        else:
            # 如果不是JSON，可能是表单数据
            data = request.form.to_dict()

        if not data:
            # 如果没有数据，尝试获取当前API数据
            poster_data = get_feishu_poster_data()
            if not poster_data:
                return jsonify({
                    "success": False,
                    "message": "未提供数据且无法从API获取数据"
                }), 400
            data = {"posters": poster_data}

        # 创建数据库连接
        db = Database()
        conn = db.connect()
        cursor = conn.cursor()

        # 保存数据
        if "posters" in data and isinstance(data["posters"], list):
            posters = data["posters"]
            saved_count = 0

            for poster in posters:
                try:
                    # 检查是否已经存在相同代码和推广时间的记录
                    cursor.execute("""
                        SELECT id FROM feishu_promo_data
                        WHERE code = ? AND publish_date = ?
                    """, (poster.get('code', ''), poster.get('publish_date', '')))

                    existing_record = cursor.fetchone()

                    if existing_record:
                        # 更新现有记录
                        cursor.execute("""
                            UPDATE feishu_promo_data
                            SET name = ?, offline_date = ?, publish_channel = ?, remarks = ?,
                                banner_url = ?, long_image_url = ?
                            WHERE id = ?
                        """, (
                            poster.get('name', ''),
                            poster.get('offline_date', ''),
                            poster.get('publish_channel', ''),
                            poster.get('remarks', ''),
                            poster.get('banner_url', ''),
                            poster.get('long_image_url', ''),
                            existing_record[0]
                        ))
                    else:
                        # 插入新记录
                        cursor.execute("""
                            INSERT INTO feishu_promo_data
                            (code, name, publish_date, offline_date, publish_channel, remarks, banner_url, long_image_url)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            poster.get('code', ''),
                            poster.get('name', ''),
                            poster.get('publish_date', ''),
                            poster.get('offline_date', ''),
                            poster.get('publish_channel', ''),
                            poster.get('remarks', ''),
                            poster.get('banner_url', ''),
                            poster.get('long_image_url', '')
                        ))

                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存推广记录时出错: {str(e)}")

            conn.commit()

            return jsonify({
                "success": True,
                "message": f"成功保存 {saved_count}/{len(posters)} 条推广记录",
                "saved_count": saved_count
            })
        else:
            return jsonify({
                "success": False,
                "message": "数据格式错误，无法保存推广记录"
            }), 400
    except Exception as e:
        logger.error(f"保存推广数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"保存推广数据时出错: {str(e)}"
        }), 500


@feishu_bp.route('/api/feishu/promotion-overview', methods=['GET'])
def get_promotion_overview():
    """获取推广效果总览数据"""
    try:
        # 创建数据库连接
        db = Database()
        conn = db.connect()  # 不传递路径参数
        cursor = conn.cursor()

        # 获取查询参数（支持时间范围和渠道筛选）
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        channel = request.args.get('channel')
        company = request.args.get('company')  # 支持按基金公司筛选

        # 构建查询条件
        conditions = []
        params = []
        
        if start_date:
            conditions.append("publish_date >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("publish_date <= ?")
            params.append(end_date)
        
        if channel:
            conditions.append("publish_channel = ?")
            params.append(channel)
        
        # 准备SQL查询
        sql_condition = " AND ".join(conditions) if conditions else ""
        where_clause = f"WHERE {sql_condition}" if sql_condition else ""
        
        # 获取所有推广记录
        cursor.execute(f"""
            SELECT code, name, publish_date, offline_date, publish_channel 
            FROM feishu_promo_data
            {where_clause}
        """, params)
        
        promo_records = cursor.fetchall()
        
        # 统计数据
        total_promotions = len(promo_records)
        total_etfs = len(set([record[0] for record in promo_records]))  # 唯一ETF数量
        
        # 渠道分布 - 使用字典进行标准化和合并
        channel_counts = {}
        
        cursor.execute(f"""
            SELECT publish_channel, COUNT(*) as count
            FROM feishu_promo_data
            {where_clause}
            GROUP BY publish_channel
            ORDER BY count DESC
        """, params)
        
        for channel_record in cursor.fetchall():
            if not channel_record[0]:  # 跳过空渠道
                continue
                
            channel_name = channel_record[0]
            count = channel_record[1]
            
            # 标准化渠道名称（处理多渠道情况）
            if ',' in channel_name:
                # 拆分、排序并重新组合渠道名称
                channels = sorted([ch.strip() for ch in channel_name.split(',')])
                normalized_name = ', '.join(channels)
                
                # 更新计数或创建新条目
                if normalized_name in channel_counts:
                    channel_counts[normalized_name] += count
                else:
                    channel_counts[normalized_name] = count
            else:
                # 单一渠道
                if channel_name in channel_counts:
                    channel_counts[channel_name] += count
                else:
                    channel_counts[channel_name] = count
        
        # 转换为列表格式
        channels = [
            {'name': name, 'count': count}
            for name, count in sorted(channel_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # 基金公司分布
        company_stats = []
        if company:
            # 添加公司筛选条件
            if sql_condition:
                sql_condition += " AND "
                company_where_clause = f"WHERE {sql_condition} code IN (SELECT code FROM etf_info WHERE manager_short = ?)"
            else:
                company_where_clause = "WHERE code IN (SELECT code FROM etf_info WHERE manager_short = ?)"
            
            params.append(company)
            
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM feishu_promo_data 
                {company_where_clause}
            """, params)
            company_promo_count = cursor.fetchone()[0]
        else:
            # 获取各公司推广数量统计
            cursor.execute(f"""
                SELECT e.manager_short, COUNT(*) as count
                FROM feishu_promo_data f
                JOIN etf_info e ON f.code = e.code
                {where_clause}
                GROUP BY e.manager_short
                ORDER BY count DESC
                LIMIT 5
            """, params)
            
            for company_record in cursor.fetchall():
                if company_record[0]:  # 确保公司名不为空
                    company_stats.append({
                        'name': company_record[0],
                        'count': company_record[1]
                    })
        
        # 计算平均推广指标（自选增长、持有人增长、持仓价值增长）
        total_attention_change = 0
        total_holders_change = 0
        total_value_change = 0
        count_with_metrics = 0
        
        for record in promo_records:
            etf_code, etf_name, publish_date, offline_date, channel = record
            
            # 跳过未完成的推广
            if not publish_date or not offline_date:
                continue
                
            # 解析日期
            try:
                if '/' in publish_date:
                    pub_date = datetime.strptime(publish_date, '%Y/%m/%d')
                else:
                    pub_date = datetime.strptime(publish_date, '%Y-%m-%d')
                    
                if '/' in offline_date:
                    off_date = datetime.strptime(offline_date, '%Y/%m/%d')
                else:
                    off_date = datetime.strptime(offline_date, '%Y-%m-%d')
                
                # 计算推广前的数据（推广日期前一天）
                prev_day = pub_date - timedelta(days=1)
                prev_day_str = prev_day.strftime('%Y-%m-%d')
                
                # 获取推广前后的指标
                pub_attention = db.get_attention_on_date(etf_code, prev_day_str) or 0
                pub_holders = db.get_holders_on_date(etf_code, prev_day_str) or 0
                pub_value = db.get_value_on_date(etf_code, prev_day_str) or 0
                
                off_attention = db.get_attention_on_date(etf_code, offline_date) or 0
                off_holders = db.get_holders_on_date(etf_code, offline_date) or 0
                off_value = db.get_value_on_date(etf_code, offline_date) or 0
                
                # 计算变化值
                attention_change = off_attention - pub_attention
                holders_change = off_holders - pub_holders
                value_change = off_value - pub_value
                
                total_attention_change += attention_change
                total_holders_change += holders_change
                total_value_change += value_change
                count_with_metrics += 1
                
            except (ValueError, TypeError) as e:
                logger.warning(f"计算指标变化时出错: {str(e)}, code={etf_code}, publish_date={publish_date}, offline_date={offline_date}")
                continue
        
        # 计算平均值
        avg_attention_change = round(total_attention_change / count_with_metrics if count_with_metrics > 0 else 0)
        avg_holders_change = round(total_holders_change / count_with_metrics if count_with_metrics > 0 else 0)
        avg_value_change = round(total_value_change / count_with_metrics if count_with_metrics > 0 else 0)
        
        # 组装结果
        overview_data = {
            "total_promotions": total_promotions,
            "total_etfs": total_etfs,
            "channels": channels,
            "company_stats": company_stats,
            "avg_attention_change": avg_attention_change,
            "avg_holders_change": avg_holders_change,
            "avg_value_change": avg_value_change,
        }
        
        return jsonify({"success": True, "data": overview_data})
        
    except Exception as e:
        logger.error(f"获取推广效果总览数据时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@feishu_bp.route('/api/feishu/promotion-rankings', methods=['GET'])
def get_promotion_rankings():
    """获取推广效果排行榜数据"""
    try:
        # 创建数据库连接
        db = Database()
        conn = db.connect()  # 不传递路径参数
        cursor = conn.cursor()
        
        # 获取查询参数
        sort_by = request.args.get('sort_by', 'attention_pct')  # 默认按自选增长率排序
        sort_order = request.args.get('sort_order', 'desc')  # 默认降序
        limit = request.args.get('limit', 10, type=int)  # 默认返回前10条
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        channel = request.args.get('channel')
        company = request.args.get('company')
        
        # 构建查询条件
        conditions = []
        params = []
        
        if start_date:
            conditions.append("fp.publish_date >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("fp.publish_date <= ?")
            params.append(end_date)
        
        if channel and channel != 'all':
            conditions.append("fp.publish_channel = ?")
            params.append(channel)
            
        # 处理基金公司筛选
        company_join = ""
        if company and company != 'all':
            company_join = "JOIN etf_info ei ON fp.code = ei.code"
            conditions.append("ei.manager_short = ?")
            params.append(company)
        
        # 构建排序字段映射
        sort_field_map = {
            'attention_pct': 'attention_pct_change',  # 自选增长率
            'attention_abs': 'attention_change',      # 自选绝对增长
            'holders_pct': 'holders_pct_change',      # 持有人增长率
            'holders_abs': 'holders_change',          # 持有人绝对增长
            'value_pct': 'value_pct_change',          # 持仓价值增长率
            'value_abs': 'value_change',              # 持仓价值绝对增长
            'days': 'promo_days'                      # 推广天数
        }
        
        # 获取排序字段，如果不在映射中则使用默认值
        sort_field = sort_field_map.get(sort_by, 'attention_pct_change')
        
        # 构建排序子句
        order_clause = f"ORDER BY {sort_field} {sort_order}"
        
        # 查询推广记录
        query = f"""
            WITH promotion_stats AS (
                SELECT 
                    fp.code,
                    fp.name,
                    fp.publish_date,
                    fp.offline_date,
                    fp.publish_channel,
                    fp.remarks AS theme,
                    (julianday(REPLACE(fp.offline_date, '/', '-')) - julianday(REPLACE(fp.publish_date, '/', '-')) + 1) AS promo_days,
                    att1.attention_count AS pub_attention,
                    att2.attention_count AS off_attention,
                    hold1.holder_count AS pub_holders,
                    hold2.holder_count AS off_holders,
                    hold1.holding_value AS pub_value,
                    hold2.holding_value AS off_value,
                    (att2.attention_count - att1.attention_count) AS attention_change,
                    (hold2.holder_count - hold1.holder_count) AS holders_change,
                    (hold2.holding_value - hold1.holding_value) AS value_change,
                    CASE 
                        WHEN att1.attention_count > 0 THEN ROUND((att2.attention_count - att1.attention_count) * 100.0 / att1.attention_count, 2)
                        ELSE 0 
                    END AS attention_pct_change,
                    CASE 
                        WHEN hold1.holder_count > 0 THEN ROUND((hold2.holder_count - hold1.holder_count) * 100.0 / hold1.holder_count, 2)
                        ELSE 0 
                    END AS holders_pct_change,
                    CASE 
                        WHEN hold1.holding_value > 0 THEN ROUND((hold2.holding_value - hold1.holding_value) * 100.0 / hold1.holding_value, 2)
                        ELSE 0 
                    END AS value_pct_change
                FROM 
                    feishu_promo_data fp
                    {company_join}
                    LEFT JOIN (
                        SELECT code, date, attention_count FROM etf_attention_history
                    ) att1 ON fp.code = att1.code AND att1.date = date(julianday(REPLACE(fp.publish_date, '/', '-')) - 1)
                    LEFT JOIN (
                        SELECT code, date, attention_count FROM etf_attention_history
                    ) att2 ON fp.code = att2.code AND att2.date = REPLACE(fp.offline_date, '/', '-')
                    LEFT JOIN (
                        SELECT code, date, holder_count, holding_value FROM etf_holders_history
                    ) hold1 ON fp.code = hold1.code AND hold1.date = date(julianday(REPLACE(fp.publish_date, '/', '-')) - 1)
                    LEFT JOIN (
                        SELECT code, date, holder_count, holding_value FROM etf_holders_history
                    ) hold2 ON fp.code = hold2.code AND hold2.date = REPLACE(fp.offline_date, '/', '-')
                WHERE
                    fp.publish_date IS NOT NULL
                    AND fp.offline_date IS NOT NULL
                    AND fp.offline_date != ''
                    {' AND ' + ' AND '.join(conditions) if conditions else ''}
            )
            SELECT 
                code,
                name,
                publish_date,
                offline_date,
                publish_channel,
                theme,
                promo_days,
                pub_attention,
                off_attention,
                attention_change,
                attention_pct_change,
                pub_holders,
                off_holders,
                holders_change,
                holders_pct_change,
                pub_value,
                off_value,
                value_change,
                value_pct_change,
                COALESCE((SELECT manager_short FROM etf_info WHERE code = promotion_stats.code), '') AS company_name
            FROM 
                promotion_stats
            {order_clause}
            LIMIT ?
        """
        
        # 添加limit参数
        params.append(limit)
        
        # 执行查询
        logger.info(f"执行排行榜查询: sort_by={sort_by}, sort_order={sort_order}, limit={limit}")
        cursor.execute(query, params)
        
        # 获取列名
        columns = [description[0] for description in cursor.description]
        
        # 获取数据
        rows = cursor.fetchall()
        
        # 转换为字典列表
        rankings = []
        for row in rows:
            item = {}
            for i, column in enumerate(columns):
                item[column] = row[i]
            rankings.append(item)
        
        return jsonify({"success": True, "data": rankings})
        
    except Exception as e:
        logger.error(f"获取推广效果排行榜时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@feishu_bp.route('/api/feishu/filter-options', methods=['GET'])
def get_filter_options():
    """获取筛选选项数据（渠道和基金公司）"""
    try:
        # 创建数据库连接
        db = Database()
        conn = db.connect()
        cursor = conn.cursor()
        
        # 查询所有不同的渠道
        cursor.execute("""
            SELECT DISTINCT publish_channel
            FROM feishu_promo_data
            WHERE publish_channel IS NOT NULL AND publish_channel != ''
            ORDER BY publish_channel
        """)
        
        channels = [row[0] for row in cursor.fetchall()]
        
        # 处理渠道名称
        processed_channels = []
        for channel in channels:
            # 如果包含逗号，分割并标准化
            if ',' in channel:
                parts = [part.strip() for part in channel.split(',')]
                # 将"APP首页"标准化为"首页"等
                normalized_parts = []
                for part in parts:
                    if part == 'APP首页' or part == 'APP 首页':
                        normalized_parts.append('首页')
                    elif part == 'APP理财界面' or part == 'APP 理财界面':
                        normalized_parts.append('理财页')
                    else:
                        normalized_parts.append(part)
                # 排序并去重
                normalized_parts = sorted(list(set(normalized_parts)))
                processed_channel = '+'.join(normalized_parts)
            else:
                # 单一渠道也进行标准化
                if channel == 'APP首页' or channel == 'APP 首页':
                    processed_channel = '首页'
                elif channel == 'APP理财界面' or channel == 'APP 理财界面':
                    processed_channel = '理财页'
                else:
                    processed_channel = channel
            
            # 避免重复添加
            if processed_channel not in processed_channels:
                processed_channels.append(processed_channel)
        
        # 查询所有基金公司
        cursor.execute("""
            SELECT DISTINCT manager_short
            FROM etf_info
            WHERE manager_short IS NOT NULL AND manager_short != ''
            ORDER BY manager_short
        """)
        
        companies = [row[0] for row in cursor.fetchall()]
        
        return jsonify({
            "success": True, 
            "data": {
                "channels": processed_channels,
                "companies": companies
            }
        })
        
    except Exception as e:
        logger.error(f"获取筛选选项数据时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)})
