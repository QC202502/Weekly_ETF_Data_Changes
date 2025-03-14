import pandas as pd
import glob
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# 全局变量存储数据
etf_data = None
business_etfs = set()  # 存储商务品ETF代码

def load_latest_data():
    """加载最新的ETF数据和商务品信息"""
    global etf_data, business_etfs
    
    # 动态获取最新数据文件
    files = glob.glob('ETF_基础数据合并_*.csv')
    if not files:
        return "未找到ETF基础数据文件"
    
    # 提取最新文件日期
    filename = sorted(files)[-1]
    date_str = filename.split('_')[-1].split('.')[0]
    
    try:
        # 读取ETF基础数据
        etf_data = pd.read_csv(filename, encoding='utf-8-sig')
        
        # 确保证券代码为字符串
        etf_data['证券代码'] = etf_data['证券代码'].astype(str).str.strip()
        
        # 获取当前日期
        current_date = datetime.strptime(date_str, "%Y%m%d")
        current_str = current_date.strftime("%m月%d日")
        
        # 读取商务协议文件
        商务协议_path = f'/Users/admin/Downloads/ETF单产品商务协议{date_str}.xlsx'
        try:
            # 尝试读取商务协议文件
            商务协议 = pd.read_excel(商务协议_path, engine='openpyxl')
            
            # 确保证券代码为字符串并去除空格
            商务协议['证券代码'] = 商务协议['证券代码'].astype(str).str.strip()
            
            # 添加商务品标记
            商务协议['是否商务品'] = '商务'
            
            # 合并商务协议数据
            etf_data = etf_data.merge(
                商务协议[['证券代码', '是否商务品']],
                on='证券代码',
                how='left'
            ).fillna({'是否商务品': '非商务'})
            
            # 更新商务品集合
            business_etfs = set(商务协议['证券代码'].unique())
            
            return f"数据已加载，日期：{current_str}，商务品数量：{len(business_etfs)}个"
            
        except FileNotFoundError:
            return f"警告：商务协议文件缺失：{商务协议_path}，将无法显示商务品信息"
        except Exception as e:
            return f"读取商务协议文件出错: {str(e)}，将无法显示商务品信息"
        
    except Exception as e:
        return f"加载数据出错：{str(e)}"

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """搜索ETF竞品"""
    if etf_data is None:
        return jsonify({"error": "数据未加载，请先加载数据"})
    
    # 获取请求参数
    code = request.form.get('code', '').strip()
    
    if not code:
        return jsonify({"error": "请输入ETF证券代码"})
    
    try:
        # 查找输入的ETF
        target_etf = etf_data[etf_data['证券代码'] == code]
        
        if target_etf.empty:
            return jsonify({"error": f"未找到证券代码为 {code} 的ETF"})
        
        # 获取跟踪指数代码
        tracking_index_code = target_etf['跟踪指数代码'].iloc[0]
        tracking_index_name = target_etf['跟踪指数名称'].iloc[0]
        
        # 查找同跟踪指数的所有ETF产品
        alternative_etfs = etf_data[etf_data['跟踪指数代码'] == tracking_index_code]
        
        # 去重并排序
        alternative_etfs = alternative_etfs.drop_duplicates(subset=['证券代码'])
        alternative_etfs = alternative_etfs.sort_values(by='月成交额[交易日期]最新收盘日[单位]百万元', ascending=False)
        
        # 提取需要的字段
        current_date = [col for col in alternative_etfs.columns if '证券名称' in col][0]
        
        result = []
        for _, row in alternative_etfs.iterrows():
            # 简化基金管理人名称
            manager = get_manager_short(row['基金管理人'])
            
            # 格式化数据
            item = {
                "证券代码": row['证券代码'],
                "产品名称": row[current_date],
                "管理人": manager,
                "规模(亿)": round(row['基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'], 2),
                "管理费率(%)": row['管理费率[单位]%'],
                "月日均交易额(百万)": round(row['月成交额[交易日期]最新收盘日[单位]百万元'], 2),
                "是否商务品": row.get('是否商务品', '未知')
            }
            result.append(item)
        
        return jsonify({
            "success": True,
            "tracking_index_code": tracking_index_code,
            "tracking_index_name": tracking_index_name,
            "data": result
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"查询出错：{str(e)}"})

@app.route('/load_data')
def load_data():
    """加载数据接口"""
    message = load_latest_data()
    return jsonify({"message": message})

def get_manager_short(full_name):
    """基金管理人简称提取（从etf_reporter.py复制）"""
    special_mapping = {
        '汇添富基金管理有限公司': '汇添富',
        '易方达基金管理有限公司': '易方达',
        '华夏基金管理有限公司': '华夏',
        '南方基金管理股份有限公司': '南方',
        '嘉实基金管理有限公司': '嘉实'
    }
    if full_name in special_mapping:
        return special_mapping[full_name]

    patterns = ['基金管理有限公司', '基金管理公司', '基金', '管理有限公司', '股份有限公司']
    for pattern in patterns:
        if pattern in full_name:
            return full_name.split(pattern)[0]

    return full_name[:4] if len(full_name) >= 4 else full_name

# 创建templates目录
os.makedirs('templates', exist_ok=True)

# 创建HTML模板
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETF竞品查询工具</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding: 20px;
        }
        .header {
            margin-bottom: 30px;
        }
        .result-container {
            margin-top: 30px;
        }
        .loading {
            display: none;
            margin-top: 20px;
        }
        .status-message {
            margin-top: 10px;
            font-style: italic;
        }
        .highlight {
            background-color: #ffffcc;
        }
        .business {
            color: #FF0000;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ETF竞品查询工具</h1>
            <p>输入ETF证券代码，查询同跟踪指数下的所有ETF产品信息</p>
            <button id="loadDataBtn" class="btn btn-secondary">加载最新数据</button>
            <div class="status-message" id="statusMessage"></div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="input-group mb-3">
                    <input type="text" id="etfCode" class="form-control" placeholder="请输入ETF证券代码">
                    <button class="btn btn-primary" id="searchBtn">查询</button>
                </div>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span class="ms-2">正在查询...</span>
        </div>
        
        <div class="result-container" id="resultContainer" style="display:none;">
            <h3>查询结果</h3>
            <div id="indexInfo" class="alert alert-info"></div>
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>证券代码</th>
                        <th>产品名称</th>
                        <th>管理人</th>
                        <th>规模(亿)</th>
                        <th>管理费率(%)</th>
                        <th>月日均交易额(百万)</th>
                        <th>是否商务品</th>
                    </tr>
                </thead>
                <tbody id="resultTable">
                </tbody>
            </table>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('searchBtn').addEventListener('click', function() {
            const etfCode = document.getElementById('etfCode').value.trim();
            if (!etfCode) {
                alert('请输入ETF证券代码');
                return;
            }
            
            // 显示加载中
            document.getElementById('loading').style.display = 'flex';
            document.getElementById('resultContainer').style.display = 'none';
            
            // 发送请求
            const formData = new FormData();
            formData.append('code', etfCode);
            
            fetch('/search', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // 隐藏加载中
                document.getElementById('loading').style.display = 'none';
                
                if (data.error) {
                    alert(data.error);
                    return;
                }
                
                // 显示结果
                document.getElementById('resultContainer').style.display = 'block';
                document.getElementById('indexInfo').textContent = 
                    `跟踪指数: ${data.tracking_index_name} (${data.tracking_index_code}), 共${data.data.length}只ETF产品`;
                
                const resultTable = document.getElementById('resultTable');
                resultTable.innerHTML = '';
                
                data.data.forEach(item => {
                    const row = document.createElement('tr');
                    
                    // 高亮显示当前查询的ETF
                    if (item.证券代码 === etfCode) {
                        row.classList.add('highlight');
                    }
                    
                    // 添加单元格
                    const fields = ['证券代码', '产品名称', '管理人', '规模(亿)', '管理费率(%)', '月日均交易额(百万)', '是否商务品'];
                    fields.forEach(field => {
                        const cell = document.createElement('td');
                        cell.textContent = item[field];
                        
                        // 商务品标红
                        if (field === '是否商务品' && item[field] === '商务') {
                            cell.classList.add('business');
                        }
                        
                        row.appendChild(cell);
                    });
                    
                    resultTable.appendChild(row);
                });
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                alert('查询出错: ' + error);
            });
        });
        
        // 加载数据按钮
        document.getElementById('loadDataBtn').addEventListener('click', function() {
            const statusMessage = document.getElementById('statusMessage');
            statusMessage.textContent = '正在加载数据...';
            
            fetch('/load_data')
            .then(response => response.json())
            .then(data => {
                statusMessage.textContent = data.message;
            })
            .catch(error => {
                statusMessage.textContent = '加载数据出错: ' + error;
            });
        });
        
        // 页面加载时自动加载数据
        window.addEventListener('load', function() {
            document.getElementById('loadDataBtn').click();
        });
    </script>
</body>
</html>
    ''')

if __name__ == '__main__':
    print("ETF竞品查询工具启动中...")
    print("初始加载数据...")
    load_latest_data()
    print("启动Web服务器，请访问 http://127.0.0.1:5000/")
    app.run(debug=True)