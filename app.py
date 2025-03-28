import os
from flask import Flask, render_template
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import socket
import argparse

# 版本信息
__version__ = "3.0.0"   
RELEASE_DATE = "2025-03-27"

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
    import os
    import json
    from datetime import datetime
    
    code = request.args.get('code', '')
    
    # 获取推荐数据
    recommendations = {
        "attention": [],
        "holders": [],
        "amount": [],
        "price_return": [],
        "trade_date": "3月19日"
    }
    
    try:
        # 查找最新的ETF价格推荐数据文件
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        today = datetime.now().strftime('%Y%m%d')
        price_recommendation_file = os.path.join(data_dir, f"etf_price_recommendations_{today}.json")
        
        # 读取ETF价格推荐数据
        if os.path.exists(price_recommendation_file):
            with open(price_recommendation_file, 'r', encoding='utf-8') as f:
                price_data = json.load(f)
                recommendations["price_return"] = price_data.get("price_return", [])
                # 获取交易日期信息，如果JSON中没有trade_date字段，则使用默认值
                recommendations["trade_date"] = price_data.get("trade_date", "3月19日")
    except Exception as e:
        print(f"加载ETF价格推荐数据出错: {str(e)}")
    
    return render_template('dashboard.html', search_code=code, recommendations=recommendations)

# 检查端口是否可用
def is_port_available(port):
    """检查指定端口是否可用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except socket.error:
            return False

# 查找可用端口
def find_available_port(start_port, max_attempts=100):
    """从指定端口开始查找可用端口"""
    port = start_port
    for _ in range(max_attempts):
        if is_port_available(port):
            return port
        port += 1
    return None

# 启动应用
if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='ETF数据分析平台')
    parser.add_argument('--port', type=int, default=5007, help='指定服务端口，默认为5007')
    args = parser.parse_args()
    
    # 创建必要的目录
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # 预加载数据
    print("正在预加载ETF数据...")
    from services.data_service import load_latest_data
    load_result, etf_data, business_etfs, current_date_str, previous_date_str, date_range = load_latest_data()
    print(f"数据加载结果: {load_result}")
    
    # 检查端口是否可用，如果不可用则自动查找可用端口
    port = args.port
    if not is_port_available(port):
        print(f"端口 {port} 已被占用，正在查找可用端口...")
        available_port = find_available_port(port + 1)
        if available_port:
            port = available_port
            print(f"已自动切换到可用端口: {port}")
        else:
            print("无法找到可用端口，请手动指定其他端口或关闭占用端口的程序")
            print("提示：您可以使用 --port 参数指定其他端口，例如: python app.py --port 8080")
            exit(1)
    
    # 启动应用
    print(f"服务已启动，请访问 http://localhost:{port} 或 http://127.0.0.1:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)
    