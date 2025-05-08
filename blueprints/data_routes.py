from flask import Blueprint, jsonify, request, send_file, current_app
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import pandas as pd
import glob

# 导入数据加载函数
from services.data_service import load_latest_data
from database.models import Database # 确保导入Database

# 创建蓝图
data_bp = Blueprint('data', __name__)

# 全局变量
etf_data = None
business_etfs = set()  # 存储商务品ETF代码
current_date_str = ""
previous_date_str = ""
date_range = ""

@data_bp.route('/load_data')
def load_data_route():
    """加载数据路由"""
    try:
        result = load_latest_data()
        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'message': '数据加载成功',
                'data': result['message']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['message']
            })
    except Exception as e:
        print(f"加载数据时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'加载数据时出错: {str(e)}'
        })

@data_bp.route('/upload_data', methods=['GET', 'POST'])
def upload_data():
    """上传数据文件"""
    if request.method == 'POST':
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({"error": "未选择文件"})
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({"error": "未选择文件"})
        
        if file:
            # 安全地获取文件名
            filename = secure_filename(file.filename)
            
            # 保存文件
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            return jsonify({
                "success": True,
                "message": f"文件 {filename} 上传成功",
                "file_path": file_path
            })
    
    from flask import render_template
    return render_template('upload.html')

@data_bp.route('/download_report/<filename>')
def download_report(filename):
    """下载报告"""
    return send_file(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@data_bp.route('/fund_company_attention_history', methods=['GET'])
def fund_company_attention_history():
    """获取基金公司自选历史数据"""
    company_name = request.args.get('name')
    if not company_name:
        return jsonify({"error": "缺少基金公司名称参数 (name)"}), 400
    
    try:
        db = Database()
        # 注意：get_fund_company_attention_history 方法需要在Database模型中实现
        data = db.get_fund_company_attention_history(company_name)
        current_app.logger.info(f"基金公司自选历史查询: 公司={company_name}, 记录数={len(data)}")
        for record in data[:5]: # 打印前5条记录用于调试
            current_app.logger.debug(f"处理基金公司自选历史记录: {record}")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"查询基金公司 {company_name} 自选历史数据失败: {str(e)}")
        return jsonify({"error": f"查询基金公司自选历史数据失败: {str(e)}"}), 500

@data_bp.route('/fund_company_holders_history', methods=['GET'])
def fund_company_holders_history():
    """获取基金公司持有人和持仓价值历史数据"""
    company_name = request.args.get('name')
    if not company_name:
        return jsonify({"error": "缺少基金公司名称参数 (name)"}), 400
    
    try:
        db = Database()
        # 注意：get_fund_company_holders_history 方法需要在Database模型中实现
        data = db.get_fund_company_holders_history(company_name)
        current_app.logger.info(f"基金公司持有人历史查询: 公司={company_name}, 记录数={len(data)}")
        for record in data[:5]: # 打印前5条记录用于调试
            current_app.logger.debug(f"处理基金公司持有人历史记录: {record}")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"查询基金公司 {company_name} 持有人历史数据失败: {str(e)}")
        return jsonify({"error": f"查询基金公司持有人历史数据失败: {str(e)}"}), 500