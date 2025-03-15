import os
from flask import Flask, render_template
import matplotlib
matplotlib.use('Agg')  # 非交互式后端

# 版本信息
__version__ = "2.9.1"   
RELEASE_DATE = "2025-03-15"

# 创建Flask应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 限制上传文件大小为50MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'reports'), exist_ok=True)

# 注册蓝图
from blueprints.data_routes import data_bp
from blueprints.analysis_routes import analysis_bp
from blueprints.search_routes import search_bp

# 修改注册方式，去掉URL前缀
app.register_blueprint(data_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(search_bp)

# 主页路由
@app.route('/')
def index():
    """首页"""
    # 检查是否有code参数，如果有则预填充搜索框
    from flask import request
    code = request.args.get('code', '')
    return render_template('dashboard.html', search_code=code)

# 启动应用
if __name__ == '__main__':
    # 创建必要的目录
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # 预加载数据
    print("正在预加载ETF数据...")
    from services.data_service import load_latest_data
    load_result, etf_data, business_etfs, current_date_str, previous_date_str, date_range = load_latest_data()
    print(f"数据加载结果: {load_result}")
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5001)