/**
 * ETF图表模块
 * 用于展示ETF自选人数、持仓人数和持仓价值的时序图
 * 使用Chart.js实现苹果风格的交互式图表
 * 版本: 1.0.0 (2025-04-04)
 */

// 初始化模块
console.log("ETF图表模块已加载 v1.0.0 (2025-04-04)");

// 定义图表颜色
const CHART_COLORS = {
    attention: {
        fill: 'rgba(75, 192, 192, 0.2)',
        stroke: 'rgba(75, 192, 192, 1)'
    },
    holder: {
        fill: 'rgba(54, 162, 235, 0.2)',
        stroke: 'rgba(54, 162, 235, 1)'
    },
    amount: {
        fill: 'rgba(255, 159, 64, 0.5)',
        stroke: 'rgba(255, 159, 64, 1)'
    }
};

// 格式化数字
function formatNumber(num, decimals = 0) {
    if (num === null || isNaN(num)) {
        return '-';
    }
    
    // 持仓价值单位自动转换
    if (arguments.length > 2 && arguments[2] === 'amount') {
        if (Math.abs(num) >= 100000000) { // 1亿及以上
            return (num / 100000000).toFixed(2) + '亿';
        } else if (Math.abs(num) >= 10000) { // 1万及以上
            return (num / 10000).toFixed(2) + '万';
        } else {
            return num.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            });
        }
    }
    
    // 如果是整数且不需要小数位
    if (Number.isInteger(num) && decimals === 0) {
        // 大于100万显示为"xx.x万"
        if (num >= 1000000) {
            return (num / 10000).toFixed(1) + '万';
        }
        // 大于1万显示为"x.xx万"
        else if (num >= 10000) {
            return (num / 10000).toFixed(2) + '万';
        }
        // 否则显示原值
        return num.toLocaleString();
    }
    
    // 有小数的情况
    return num.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// 静态变量，跟踪Chart.js是否已加载
let chartJSPromise = null;

// 动态加载Chart.js库
async function loadChartJSLibrary() {
    // 如果已经有加载中的Promise，直接返回
    if (chartJSPromise) {
        return chartJSPromise;
    }
    
    // 检查是否已加载
    if (window.Chart) {
        console.log('Chart.js已经加载');
        return Promise.resolve(window.Chart);
    }
    
    console.log('开始加载Chart.js...');
    
    // 尝试多个CDN源
    const cdnUrls = [
        'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js',
        'https://unpkg.com/chart.js@3.9.1/dist/chart.min.js'
    ];
    
    // 创建新的Promise
    chartJSPromise = new Promise((resolve, reject) => {
        // 尝试加载函数
        function tryLoadScript(urlIndex) {
            if (urlIndex >= cdnUrls.length) {
                reject(new Error('所有Chart.js CDN源加载失败'));
                return;
            }
            
            const script = document.createElement('script');
            script.src = cdnUrls[urlIndex];
            script.async = true;
            
            script.onload = function() {
                console.log(`成功从 ${cdnUrls[urlIndex]} 加载Chart.js`);
                if (window.Chart) {
                    resolve(window.Chart);
                } else {
                    console.warn('Chart.js已加载但window.Chart不存在，尝试下一个源');
                    tryLoadScript(urlIndex + 1);
                }
            };
            
            script.onerror = function() {
                console.warn(`从 ${cdnUrls[urlIndex]} 加载Chart.js失败，尝试下一个源`);
                tryLoadScript(urlIndex + 1);
            };
            
            document.head.appendChild(script);
        }
        
        // 开始尝试加载
        tryLoadScript(0);
    });
    
    return chartJSPromise;
}

// 创建ETF时序图容器
export function createETFChartContainer(etfCode, etfName, manager = '') {
    const chartContainerId = `chart-container-${etfCode.replace('.', '-')}`;
    
    // 创建图表容器HTML
    const containerHTML = `
    <div class="etf-chart-section mt-4">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5><i class="bi bi-graph-up"></i> ${etfCode}｜${etfName}｜${manager}｜客户数据趋势</h5>
                <div class="btn-group btn-group-sm" role="group">
                    <button type="button" class="btn btn-outline-secondary active" data-period="all">全部</button>
                    <button type="button" class="btn btn-outline-secondary" data-period="month">一个月</button>
                    <button type="button" class="btn btn-outline-secondary" data-period="week">一周</button>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-8">
                        <div id="${chartContainerId}" class="chart-container" style="height: 300px;">
                            <div class="text-center py-5">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">正在加载...</span>
                                </div>
                                <p class="mt-2">正在加载图表数据...</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card stats-card" id="${chartContainerId}-stats">
                            <div class="card-header d-flex align-items-center">
                                <h6 class="mb-0">数据变化统计</h6>
                            </div>
                            <div class="card-body p-0">
                                <div class="text-center py-3">
                                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                                        <span class="visually-hidden">计算中...</span>
                                    </div>
                                    <p class="mt-2 small">计算历史数据变化...</p>
                                </div>
                            </div>
                        </div>
                        <div class="card stats-card mt-3">
                            <div class="card-header d-flex align-items-center">
                                <h6 class="mb-0">时间范围选择</h6>
                            </div>
                            <div class="card-body">
                                <div class="row g-2">
                                    <div class="col-6">
                                        <label for="${chartContainerId}-start-date" class="form-label small">开始日期</label>
                                        <input type="date" class="form-control form-control-sm" id="${chartContainerId}-start-date">
                                    </div>
                                    <div class="col-6">
                                        <label for="${chartContainerId}-end-date" class="form-label small">结束日期</label>
                                        <input type="date" class="form-control form-control-sm" id="${chartContainerId}-end-date">
                                    </div>
                                    <div class="col-12 mt-2">
                                        <button class="btn btn-sm btn-primary w-100" id="${chartContainerId}-apply-date">应用日期范围</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
    
    return {
        containerId: chartContainerId,
        html: containerHTML
    };
}

// 获取ETF历史数据
export async function fetchETFHistoryData(etfCode) {
    try {
        console.log(`获取ETF历史数据: ${etfCode}`);
        
        // 获取自选人数历史数据
        const attentionResponse = await fetch(`/etf_attention_history?code=${encodeURIComponent(etfCode)}`);
        const attentionData = await attentionResponse.json();
        
        // 获取持有人数和持仓价值历史数据
        const holdersResponse = await fetch(`/etf_holders_history?code=${encodeURIComponent(etfCode)}`);
        const holdersData = await holdersResponse.json();
        
        return {
            attention: attentionData,
            holders: holdersData
        };
    } catch (error) {
        console.error('获取ETF历史数据出错:', error);
        throw error;
    }
}

// 准备图表数据
function prepareChartData(historyData, options = {}) {
    const { period = 'all', startDate = null, endDate = null } = options;
    
    if (!historyData) {
        console.error('历史数据为空');
        return null;
    }
    
    // 初始化数据容器
    const attention = historyData.attention || [];
    const holders = historyData.holders || [];
    
    // 如果两者都为空数组，返回null
    if (attention.length === 0 && holders.length === 0) {
        console.warn('自选人数和持有人数据都为空');
        return null;
    }
    
    // 获取日期集合
    const dateSet = new Set();
    
    attention.forEach(item => {
        if (item && item.date) {
            dateSet.add(item.date);
        }
    });
    
    holders.forEach(item => {
        if (item && item.date) {
            dateSet.add(item.date);
        }
    });
    
    // 如果没有日期数据，返回null
    if (dateSet.size === 0) {
        console.warn('未找到有效的日期数据');
        return null;
    }
    
    // 将日期按升序排序
    const sortedDates = Array.from(dateSet).sort();
    
    // 根据所选时间范围过滤数据
    let filteredDates = sortedDates;
    
    if (period === 'custom' && startDate && endDate) {
        // 使用自定义日期范围
        filteredDates = sortedDates.filter(date => date >= startDate && date <= endDate);
        console.log(`应用自定义日期范围: ${startDate} 到 ${endDate}, 筛选到 ${filteredDates.length} 个日期`);
    } else if (period === 'month') {
        // 过滤最近30天数据
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - 30);
        const cutoffStr = cutoffDate.toISOString().split('T')[0];
        filteredDates = sortedDates.filter(date => date >= cutoffStr);
    } else if (period === 'week') {
        // 过滤最近7天数据
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - 7);
        const cutoffStr = cutoffDate.toISOString().split('T')[0];
        filteredDates = sortedDates.filter(date => date >= cutoffStr);
    }
    
    // 如果筛选后的日期为空，使用全部日期
    if (filteredDates.length === 0) {
        console.warn(`使用所选时间范围 '${period}' 后，没有符合条件的数据。使用全部数据。`);
        filteredDates = sortedDates;
    }
    
    // 准备数据点
    const labels = [];
    const attentionData = [];
    const holderData = [];
    const amountData = [];
    
    filteredDates.forEach(date => {
        // 只显示月-日，格式为"MM-DD"
        labels.push(date.replace(/^\d{4}-/, ''));
        
        // 查找该日期的自选人数
        const attentionItem = attention.find(item => item && item.date === date);
        attentionData.push(attentionItem ? attentionItem.attention_count : null);
        
        // 查找该日期的持有人数和持仓价值
        const holdersItem = holders.find(item => item && item.date === date);
        holderData.push(holdersItem ? holdersItem.holder_count : null);
        amountData.push(holdersItem ? holdersItem.holding_value : null);
    });
    
    console.log('准备图表数据结果：', {
        dateCount: filteredDates.length,
        hasAttention: attentionData.some(v => v !== null),
        hasHolders: holderData.some(v => v !== null),
        hasAmount: amountData.some(v => v !== null)
    });
    
    return {
        labels,
        attention: attentionData,
        holders: holderData,
        amounts: amountData
    };
}

// 计算历史数据的变化值
function calculateHistoricalChanges(historyData) {
    if (!historyData || (!historyData.attention || !historyData.holders)) {
        return { error: "无足够历史数据计算变化值" };
    }
    
    // 按日期降序排序
    const sortAttention = [...historyData.attention].sort((a, b) => 
        new Date(b.date) - new Date(a.date));
    const sortHolders = [...historyData.holders].sort((a, b) => 
        new Date(b.date) - new Date(a.date));
    
    // 获取最新日期
    const latestAttentionDate = sortAttention.length > 0 ? sortAttention[0].date : null;
    const latestHoldersDate = sortHolders.length > 0 ? sortHolders[0].date : null;
    
    // 初始化结果对象
    const result = {
        latestAttentionDate: latestAttentionDate, 
        latestHoldersDate: latestHoldersDate,
        attention: {
            total: sortAttention.length > 0 ? sortAttention[0].attention_count : null,
            latest: null,
            day5: null,
            day10: null,
            month1: null,
            month2: null,
            month3: null,
        },
        holders: {
            total: sortHolders.length > 0 ? sortHolders[0].holder_count : null,
            latest: null,
            day5: null,
            day10: null,
            month1: null,
            month2: null,
            month3: null,
        },
        amount: {
            total: sortHolders.length > 0 ? sortHolders[0].holding_value : null,
            latest: null,
            day5: null,
            day10: null,
            month1: null,
            month2: null,
            month3: null,
        }
    };
    
    // 计算自选人数变化
    if (sortAttention.length > 0) {
        const latest = sortAttention[0].attention_count;
        
        // 最新一天变化 (需要至少两天数据)
        if (sortAttention.length > 1) {
            result.attention.latest = latest - sortAttention[1].attention_count;
        }
        
        // 5日变化
        const day5Index = findDateIndex(sortAttention, 5);
        if (day5Index >= 0) {
            result.attention.day5 = latest - sortAttention[day5Index].attention_count;
        }
        
        // 10日变化
        const day10Index = findDateIndex(sortAttention, 10);
        if (day10Index >= 0) {
            result.attention.day10 = latest - sortAttention[day10Index].attention_count;
        }
        
        // 一个月变化 (30日)
        const month1Index = findDateIndex(sortAttention, 30);
        if (month1Index >= 0) {
            result.attention.month1 = latest - sortAttention[month1Index].attention_count;
        }
        
        // 两个月变化 (60日)
        const month2Index = findDateIndex(sortAttention, 60);
        if (month2Index >= 0) {
            result.attention.month2 = latest - sortAttention[month2Index].attention_count;
        }
        
        // 三个月变化 (90日)
        const month3Index = findDateIndex(sortAttention, 90);
        if (month3Index >= 0) {
            result.attention.month3 = latest - sortAttention[month3Index].attention_count;
        }
    }
    
    // 计算持有人数和持仓价值变化
    if (sortHolders.length > 0) {
        const latestHolders = sortHolders[0].holder_count;
        const latestAmount = sortHolders[0].holding_value;
        
        // 最新一天变化 (需要至少两天数据)
        if (sortHolders.length > 1) {
            result.holders.latest = latestHolders - sortHolders[1].holder_count;
            result.amount.latest = latestAmount - sortHolders[1].holding_value;
        }
        
        // 5日变化
        const day5Index = findDateIndex(sortHolders, 5);
        if (day5Index >= 0) {
            result.holders.day5 = latestHolders - sortHolders[day5Index].holder_count;
            result.amount.day5 = latestAmount - sortHolders[day5Index].holding_value;
        }
        
        // 10日变化
        const day10Index = findDateIndex(sortHolders, 10);
        if (day10Index >= 0) {
            result.holders.day10 = latestHolders - sortHolders[day10Index].holder_count;
            result.amount.day10 = latestAmount - sortHolders[day10Index].holding_value;
        }
        
        // 一个月变化 (30日)
        const month1Index = findDateIndex(sortHolders, 30);
        if (month1Index >= 0) {
            result.holders.month1 = latestHolders - sortHolders[month1Index].holder_count;
            result.amount.month1 = latestAmount - sortHolders[month1Index].holding_value;
        }
        
        // 两个月变化 (60日)
        const month2Index = findDateIndex(sortHolders, 60);
        if (month2Index >= 0) {
            result.holders.month2 = latestHolders - sortHolders[month2Index].holder_count;
            result.amount.month2 = latestAmount - sortHolders[month2Index].holding_value;
        }
        
        // 三个月变化 (90日)
        const month3Index = findDateIndex(sortHolders, 90);
        if (month3Index >= 0) {
            result.holders.month3 = latestHolders - sortHolders[month3Index].holder_count;
            result.amount.month3 = latestAmount - sortHolders[month3Index].holding_value;
        }
    }
    
    return result;
}

// 辅助函数：查找n天前的数据索引
function findDateIndex(sortedData, daysBefore) {
    if (!sortedData || sortedData.length === 0) return -1;
    
    const latestDate = new Date(sortedData[0].date);
    const targetDate = new Date(latestDate);
    targetDate.setDate(targetDate.getDate() - daysBefore);
    
    // 找到最接近的日期
    let closestIndex = -1;
    let minDiff = Number.MAX_SAFE_INTEGER;
    
    for (let i = 0; i < sortedData.length; i++) {
        const currentDate = new Date(sortedData[i].date);
        if (currentDate <= targetDate) {
            const diff = Math.abs(currentDate - targetDate);
            if (diff < minDiff) {
                minDiff = diff;
                closestIndex = i;
            }
        }
    }
    
    return closestIndex;
}

// 显示历史数据变化统计
function displayHistoricalChanges(containerId, changes) {
    const statsContainer = document.getElementById(`${containerId}-stats`);
    if (!statsContainer) return;
    
    const statsCardBody = statsContainer.querySelector('.card-body');
    if (!statsCardBody) return;
    
    // 更新数据变化统计表格
    updateDataChangeStatsTable(changes);
    
    // 格式化日期为"M月D日"
    const formatDate = (dateStr) => {
        if (!dateStr) return "无数据";
        const date = new Date(dateStr);
        return `${date.getMonth() + 1}月${date.getDate()}日`;
    };
    
    // 格式化变化值
    const formatChangeValue = (value, isAmount = false) => {
        if (value === null) return "-";
        const sign = value >= 0 ? "+" : "";
        if (isAmount) {
            return `${sign}${formatNumber(value, 0, 'amount')}`;
        }
        return `${sign}${formatNumber(value)}`;
    };
    
    // 获取格式化日期
    const attentionDate = formatDate(changes.latestAttentionDate);
    const holdersDate = formatDate(changes.latestHoldersDate);
    
    // 构建表格HTML - 使用苹果风格，确保统计项居中
    const tableHTML = `
    <table class="table mb-0" id="${containerId}-data-table">
        <thead class="table-light">
            <tr>
                <th scope="col" class="text-center" style="width: 22%;">统计项</th>
                <th scope="col" class="text-center" style="width: 26%;">自选人数</th>
                <th scope="col" class="text-center" style="width: 26%;">持有人数</th>
                <th scope="col" class="text-center" style="width: 26%;">持仓价值</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <th scope="row" class="text-center">${attentionDate}总数</th>
                <td class="text-center">${formatNumber(changes.attention.total)}</td>
                <td class="text-center">${formatNumber(changes.holders.total)}</td>
                <td class="text-center">${formatNumber(changes.amount.total, 0, 'amount')}</td>
            </tr>
            <tr>
                <th scope="row" class="text-center">${attentionDate}变化</th>
                <td class="text-center ${changes.attention.latest >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.attention.latest)}</td>
                <td class="text-center ${changes.holders.latest >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.holders.latest)}</td>
                <td class="text-center ${changes.amount.latest >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.amount.latest, true)}</td>
            </tr>
            <tr>
                <th scope="row" class="text-center">近5日变化</th>
                <td class="text-center ${changes.attention.day5 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.attention.day5)}</td>
                <td class="text-center ${changes.holders.day5 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.holders.day5)}</td>
                <td class="text-center ${changes.amount.day5 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.amount.day5, true)}</td>
            </tr>
            <tr>
                <th scope="row" class="text-center">近10日变化</th>
                <td class="text-center ${changes.attention.day10 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.attention.day10)}</td>
                <td class="text-center ${changes.holders.day10 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.holders.day10)}</td>
                <td class="text-center ${changes.amount.day10 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.amount.day10, true)}</td>
            </tr>
            <tr>
                <th scope="row" class="text-center">近一个月变化</th>
                <td class="text-center ${changes.attention.month1 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.attention.month1)}</td>
                <td class="text-center ${changes.holders.month1 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.holders.month1)}</td>
                <td class="text-center ${changes.amount.month1 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.amount.month1, true)}</td>
            </tr>
            <tr>
                <th scope="row" class="text-center">近两个月变化</th>
                <td class="text-center ${changes.attention.month2 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.attention.month2)}</td>
                <td class="text-center ${changes.holders.month2 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.holders.month2)}</td>
                <td class="text-center ${changes.amount.month2 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.amount.month2, true)}</td>
            </tr>
            <tr>
                <th scope="row" class="text-center">近三个月变化</th>
                <td class="text-center ${changes.attention.month3 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.attention.month3)}</td>
                <td class="text-center ${changes.holders.month3 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.holders.month3)}</td>
                <td class="text-center ${changes.amount.month3 >= 0 ? 'text-increase' : 'text-decrease'}">${formatChangeValue(changes.amount.month3, true)}</td>
            </tr>
        </tbody>
    </table>`;
    
    // 更新卡片内容 - 直接替换卡片内容，使用更精简的标题
    const cardHTML = `
    <div class="card-header d-flex align-items-center">
        <h6 class="mb-0">数据变化统计</h6>
    </div>
    ${tableHTML}`;
    
    statsContainer.innerHTML = cardHTML;
    
    // 应用苹果风格
    statsContainer.classList.add('stats-card');
}

// 更新数据变化统计表格
function updateDataChangeStatsTable(changes) {
    // 更新总数
    updateTableCell('attention-total', formatNumber(changes.attention.total));
    updateTableCell('holders-total', formatNumber(changes.holders.total));
    updateTableCell('amount-total', formatNumber(changes.amount.total, 0, 'amount'));
    
    // 更新最新变化
    updateTableCellWithChange('attention-latest', changes.attention.latest);
    updateTableCellWithChange('holders-latest', changes.holders.latest);
    updateTableCellWithChange('amount-latest', changes.amount.latest, true);
    
    // 更新5日变化
    updateTableCellWithChange('attention-day5', changes.attention.day5);
    updateTableCellWithChange('holders-day5', changes.holders.day5);
    updateTableCellWithChange('amount-day5', changes.amount.day5, true);
    
    // 更新10日变化
    updateTableCellWithChange('attention-day10', changes.attention.day10);
    updateTableCellWithChange('holders-day10', changes.holders.day10);
    updateTableCellWithChange('amount-day10', changes.amount.day10, true);
    
    // 更新一个月变化
    updateTableCellWithChange('attention-month1', changes.attention.month1);
    updateTableCellWithChange('holders-month1', changes.holders.month1);
    updateTableCellWithChange('amount-month1', changes.amount.month1, true);
    
    // 更新两个月变化
    updateTableCellWithChange('attention-month2', changes.attention.month2);
    updateTableCellWithChange('holders-month2', changes.holders.month2);
    updateTableCellWithChange('amount-month2', changes.amount.month2, true);
    
    // 更新三个月变化
    updateTableCellWithChange('attention-month3', changes.attention.month3);
    updateTableCellWithChange('holders-month3', changes.holders.month3);
    updateTableCellWithChange('amount-month3', changes.amount.month3, true);
}

// 更新表格单元格
function updateTableCell(cellId, value) {
    const cell = document.getElementById(cellId);
    if (cell) {
        cell.textContent = value || '-';
    }
}

// 更新带变化的表格单元格（增长为红色，减少为绿色）
function updateTableCellWithChange(cellId, value) {
    const cell = document.getElementById(cellId);
    if (!cell) return;
    
    if (value === null) {
        cell.textContent = '-';
        cell.className = 'text-center';
        return;
    }
    
    const isAmount = cellId.startsWith('amount-');
    const isIncrease = value >= 0;
    const className = isIncrease ? 'text-increase' : 'text-decrease';
    const sign = isIncrease ? '+' : '';
    
    if (isAmount) {
        cell.textContent = `${sign}${formatNumber(value, 0, 'amount')}`;
    } else {
        cell.textContent = `${sign}${formatNumber(value)}`;
    }
    cell.className = `text-center ${className}`;
}

// 初始化苹果风格图表
export async function initETFChart(containerId, historyData, options = {}) {
    try {
        console.log('开始初始化ETF图表，容器ID:', containerId);
        
        // 确保已加载Chart.js
        await loadChartJSLibrary();
        console.log('Chart.js加载成功');
        
        // 处理数据
        const chartData = prepareChartData(historyData, options);
        if (!chartData || !chartData.labels || chartData.labels.length === 0) {
            console.warn('没有可用的图表数据');
            document.getElementById(containerId).innerHTML = '<div class="alert alert-warning">暂无历史数据</div>';
            return null;
        }
        
        // 检查是否有实际数据
        const hasAttentionData = chartData.attention.some(v => v !== null);
        const hasHoldersData = chartData.holders.some(v => v !== null);
        const hasAmountData = chartData.amounts.some(v => v !== null);
        
        if (!hasAttentionData && !hasHoldersData && !hasAmountData) {
            console.warn('图表数据全部为空值');
            document.getElementById(containerId).innerHTML = '<div class="alert alert-warning">暂无历史数据</div>';
            return null;
        }
        
        // 清除加载提示
        document.getElementById(containerId).innerHTML = '<canvas id="' + containerId + '-canvas"></canvas>';
        
        // 创建图表
        const ctx = document.getElementById(containerId + '-canvas').getContext('2d');
        
        // 准备数据集
        const datasets = [];
        
        // 只添加有数据的系列
        if (hasAttentionData) {
            datasets.push({
                label: '自选人数',
                data: chartData.attention,
                backgroundColor: CHART_COLORS.attention.fill,
                borderColor: CHART_COLORS.attention.stroke,
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 3,
                yAxisID: 'y',
                // 添加数据点标签
                datalabels: {
                    align: 'top',
                    anchor: 'end',
                    display: function(context) {
                        return context.dataIndex % 3 === 0 && context.dataset.data[context.dataIndex] !== null; 
                    },
                    formatter: function(value) {
                        return value !== null ? formatNumber(value, 0) : '';
                    },
                    font: {
                        size: 10
                    }
                }
            });
        }
        
        if (hasHoldersData) {
            datasets.push({
                label: '持有人数',
                data: chartData.holders,
                backgroundColor: CHART_COLORS.holder.fill,
                borderColor: CHART_COLORS.holder.stroke,
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 3,
                yAxisID: 'y',
                // 添加数据点标签
                datalabels: {
                    align: 'top',
                    anchor: 'end',
                    display: function(context) {
                        return context.dataIndex % 3 === 0 && context.dataset.data[context.dataIndex] !== null;
                    },
                    formatter: function(value) {
                        return value !== null ? formatNumber(value, 0) : '';
                    },
                    font: {
                        size: 10
                    }
                }
            });
        }
        
        if (hasAmountData) {
            datasets.push({
                label: '持仓价值(元)',
                data: chartData.amounts,
                backgroundColor: CHART_COLORS.amount.fill,
                borderColor: CHART_COLORS.amount.stroke,
                borderWidth: 2,
                type: 'bar',
                yAxisID: 'y1'
            });
        }
        
        // 创建图表
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    // 启用数据标签插件
                    datalabels: {
                        color: 'rgba(0, 0, 0, 0.7)',
                        backgroundColor: 'rgba(255, 255, 255, 0.7)',
                        borderRadius: 3,
                        padding: 2
                    },
                    tooltip: {
                        bodyFont: {
                            family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif'
                        },
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    if (context.dataset.label === '持仓价值(元)') {
                                        label += formatNumber(context.parsed.y, 2);
                                    } else {
                                        label += formatNumber(context.parsed.y, 0);
                                    }
                                }
                                return label;
                            }
                        }
                    },
                    legend: {
                        position: 'top',
                        labels: {
                            boxWidth: 15,
                            padding: 15,
                            font: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif'
                            }
                        }
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif'
                            }
                        }
                    },
                    y: {
                        type: 'linear',
                        display: hasAttentionData || hasHoldersData,
                        position: 'left',
                        grid: {
                            borderDash: [2],
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif'
                            },
                            callback: function(value) {
                                return formatNumber(value, 0);
                            }
                        },
                        title: {
                            display: true,
                            text: '人数',
                            font: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                                size: 12
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: hasAmountData,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            font: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif'
                            },
                            callback: function(value) {
                                return formatNumber(value, 0);
                            }
                        },
                        title: {
                            display: true,
                            text: '持仓价值(元)',
                            font: {
                                family: 'SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif',
                                size: 12
                            }
                        }
                    }
                },
                animations: {
                    tension: {
                        duration: 1000,
                        easing: 'easeInOutQuad',
                        from: 0.8,
                        to: 0.3,
                        loop: false
                    }
                }
            }
        });
        
        console.log('图表初始化成功');
        
        // 计算并显示历史数据变化
        const changes = calculateHistoricalChanges(historyData);
        displayHistoricalChanges(containerId, changes);
        
        // 绑定时间范围选择事件
        bindPeriodButtons(chart, historyData, containerId);
        
        // 绑定自定义日期范围事件
        bindCustomDateRange(chart, historyData, containerId);
        
        return chart;
    } catch (error) {
        console.error('初始化ETF图表出错:', error);
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <p>加载图表出错</p>
                    <small class="text-muted">${error.message}</small>
                    <p class="mt-2">
                        <button class="btn btn-sm btn-outline-danger" onclick="location.reload()">重新加载页面</button>
                    </p>
                </div>
            `;
        }
        return null;
    }
}

// 绑定时间范围按钮事件
function bindPeriodButtons(chart, historyData, containerId) {
    const containerElement = document.getElementById(containerId).closest('.etf-chart-section');
    if (!containerElement) return;
    
    const periodButtons = containerElement.querySelectorAll('[data-period]');
    
    periodButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 更新按钮状态
            periodButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // 更新图表数据
            const period = this.getAttribute('data-period');
            const chartData = prepareChartData(historyData, { period });
            
            // 更新图表
            chart.data.labels = chartData.labels;
            chart.data.datasets[0].data = chartData.attention;
            chart.data.datasets[1].data = chartData.holders;
            chart.data.datasets[2].data = chartData.amounts;
            chart.update();
        });
    });
}

// 绑定自定义日期范围事件
function bindCustomDateRange(chart, historyData, containerId) {
    const startDateInput = document.getElementById(`${containerId}-start-date`);
    const endDateInput = document.getElementById(`${containerId}-end-date`);
    const applyButton = document.getElementById(`${containerId}-apply-date`);
    
    if (!startDateInput || !endDateInput || !applyButton) return;
    
    // 设置初始日期范围
    const dates = [...new Set([
        ...(historyData.attention || []).map(item => item.date),
        ...(historyData.holders || []).map(item => item.date)
    ])].sort();
    
    if (dates.length > 0) {
        startDateInput.value = dates[0];
        endDateInput.value = dates[dates.length - 1];
    }
    
    // 应用按钮点击事件
    applyButton.addEventListener('click', function() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        
        if (!startDate || !endDate) {
            alert('请选择有效的开始和结束日期');
            return;
        }
        
        // 更新图表数据
        const customOptions = { 
            period: 'custom',
            startDate: startDate,
            endDate: endDate
        };
        
        // 修改prepareChartData函数处理自定义日期范围
        const chartData = prepareChartData(historyData, customOptions);
        
        // 更新图表
        chart.data.labels = chartData.labels;
        chart.data.datasets.forEach((dataset, index) => {
            if (index === 0 && chartData.attention) dataset.data = chartData.attention;
            else if (index === 1 && chartData.holders) dataset.data = chartData.holders;
            else if (index === 2 && chartData.amounts) dataset.data = chartData.amounts;
        });
        chart.update();
    });
}

// 在ETF详情页面展示图表
export async function displayETFCharts(etfCode, etfName, targetElement, manager = '') {
    try {
        // 创建图表容器
        const { containerId, html } = createETFChartContainer(etfCode, etfName, manager);
        
        // 添加容器到页面
        if (typeof targetElement === 'string') {
            targetElement = document.getElementById(targetElement);
        }
        
        if (!targetElement) {
            console.error('目标元素不存在');
            return null;
        }
        
        targetElement.insertAdjacentHTML('beforeend', html);
        
        // 获取历史数据
        const historyData = await fetchETFHistoryData(etfCode);
        
        // 初始化图表
        return await initETFChart(containerId, historyData);
    } catch (error) {
        console.error('展示ETF图表出错:', error);
        return null;
    }
} 