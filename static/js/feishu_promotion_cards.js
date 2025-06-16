/**
 * 推广效果分析 - 关键指标总览卡片组件
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化总览卡片
    initPromotionOverview();
});

/**
 * 初始化推广效果总览卡片
 */
function initPromotionOverview() {
    // 获取筛选条件
    const startDateInput = document.getElementById('filter-start-date');
    const endDateInput = document.getElementById('filter-end-date');
    const channelSelect = document.getElementById('filter-channel');
    const companySelect = document.getElementById('filter-company');
    
    // 监听筛选条件变化，重新加载数据
    [startDateInput, endDateInput, channelSelect, companySelect].forEach(element => {
        if (element) {
            element.addEventListener('change', loadOverviewData);
        }
    });
    
    // 初始加载数据
    loadOverviewData();
}

/**
 * 加载总览数据
 */
function loadOverviewData() {
    // 获取筛选条件
    const startDate = document.getElementById('filter-start-date')?.value || '';
    const endDate = document.getElementById('filter-end-date')?.value || '';
    const channel = document.getElementById('filter-channel')?.value || '';
    const company = document.getElementById('filter-company')?.value || '';
    
    // 构建查询参数
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (channel && channel !== 'all') params.append('channel', channel);
    if (company && company !== 'all') params.append('company', company);
    
    // 显示加载状态
    document.getElementById('overview-container').innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">加载数据中...</p></div>';
    
    console.log('正在加载推广效果总览数据...');
    
    // 发送API请求
    fetch(`/api/feishu/promotion-overview?${params.toString()}`)
        .then(response => response.json())
        .then(result => {
            console.log('获取到总览数据:', result);
            if (result.success) {
                renderOverviewCards(result.data);
            } else {
                showError('加载总览数据失败: ' + (result.error || '未知错误'));
            }
        })
        .catch(error => {
            console.error('请求总览数据时出错:', error);
            showError('请求总览数据时出错: ' + error.message);
        });
}

/**
 * 渲染总览卡片
 * @param {Object} data - 总览数据
 */
function renderOverviewCards(data) {
    const container = document.getElementById('overview-container');
    
    // 清空容器
    container.innerHTML = '';
    
    // 创建卡片行
    const row = document.createElement('div');
    row.className = 'row g-3 mb-4';
    
    // 添加总体指标卡片
    row.innerHTML = `
        <!-- 推广活动数 -->
        <div class="col-md-3">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">推广活动总数</h6>
                    <div class="d-flex align-items-center">
                        <div class="display-5 fw-semibold me-2">${data.total_promotions}</div>
                        <div class="text-muted">活动</div>
                    </div>
                    <div class="text-muted small mt-2">覆盖 ${data.total_etfs} 只ETF产品</div>
                </div>
            </div>
        </div>

        <!-- 平均自选增长 -->
        <div class="col-md-3">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">平均自选人数增长</h6>
                    <div class="d-flex align-items-center">
                        <div class="display-5 fw-semibold me-2 ${data.avg_attention_change > 0 ? 'text-success' : data.avg_attention_change < 0 ? 'text-danger' : ''}">${data.avg_attention_change > 0 ? '+' : ''}${data.avg_attention_change.toLocaleString()}</div>
                        <div class="text-muted">人</div>
                    </div>
                    <div class="text-muted small mt-2">每次推广平均效果</div>
                </div>
            </div>
        </div>

        <!-- 平均持有人增长 -->
        <div class="col-md-3">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">平均持有人数增长</h6>
                    <div class="d-flex align-items-center">
                        <div class="display-5 fw-semibold me-2 ${data.avg_holders_change > 0 ? 'text-success' : data.avg_holders_change < 0 ? 'text-danger' : ''}">${data.avg_holders_change > 0 ? '+' : ''}${data.avg_holders_change.toLocaleString()}</div>
                        <div class="text-muted">人</div>
                    </div>
                    <div class="text-muted small mt-2">每次推广平均效果</div>
                </div>
            </div>
        </div>

        <!-- 平均持仓价值增长 -->
        <div class="col-md-3">
            <div class="card h-100 border-0 shadow-sm">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">平均持仓价值增长</h6>
                    <div class="d-flex align-items-center">
                        <div class="display-5 fw-semibold me-2 ${data.avg_value_change > 0 ? 'text-success' : data.avg_value_change < 0 ? 'text-danger' : ''}">${data.avg_value_change > 0 ? '+' : ''}${formatLargeNumber(data.avg_value_change)}</div>
                        <div class="text-muted">元</div>
                    </div>
                    <div class="text-muted small mt-2">每次推广平均效果</div>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(row);
    
    // 添加分布分析
    const distributionRow = document.createElement('div');
    distributionRow.className = 'row g-3';
    
    // 渠道分布卡片
    const channelCard = document.createElement('div');
    channelCard.className = 'col-md-6';
    channelCard.innerHTML = `
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <h6 class="card-title fw-semibold">推广渠道分布</h6>
                <div class="mt-3" id="channel-distribution-chart" style="height: 200px;"></div>
            </div>
        </div>
    `;
    distributionRow.appendChild(channelCard);
    
    // 基金公司分布卡片
    const companyCard = document.createElement('div');
    companyCard.className = 'col-md-6';
    companyCard.innerHTML = `
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
                <h6 class="card-title fw-semibold">基金公司分布</h6>
                <div class="mt-3" id="company-distribution-chart" style="height: 200px;"></div>
            </div>
        </div>
    `;
    distributionRow.appendChild(companyCard);
    
    container.appendChild(distributionRow);
    
    // 渲染图表
    renderChannelChart(data.channels);
    renderCompanyChart(data.company_stats);
}

/**
 * 渲染渠道分布图表
 */
function renderChannelChart(channels) {
    console.log('渲染渠道图表，数据:', channels);
    
    if (!channels || channels.length === 0) {
        console.warn('没有渠道数据可供渲染');
        document.getElementById('channel-distribution-chart').innerHTML = '<div class="text-center text-muted py-5">暂无渠道数据</div>';
        return;
    }
    
    // 调试容器
    const debugInfo = document.createElement('div');
    debugInfo.className = 'mt-2 small text-muted';
    debugInfo.textContent = `数据项: ${channels.length}`;
    
    // 准备数据
    const labels = channels.map(item => formatChannelName(item.name));
    const values = channels.map(item => item.count);
    
    console.log('处理后的渠道数据 - 标签:', labels, '值:', values);
    
    // 渲染图表
    const container = document.getElementById('channel-distribution-chart');
    
    // 确保容器存在且已经在DOM中
    if (!container) {
        console.error('找不到渠道图表容器元素');
        return;
    }

    // 显示开始渲染
    container.innerHTML = '<div class="text-center">正在渲染图表...</div>';
    
    // 创建canvas元素
    setTimeout(() => {
        try {
            container.innerHTML = '';
            const canvas = document.createElement('canvas');
            canvas.id = 'channel-chart-canvas';
            container.appendChild(canvas);
            container.appendChild(debugInfo);
            
            console.log('已创建渠道图表Canvas元素');
            
            // 如果已经存在图表，先销毁
            if (window.channelChart) {
                window.channelChart.destroy();
                console.log('已销毁旧的渠道图表');
            }
            
            console.log('开始绘制新的渠道图表...');
            window.channelChart = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '推广活动数',
                        data: values,
                        backgroundColor: [
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(153, 102, 255, 0.7)'
                        ],
                        borderColor: [
                            'rgba(54, 162, 235, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(255, 99, 132, 1)',
                            'rgba(153, 102, 255, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.parsed.x} 次推广`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    },
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            console.log('渠道图表渲染完成');
        } catch (error) {
            console.error('渲染渠道图表时出错:', error);
            container.innerHTML = `<div class="alert alert-danger">渲染图表时出错: ${error.message}</div>`;
        }
    }, 300);
}

/**
 * 渲染基金公司分布图表
 */
function renderCompanyChart(companies) {
    console.log('渲染公司图表，数据:', companies);
    
    if (!companies || companies.length === 0) {
        console.warn('没有公司数据可供渲染');
        document.getElementById('company-distribution-chart').innerHTML = '<div class="text-center text-muted py-5">暂无公司数据</div>';
        return;
    }
    
    // 调试容器
    const debugInfo = document.createElement('div');
    debugInfo.className = 'mt-2 small text-muted';
    debugInfo.textContent = `数据项: ${companies.length}`;
    
    // 准备数据
    const labels = companies.map(item => item.name);
    const values = companies.map(item => item.count);
    
    console.log('处理后的公司数据 - 标签:', labels, '值:', values);
    
    // 渲染图表
    const container = document.getElementById('company-distribution-chart');
    
    // 确保容器存在且已经在DOM中
    if (!container) {
        console.error('找不到公司图表容器元素');
        return;
    }
    
    // 显示开始渲染
    container.innerHTML = '<div class="text-center">正在渲染图表...</div>';

    // 创建canvas元素
    setTimeout(() => {
        try {
            container.innerHTML = '';
            const canvas = document.createElement('canvas');
            canvas.id = 'company-chart-canvas';
            container.appendChild(canvas);
            container.appendChild(debugInfo);
            
            console.log('已创建公司图表Canvas元素');
            
            // 如果已经存在图表，先销毁
            if (window.companyChart) {
                window.companyChart.destroy();
                console.log('已销毁旧的公司图表');
            }
            
            console.log('开始绘制新的公司图表...');
            window.companyChart = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '推广活动数',
                        data: values,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(153, 102, 255, 0.7)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.parsed.x} 次推广`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    },
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            console.log('公司图表渲染完成');
        } catch (error) {
            console.error('渲染公司图表时出错:', error);
            container.innerHTML = `<div class="alert alert-danger">渲染图表时出错: ${error.message}</div>`;
        }
    }, 600);
}

/**
 * 格式化渠道名称
 * @param {string} channel - 渠道名称
 * @returns {string} - 格式化后的渠道名称
 */
function formatChannelName(channel) {
    if (!channel) return '未知';
    
    // 简化渠道名称映射
    const simplifiedNames = {
        'APP首页': '首页',
        'APP 首页': '首页',
        'APP理财界面': '理财页',
        'APP 理财界面': '理财页',
    };
    
    // 处理多渠道组合的情况
    if (channel.includes(',')) {
        // 分割并修剪空格
        let channels = channel.split(',').map(ch => ch.trim());
        
        // 将每个渠道名称转换为简化形式
        channels = channels.map(ch => simplifiedNames[ch] || ch);
        
        // 排序以确保"首页+理财页"和"理财页+首页"统一表示
        channels.sort();
        
        // 去重
        channels = [...new Set(channels)];
        
        return channels.join('+');
    }
    
    // 单一渠道
    return simplifiedNames[channel] || channel;
}

/**
 * 格式化大数字（如 1000000 -> 1.0M）
 * @param {number} num - 要格式化的数字
 * @returns {string} - 格式化后的字符串
 */
function formatLargeNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '0';
    
    const absNum = Math.abs(num);
    if (absNum >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (absNum >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    } else {
        return num.toString();
    }
}

/**
 * 显示错误信息
 * @param {string} message - 错误信息
 */
function showError(message) {
    const container = document.getElementById('overview-container');
    container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle-fill me-2"></i> ${message}
        </div>
    `;
} 