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
__version__ = "3.1.0"   
RELEASE_DATE = "2025-04-04"

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

def preload_data():
    """预加载ETF数据到内存"""
    try:
        print("正在预加载ETF数据...")
        # 初始化数据库
        db = Database()
        
        # 记录今天的日期
        today = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 查找最新的ETF数据文件
        etf_files = [f for f in os.listdir('data') if f.startswith('ETF_DATA_') and f.endswith('.xlsx')]
        etf_files.sort(reverse=True)  # 按文件名降序排序，最新的文件名最大
        
        if etf_files:
            latest_etf_file = os.path.join('data', etf_files[0])
            print(f"找到最新ETF数据文件: {latest_etf_file}")
            df = pd.read_excel(latest_etf_file, engine='openpyxl')
            if db.save_etf_info(df):
                print(f"成功导入ETF数据：{len(df)}条记录")
            else:
                print("导入ETF数据失败")
        else:
            print("未找到ETF数据文件")
        
        # 查找最新的自选数据文件
        attention_files = [f for f in os.listdir('data') if f.startswith('客户ETF自选人数') and f.endswith('.xlsx')]
        attention_files.sort(reverse=True)
        
        if attention_files:
            latest_attention_file = os.path.join('data', attention_files[0])
            print(f"找到最新自选人数文件: {latest_attention_file}")
            df = pd.read_excel(latest_attention_file, engine='openpyxl')
            if db.save_etf_attention(df):
                print(f"成功导入自选数据：{len(df)}条记录")
            else:
                print("导入自选数据失败")
        else:
            print("未找到自选人数文件")
        
        # 查找最新的持有人数据文件
        holders_files = [f for f in os.listdir('data') if f.startswith('客户ETF保有量') and f.endswith('.xlsx')]
        holders_files.sort(reverse=True)
        
        if holders_files:
            latest_holders_file = os.path.join('data', holders_files[0])
            print(f"找到最新持有人数据文件: {latest_holders_file}")
            df = pd.read_excel(latest_holders_file, engine='openpyxl')
            if db.save_etf_holders(df):
                print(f"成功导入持有人数据：{len(df)}条记录")
            else:
                print("导入持有人数据失败")
        else:
            print("未找到持有人数据文件")
        
        # 查找商务协议数据文件
        business_files = [f for f in os.listdir('data') if f.startswith('ETF单产品商务协议') and f.endswith('.xlsx')]
        business_files.sort(reverse=True)
        
        if business_files:
            latest_business_file = os.path.join('data', business_files[0])
            print(f"找到最新商务协议文件: {latest_business_file}")
            df = pd.read_excel(latest_business_file, engine='openpyxl')
            if db.save_business_etf(df):
                print(f"成功导入商务协议数据：{len(df)}条记录")
            else:
                print("导入商务协议数据失败")
        else:
            print("未找到商务协议文件")
        
        # 自动将当前数据保存到历史表中
        try:
            # 确保历史表存在
            cursor = db.conn.cursor()
            
            # 创建ETF自选历史表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etf_attention_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    attention_count INTEGER,
                    date TEXT,
                    update_time TIMESTAMP
                )
            """)
            
            # 创建ETF持有人历史表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etf_holders_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    holder_count INTEGER,
                    holding_amount REAL,
                    date TEXT,
                    update_time TIMESTAMP
                )
            """)
            
            # 创建ETF规模历史表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etf_fund_size_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    fund_size REAL,
                    date TEXT,
                    update_time TIMESTAMP
                )
            """)
            
            # 检查是否已有今天的历史数据
            cursor.execute("SELECT COUNT(*) FROM etf_fund_size_history WHERE date = ?", (today,))
            if cursor.fetchone()[0] == 0:
                # 保存ETF规模历史数据
                cursor.execute("""
                    INSERT INTO etf_fund_size_history (code, fund_size, date, update_time)
                    SELECT code, fund_size, ?, ?
                    FROM etf_info
                    WHERE fund_size > 0
                """, (today, current_time))
                print(f"已保存当天ETF规模数据到历史表")
            else:
                print(f"当天({today})ETF规模历史数据已存在，跳过")
            
            # 检查是否已有今天的持有人历史数据
            cursor.execute("SELECT COUNT(*) FROM etf_holders_history WHERE date = ?", (today,))
            if cursor.fetchone()[0] == 0:
                # 保存ETF持有人历史数据
                cursor.execute("""
                    INSERT INTO etf_holders_history (code, holder_count, holding_amount, date, update_time)
                    SELECT code, holder_count, holding_amount, ?, ?
                    FROM etf_holders
                """, (today, current_time))
                print(f"已保存当天ETF持有人数据到历史表")
            else:
                print(f"当天({today})ETF持有人历史数据已存在，跳过")
            
            # 检查是否已有今天的自选历史数据
            cursor.execute("SELECT COUNT(*) FROM etf_attention_history WHERE date = ?", (today,))
            if cursor.fetchone()[0] == 0:
                # 保存ETF自选历史数据
                cursor.execute("""
                    INSERT INTO etf_attention_history (code, attention_count, date, update_time)
                    SELECT code, attention_count, ?, ?
                    FROM etf_attention
                """, (today, current_time))
                print(f"已保存当天ETF自选数据到历史表")
            else:
                print(f"当天({today})ETF自选历史数据已存在，跳过")
            
            db.conn.commit()
        except Exception as e:
            print(f"保存历史数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 验证数据
        etf_data = db.get_all_etf_info()
        business_etfs = db.get_all_business_etf()
        print(f"当前数据库中的ETF数据：{len(etf_data)}条记录")
        print(f"当前数据库中的商务ETF数据：{len(business_etfs)}条记录")
        
    except Exception as e:
        print(f"预加载数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print("请确保已经导入了ETF数据")
        exit(1)

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
    