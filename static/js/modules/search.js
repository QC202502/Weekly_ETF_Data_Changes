/**
 * 搜索功能模块
 */
import { showLoading, hideLoading, showAlert, formatNumber, showMessage } from './utils.js';

// 搜索ETF函数
export function searchETF() {
    console.log('搜索ETF函数被调用');
    
    try {
        // 添加调试信息
        const debugInfo = document.getElementById('debug-info');
        if (debugInfo) {
            const elements = {
                'searchInput': document.getElementById('searchInput'),
                'search-input': document.getElementById('search-input'),
                'searchForm': document.getElementById('searchForm'),
                'statusMessage': document.getElementById('statusMessage'),
                'searchResults': document.getElementById('searchResults'),
                'loading': document.getElementById('loading')
            };
            
            let debugHtml = '<b>元素状态:</b><br>';
            for (const [id, element] of Object.entries(elements)) {
                debugHtml += `${id}: ${element ? '存在' : '<span style="color:red">不存在</span>'}<br>`;
            }
            debugInfo.innerHTML = debugHtml;
        }
        
        // 获取搜索关键词 - 尝试两种可能的输入框ID
        let searchInput = document.getElementById('searchInput'); // 搜索页面使用的ID
        if (!searchInput) {
            searchInput = document.getElementById('search-input'); // 模块模板使用的ID
        }
        
        if (!searchInput) {
            console.error('未找到搜索输入框元素 (ID: searchInput 或 search-input)');
            
            // 记录页面上所有input元素以便调试
            const allInputs = document.querySelectorAll('input');
            console.log(`页面上有 ${allInputs.length} 个输入框元素`);
            if (allInputs.length > 0) {
                console.log('可用的输入框元素:');
                allInputs.forEach((input, index) => {
                    console.log(`输入框 ${index + 1}: id=${input.id}, name=${input.name}, type=${input.type}, class=${input.className}`);
                });
            }
            
            showMessage('danger', '系统错误：未找到搜索输入框');
            return;
        }
        
        const keyword = searchInput.value.trim();
        console.log('获取到搜索关键词:', keyword);
        
        if (!keyword) {
            showMessage('warning', '请输入搜索关键词');
            return;
        }
        
        // 显示加载状态
        showLoading();
        const statusMessage = document.getElementById('statusMessage');
        if (statusMessage) {
            statusMessage.textContent = '正在搜索，请稍候...';
            statusMessage.style.display = 'block';
        }
        
        console.log('发送搜索请求，关键词:', keyword);
        
        // 发送搜索请求
        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            },
            body: `code=${encodeURIComponent(keyword)}`
        })
        .then(response => {
            console.log('搜索响应状态:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            if (statusMessage) {
                statusMessage.style.display = 'none';
            }
            console.log('搜索结果:', data);
            
            if (data.error) {
                showMessage('danger', data.error);
                const searchResults = document.getElementById('searchResults');
                if (searchResults) {
                    searchResults.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                }
            } else {
                handleSearchResult(data);
            }
        })
        .catch(error => {
            hideLoading();
            if (statusMessage) {
                statusMessage.style.display = 'none';
            }
            console.error('搜索出错:', error);
            showMessage('danger', `搜索出错: ${error.message}`);
            const searchResults = document.getElementById('searchResults');
            if (searchResults) {
                searchResults.innerHTML = `<div class="alert alert-danger">搜索出错: ${error.message}</div>`;
            }
        });
    } catch (error) {
        console.error('搜索函数运行时错误:', error);
        showMessage('danger', `运行时错误: ${error.message}`);
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.innerHTML = `<div class="alert alert-danger">运行时错误: ${error.message}</div>`;
        }
    }
}

// 处理搜索结果
export function handleSearchResult(data) {
    try {
        console.log('处理搜索结果:', data);
        
        // 同时查找两种可能的结果容器ID
        const resultsContainer = document.getElementById('search-results') || document.getElementById('searchResults');
        
        // 调试信息
        const debugInfo = document.getElementById('debug-info');
        if (debugInfo) {
            debugInfo.style.display = 'block';
            const debugContent = document.getElementById('debug-content');
            if (debugContent) {
                debugContent.innerHTML = `
                    <p>搜索结果数据：</p>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                    <p>结果容器: ${resultsContainer ? '找到' : '未找到'}</p>
                    <p>容器ID: ${resultsContainer ? resultsContainer.id : '无'}</p>
                `;
            }
        }
        
        if (!resultsContainer) {
            console.error('未找到结果容器元素 (search-results 或 searchResults)');
            return;
        }
        
        if (!data) {
            console.error('搜索结果数据为空');
            showMessage('danger', '搜索结果为空');
            resultsContainer.innerHTML = '<div class="alert alert-danger">搜索结果数据为空</div>';
            return;
        }
        
        if (data.error) {
            console.error('搜索结果包含错误:', data.error);
            showMessage('danger', data.error);
            resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }
        
        // 检查结果格式
        if (!data.results || !Array.isArray(data.results) || data.results.length === 0) {
            showMessage('warning', data.message || '未找到相关ETF');
            resultsContainer.innerHTML = '<div class="alert alert-warning">未找到相关ETF</div>';
            return;
        }
        
        // 构建表格HTML
        let tableHtml = `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>代码</th>
                            <th>名称</th>
                            <th>管理人</th>
                            <th>规模(亿)</th>
                            <th>管理费率(%)</th>
                            <th>跟踪误差(%)</th>
                            <th>持有人数</th>
                            <th>关注人数</th>
                            <th>类型</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // 计算汇总数据
        let totalScale = 0;
        let totalFeeRate = 0;
        let totalHolders = 0;
        let totalAttention = 0;
        let businessCount = 0;
        
        data.results.forEach((etf, index) => {
            try {
                console.log(`处理ETF结果[${index}]:`, etf);
                
                // 确保所有字段都有默认值
                const etfSafe = {
                    code: etf.code || '',
                    name: etf.name || '',
                    manager: etf.manager || etf.fund_manager || '',
                    fund_size: Number(etf.fund_size || 0),
                    management_fee_rate: Number(etf.management_fee_rate || 0),
                    tracking_error: Number(etf.tracking_error || 0),
                    total_holder_count: Number(etf.total_holder_count || 0),
                    attention_count: Number(etf.attention_count || 0),
                    is_business: Boolean(etf.is_business),
                    business_text: etf.business_text || (etf.is_business ? '商务品' : '非商务品')
                };
                
                // 累加统计数据
                totalScale += etfSafe.fund_size;
                totalFeeRate += etfSafe.management_fee_rate;
                totalHolders += etfSafe.total_holder_count;
                totalAttention += etfSafe.attention_count;
                if (etfSafe.is_business) businessCount++;
                
                tableHtml += `
                    <tr>
                        <td>${etfSafe.code}</td>
                        <td>${etfSafe.name}</td>
                        <td>${etfSafe.manager}</td>
                        <td>${formatNumber(etfSafe.fund_size)}</td>
                        <td>${formatNumber(etfSafe.management_fee_rate)}</td>
                        <td>${formatNumber(etfSafe.tracking_error)}</td>
                        <td>${formatNumber(etfSafe.total_holder_count, 0)}</td>
                        <td>${formatNumber(etfSafe.attention_count, 0)}</td>
                        <td>${etfSafe.business_text}</td>
                    </tr>
                `;
            } catch (e) {
                console.error('处理ETF数据时出错:', e, etf);
            }
        });
        
        // 添加汇总行
        const avgFeeRate = data.results.length > 0 ? totalFeeRate / data.results.length : 0;
        
        tableHtml += `
                </tbody>
                <tfoot>
                    <tr class="table-info">
                        <td colspan="3">汇总 (${data.results.length}个ETF，其中${businessCount}个商务品)</td>
                        <td>${formatNumber(totalScale)}</td>
                        <td>${formatNumber(avgFeeRate)}</td>
                        <td>-</td>
                        <td>${formatNumber(totalHolders, 0)}</td>
                        <td>${formatNumber(totalAttention, 0)}</td>
                        <td>${formatNumber((businessCount / (data.results.length || 1)) * 100, 1)}%</td>
                    </tr>
                </tfoot>
            </table>
        </div>
        `;
        
        // 更新结果容器
        resultsContainer.innerHTML = tableHtml;
        
        // 同时更新隐藏的结果容器(如果存在)
        const altResultsContainer = 
            resultsContainer.id === 'search-results' 
                ? document.getElementById('searchResults') 
                : document.getElementById('search-results');
        
        if (altResultsContainer) {
            altResultsContainer.innerHTML = tableHtml;
        }
        
        // 保存搜索结果到全局变量，用于导出
        window.currentSearchResults = data;
        
        // 显示导出按钮
        const exportButton = document.getElementById('export-markdown-button');
        if (exportButton) {
            exportButton.style.display = 'inline-block';
        }
        
        // 成功处理结果后显示成功消息
        showMessage('success', `成功找到 ${data.results.length} 个匹配的ETF`);
    } catch (error) {
        console.error('处理搜索结果时出错:', error);
        showMessage('danger', `处理搜索结果时出错: ${error.message}`);
        
        const resultsContainer = document.getElementById('search-results') || document.getElementById('searchResults');
        if (resultsContainer) {
            resultsContainer.innerHTML = `<div class="alert alert-danger">处理搜索结果时出错: ${error.message}</div>`;
        }
    }
}

// 渲染指数分组结果
function renderIndexGroupResults(data) {
    let html = `<div class="alert alert-success">找到${data.index_count}个匹配的指数，共有${data.count}个ETF，按跟踪指数分组</div>`;
    
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
        
        // 添加ETF行和汇总数据
        const { etfRows, summaryRow } = renderETFTableRows(group.etfs);
        html += etfRows;
        html += summaryRow;
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    });
    
    return html;
}

// 渲染公司搜索结果
function renderCompanyResults(data) {
    let html = `<div class="alert alert-success">找到 ${data.count} 个匹配"${data.keyword}"的ETF产品</div>`;
    
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
    
    // 添加ETF行和汇总数据
    const { etfRows, summaryRow } = renderETFTableRows(data.results, true);
    html += etfRows;
    html += summaryRow;
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    return html;
}

// 渲染ETF代码搜索结果
function renderETFCodeResults(data) {
    // 添加指数简介信息
    let introHtml = '';
    if (data.index_intro) {
        introHtml = `<div class="alert alert-info mb-2">指数简介：${data.index_intro}</div>`;
    }
    
    let html = introHtml + `<div class="alert alert-success">该ETF跟踪「${data.index_name}」（${data.index_code}），指数总规模 ${data.total_scale}（单位：亿元），跟踪ETF数量${data.etf_count}</div>`;
    
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
    
    // 添加ETF行和汇总数据
    const { etfRows, summaryRow } = renderETFTableRows(data.results);
    html += etfRows;
    html += summaryRow;
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    return html;
}

// 渲染通用搜索结果
function renderGeneralResults(data) {
    let html = `<div class="alert alert-success">找到 ${data.count} 个匹配"${data.keyword}"的ETF产品</div>`;
    
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
    
    // 添加ETF行和汇总数据
    const { etfRows, summaryRow } = renderETFTableRows(data.results);
    html += etfRows;
    html += summaryRow;
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    return html;
}

// 渲染ETF表格行
function renderETFTableRows(etfs) {
    let etfRows = '';
    let totalVolume = 0;
    let totalFeeRate = 0;
    let totalScale = 0;
    let totalAttentionCount = 0;
    let totalAttentionChange = 0;
    let totalHoldersCount = 0;
    let totalHoldersChange = 0;
    let totalAmount = 0;
    let totalAmountChange = 0;
    let businessCount = 0;
    
    // 格式化数字的辅助函数
    const formatNumber = (value, decimals = 2) => {
        if (value === undefined || value === null || isNaN(value)) {
            return '0.00';
        }
        return Number(value).toFixed(decimals);
    };
    
    etfs.forEach(etf => {
        // 确保数据存在
        const fund_size = Number(etf.fund_size || 0);
        const management_fee_rate = Number(etf.management_fee_rate || 0);
        const total_holder_count = Number(etf.total_holder_count || 0);
        const attention_count = Number(etf.attention_count || 0);
        const is_business = Boolean(etf.is_business);
        
        // 累加统计数据
        totalScale += fund_size;
        totalFeeRate += management_fee_rate;
        totalHoldersCount += total_holder_count;
        totalAttentionCount += attention_count;
        if (is_business) businessCount++;
        
        etfRows += `
            <tr>
                <td>${etf.code || ''}</td>
                <td>${etf.name || ''}</td>
                <td>${etf.manager || ''}</td>
                <td>${formatNumber(fund_size)}</td>
                <td>${formatNumber(management_fee_rate)}</td>
                <td>${formatNumber(etf.tracking_error || 0)}</td>
                <td>${formatNumber(total_holder_count, 0)}</td>
                <td>${formatNumber(attention_count, 0)}</td>
                <td>${etf.business_text || '非商务品'}</td>
            </tr>
        `;
    });
    
    // 添加汇总行
    const avgFeeRate = etfs.length > 0 ? totalFeeRate / etfs.length : 0;
    const summaryRow = `
        <tr class="table-info">
            <td colspan="3">汇总 (${etfs.length}个ETF，其中${businessCount}个商务品)</td>
            <td>${formatNumber(totalScale)}</td>
            <td>${formatNumber(avgFeeRate)}</td>
            <td>-</td>
            <td>${formatNumber(totalHoldersCount, 0)}</td>
            <td>${formatNumber(totalAttentionCount, 0)}</td>
            <td>${formatNumber((businessCount / (etfs.length || 1)) * 100, 1)}%</td>
        </tr>
    `;
    
    return { etfRows, summaryRow };
}