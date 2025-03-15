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

// 搜索ETF函数
function searchETF() {
    console.log('搜索ETF函数被调用');
    
    // 获取搜索关键词
    const searchInput = document.getElementById('search-input');
    if (!searchInput) {
        console.error('未找到搜索输入框元素');
        showMessage('danger', '系统错误：未找到搜索输入框');
        return;
    }
    
    const keyword = searchInput.value.trim();
    console.log('获取到搜索关键词:', keyword);
    
    if (!keyword) {
        showMessage('warning', '请输入搜索关键词');
        return;
    }
    
    showLoading();
    console.log('发送搜索请求，关键词:', keyword);
    
    // 创建FormData对象
    const formData = new FormData();
    formData.append('code', keyword);  // 使用'code'作为参数名
    
    // 发送搜索请求
    fetch('/search', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('搜索响应状态:', response.status);
        return response.json();
    })
    .then(data => {
        hideLoading();
        console.log('搜索结果:', data);
        
        if (data.error) {
            showMessage('danger', data.error);
            document.getElementById('search-results').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        } else {
            handleSearchResult(data);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('搜索出错:', error);
        document.getElementById('search-results').innerHTML = `<div class="alert alert-danger">搜索出错: ${error}</div>`;
    });
}

// 处理搜索结果
function handleSearchResult(data) {
    console.log('处理搜索结果:', data);
    const resultsContainer = document.getElementById('search-results');
    
    if (!resultsContainer) {
        console.error('未找到搜索结果容器');
        return;
    }
    
    if (data.error) {
        resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
    }
    
    // 检查是否有结果
    if ((data.results && data.results.length === 0) || 
        (data.index_groups && data.index_groups.length === 0)) {
        resultsContainer.innerHTML = `<div class="alert alert-warning">未找到匹配"${data.keyword}"的ETF产品</div>`;
        return;
    }
    
    let html = '';
    
    // 根据搜索类型展示不同的结果
    if (data.search_type === "跟踪指数名称" && data.index_groups) {
        // 显示搜索关键词和结果数量
        html += `<div class="alert alert-success">找到 ${data.count} 个匹配"${data.keyword}"的ETF，按跟踪指数分组</div>`;
        
        // 为每个指数创建一个表格
        data.index_groups.forEach(group => {
            html += `
                <div class="card mb-4">
                    <div class="card-header">
                        <h5>${group.index_name} (${group.index_code})</h5>
                        <div class="small text-muted">总规模: ${group.total_scale}亿元 | ETF数量: ${group.etf_count}</div>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>基金代码</th>
                                        <th>基金简称</th>
                                        <th>管理人简称</th>
                                        <th>月日均交易量(亿元)</th>
                                        <th>管理费率(%)</th>
                                        <th>规模(亿元)</th>
                                        <th>是否为商务品</th>
                                        <th>关注人数</th>
                                        <th>本周新增关注</th>
                                        <th>持仓人数</th>
                                        <th>本周新增持仓</th>
                                        <th>保有规模(亿元)</th>
                                        <th>本周新增保有(亿元)</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;
            
            // 添加ETF行
            group.etfs.forEach(etf => {
                const businessClass = etf.is_business ? 'table-danger' : '';
                const attentionChangeClass = etf.attention_change > 0 ? 'text-success' : (etf.attention_change < 0 ? 'text-danger' : '');
                const holdersChangeClass = etf.holders_change > 0 ? 'text-success' : (etf.holders_change < 0 ? 'text-danger' : '');
                const amountChangeClass = etf.amount_change > 0 ? 'text-success' : (etf.amount_change < 0 ? 'text-danger' : '');
                
                html += `
                    <tr class="${businessClass}">
                        <td>${etf.code}</td>
                        <td>${etf.name}</td>
                        <td>${etf.manager}</td>
                        <td>${etf.volume.toFixed(2)}</td>
                        <td>${etf.fee_rate.toFixed(2)}%</td>
                        <td>${etf.scale.toFixed(2)}</td>
                        <td>${etf.business_text}</td>
                        <td>${etf.attention_count.toLocaleString()}</td>
                        <td class="${attentionChangeClass}">${etf.attention_change > 0 ? '+' : ''}${etf.attention_change.toLocaleString()}</td>
                        <td>${etf.holders_count.toLocaleString()}</td>
                        <td class="${holdersChangeClass}">${etf.holders_change > 0 ? '+' : ''}${etf.holders_change.toLocaleString()}</td>
                        <td>${etf.amount.toFixed(2)}</td>
                        <td class="${amountChangeClass}">${etf.amount_change > 0 ? '+' : ''}${etf.amount_change.toFixed(2)}</td>
                    </tr>
                `;
            });
            
            html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        });
    } else if (data.search_type === "基金公司名称") {
        // 显示搜索关键词和结果数量
        html += `<div class="alert alert-success">找到 ${data.count} 个匹配"${data.keyword}"的ETF产品</div>`;
        
        // 创建表格
        html += `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>产品代码</th>
                            <th>产品简称</th>
                            <th>跟踪指数代码</th>
                            <th>月日均交易量(亿元)</th>
                            <th>管理费率(%)</th>
                            <th>规模(亿元)</th>
                            <th>是否为商务品</th>
                            <th>关注人数</th>
                            <th>本周新增关注</th>
                            <th>持仓人数</th>
                            <th>本周新增持仓</th>
                            <th>保有规模(亿元)</th>
                            <th>本周新增保有(亿元)</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // 添加ETF行
        data.results.forEach(etf => {
            const businessClass = etf.is_business ? 'table-danger' : '';
            const attentionChangeClass = etf.attention_change > 0 ? 'text-success' : (etf.attention_change < 0 ? 'text-danger' : '');
            const holdersChangeClass = etf.holders_change > 0 ? 'text-success' : (etf.holders_change < 0 ? 'text-danger' : '');
            const amountChangeClass = etf.amount_change > 0 ? 'text-success' : (etf.amount_change < 0 ? 'text-danger' : '');
            
            html += `
                <tr class="${businessClass}">
                    <td>${etf.code}</td>
                    <td>${etf.name}</td>
                    <td>${etf.index_code}</td>
                    <td>${etf.volume.toFixed(2)}</td>
                    <td>${etf.fee_rate.toFixed(2)}%</td>
                    <td>${etf.scale.toFixed(2)}</td>
                    <td>${etf.business_text}</td>
                    <td>${etf.attention_count.toLocaleString()}</td>
                    <td class="${attentionChangeClass}">${etf.attention_change > 0 ? '+' : ''}${etf.attention_change.toLocaleString()}</td>
                    <td>${etf.holders_count.toLocaleString()}</td>
                    <td class="${holdersChangeClass}">${etf.holders_change > 0 ? '+' : ''}${etf.holders_change.toLocaleString()}</td>
                    <td>${etf.amount.toFixed(2)}</td>
                    <td class="${amountChangeClass}">${etf.amount_change > 0 ? '+' : ''}${etf.amount_change.toFixed(2)}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        // ETF基金代码、跟踪指数代码或通用搜索
        // 显示搜索关键词和结果数量
        html += `<div class="alert alert-success">找到 ${data.count} 个匹配"${data.keyword}"的ETF产品</div>`;
        
        // 创建表格
        html += `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>基金代码</th>
                            <th>基金简称</th>
                            <th>管理人简称</th>
                            <th>月日均交易量(亿元)</th>
                            <th>管理费率(%)</th>
                            <th>规模(亿元)</th>
                            <th>是否为商务品</th>
                            <th>关注人数</th>
                            <th>本周新增关注</th>
                            <th>持仓人数</th>
                            <th>本周新增持仓</th>
                            <th>保有规模(亿元)</th>
                            <th>本周新增保有(亿元)</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // 添加ETF行
        data.results.forEach(etf => {
            const businessClass = etf.is_business ? 'table-danger' : '';
            const attentionChangeClass = etf.attention_change > 0 ? 'text-success' : (etf.attention_change < 0 ? 'text-danger' : '');
            const holdersChangeClass = etf.holders_change > 0 ? 'text-success' : (etf.holders_change < 0 ? 'text-danger' : '');
            const amountChangeClass = etf.amount_change > 0 ? 'text-success' : (etf.amount_change < 0 ? 'text-danger' : '');
            
            html += `
                <tr class="${businessClass}">
                    <td>${etf.code}</td>
                    <td>${etf.name}</td>
                    <td>${etf.manager}</td>
                    <td>${etf.volume.toFixed(2)}</td>
                    <td>${etf.fee_rate.toFixed(2)}%</td>
                    <td>${etf.scale.toFixed(2)}</td>
                    <td>${etf.business_text}</td>
                    <td>${etf.attention_count.toLocaleString()}</td>
                    <td class="${attentionChangeClass}">${etf.attention_change > 0 ? '+' : ''}${etf.attention_change.toLocaleString()}</td>
                    <td>${etf.holders_count.toLocaleString()}</td>
                    <td class="${holdersChangeClass}">${etf.holders_change > 0 ? '+' : ''}${etf.holders_change.toLocaleString()}</td>
                    <td>${etf.amount.toFixed(2)}</td>
                    <td class="${amountChangeClass}">${etf.amount_change > 0 ? '+' : ''}${etf.amount_change.toFixed(2)}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    resultsContainer.innerHTML = html;
}

// 加载市场概览数据
function loadOverview() {
    showLoading();
    
    fetch('/overview')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            // 更新基本统计数据
            document.getElementById('total-etfs').textContent = data.total_etfs;
            document.getElementById('total-companies').textContent = data.total_companies;
            document.getElementById('total-scale').textContent = data.total_scale;
            document.getElementById('business-etfs').textContent = data.business_etfs;
            
            // 更新图表
            document.getElementById('pie-chart').src = data.pie_chart;
            document.getElementById('company-chart').src = data.company_chart;
            
            // 更新商务品表格
            const tableBody = document.getElementById('business-table');
            tableBody.innerHTML = '';
            
            data.business_companies.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.company || '-'}</td>
                    <td>${item.count || '-'}</td>
                    <td>${item.scale || '-'}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '加载市场概览数据出错: ' + error);
        });
}

// 加载商务品分析数据
function loadBusinessAnalysis() {
    showLoading();
    
    fetch('/business_analysis')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            // 更新基本统计数据
            document.getElementById('total-business').textContent = data.total_business;
            document.getElementById('business-companies').textContent = data.business_companies_count;
            document.getElementById('business-scale').textContent = data.total_scale;
            
            // 更新商务品表格
            const tableBody = document.getElementById('business-table');
            tableBody.innerHTML = '';
            
            if (data.companies && data.companies.length > 0) {
                data.companies.forEach(item => {
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
            
            showMessage('success', data.message);
            
            // 显示下载链接
            document.getElementById('report-result').style.display = 'block';
            document.getElementById('download-report-link').href = data.report_url;
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '生成报告出错: ' + error);
        });
}

// 加载数据
function loadData() {
    showLoading();
    
    fetch('/load_data')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            showMessage('success', data.message);
            
            // 更新数据状态
            document.getElementById('data-status').textContent = `数据日期: ${data.date_range}`;
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '加载数据出错: ' + error);
        });
}

// 导航功能
function showSection(sectionId) {
    // 隐藏所有内容区域
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // 显示选中的内容区域
    document.getElementById(sectionId).style.display = 'block';
    
    // 更新导航项的激活状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // 激活对应的导航项
    document.querySelector(`#nav-${sectionId.replace('section-', '')}`).classList.add('active');
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，初始化事件监听器');
    
    // 绑定搜索按钮点击事件
    const searchButton = document.querySelector('#section-search button');
    if (searchButton) {
        console.log('找到搜索按钮，绑定点击事件');
        searchButton.addEventListener('click', searchETF);
    } else {
        console.error('未找到搜索按钮');
    }
    
    // 绑定搜索输入框回车事件
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        console.log('找到搜索输入框，绑定回车事件');
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchETF();
            }
        });
    } else {
        console.error('未找到搜索输入框');
    }
    
    // 绑定导航事件
    document.getElementById('nav-search').addEventListener('click', function(e) {
        e.preventDefault();
        showSection('section-search');
    });
    
    document.getElementById('nav-overview').addEventListener('click', function(e) {
        e.preventDefault();
        showSection('section-overview');
        loadOverview();
    });
    
    document.getElementById('nav-business').addEventListener('click', function(e) {
        e.preventDefault();
        showSection('section-business');
        loadBusinessAnalysis();
    });
    
    document.getElementById('nav-report').addEventListener('click', function(e) {
        e.preventDefault();
        showSection('section-report');
    });
    
    // 绑定加载数据按钮
    document.getElementById('load-data-btn').addEventListener('click', function(e) {
        e.preventDefault();
        loadData();
    });
    
    // 如果搜索框有预填充的值，自动触发搜索
    if (searchInput && searchInput.value.trim()) {
        console.log("检测到预填充的搜索关键词，自动搜索:", searchInput.value);
        searchETF();
    }
});