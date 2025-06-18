/**
 * 推广效果分析 - 排行榜组件
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化排行榜
    initPromotionRankings();
});

/**
 * 初始化推广效果排行榜
 */
function initPromotionRankings() {
    // 获取筛选条件和排序控件
    const sortBySelect = document.getElementById('ranking-sort-by');
    const sortOrderSelect = document.getElementById('ranking-sort-order');
    const limitSelect = document.getElementById('ranking-limit');
    const startDateInput = document.getElementById('filter-start-date');
    const endDateInput = document.getElementById('filter-end-date');
    const channelSelect = document.getElementById('filter-channel');
    const companySelect = document.getElementById('filter-company');
    
    // 监听排序和筛选条件变化
    [sortBySelect, sortOrderSelect, limitSelect].forEach(element => {
        if (element) {
            element.addEventListener('change', loadRankingsData);
        }
    });
    
    // 监听筛选按钮点击
    const applyFilterButton = document.getElementById('apply-filter');
    if (applyFilterButton) {
        applyFilterButton.addEventListener('click', loadRankingsData);
    }
    
    // 加载筛选选项数据
    loadFilterOptions();
    
    // 初始加载数据
    loadRankingsData();
}

/**
 * 加载筛选选项数据（渠道和基金公司）
 */
function loadFilterOptions() {
    fetch('/api/feishu/filter-options')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                populateChannelOptions(result.data.channels);
                populateCompanyOptions(result.data.companies);
            } else {
                console.error('加载筛选选项失败:', result.error);
            }
        })
        .catch(error => {
            console.error('请求筛选选项时出错:', error);
        });
}

/**
 * 填充渠道选项
 * @param {Array} channels - 渠道列表
 */
function populateChannelOptions(channels) {
    const channelSelect = document.getElementById('filter-channel');
    if (!channelSelect) return;
    
    // 清空除了第一个"全部渠道"选项外的所有选项
    while (channelSelect.options.length > 1) {
        channelSelect.remove(1);
    }
    
    // 添加新选项
    channels.forEach(channel => {
        const option = document.createElement('option');
        option.value = channel;
        option.textContent = channel;
        channelSelect.appendChild(option);
    });
}

/**
 * 填充基金公司选项
 * @param {Array} companies - 基金公司列表
 */
function populateCompanyOptions(companies) {
    const companySelect = document.getElementById('filter-company');
    if (!companySelect) return;
    
    // 清空除了第一个"全部公司"选项外的所有选项
    while (companySelect.options.length > 1) {
        companySelect.remove(1);
    }
    
    // 添加新选项
    companies.forEach(company => {
        const option = document.createElement('option');
        option.value = company;
        option.textContent = company;
        companySelect.appendChild(option);
    });
}

/**
 * 加载排行榜数据
 */
function loadRankingsData() {
    // 获取排序参数
    const sortBy = document.getElementById('ranking-sort-by')?.value || 'attention_pct';
    const sortOrder = document.getElementById('ranking-sort-order')?.value || 'desc';
    const limit = document.getElementById('ranking-limit')?.value || 10;
    
    // 获取筛选条件
    const startDate = document.getElementById('filter-start-date')?.value || '';
    const endDate = document.getElementById('filter-end-date')?.value || '';
    const channel = document.getElementById('filter-channel')?.value || '';
    const company = document.getElementById('filter-company')?.value || '';
    
    // 构建查询参数
    const params = new URLSearchParams();
    params.append('sort_by', sortBy);
    params.append('sort_order', sortOrder);
    params.append('limit', limit);
    
    // 转换日期格式（从yyyy-MM-dd到yyyy/MM/dd）
    if (startDate) {
        const formattedDate = formatDateForAPI(startDate);
        params.append('start_date', formattedDate);
    }
    
    if (endDate) {
        const formattedDate = formatDateForAPI(endDate);
        params.append('end_date', formattedDate);
    }
    
    if (channel && channel !== 'all') params.append('channel', channel);
    if (company && company !== 'all') params.append('company', company);
    
    // 显示加载状态
    document.getElementById('rankings-container').innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">加载排行榜数据中...</p></div>';
    
    // 发送API请求
    fetch(`/api/feishu/promotion-rankings?${params.toString()}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                renderRankingsData(result.data, sortBy);
            } else {
                showError('加载排行榜数据失败: ' + (result.error || '未知错误'));
            }
        })
        .catch(error => {
            showError('请求排行榜数据时出错: ' + error.message);
        });
}

/**
 * 渲染排行榜数据
 * @param {Array} data - 排行榜数据
 * @param {string} sortBy - 排序字段
 */
function renderRankingsData(data, sortBy) {
    const container = document.getElementById('rankings-container');
    if (!container) return;
    
    // 如果没有数据
    if (!data || data.length === 0) {
        container.innerHTML = '<div class="alert alert-info">没有符合条件的数据</div>';
        return;
    }
    
    // 确定要展示的指标
    let metric = '自选人数';
    let metricPrefix = 'attention';
    
    if (sortBy.startsWith('holders')) {
        metric = '持有人数';
        metricPrefix = 'holders';
    } else if (sortBy.startsWith('value')) {
        metric = '持仓价值';
        metricPrefix = 'value';
    }
    
    // 是百分比还是绝对值
    const isPercentage = sortBy.endsWith('pct');
    
    // 创建排行榜容器
    container.innerHTML = '';
    
    // 创建图表区域
    const chartRow = document.createElement('div');
    chartRow.className = 'row mb-4';
    
    // 排行榜图表
    const chartCol = document.createElement('div');
    chartCol.className = 'col-12';
    chartCol.innerHTML = `
        <div class="card shadow-sm border-0">
            <div class="card-body">
                <h5 class="card-title">${metric}${isPercentage ? '增长率' : '增长值'}排行榜</h5>
                <div class="chart-container" style="position: relative; height: 400px;">
                    <canvas id="rankings-chart"></canvas>
                </div>
            </div>
        </div>
    `;
    chartRow.appendChild(chartCol);
    container.appendChild(chartRow);
    
    // 创建统计概览卡片
    const statsRow = document.createElement('div');
    statsRow.className = 'row mb-4';
    
    // 计算统计数据
    const validData = data.filter(item => item[`${metricPrefix}_change`] !== null);
    const totalCount = validData.length;
    let positiveCount = 0;
    let negativeCount = 0;
    let totalChange = 0;
    
    validData.forEach(item => {
        const change = item[`${metricPrefix}_change`] || 0;
        if (change > 0) positiveCount++;
        else if (change < 0) negativeCount++;
        totalChange += change;
    });
    
    const avgChange = totalCount > 0 ? totalChange / totalCount : 0;
    
    // 格式化平均变化值
    let formattedAvgChange = avgChange;
    if (metricPrefix === 'value') {
        formattedAvgChange = formatCurrency(avgChange);
    }
    
    // 添加统计卡片
    statsRow.innerHTML = `
        <div class="col-md-3">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-body text-center">
                    <h6 class="card-subtitle mb-2 text-muted">符合条件的推广活动</h6>
                    <h3 class="card-title">${totalCount}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-body text-center">
                    <h6 class="card-subtitle mb-2 text-muted">平均${metric}增长</h6>
                    <h3 class="card-title ${avgChange > 0 ? 'text-success' : (avgChange < 0 ? 'text-danger' : '')}">${avgChange > 0 ? '+' : ''}${formattedAvgChange}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-body text-center">
                    <h6 class="card-subtitle mb-2 text-muted">正向增长活动</h6>
                    <h3 class="card-title text-success">${positiveCount} <small class="text-muted">(${totalCount > 0 ? Math.round(positiveCount / totalCount * 100) : 0}%)</small></h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-body text-center">
                    <h6 class="card-subtitle mb-2 text-muted">负向增长活动</h6>
                    <h3 class="card-title text-danger">${negativeCount} <small class="text-muted">(${totalCount > 0 ? Math.round(negativeCount / totalCount * 100) : 0}%)</small></h3>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(statsRow);
    
    // 创建详细数据表格
    const tableRow = document.createElement('div');
    tableRow.className = 'row';
    
    const tableCol = document.createElement('div');
    tableCol.className = 'col-12';
    tableCol.innerHTML = `
        <div class="card shadow-sm border-0">
            <div class="card-body">
                <h5 class="card-title">详细数据</h5>
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th scope="col" style="width: 40px;">#</th>
                                <th scope="col" style="width: 80px;">产品代码</th>
                                <th scope="col">产品名称</th>
                                <th scope="col">基金公司</th>
                                <th scope="col">推广渠道</th>
                                <th scope="col">推广时间</th>
                                <th scope="col">下线时间</th>
                                <th scope="col" style="width: 80px;">推广天数</th>
                                <th scope="col">推广前${metric}</th>
                                <th scope="col">推广后${metric}</th>
                                <th scope="col">${metric}增长</th>
                                <th scope="col">${metric}增长率</th>
                            </tr>
                        </thead>
                        <tbody id="rankings-table-body">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    tableRow.appendChild(tableCol);
    container.appendChild(tableRow);
    
    // 填充表格数据
    const tableBody = document.getElementById('rankings-table-body');
    
    data.forEach((item, index) => {
        const row = document.createElement('tr');
        
        // 计算推广天数（如果promo_days为空）
        let promoDays = item.promo_days;
        if (promoDays === null) {
            if (item.publish_date && item.offline_date) {
                // 尝试计算推广天数
                const publishDate = parseDate(item.publish_date);
                const offlineDate = parseDate(item.offline_date);
                if (publishDate && offlineDate) {
                    const diffTime = Math.abs(offlineDate - publishDate);
                    promoDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // 加1是因为包含首尾日期
                }
            }
        }
        
        // 确定增长值和增长率（处理null值）
        const changeValue = item[`${metricPrefix}_change`] || 0;
        const changePct = item[`${metricPrefix}_pct_change`] || 0;
        
        // 增长值和增长率的CSS类
        const changeClass = changeValue > 0 ? 'text-success' : (changeValue < 0 ? 'text-danger' : '');
        const changePctClass = changePct > 0 ? 'text-success' : (changePct < 0 ? 'text-danger' : '');
        
        // 格式化增长值（对持仓价值进行特殊处理）
        let formattedChange = changeValue;
        if (metricPrefix === 'value') {
            formattedChange = formatCurrency(changeValue);
        }
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${item.code || '-'}</td>
            <td title="${item.name || ''}">${truncateText(item.name || '-', 10)}</td>
            <td>${item.company_name || '-'}</td>
            <td title="${item.publish_channel || ''}">${truncateText(formatChannelName(item.publish_channel || '-'), 10)}</td>
            <td>${formatDisplayDate(item.publish_date)}</td>
            <td>${formatDisplayDate(item.offline_date)}</td>
            <td class="text-center">${promoDays !== null ? promoDays : '-'}</td>
            <td>${item[`pub_${metricPrefix}`] !== null ? (metricPrefix === 'value' ? formatCurrency(item[`pub_${metricPrefix}`]) : item[`pub_${metricPrefix}`]) : '-'}</td>
            <td>${item[`off_${metricPrefix}`] !== null ? (metricPrefix === 'value' ? formatCurrency(item[`off_${metricPrefix}`]) : item[`off_${metricPrefix}`]) : '-'}</td>
            <td class="${changeClass} fw-bold">${changeValue > 0 ? '+' : ''}${formattedChange}</td>
            <td class="${changePctClass} fw-bold">${changePct > 0 ? '+' : ''}${changePct}%</td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // 渲染图表
    renderRankingsChart(data, metric, metricPrefix, isPercentage);
}

/**
 * 渲染排行榜图表
 * @param {Array} data - 排行榜数据
 * @param {string} metric - 指标名称
 * @param {string} metricPrefix - 指标前缀
 * @param {boolean} isPercentage - 是否为百分比
 */
function renderRankingsChart(data, metric, metricPrefix, isPercentage) {
    const ctx = document.getElementById('rankings-chart');
    if (!ctx) return;
    
    // 只使用有完整数据的项目
    const filteredData = data.filter(item => 
        item[`${metricPrefix}_change`] !== null && 
        item[`${metricPrefix}_pct_change`] !== null
    );
    
    if (filteredData.length === 0) {
        ctx.parentNode.innerHTML = '<div class="alert alert-info mt-3">没有足够的数据来生成图表</div>';
        return;
    }
    
    // 准备数据
    const labels = filteredData.map(item => `${item.code} ${truncateText(item.name || '', 6)}`);
    let values = [];
    
    if (isPercentage) {
        values = filteredData.map(item => item[`${metricPrefix}_pct_change`] || 0);
    } else {
        values = filteredData.map(item => item[`${metricPrefix}_change`] || 0);
    }
    
    // 如果是持仓价值，则进行数值缩放
    if (metricPrefix === 'value' && !isPercentage) {
        values = values.map(value => value / 10000); // 转换为万元
    }
    
    // 颜色数组
    const backgroundColors = filteredData.map(item => {
        const value = isPercentage ? (item[`${metricPrefix}_pct_change`] || 0) : (item[`${metricPrefix}_change`] || 0);
        return value >= 0 ? 'rgba(40, 167, 69, 0.7)' : 'rgba(220, 53, 69, 0.7)';
    });
    
    const borderColors = filteredData.map(item => {
        const value = isPercentage ? (item[`${metricPrefix}_pct_change`] || 0) : (item[`${metricPrefix}_change`] || 0);
        return value >= 0 ? 'rgba(40, 167, 69, 1)' : 'rgba(220, 53, 69, 1)';
    });
    
    // 销毁旧图表
    if (window.rankingsChart) {
        window.rankingsChart.destroy();
    }
    
    // 创建新图表
    window.rankingsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `${metric}${isPercentage ? '增长率' : '增长值'}`,
                data: values,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.x;
                            if (isPercentage) {
                                return `${value > 0 ? '+' : ''}${value}%`;
                            } else if (metricPrefix === 'value') {
                                return `${value > 0 ? '+' : ''}${value} 万元`;
                            } else {
                                return `${value > 0 ? '+' : ''}${value} 人`;
                            }
                        },
                        title: function(context) {
                            const index = context[0].dataIndex;
                            const item = filteredData[index];
                            return `${item.code} ${item.name} (${item.company_name || '未知公司'})`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: `ETF产品推广${metric}${isPercentage ? '增长率' : '增长值'}排行榜`,
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: isPercentage ? '增长率(%)' : (metricPrefix === 'value' ? '增长值(万元)' : '增长值(人)')
                    },
                    ticks: {
                        callback: function(value) {
                            if (isPercentage) {
                                return value + '%';
                            } else if (metricPrefix === 'value') {
                                return value;
                            } else {
                                return value;
                            }
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'ETF产品'
                    }
                }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

/**
 * 格式化日期用于API请求
 * @param {string} dateStr - 日期字符串，格式为 yyyy-MM-dd
 * @returns {string} - 格式化后的日期，格式为 yyyy/MM/dd
 */
function formatDateForAPI(dateStr) {
    if (!dateStr) return '';
    return dateStr.replace(/-/g, '/');
}

/**
 * 格式化日期显示
 * @param {string} dateStr - 日期字符串
 * @returns {string} - 格式化后的日期
 */
function formatDisplayDate(dateStr) {
    if (!dateStr) return '-';
    
    // 尝试解析日期
    const date = parseDate(dateStr);
    if (!date) return dateStr; // 如果解析失败，返回原始字符串
    
    // 格式化为 yyyy-MM-dd
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

/**
 * 解析日期字符串为Date对象
 * @param {string} dateStr - 日期字符串 (例如 "2025/06/13")
 * @returns {Date|null} - Date对象或null
 */
function parseDate(dateStr) {
    if (!dateStr) return null;
    
    // 尝试多种格式解析
    const formats = [
        // yyyy/MM/dd
        {
            regex: /^(\d{4})\/(\d{1,2})\/(\d{1,2})$/,
            parse: function(match) {
                return new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]));
            }
        },
        // yyyy-MM-dd
        {
            regex: /^(\d{4})-(\d{1,2})-(\d{1,2})$/,
            parse: function(match) {
                return new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]));
            }
        }
    ];
    
    for (const format of formats) {
        const match = dateStr.match(format.regex);
        if (match) {
            return format.parse(match);
        }
    }
    
    return null;
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
 * 截断文本
 * @param {string} text - 要截断的文本
 * @param {number} maxLength - 最大长度
 * @returns {string} - 截断后的文本
 */
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * 格式化货币
 * @param {number} value - 金额值
 * @returns {string} - 格式化后的金额
 */
function formatCurrency(value) {
    if (value === null || value === undefined) return '-';
    
    const absValue = Math.abs(value);
    if (absValue >= 100000000) {
        return (value / 100000000).toFixed(2) + '亿';
    } else if (absValue >= 10000) {
        return (value / 10000).toFixed(2) + '万';
    } else {
        return value.toLocaleString();
    }
}

/**
 * 显示错误信息
 * @param {string} message - 错误信息
 */
function showError(message) {
    const container = document.getElementById('rankings-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle-fill me-2"></i> ${message}
        </div>
    `;
} 