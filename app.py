import os
from flask import Flask, render_template, request, send_from_directory
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import socket
import argparse
from database.models import Database
import pandas as pd
import logging
import sys
from datetime import datetime
import time
import json

# 配置全局日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# 版本信息
__version__ = "3.5.1"   
RELEASE_DATE = "2025-04-16"

# 创建Flask应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 限制上传文件大小为50MB
app.logger.setLevel(logging.DEBUG)

# 禁用静态文件缓存
@app.after_request
def add_cache_control(response):
    """为静态资源添加缓存控制头"""
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

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
    from datetime import datetime
    
    code = request.args.get('code', '')
    
    # 获取推荐数据
    recommendations = {
        "attention": [],
        "holders": [],
        "value": [],
        "price_return": [],
        "trade_date": "",  # 将由数据库提供的最新日期填充
        "date_for_title": ""  # 将由数据库提供的最新日期填充
    }
    
    try:
        # 创建数据库连接
        db = Database()
        
        # 获取最新的交易日期
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(date) FROM etf_price")
        latest_date = cursor.fetchone()[0]
        
        if latest_date:
            # 直接使用最新数据的日期，而不是当前日期
            date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
            # 格式化为"MM月DD日"
            recommendations["trade_date"] = f"{date_obj.month}月{date_obj.day}日"
            # 给页面标题使用的日期，格式为"04月16日"，补零
            recommendations["date_for_title"] = f"{date_obj.month:02d}月{date_obj.day:02d}日"
            print(f"最新数据日期: {latest_date}, 格式化为: {recommendations['date_for_title']}")
        else:
            # 如果没有最新日期，使用默认值
            recommendations["trade_date"] = "最新"
            recommendations["date_for_title"] = "最新"
        
        # 获取ETF价格数据
        price_data = db.get_etf_price_recommendations()
        if price_data is not None:
            recommendations["price_return"] = price_data
        
        # 获取ETF持有人数据
        holders_data = db.get_etf_holders_recommendations()
        if holders_data is not None:
            recommendations["holders"] = holders_data
        
        # 获取ETF自选数据
        attention_data = db.get_etf_attention_recommendations()
        if attention_data is not None:
            recommendations["attention"] = attention_data
        
        # 获取ETF持仓价值数据
        value_data = db.get_etf_value_recommendations()
        if value_data is not None:
            recommendations["value"] = value_data
            
    except Exception as e:
        print(f"加载ETF推荐数据出错: {str(e)}")
    
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

def preload_data():
    """预加载ETF数据到内存"""
    try:
        print("开始预加载ETF数据...")
        start_time = time.time()
        
        # 从数据库加载
        db = Database()
        
        # 获取推荐数据
        price_recommendations = db.get_etf_price_recommendations()
        holders_recommendations = db.get_etf_holders_recommendations()
        attention_recommendations = db.get_etf_attention_recommendations()
        value_recommendations = db.get_etf_value_recommendations()
        
        # 读取价格建议文件
        today = datetime.now().strftime('%Y%m%d')
        price_recommendations_file = os.path.join(app.config['UPLOAD_FOLDER'], f'etf_price_recommendations_{today}.json')
        
        if os.path.exists(price_recommendations_file):
            try:
                with open(price_recommendations_file, 'r') as f:
                    from_file = json.load(f)
                if isinstance(from_file, list) and len(from_file) > 0:
                    print(f"从文件加载价格推荐数据: {len(from_file)}条记录")
                    price_recommendations = from_file
            except Exception as e:
                print(f"读取价格推荐文件失败: {str(e)}")
        
        # 保存到应用配置
        app.config['PRICE_RECOMMENDATIONS'] = price_recommendations
        app.config['HOLDERS_RECOMMENDATIONS'] = holders_recommendations
        app.config['ATTENTION_RECOMMENDATIONS'] = attention_recommendations
        app.config['VALUE_RECOMMENDATIONS'] = value_recommendations
        
        print(f"ETF价格推荐数据: {len(price_recommendations)}条记录")
        print(f"ETF持有人推荐数据: {len(holders_recommendations)}条记录")
        print(f"ETF自选推荐数据: {len(attention_recommendations)}条记录")
        print(f"ETF持仓价值推荐数据: {len(value_recommendations)}条记录")
        
        # 写入价格推荐文件
        try:
            today = datetime.now().strftime('%Y%m%d')
            price_recommendations_file = os.path.join(app.config['UPLOAD_FOLDER'], f'etf_price_recommendations_{today}.json')
            
            with open(price_recommendations_file, 'w') as f:
                json.dump(price_recommendations, f)
            
            print(f"价格推荐数据已保存到: {price_recommendations_file}")
        except Exception as e:
            print(f"保存价格推荐数据失败: {str(e)}")
        
        # 记录加载时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"ETF数据预加载完成，耗时: {elapsed_time:.2f}秒")
        
        # 记录成功加载状态
        app.config['DATA_LOADED'] = True
        
        # 注意：删除了自动将当前数据保存到历史表的逻辑，防止生成模拟数据
        
    except Exception as e:
        print(f"预加载ETF数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        app.config['DATA_LOADED'] = False

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
    preload_data()
    
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
    print(f"如果浏览器无法访问，请确认使用的是 http://localhost:{port} 而不是 https://localhost:{port}")
    print(f"您也可以尝试使用其他端口启动，例如: python app.py --port 8080")
    app.run(debug=True, host='0.0.0.0', port=port)
    