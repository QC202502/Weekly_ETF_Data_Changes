/**
 * ETF搜索模块
 * 处理搜索请求和结果展示
 * 版本: 2.0.1 (2025-04-04) - 添加持仓人数和持仓金额支持
 */

import { showLoading, hideLoading, showAlert, formatNumber, showMessage } from './utils.js';

console.log("搜索模块已加载 v2.0.1 (2025-04-04)");

// 搜索ETF函数
export function searchETF() {
    console.log('搜索ETF函数被调用');
    
    try {
        // 移除调试信息显示
        const debugInfo = document.getElementById('debug-info');
        if (debugInfo) {
            debugInfo.style.display = 'none';
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
            // 针对ETF基金代码搜索，确保数据完整性
            if (data.search_type === "ETF基金代码") {
                console.log('ETF基金代码搜索处理，检查数据完整性...');
                // 计算总规模
                if (!data.total_scale && data.results && data.results.length > 0) {
                    let totalScale = 0;
                    data.results.forEach(etf => {
                        totalScale += Number(etf.fund_size || 0);
                    });
                    
                    if (data.related_etfs && data.related_etfs.length > 0) {
                        data.related_etfs.forEach(etf => {
                            totalScale += Number(etf.fund_size || 0);
                        });
                    }
                    
                    data.total_scale = totalScale;
                    console.log('已计算并添加总规模:', totalScale);
                }
                
                // 添加ETF数量
                if (!data.etf_count) {
                    const mainCount = data.results ? data.results.length : 0;
                    const relatedCount = data.related_etfs ? data.related_etfs.length : 0;
                    data.etf_count = mainCount + relatedCount;
                    console.log('已计算并添加ETF数量:', data.etf_count);
                }
            }
            
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
    console.log('处理搜索结果:', data);
    console.log('v2.0.1 持仓人数:', data.results && data.results[0] ? data.results[0].holder_count : 'N/A', '持仓金额:', data.results && data.results[0] ? data.results[0].holding_amount : 'N/A');
    
    // 针对ETF基金代码搜索的调试信息
    if (data.search_type === "ETF基金代码") {
        console.log('ETF基金代码搜索调试信息:');
        console.log('- search_type:', data.search_type);
        console.log('- index_name:', data.index_name);
        console.log('- index_code:', data.index_code);
        console.log('- total_scale:', data.total_scale);
        console.log('- etf_count:', data.etf_count);
        console.log('- index_intro:', data.index_intro ? data.index_intro.substring(0, 50) + '...' : 'N/A');
    }
    
    // 同时查找两种可能的结果容器ID
    const resultsContainer = document.getElementById('search-results') || document.getElementById('searchResults');
    
    // 隐藏调试信息
    const debugInfo = document.getElementById('debug-info');
    if (debugInfo) {
        debugInfo.style.display = 'none';
    }
    
    // 保存当前搜索结果
    window.currentSearchResults = data;
    
    // 显示导出Markdown按钮（无论是否有搜索结果）
    const exportMarkdownButton = document.getElementById('export-markdown-button');
    if (exportMarkdownButton) {
        exportMarkdownButton.style.display = 'inline-block';
        console.log('显示导出Markdown按钮 - display设置为inline-block');
    } else {
        console.error('无法找到导出Markdown按钮元素 (ID: export-markdown-button)');
    }
    
    // 隐藏推荐栏
    const recommendationContainer = document.getElementById('recommendation-container');
    if (recommendationContainer) {
        recommendationContainer.style.display = 'none';
    }
    
    // 检查结果容器
    if (!resultsContainer) {
        console.error('未找到搜索结果容器');
        return;
    }
    
    // 根据搜索类型生成不同的HTML
    let htmlContent = '';
    
    // 添加数据截止日期信息
    if (data.data_date) {
        htmlContent += `
            <div class="alert alert-info">
                <small class="text-muted">数据截止日期: ${data.data_date}</small>
            </div>
        `;
    }
    
    // 检查是否有指数介绍
    if (data.index_intro) {
        htmlContent += `
            <div class="alert alert-light">
                <h5>指数介绍: ${data.index_name || data.index_code}</h5>
                <p>${data.index_intro}</p>
            </div>
        `;
    }
    
    // 检查搜索类型并处理结果
    if ((data.is_grouped && data.index_count === 0) || 
        (!data.is_grouped && (!data.results || data.results.length === 0))) {
        console.log("搜索无结果");
        resultsContainer.innerHTML = `<div class="alert alert-info">未找到相关ETF</div>`;
    } else {
        if (data.search_type === 'ETF基金代码') {
            // 添加指数简介信息
            if (data.index_intro) {
                htmlContent += `<div class="alert alert-info mb-3">
                    <h5 class="alert-heading">${data.index_name || ''} (${data.index_code || ''})</h5>
                    <p>${data.index_intro}</p>
                </div>`;
            }
            
            // 合并主ETF和同指数ETF
            let allETFs = [...data.results];
            if (data.related_etfs && data.related_etfs.length > 0) {
                allETFs = allETFs.concat(data.related_etfs);
            }
            
            // 按区间日均成交额从高到低排序
            allETFs.sort((a, b) => {
                const volumeA = Number(a.daily_avg_volume || 0);
                const volumeB = Number(b.daily_avg_volume || 0);
                return volumeB - volumeA;
            });
            
            // 生成单一表格
            htmlContent += generateETFTable(allETFs, `${data.index_name || ''}跟踪ETF (${allETFs.length}个)`);
        } else if (data.is_grouped && (data.search_type === '通用搜索(按指数分组)' || data.search_type === '跟踪指数名称(按指数分组)')) {
            // 显示按指数分组的搜索结果
            htmlContent += renderIndexGroupResults(data);
        } else if (data.search_type === '基金公司名称') {
            // 基金公司搜索结果显示为普通表格，不分组
            htmlContent += generateETFTable(data.results, `${data.company_name || '基金公司'}旗下ETF`);
        } else {
            // 其他搜索类型使用通用表格
            htmlContent += generateETFTable(data.results, data.search_type || '搜索结果');
        }
        
        // 更新结果容器
        resultsContainer.innerHTML = htmlContent;
        
        // 同时更新隐藏的结果容器(如果存在)
        const altResultsContainer = 
            resultsContainer.id === 'search-results' 
                ? document.getElementById('searchResults') 
                : document.getElementById('search-results');
        
        if (altResultsContainer) {
            altResultsContainer.innerHTML = htmlContent;
        }
        
        // 成功处理结果后显示成功消息
        let successMessage = '';
        if (data.search_type === 'ETF基金代码') {
            successMessage = `找到${data.count}个主要ETF和${data.related_count || 0}个同指数ETF`;
        } else if (data.is_grouped) {
            successMessage = `按跟踪指数分组，找到${data.index_count}个指数，共${data.count}个ETF`;
        } else {
            successMessage = `成功找到${data.count}个匹配的ETF`;
        }
        showMessage('success', successMessage);
    }
}

// 简化公司名称的函数
const simplifyCompany = (company) => {
    if (!company) return '';
    // 删除"基金"及其后面的字符
    return company.replace(/基金.*$/, '');
};

// 生成ETF表格
function generateETFTable(etfs, title = '搜索结果') {
    // 调试信息
    console.log(`生成ETF表格: ${title}，收到${etfs.length}条记录`);
    if (etfs.length > 0) {
        const firstETF = etfs[0];
        console.log("第一条ETF数据:", firstETF);
        console.log("持仓人数:", firstETF.holder_count);
        console.log("持仓金额:", firstETF.holding_amount);
    }
    
    // 简化公司名称的函数
    const simplifyCompany = (company) => {
        if (!company) return '';
        // 删除"基金"及其后面的字符
        return company.replace(/基金.*$/, '');
    };
    
    // 移除代码后缀的函数
    const removeCodeSuffix = (code) => {
        if (!code) return '';
        return code.replace(/\.(SZ|SH|BJ)$/i, '');
    };
    
    // 找出总规模最大和交易量最大的ETF
    let maxFundSizeETF = [...etfs].sort((a, b) => 
        (Number(b.fund_size || 0) - Number(a.fund_size || 0)))[0] || null;
    
    let maxVolumeETF = [...etfs].sort((a, b) => 
        (Number(b.daily_avg_volume || 0) - Number(a.daily_avg_volume || 0)))[0] || null;
    
    // 标记高亮的项目：找出管理费率最低中交易量最大的ETF
    let minFeeETFs = [...etfs].sort((a, b) => 
        (Number(a.management_fee_rate || 0) - Number(b.management_fee_rate || 0)));
    
    // 获取最低费率
    const lowestFee = minFeeETFs.length > 0 ? Number(minFeeETFs[0].management_fee_rate || 0) : 0;
    
    // 筛选所有具有最低费率的ETF
    const lowestFeeETFs = minFeeETFs.filter(etf => 
        Number(etf.management_fee_rate || 0) === lowestFee);
    
    // 在最低费率组中，找出交易量最大的
    let highlightETF = lowestFeeETFs.length > 0 ? 
        lowestFeeETFs.sort((a, b) => 
            Number(b.daily_avg_volume || 0) - Number(a.daily_avg_volume || 0))[0] : 
        null;
    
    // 构建表格HTML
    let tableHtml = `
        <div class="card mb-4">
            <div class="card-header">
                <h5>${title}</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>代码</th>
                                <th>名称</th>
                                <th>管理人</th>
                                <th>规模(亿)</th>
                                <th>管理费率</th>
                                <th>区间日均成交额(亿)</th>
                                <th>最近交易日成交额(亿)</th>
                                <th>跟踪误差(%)</th>
                                <th>总持有人数</th>
                                <th>持仓人数</th>
                                <th>持仓金额(元)</th>
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
    let totalHolderCount = 0;
    let totalHoldingAmount = 0;
    let totalDailyAvgVolume = 0;
    let totalDailyVolume = 0;
    
    etfs.forEach((etf, index) => {
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
                holder_count: Number(etf.holder_count || 0),
                holding_amount: Number(etf.holding_amount || 0),
                attention_count: Number(etf.attention_count || 0),
                is_business: Boolean(etf.is_business),
                business_text: etf.business_text || (etf.is_business ? '商务品' : '非商务品'),
                daily_avg_volume: Number(etf.daily_avg_volume || 0),
                daily_volume: Number(etf.daily_volume || 0)
            };
            
            // 累加统计数据
            totalScale += etfSafe.fund_size;
            totalFeeRate += etfSafe.management_fee_rate;
            totalHolders += etfSafe.total_holder_count;
            totalHolderCount += etfSafe.holder_count;
            totalHoldingAmount += etfSafe.holding_amount;
            totalAttention += etfSafe.attention_count;
            totalDailyAvgVolume += etfSafe.daily_avg_volume;
            totalDailyVolume += etfSafe.daily_volume;
            if (etfSafe.is_business) businessCount++;
            
            // 检查是否需要高亮
            const isMinFeeHighlight = highlightETF && etf.code === highlightETF.code;
            const isMaxSizeHighlight = maxFundSizeETF && etf.code === maxFundSizeETF.code;
            const isMaxVolumeHighlight = maxVolumeETF && etf.code === maxVolumeETF.code;
            
            // 设置行样式
            let highlightClass = '';
            if (isMinFeeHighlight) highlightClass = ' class="table-warning"';
            
            // 处理代码和管理费率的显示
            const displayCode = removeCodeSuffix(etfSafe.code);
            
            // 设置显示格式和高亮
            const codeDisplay = isMaxSizeHighlight || isMaxVolumeHighlight ? 
                `<strong style="color: #007bff;">${displayCode}</strong>` : displayCode;
            
            const fundSizeDisplay = isMaxSizeHighlight ? 
                `<strong style="color: #007bff;">${formatNumber(etfSafe.fund_size)}</strong>` : 
                formatNumber(etfSafe.fund_size);
            
            const volumeDisplay = isMaxVolumeHighlight ? 
                `<strong style="color: #007bff;">${formatNumber(etfSafe.daily_avg_volume, 2)}</strong>` : 
                formatNumber(etfSafe.daily_avg_volume, 2);
            
            tableHtml += `
                <tr${highlightClass}>
                    <td>${codeDisplay}</td>
                    <td>${etfSafe.name}</td>
                    <td>${simplifyCompany(etfSafe.manager)}</td>
                    <td>${fundSizeDisplay}</td>
                    <td>${formatNumber(etfSafe.management_fee_rate, 4)}</td>
                    <td>${volumeDisplay}</td>
                    <td>${formatNumber(etfSafe.daily_volume, 2)}</td>
                    <td>${formatNumber(etfSafe.tracking_error)}</td>
                    <td>${formatNumber(etfSafe.total_holder_count, 0)}</td>
                    <td>${formatNumber(etfSafe.holder_count, 0)}</td>
                    <td>${formatNumber(etfSafe.holding_amount, 2)}</td>
                    <td>${formatNumber(etfSafe.attention_count, 0)}</td>
                    <td>${etfSafe.business_text}</td>
                </tr>
            `;
        } catch (e) {
            console.error('处理ETF数据时出错:', e, etf);
        }
    });
    
    // 添加汇总行
    const avgFeeRate = etfs.length > 0 ? totalFeeRate / etfs.length : 0;
    
    tableHtml += `
                </tbody>
                <tfoot>
                    <tr class="table-info">
                        <td colspan="3">汇总 (${etfs.length}个ETF${businessCount > 0 ? '，其中'+businessCount+'个商务品' : ''})</td>
                        <td>${formatNumber(totalScale)}</td>
                        <td>${formatNumber(avgFeeRate, 4)}</td>
                        <td>${formatNumber(totalDailyAvgVolume, 2)}</td>
                        <td>${formatNumber(totalDailyVolume, 2)}</td>
                        <td>-</td>
                        <td>${formatNumber(totalHolders, 0)}</td>
                        <td>${formatNumber(totalHolderCount, 0)}</td>
                        <td>${formatNumber(totalHoldingAmount, 2)}</td>
                        <td>${formatNumber(totalAttention, 0)}</td>
                        <td>${etfs.length > 0 ? formatNumber((businessCount / etfs.length) * 100, 1)+'%' : '-'}</td>
                    </tr>
                </tfoot>
            </table>
        </div>
    </div>
</div>
    `;
    
    return tableHtml;
}

// 渲染指数分组结果
function renderIndexGroupResults(data) {
    let html = `<div class="alert alert-success">找到${data.index_count}个匹配的指数，共有${data.count}个ETF，按跟踪指数规模排序</div>`;
    
    // 简化公司名称的函数
    const simplifyCompany = (company) => {
        if (!company) return '';
        // 删除"基金"及其后面的字符
        return company.replace(/基金.*$/, '');
    };
    
    // 移除代码后缀的函数
    const removeCodeSuffix = (code) => {
        if (!code) return '';
        return code.replace(/\.(SZ|SH|BJ)$/i, '');
    };
    
    // 为每个指数创建一个表格
    data.index_groups.forEach(group => {
        // 按区间日均成交额从高到低排序
        group.etfs.sort((a, b) => {
            const volumeA = Number(a.daily_avg_volume || 0);
            const volumeB = Number(b.daily_avg_volume || 0);
            return volumeB - volumeA;
        });
        
        // 找出总规模最大和交易量最大的ETF
        let maxFundSizeETF = [...group.etfs].sort((a, b) => 
            (Number(b.fund_size || 0) - Number(a.fund_size || 0)))[0] || null;
        
        let maxVolumeETF = [...group.etfs].sort((a, b) => 
            (Number(b.daily_avg_volume || 0) - Number(a.daily_avg_volume || 0)))[0] || null;
        
        // 标记高亮的项目：找出管理费率最低中交易量最大的ETF
        let minFeeETFs = [...group.etfs].sort((a, b) => 
            (Number(a.management_fee_rate || 0) - Number(b.management_fee_rate || 0)));
        
        // 获取最低费率
        const lowestFee = minFeeETFs.length > 0 ? Number(minFeeETFs[0].management_fee_rate || 0) : 0;
        
        // 筛选所有具有最低费率的ETF
        const lowestFeeETFs = minFeeETFs.filter(etf => 
            Number(etf.management_fee_rate || 0) === lowestFee);
        
        // 在最低费率组中，找出交易量最大的
        let highlightETF = lowestFeeETFs.length > 0 ? 
            lowestFeeETFs.sort((a, b) => 
                Number(b.daily_avg_volume || 0) - Number(a.daily_avg_volume || 0))[0] : 
            null;
        
        html += `
            <div class="card mb-4">
                <div class="card-header">
                    <h5>${group.index_name || '未知指数'} (${group.index_code || '无代码'})</h5>
                    <div class="small text-muted">总规模: ${formatNumber(group.total_scale)}亿元 | ETF数量: ${group.etf_count}</div>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead>
                                <tr>
                                    <th>代码</th>
                                    <th>名称</th>
                                    <th>管理人</th>
                                    <th>规模(亿)</th>
                                    <th>管理费率</th>
                                    <th>区间日均成交额(亿)</th>
                                    <th>最近交易日成交额(亿)</th>
                                    <th>跟踪误差(%)</th>
                                    <th>总持有人数</th>
                                    <th>持仓人数</th>
                                    <th>持仓金额(元)</th>
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
        let businessCount = 0;
        let totalHolderCount = 0;
        let totalHoldingAmount = 0;
        let totalAttention = 0;
        let totalDailyAvgVolume = 0;
        let totalDailyVolume = 0;
        
        // 添加每个ETF的行
        group.etfs.forEach(etf => {
            // 确保所有字段都有默认值
            const etfSafe = {
                code: etf.code || '',
                name: etf.name || '',
                manager: etf.manager || etf.fund_manager || '',
                fund_size: Number(etf.scale || etf.fund_size || 0),
                management_fee_rate: Number(etf.fee_rate || etf.management_fee_rate || 0),
                tracking_error: Number(etf.tracking_error || 0),
                total_holder_count: Number(etf.holders_count || etf.total_holder_count || 0),
                holder_count: Number(etf.holder_count || 0),
                holding_amount: Number(etf.holding_amount || 0),
                attention_count: Number(etf.attention_count || 0),
                is_business: Boolean(etf.is_business),
                business_text: etf.business_text || (etf.is_business ? '商务品' : '非商务品'),
                daily_avg_volume: Number(etf.daily_avg_volume || etf.volume || 0),
                daily_volume: Number(etf.daily_volume || 0)
            };
            
            // 累加统计数据
            totalScale += etfSafe.fund_size;
            totalFeeRate += etfSafe.management_fee_rate;
            totalHolders += etfSafe.total_holder_count;
            totalHolderCount += etfSafe.holder_count;
            totalHoldingAmount += etfSafe.holding_amount;
            totalAttention += etfSafe.attention_count;
            totalDailyAvgVolume += etfSafe.daily_avg_volume;
            totalDailyVolume += etfSafe.daily_volume;
            if (etfSafe.is_business) businessCount++;
            
            // 检查是否需要高亮
            const isMinFeeHighlight = highlightETF && etf.code === highlightETF.code;
            const isMaxSizeHighlight = maxFundSizeETF && etf.code === maxFundSizeETF.code;
            const isMaxVolumeHighlight = maxVolumeETF && etf.code === maxVolumeETF.code;
            
            // 设置行样式
            let highlightClass = '';
            if (isMinFeeHighlight) highlightClass = ' class="table-warning"';
            
            // 处理代码和管理费率的显示
            const displayCode = removeCodeSuffix(etfSafe.code);
            
            // 设置显示格式和高亮
            const codeDisplay = isMaxSizeHighlight || isMaxVolumeHighlight ? 
                `<strong style="color: #007bff;">${displayCode}</strong>` : displayCode;
            
            const fundSizeDisplay = isMaxSizeHighlight ? 
                `<strong style="color: #007bff;">${formatNumber(etfSafe.fund_size)}</strong>` : 
                formatNumber(etfSafe.fund_size);
            
            const volumeDisplay = isMaxVolumeHighlight ? 
                `<strong style="color: #007bff;">${formatNumber(etfSafe.daily_avg_volume, 2)}</strong>` : 
                formatNumber(etfSafe.daily_avg_volume, 2);
            
            html += `
                <tr${highlightClass}>
                    <td>${codeDisplay}</td>
                    <td>${etfSafe.name}</td>
                    <td>${simplifyCompany(etfSafe.manager)}</td>
                    <td>${fundSizeDisplay}</td>
                    <td>${formatNumber(etfSafe.management_fee_rate, 4)}</td>
                    <td>${volumeDisplay}</td>
                    <td>${formatNumber(etfSafe.daily_volume, 2)}</td>
                    <td>${formatNumber(etfSafe.tracking_error)}</td>
                    <td>${formatNumber(etfSafe.total_holder_count, 0)}</td>
                    <td>${formatNumber(etfSafe.holder_count, 0)}</td>
                    <td>${formatNumber(etfSafe.holding_amount, 2)}</td>
                    <td>${formatNumber(etfSafe.attention_count, 0)}</td>
                    <td>${etfSafe.business_text}</td>
                </tr>
            `;
        });
        
        // 添加汇总行
        const avgFeeRate = group.etfs.length > 0 ? totalFeeRate / group.etfs.length : 0;
        
        html += `
                            </tbody>
                            <tfoot>
                                <tr class="table-info">
                                    <td colspan="3">汇总 (${group.etfs.length}个ETF${businessCount > 0 ? '，其中'+businessCount+'个商务品' : ''})</td>
                                    <td>${formatNumber(totalScale)}</td>
                                    <td>${formatNumber(avgFeeRate, 4)}</td>
                                    <td>${formatNumber(totalDailyAvgVolume, 2)}</td>
                                    <td>${formatNumber(totalDailyVolume, 2)}</td>
                                    <td>-</td>
                                    <td>${formatNumber(totalHolders, 0)}</td>
                                    <td>${formatNumber(totalHolderCount, 0)}</td>
                                    <td>${formatNumber(totalHoldingAmount, 2)}</td>
                                    <td>${formatNumber(totalAttention, 0)}</td>
                                    <td>${group.etfs.length > 0 ? formatNumber((businessCount / group.etfs.length) * 100, 1)+'%' : '-'}</td>
                                </tr>
                            </tfoot>
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