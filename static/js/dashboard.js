// 显示加载中
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

// 隐藏加载中
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// 显示消息
function showMessage(type, message) {
    const messageElement = document.getElementById('status-message');
    messageElement.className = `alert alert-${type} status-message`;
    messageElement.textContent = message;
    messageElement.style.display = 'block';
    
    // 3秒后自动隐藏
    setTimeout(() => {
        messageElement.style.display = 'none';
    }, 3000);
}

// 处理搜索结果的函数
function handleSearchResult(data) {
    console.log("搜索结果:", data);
    
    if (data.error) {
        document.getElementById('search-results').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
    }
    
    if (data.success) {
        let html = '';
        
        // 检查是否是按跟踪指数名称分组的结果
        if (data.search_type === "跟踪指数名称" && data.index_groups) {
            // 显示搜索关键词
            html += `<div class="alert alert-info">搜索关键词: "${data.keyword}" - 找到 ${data.index_groups.length} 个相关指数</div>`;
            
            // 遍历每个指数分组
            data.index_groups.forEach(group => {
                // 按月日均交易额排序
                if (group.data && group.data.length > 0) {
                    group.data.sort((a, b) => {
                        // 尝试获取交易额数据
                        let volumeA = 0;
                        let volumeB = 0;
                        
                        for (const key in a) {
                            if (key.includes('交易额') || key.includes('日均')) {
                                const val = parseFloat(a[key]);
                                if (!isNaN(val)) {
                                    volumeA = val;
                                    break;
                                }
                            }
                        }
                        
                        for (const key in b) {
                            if (key.includes('交易额') || key.includes('日均')) {
                                const val = parseFloat(b[key]);
                                if (!isNaN(val)) {
                                    volumeB = val;
                                    break;
                                }
                            }
                        }
                        
                        // 降序排列
                        return volumeB - volumeA;
                    });
                }
                
                html += createResultTable(group.data, group.tracking_index_name, group.tracking_index_code, group.total_scale);
            });
        } else if (data.data && data.data.length > 0) {
            // 标准搜索结果格式
            // 显示搜索类型
            html += `<div class="alert alert-info">搜索类型: ${data.search_type} - 找到 ${data.data.length} 个结果</div>`;
            
            // 按月日均交易额排序
            data.data.sort((a, b) => {
                // 尝试获取交易额数据
                let volumeA = 0;
                let volumeB = 0;
                
                for (const key in a) {
                    if (key.includes('交易额') || key.includes('日均')) {
                        const val = parseFloat(a[key]);
                        if (!isNaN(val)) {
                            volumeA = val;
                            break;
                        }
                    }
                }
                
                for (const key in b) {
                    if (key.includes('交易额') || key.includes('日均')) {
                        const val = parseFloat(b[key]);
                        if (!isNaN(val)) {
                            volumeB = val;
                            break;
                        }
                    }
                }
                
                // 降序排列
                return volumeB - volumeA;
            });
            
            html += createResultTable(data.data, data.tracking_index_name, data.tracking_index_code);
        } else {
            html = '<div class="alert alert-warning">未找到匹配的ETF产品</div>';
        }
        
        document.getElementById('search-results').innerHTML = html;
    } else {
        document.getElementById('search-results').innerHTML = '<div class="alert alert-warning">未找到匹配的ETF产品</div>';
    }
}

// 创建结果表格的函数
function createResultTable(data, indexName, indexCode, totalScale) {
    let html = `
        <div class="card mb-4">
            <div class="card-header">
                <h5>跟踪指数: ${indexName || '未知'} (${indexCode || '未知'})${totalScale ? ' - 总规模: ' + totalScale + ' 亿元' : ''}</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>证券代码</th>
                                <th>证券名称</th>
                                <th>基金管理人</th>
                                <th>基金规模(亿)</th>
                                <th>管理费率(%)</th>
                                <th>月日均交易额(亿)</th>
                                <th>是否商务品</th>
                            </tr>
                        </thead>
                        <tbody>`;
    
    // 添加数据行
    data.forEach(item => {
        const isBusinessClass = item['是否商务品'] === '商务' ? 'table-success' : '';
        
        // 尝试获取不同可能的列名
        const code = item['证券代码'] || '';
        const name = item['证券简称'] || item['证券名称'] || item['产品名称'] || item['基金名称'] || '未知';
        const manager = item['管理人简称'] || 
                       (item['基金管理人'] ? item['基金管理人'].replace(/基金管理.*公司|基金管理公司|基金|管理有限公司|股份有限公司/g, '') : '未知');
        
        // 查找规模列并格式化为小数点后两位
        let scale = '未知';
        for (const key in item) {
            if (key.includes('基金规模') && key.includes('亿元')) {
                const scaleValue = parseFloat(item[key]);
                if (!isNaN(scaleValue)) {
                    scale = scaleValue.toFixed(2);
                } else {
                    scale = item[key];
                }
                break;
            }
        }
        
        // 查找正确的管理费率列并格式化为小数点后两位
        let fee = '未知';
        if (item['正确管理费率']) {
            const feeValue = parseFloat(item['正确管理费率']);
            if (!isNaN(feeValue)) {
                fee = feeValue.toFixed(2);
            } else {
                fee = item['正确管理费率'];
            }
        } else {
            for (const key in item) {
                if (key.includes('管理费率') && !key.includes('托管')) {
                    const feeValue = parseFloat(item[key]);
                    if (!isNaN(feeValue)) {
                        fee = feeValue.toFixed(2);
                    } else {
                        fee = item[key];
                    }
                    break;
                }
            }
        }
        
        // 查找交易额列并格式化为小数点后两位
        let volume = '未知';
        for (const key in item) {
            if (key.includes('交易额') || key.includes('日均')) {
                const volumeValue = parseFloat(item[key]);
                if (!isNaN(volumeValue)) {
                    volume = volumeValue.toFixed(2);
                } else {
                    volume = item[key];
                }
                break;
            }
        }
        
        html += `
            <tr class="${isBusinessClass}">
                <td>${code}</td>
                <td>${name}</td>
                <td>${manager}</td>
                <td>${scale !== '未知' ? scale : '未知'}</td>
                <td>${fee !== '未知' ? fee : '未知'}</td>
                <td>${volume !== '未知' ? volume : '未知'}</td>
                <td>${item['是否商务品'] || '未知'}</td>
            </tr>`;
    });
    
    html += `
            </tbody>
        </table>
    </div>
</div>
</div>`;

    return html;
}

// 加载数据
function loadData() {
    showLoading();
    
    fetch('/load_data')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                document.getElementById('data-status').textContent = '数据已加载';
                showMessage('success', data.message);
            } else {
                document.getElementById('data-status').textContent = '加载失败';
                showMessage('danger', data.message);
            }
        })
        .catch(error => {
            hideLoading();
            document.getElementById('data-status').textContent = '加载出错';
            showMessage('danger', '加载数据出错: ' + error);
        });
}

// 加载市场概览数据
function loadOverviewData() {
    showLoading();
    
    fetch('/overview')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            // 填充统计数据
            if (data.stats) {
                document.getElementById('total-etfs').textContent = data.stats.total_etfs || '-';
                document.getElementById('total-companies').textContent = data.stats.total_companies || '-';
                document.getElementById('total-scale').textContent = data.stats.total_scale || '-';
                document.getElementById('business-etfs').textContent = data.stats.business_etfs || '-';
            }
            
            // 显示图表
            if (data.charts && data.charts.pie_chart) {
                const pieImg = document.getElementById('pie-chart');
                pieImg.src = 'data:image/png;base64,' + data.charts.pie_chart;
                pieImg.style.display = 'block'; // 确保图片显示
                pieImg.onerror = function() {
                    console.error('饼图加载失败');
                    this.style.display = 'none';
                    const container = this.parentElement;
                    container.innerHTML += '<div class="alert alert-warning">图表加载失败</div>';
                };
            }
            
            if (data.charts && data.charts.company_chart) {
                const companyImg = document.getElementById('company-chart');
                companyImg.src = 'data:image/png;base64,' + data.charts.company_chart;
                companyImg.style.display = 'block'; // 确保图片显示
                companyImg.onerror = function() {
                    console.error('柱状图加载失败');
                    this.style.display = 'none';
                    const container = this.parentElement;
                    container.innerHTML += '<div class="alert alert-warning">图表加载失败</div>';
                };
            }
            
            // 填充公司表格
            if (data.top_companies && data.top_companies.length > 0) {
                const tableBody = document.getElementById('company-table');
                tableBody.innerHTML = '';
                
                data.top_companies.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.company || '-'}</td>
                        <td>${item.count || '-'}</td>
                        <td>${item.scale || '-'}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
            
            // 填充商务品表格
            if (data.business_etfs && data.business_etfs.length > 0) {
                const tableBody = document.getElementById('business-table');
                tableBody.innerHTML = '';
                
                data.business_etfs.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.code || '-'}</td>
                        <td>${item.name || '-'}</td>
                        <td>${item.company || '-'}</td>
                        <td>${item.scale || '-'}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '加载市场概览数据出错: ' + error);
        });
}

// 加载商务品分析数据
function loadBusinessData() {
    showLoading();
    
    fetch('/business_analysis')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            // 填充统计数据
            if (data.stats) {
                document.getElementById('total-business').textContent = data.stats.total_business || '-';
                document.getElementById('business-companies').textContent = data.stats.total_companies || '-';
                document.getElementById('business-scale').textContent = data.stats.total_scale || '-';
            }
            
            // 填充表格数据
            if (data.by_company && data.by_company.length > 0) {
                const tableBody = document.getElementById('business-analysis-table');
                tableBody.innerHTML = '';
                
                data.by_company.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.company || '-'}</td>
                        <td>${item.count || '-'}</td>
                        <td>${item.scale || '-'}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '加载商务品分析数据出错: ' + error);
        });
}

// 生成报告
function generateReport() {
    showLoading();
    
    fetch('/generate_report')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            if (data.success) {
                showMessage('success', '报告生成成功');
                
                // 如果有下载链接，创建下载按钮
                if (data.download_url) {
                    const downloadBtn = document.createElement('a');
                    downloadBtn.href = data.download_url;
                    downloadBtn.className = 'btn btn-primary mt-3';
                    downloadBtn.innerHTML = '<i class="bi bi-download"></i> 下载报告';
                    downloadBtn.download = data.filename || 'etf_report.xlsx';
                    
                    const reportSection = document.getElementById('report-content');
                    reportSection.innerHTML = '<div class="alert alert-success">报告已生成，请点击下方按钮下载</div>';
                    reportSection.appendChild(downloadBtn);
                }
            } else {
                showMessage('warning', data.message || '报告生成失败');
            }
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '生成报告出错: ' + error);
        });
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 导航切换
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除所有active类
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            
            // 添加active类到当前点击的链接
            this.classList.add('active');
            
            // 隐藏所有内容区域
            document.querySelectorAll('.content-section').forEach(section => {
                section.style.display = 'none';
            });
            
            // 显示对应的内容区域
            if (this.id === 'nav-search') {
                document.getElementById('section-search').style.display = 'block';
            } else if (this.id === 'nav-overview') {
                document.getElementById('section-overview').style.display = 'block';
                loadOverviewData();
            } else if (this.id === 'nav-business') {
                document.getElementById('section-business').style.display = 'block';
                loadBusinessData();
            } else if (this.id === 'nav-report') {
                document.getElementById('section-report').style.display = 'block';
            }
        });
    });
    
    // 加载数据按钮
    document.getElementById('load-data-btn').addEventListener('click', function(e) {
        e.preventDefault();
        loadData();
    });
    
    // 搜索表单提交处理
    document.getElementById('search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        console.log("搜索表单已提交");
        
        // 显示加载状态
        document.getElementById('search-results').innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // 获取表单数据
        const formData = new FormData(this);
        const code = formData.get('code');
        console.log("搜索代码:", code);
        
        // 发送请求
        fetch('/search', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log("收到响应:", response.status);
            return response.json();
        })
        .then(data => {
            handleSearchResult(data);
        })
        .catch(error => {
            console.error('搜索出错:', error);
            document.getElementById('search-results').innerHTML = '<div class="alert alert-danger">搜索请求出错，请查看控制台</div>';
        });
    });
    
    // 生成报告按钮
    document.getElementById('generate-report-btn').addEventListener('click', function(e) {
        e.preventDefault();
        generateReport();
    });
    
    // 如果搜索框有预填充的值，自动触发搜索
    const searchCode = document.getElementById('search-code').value;
    if (searchCode) {
        console.log("检测到URL中的code参数，自动搜索:", searchCode);
        // 延迟一点执行搜索，确保页面已完全加载
        setTimeout(function() {
            // 创建一个FormData对象
            const formData = new FormData();
            formData.append('code', searchCode);
            
            // 显示加载状态
            document.getElementById('search-results').innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
            
            // 发送搜索请求
            fetch('/search', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                handleSearchResult(data);
            })
            .catch(error => {
                console.error('自动搜索出错:', error);
                document.getElementById('search-results').innerHTML = '<div class="alert alert-danger">搜索请求出错，请查看控制台</div>';
            });
        }, 500);
    }
    
    // 页面加载完成后自动加载数据
    loadData();
});