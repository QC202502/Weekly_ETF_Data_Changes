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
        console.error('未找到搜索输入框元素 (id="search-input")');
        
        // 调试信息：检查DOM中所有input元素
        const allInputs = document.querySelectorAll('input');
        console.error(`页面中共有 ${allInputs.length} 个input元素：`);
        allInputs.forEach((input, index) => {
            console.error(`[${index}] id=${input.id}, name=${input.name}, type=${input.type}, class=${input.className}`);
        });
        
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
        // 显示搜索关键词和结果数量 - 新格式
        html += `<div class="alert alert-success">找到${data.index_count}个匹配的指数，共有${data.count}个ETF，按跟踪指数分组</div>`;
        
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
            
            group.etfs.forEach(etf => {
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
                if (etf.is_business) businessCount++;
                
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
            
            // 计算平均管理费率
            const avgFeeRate = group.etfs.length > 0 ? totalFeeRate / group.etfs.length : 0;
            
            // 添加汇总行
            const totalAttentionChangeClass = totalAttentionChange > 0 ? 'text-success' : (totalAttentionChange < 0 ? 'text-danger' : '');
            const totalHoldersChangeClass = totalHoldersChange > 0 ? 'text-success' : (totalHoldersChange < 0 ? 'text-danger' : '');
            const totalAmountChangeClass = totalAmountChange > 0 ? 'text-success' : (totalAmountChange < 0 ? 'text-danger' : '');
            
            html += `
                <tr class="table-secondary font-weight-bold">
                    <td>汇总</td>
                    <td>${group.etfs.length}只ETF</td>
                    <td>-</td>
                    <td>${totalVolume.toFixed(2)}</td>
                    <td>${avgFeeRate.toFixed(2)}%</td>
                    <td>${totalScale.toFixed(2)}</td>
                    <td>${businessCount}只商务品</td>
                    <td>${totalAttentionCount.toLocaleString()}</td>
                    <td class="${totalAttentionChangeClass}">${totalAttentionChange > 0 ? '+' : ''}${totalAttentionChange.toLocaleString()}</td>
                    <td>${totalHoldersCount.toLocaleString()}</td>
                    <td class="${totalHoldersChangeClass}">${totalHoldersChange > 0 ? '+' : ''}${totalHoldersChange.toLocaleString()}</td>
                    <td>${totalAmount.toFixed(2)}</td>
                    <td class="${totalAmountChangeClass}">${totalAmountChange > 0 ? '+' : ''}${totalAmountChange.toFixed(2)}</td>
                </tr>
            `;
            
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
        
        data.results.forEach(etf => {
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
            if (etf.is_business) businessCount++;
            
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
        
        // 计算平均管理费率
        const avgFeeRate = data.results.length > 0 ? totalFeeRate / data.results.length : 0;
        
        // 添加汇总行
        const totalAttentionChangeClass = totalAttentionChange > 0 ? 'text-success' : (totalAttentionChange < 0 ? 'text-danger' : '');
        const totalHoldersChangeClass = totalHoldersChange > 0 ? 'text-success' : (totalHoldersChange < 0 ? 'text-danger' : '');
        const totalAmountChangeClass = totalAmountChange > 0 ? 'text-success' : (totalAmountChange < 0 ? 'text-danger' : '');
        
        html += `
            <tr class="table-secondary font-weight-bold">
                <td>汇总</td>
                <td>${data.results.length}只ETF</td>
                <td>-</td>
                <td>${totalVolume.toFixed(2)}</td>
                <td>${avgFeeRate.toFixed(2)}%</td>
                <td>${totalScale.toFixed(2)}</td>
                <td>${businessCount}只商务品</td>
                <td>${totalAttentionCount.toLocaleString()}</td>
                <td class="${totalAttentionChangeClass}">${totalAttentionChange > 0 ? '+' : ''}${totalAttentionChange.toLocaleString()}</td>
                <td>${totalHoldersCount.toLocaleString()}</td>
                <td class="${totalHoldersChangeClass}">${totalHoldersChange > 0 ? '+' : ''}${totalHoldersChange.toLocaleString()}</td>
                <td>${totalAmount.toFixed(2)}</td>
                <td class="${totalAmountChangeClass}">${totalAmountChange > 0 ? '+' : ''}${totalAmountChange.toFixed(2)}</td>
            </tr>
        `;
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else if (data.search_type === "ETF基金代码" && data.index_name && data.index_code) {
        // ETF基金代码搜索 - 新格式
        // 添加指数简介信息
        if (data.index_intro) {
            html += `<div class="alert alert-info mb-2">指数简介：${data.index_intro}</div>`;
        }
        
        html += `<div class="alert alert-success">该ETF跟踪「${data.index_name}」（${data.index_code}），指数总规模 ${data.total_scale}（单位：亿元），跟踪ETF数量${data.etf_count}</div>`;
        
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
        
        data.results.forEach(etf => {
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
            if (etf.is_business) businessCount++;
            
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
        
        // 计算平均管理费率
        const avgFeeRate = data.results.length > 0 ? totalFeeRate / data.results.length : 0;
        
        // 添加汇总行
        const totalAttentionChangeClass = totalAttentionChange > 0 ? 'text-success' : (totalAttentionChange < 0 ? 'text-danger' : '');
        const totalHoldersChangeClass = totalHoldersChange > 0 ? 'text-success' : (totalHoldersChange < 0 ? 'text-danger' : '');
        const totalAmountChangeClass = totalAmountChange > 0 ? 'text-success' : (totalAmountChange < 0 ? 'text-danger' : '');
        
        html += `
            <tr class="table-secondary font-weight-bold">
                <td>汇总</td>
                <td>${data.results.length}只ETF</td>
                <td>-</td>
                <td>${totalVolume.toFixed(2)}</td>
                <td>${avgFeeRate.toFixed(2)}%</td>
                <td>${totalScale.toFixed(2)}</td>
                <td>${businessCount}只商务品</td>
                <td>${totalAttentionCount.toLocaleString()}</td>
                <td class="${totalAttentionChangeClass}">${totalAttentionChange > 0 ? '+' : ''}${totalAttentionChange.toLocaleString()}</td>
                <td>${totalHoldersCount.toLocaleString()}</td>
                <td class="${totalHoldersChangeClass}">${totalHoldersChange > 0 ? '+' : ''}${totalHoldersChange.toLocaleString()}</td>
                <td>${totalAmount.toFixed(2)}</td>
                <td class="${totalAmountChangeClass}">${totalAmountChange > 0 ? '+' : ''}${totalAmountChange.toFixed(2)}</td>
            </tr>
        `;
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        // 跟踪指数代码或通用搜索
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
        
        data.results.forEach(etf => {
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
            if (etf.is_business) businessCount++;
            
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
        
        // 计算平均管理费率
        const avgFeeRate = data.results.length > 0 ? totalFeeRate / data.results.length : 0;
        
        // 添加汇总行
        const totalAttentionChangeClass = totalAttentionChange > 0 ? 'text-success' : (totalAttentionChange < 0 ? 'text-danger' : '');
        const totalHoldersChangeClass = totalHoldersChange > 0 ? 'text-success' : (totalHoldersChange < 0 ? 'text-danger' : '');
        const totalAmountChangeClass = totalAmountChange > 0 ? 'text-success' : (totalAmountChange < 0 ? 'text-danger' : '');
        
        html += `
            <tr class="table-secondary font-weight-bold">
                <td>汇总</td>
                <td>${data.results.length}只ETF</td>
                <td>-</td>
                <td>${totalVolume.toFixed(2)}</td>
                <td>${avgFeeRate.toFixed(2)}%</td>
                <td>${totalScale.toFixed(2)}</td>
                <td>${businessCount}只商务品</td>
                <td>${totalAttentionCount.toLocaleString()}</td>
                <td class="${totalAttentionChangeClass}">${totalAttentionChange > 0 ? '+' : ''}${totalAttentionChange.toLocaleString()}</td>
                <td>${totalHoldersCount.toLocaleString()}</td>
                <td class="${totalHoldersChangeClass}">${totalHoldersChange > 0 ? '+' : ''}${totalHoldersChange.toLocaleString()}</td>
                <td>${totalAmount.toFixed(2)}</td>
                <td class="${totalAmountChangeClass}">${totalAmountChange > 0 ? '+' : ''}${totalAmountChange.toFixed(2)}</td>
            </tr>
        `;
        
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

// 初始化推荐栏
function initRecommendations() {
    console.log('初始化推荐栏');
    
    // 绑定标签页切换事件
    document.querySelectorAll('#recommendation-tabs .nav-link').forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('href');
            
            // 移除所有active类
            document.querySelectorAll('#recommendation-tabs .nav-link').forEach(t => {
                t.classList.remove('active');
            });
            
            // 隐藏所有标签页内容
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('show', 'active');
            });
            
            // 激活当前标签页
            this.classList.add('active');
            document.querySelector(target).classList.add('show', 'active');
        });
    });
    
    // 初始化悬浮卡片
    const tooltip = document.getElementById('recommendation-tooltip');
    document.addEventListener('mousemove', function(e) {
        if (tooltip.style.display === 'block') {
            // 跟随鼠标移动，保持一定偏移
            tooltip.style.left = (e.pageX + 15) + 'px';
            tooltip.style.top = (e.pageY + 15) + 'px';
        }
    });
}

// 加载推荐数据
function loadRecommendations() {
    console.log('加载推荐数据');
    const recommendationContainer = document.getElementById('recommendation-container');
    
    // 移除对推荐容器已显示的检查，确保每次调用都能正确加载推荐数据
    // if (recommendationContainer.style.display === 'block') {
    //     return;
    // }
    
    // 显示推荐容器
    recommendationContainer.style.display = 'block';
    
    // 获取推荐数据
    fetch('/recommendations')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('获取推荐数据出错:', data.error);
                return;
            }
            
            // 渲染推荐数据
            renderRecommendations(data.recommendations);
        })
        .catch(error => {
            console.error('获取推荐数据出错:', error);
        });
}

// 渲染推荐数据
function renderRecommendations(recommendations) {
    console.log('渲染推荐数据:', recommendations);
    
    // 渲染关注人数推荐
    renderRecommendationList('attention', recommendations.attention);
    
    // 渲染持仓客户推荐
    renderRecommendationList('holders', recommendations.holders);
    
    // 渲染保有金额推荐
    renderRecommendationList('amount', recommendations.amount);
    
    // 渲染价格涨幅推荐
    renderRecommendationList('price-return', recommendations.price_return);
}

// 渲染推荐列表
function renderRecommendationList(type, items) {
    const container = document.getElementById(`${type}-recommendations`);
    if (!container) return;
    
    // 清空容器
    container.innerHTML = '';
    
    // 添加推荐项
    items.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.className = 'recommendation-item';
        itemElement.dataset.code = item.code;
        itemElement.dataset.type = type;
        
        // 设置推荐项内容 - 确保ETF代码不包含sh/sz前缀
        let displayCode = item.code;
        if (displayCode.startsWith('sh') || displayCode.startsWith('sz')) {
            displayCode = displayCode.substring(2);
        }
        
        itemElement.innerHTML = `
            <div class="etf-name">${item.name}</div>
            <div class="etf-code">${displayCode}</div>
        `;
        
        // 添加数据属性，用于悬浮卡片显示
        itemElement.dataset.manager = item.manager;
        itemElement.dataset.business = item.is_business ? 'true' : 'false';
        itemElement.dataset.businessText = item.business_text;
        itemElement.dataset.index = item.index_code;
        itemElement.dataset.scale = item.scale;
        
        // 根据推荐类型设置不同的变化值
        if (type === 'attention') {
            itemElement.dataset.change = `+${item.attention_change.toLocaleString()} 人`;
        } else if (type === 'holders') {
            itemElement.dataset.change = `+${item.holders_change.toLocaleString()} 人`;
        } else if (type === 'amount') {
            itemElement.dataset.change = `+${item.amount_change.toFixed(2)} 亿元`;
        } else if (type === 'price-return') {
            itemElement.dataset.change = `${item.daily_return.toFixed(2)}%`;
        }
        
        // 绑定点击事件
        itemElement.addEventListener('click', function() {
            handleRecommendationClick(this);
        });
        
        // 绑定鼠标悬停事件
        itemElement.addEventListener('mouseenter', function() {
            showRecommendationTooltip(this);
        });
        
        itemElement.addEventListener('mouseleave', function() {
            hideRecommendationTooltip();
        });
        
        container.appendChild(itemElement);
    });
}

// 处理推荐项点击
function handleRecommendationClick(item) {
    // 获取ETF代码
    const code = item.dataset.code;
    
    // 处理可能带有sh/sz前缀的ETF代码
    let searchCode = code;
    if (searchCode.startsWith('sh') || searchCode.startsWith('sz')) {
        searchCode = searchCode.substring(2);
    }
    
    // 移除所有选中状态
    document.querySelectorAll('.recommendation-item').forEach(i => {
        i.classList.remove('selected');
    });
    
    // 添加选中状态
    item.classList.add('selected');
    
    // 填充搜索框
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = searchCode;
    }
    
    // 触发搜索
    searchETF();
    
    // 移除淡出和隐藏推荐栏的代码，保持推荐栏一直显示
    // const recommendationContainer = document.getElementById('recommendation-container');
    // recommendationContainer.classList.add('fade-out');
    // 
    // // 3秒后隐藏并移除淡出类
    // setTimeout(() => {
    //     recommendationContainer.style.display = 'none';
    //     recommendationContainer.classList.remove('fade-out');
    // }, 3000);
}

// 显示推荐项悬浮卡片
function showRecommendationTooltip(item) {
    const tooltip = document.getElementById('recommendation-tooltip');
    const tooltipManager = document.getElementById('tooltip-manager');
    const tooltipBusiness = document.getElementById('tooltip-business');
    const tooltipIndex = document.getElementById('tooltip-index');
    const tooltipScale = document.getElementById('tooltip-scale');
    const tooltipChange = document.getElementById('tooltip-change');
    const tooltipChangeContainer = document.getElementById('tooltip-change-container');
    
    // 设置悬浮卡片内容
    tooltipManager.textContent = item.dataset.manager;
    tooltipBusiness.textContent = item.dataset.businessText;
    tooltipBusiness.className = item.dataset.business === 'true' ? 'badge badge-business' : 'badge badge-non-business';
    tooltipIndex.textContent = item.dataset.index;
    tooltipScale.textContent = item.dataset.scale;
    
    // 根据推荐类型设置变化值标题
    const type = item.dataset.type;
    const changeTitle = document.querySelector('#tooltip-change-container small');
    if (type === 'attention') {
        changeTitle.textContent = '本周新增关注: ';
    } else if (type === 'holders') {
        changeTitle.textContent = '本周新增持仓: ';
    } else if (type === 'amount') {
        changeTitle.textContent = '本周新增保有: ';
    } else if (type === 'price-return') {
        changeTitle.textContent = '当日涨幅: ';
    }
    
    tooltipChange.textContent = item.dataset.change;
    
    // 显示悬浮卡片
    tooltip.style.display = 'block';
    
    // 设置悬浮卡片位置
    const rect = item.getBoundingClientRect();
    tooltip.style.left = (rect.right + 10) + 'px';
    tooltip.style.top = rect.top + 'px';
}

// 隐藏推荐项悬浮卡片
function hideRecommendationTooltip() {
    const tooltip = document.getElementById('recommendation-tooltip');
    tooltip.style.display = 'none';
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
    
    // 绑定搜索输入框事件
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        console.log('找到搜索输入框，绑定事件');
        // 回车事件
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchETF();
            }
        });
        
        // 移除获取焦点时显示推荐栏的事件，因为我们会在页面加载时就显示推荐栏
        // searchInput.addEventListener('focus', function() {
        //     loadRecommendations();
        // });
    } else {
        console.error('未找到搜索输入框');
    }
    
    // 初始化推荐栏
    initRecommendations();
    
    // 加载推荐数据
    loadRecommendations();
    
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