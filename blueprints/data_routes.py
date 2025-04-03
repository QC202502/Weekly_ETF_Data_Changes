from flask import Blueprint, jsonify, request, send_file
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import pandas as pd
import glob

# 导入数据加载函数
from services.data_service import load_latest_data

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
    from flask import current_app
    
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
    from flask import current_app
    return send_file(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), as_attachment=True)