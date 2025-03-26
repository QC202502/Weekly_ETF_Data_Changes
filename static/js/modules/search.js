/**
 * 搜索功能模块
 */
import { showLoading, hideLoading, showMessage } from './utils.js';

// 搜索ETF函数
export function searchETF() {
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
export function handleSearchResult(data) {
    console.log('处理搜索结果:', data);
    const resultsContainer = document.getElementById('search-results');
    
    if (!resultsContainer) {
        console.error('未找到搜索结果容器');
        return;
    }
    
    if (data.error) {
        resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        // 隐藏导出Markdown按钮
        document.getElementById('export-markdown-button').style.display = 'none';
        return;
    }
    
    // 检查是否有结果
    if ((data.results && data.results.length === 0) || 
        (data.index_groups && data.index_groups.length === 0)) {
        resultsContainer.innerHTML = `<div class="alert alert-warning">未找到匹配"${data.keyword}"的ETF产品</div>`;
        // 隐藏导出Markdown按钮
        document.getElementById('export-markdown-button').style.display = 'none';
        return;
    }
    
    // 保存当前搜索结果数据，用于导出Markdown
    window.currentSearchResults = data;
    
    // 显示导出Markdown按钮
    document.getElementById('export-markdown-button').style.display = 'inline-block';
    
    let html = '';
    
    // 根据搜索类型展示不同的结果
    if (data.search_type === "跟踪指数名称" && data.index_groups) {
        html += renderIndexGroupResults(data);
    } else if (data.search_type === "基金公司名称") {
        html += renderCompanyResults(data);
    } else if (data.search_type === "ETF基金代码" && data.index_name && data.index_code) {
        html += renderETFCodeResults(data);
    } else {
        html += renderGeneralResults(data);
    }
    
    resultsContainer.innerHTML = html;
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

// 渲染ETF表格行和汇总行
function renderETFTableRows(etfs, showIndexCode = false) {
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
    
    etfs.forEach(etf => {
        const businessClass = etf.is_business ? 'table-danger' : '';
        const attentionChangeClass = etf.attention_change > 0 ? 'text-success' : (etf.attention_change < 0 ? 'text-danger' : '');
        const holdersChangeClass = etf.holders_change > 0 ? 'text-success' : (etf.holders_change < 0 ? 'text-danger' : '');
        const amountChangeClass = etf.amount_change > 0 ? 'text-success' : (etf.amount_change < 0 ? 'text-danger' : '');
        
        // 累加汇总数据
        totalVolume += etf.volume;
        totalFeeRate += etf.fee_rate;
        totalScale += etf.scale;
        totalAttentionCount += etf.attention_count;
        totalAttentionChange += etf.attention_change;
        totalHoldersCount += etf.holders_count;
        totalHoldersChange += etf.holders_change;
        totalAmount += etf.amount;
        totalAmountChange += etf.amount_change;
        
        if (etf.is_business) {
            businessCount++;
        }
        
        // 生成ETF行HTML - 修复这里使用manager而不是company
        etfRows += `
            <tr class="${businessClass}">
                <td>${etf.code}</td>
                <td>${etf.name}</td>
                ${showIndexCode ? `<td>${etf.index_code}</td>` : `<td>${etf.manager}</td>`}
                <td>${etf.volume.toFixed(2)}</td>
                <td>${etf.fee_rate.toFixed(2)}</td>
                <td>${etf.scale.toFixed(2)}</td>
                <td>${etf.is_business ? '是' : '否'}</td>
                <td>${etf.attention_count.toLocaleString()}</td>
                <td class="${attentionChangeClass}">${etf.attention_change > 0 ? '+' : ''}${etf.attention_change.toLocaleString()}</td>
                <td>${etf.holders_count.toLocaleString()}</td>
                <td class="${holdersChangeClass}">${etf.holders_change > 0 ? '+' : ''}${etf.holders_change.toLocaleString()}</td>
                <td>${etf.amount.toFixed(2)}</td>
                <td class="${amountChangeClass}">${etf.amount_change > 0 ? '+' : ''}${etf.amount_change.toFixed(2)}</td>
            </tr>
        `;
    });
    
    // 计算平均值
    const count = etfs.length;
    const avgFeeRate = count > 0 ? totalFeeRate / count : 0;
    
    // 生成汇总行HTML
    const summaryRow = `
        <tr class="table-primary font-weight-bold">
            <td colspan="${showIndexCode ? 3 : 3}">汇总 (${count}只ETF，其中${businessCount}只商务品)</td>
            <td>${totalVolume.toFixed(2)}</td>
            <td>${avgFeeRate.toFixed(2)}</td>
            <td>${totalScale.toFixed(2)}</td>
            <td>${businessCount}/${count}</td>
            <td>${totalAttentionCount.toLocaleString()}</td>
            <td>${totalAttentionChange > 0 ? '+' : ''}${totalAttentionChange.toLocaleString()}</td>
            <td>${totalHoldersCount.toLocaleString()}</td>
            <td>${totalHoldersChange > 0 ? '+' : ''}${totalHoldersChange.toLocaleString()}</td>
            <td>${totalAmount.toFixed(2)}</td>
            <td>${totalAmountChange > 0 ? '+' : ''}${totalAmountChange.toFixed(2)}</td>
        </tr>
    `;
    
    return { etfRows, summaryRow };
}