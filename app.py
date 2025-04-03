import os
from flask import Flask, render_template
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import socket
import argparse
from database.models import Database
import pandas as pd

# 版本信息
__version__ = "3.0.1"   
RELEASE_DATE = "2025-04-03"

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
    from datetime import datetime
    
    code = request.args.get('code', '')
    
    # 获取推荐数据
    recommendations = {
        "attention": [],
        "holders": [],
        "amount": [],
        "price_return": [],
        "trade_date": datetime.now().strftime("%m月%d日")
    }
    
    try:
        # 创建数据库连接
        db = Database()
        
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
        
        # 获取ETF成交额数据
        amount_data = db.get_etf_amount_recommendations()
        if amount_data is not None:
            recommendations["amount"] = amount_data
            
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
    try:
        db = Database()
        
        # 导入ETF基本信息
        etf_info_file = 'data/ETF_DATA_20250331.xlsx'
        if os.path.exists(etf_info_file):
            df = pd.read_excel(etf_info_file, engine='openpyxl')
            if db.save_etf_info(df):
                print(f"成功导入ETF基本信息：{len(df)}条记录")
            else:
                print("导入ETF基本信息失败")
        
        # 导入商务协议数据
        business_file = 'data/ETF单产品商务协议20250328.xlsx'
        if os.path.exists(business_file):
            df = pd.read_excel(business_file, engine='openpyxl')
            if db.save_business_etf(df):
                print(f"成功导入商务协议数据：{len(df)}条记录")
            else:
                print("导入商务协议数据失败")
        
        # 导入自选数据
        attention_file = 'data/客户ETF自选人数20250331.xlsx'
        if os.path.exists(attention_file):
            df = pd.read_excel(attention_file, engine='openpyxl')
            if db.save_etf_attention(df):
                print(f"成功导入自选数据：{len(df)}条记录")
            else:
                print("导入自选数据失败")
        
        # 导入持有人数据
        holders_file = 'data/客户ETF保有量20250331.xlsx'
        if os.path.exists(holders_file):
            df = pd.read_excel(holders_file, engine='openpyxl')
            if db.save_etf_holders(df):
                print(f"成功导入持有人数据：{len(df)}条记录")
            else:
                print("导入持有人数据失败")
        
        # 验证数据
        etf_data = db.get_all_etf_info()
        business_etfs = db.get_all_business_etf()
        print(f"当前数据库中的ETF数据：{len(etf_data)}条记录")
        print(f"当前数据库中的商务ETF数据：{len(business_etfs)}条记录")
        
    except Exception as e:
        print(f"预加载数据失败: {str(e)}")
        print("请确保已经导入了ETF数据")
        exit(1)
    
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
    