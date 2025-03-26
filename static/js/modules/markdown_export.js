/**
 * Markdown导出功能模块
 */

// 生成Markdown内容
export function generateMarkdown(data) {
    console.log('生成Markdown内容:', data);
    
    if (!data || data.error) {
        return '无法生成Markdown：没有有效的搜索结果';
    }
    
    // 根据搜索类型生成不同的标题和描述
    let title, description;
    let date = new Date().toISOString().split('T')[0]; // 当前日期，格式为YYYY-MM-DD
    let tags = [];
    
    // 添加ETF标签
    tags.push('ETF');
    
    // 根据搜索类型生成标题和描述
    if (data.search_type === "ETF基金代码" && data.index_name) {
        // 输入产品代码时
        title = `${data.index_name}，有哪些选择？`;
        description = `目前，全市场共有相关的${data.etf_count}只ETF。哪只规模大？哪只交易量大？哪只费率便宜？这就为你揭晓！`;
        tags.push(data.index_name);
    } else if (data.search_type === "跟踪指数名称" && data.index_groups) {
        // 输入关键词时
        title = `${data.keyword}相关ETF，有哪些选择？`;
        description = `目前，全市场共有相关的${data.index_count}个指数和${data.count}只ETF。哪只规模大？哪只交易量大？哪只费率便宜？这就为你揭晓！`;
        tags.push(data.keyword);
    } else {
        // 其他搜索类型
        title = `${data.keyword}相关ETF，有哪些选择？`;
        description = `目前，全市场共有相关的${data.count}只ETF。哪只规模大？哪只交易量大？哪只费率便宜？这就为你揭晓！`;
        tags.push(data.keyword);
    }
    
    // 构建Markdown头部
    let markdown = `---\ntitle: ${title}\ndescription: ${description}\ntags: ${tags.join(', ')}\ndate: ${date}\nimage: https://images.unsplash.com/photo-1499750310107-5fef28a66643?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=500&q=80\n\n---\n-\n\n`;
    
    // 根据搜索类型生成不同的内容
    if (data.search_type === "跟踪指数名称" && data.index_groups) {
        markdown += generateIndexGroupsMarkdown(data.index_groups);
    } else if (data.search_type === "ETF基金代码" && data.results) {
        markdown += generateETFCodeMarkdown(data);
    } else if (data.results) {
        markdown += generateGeneralMarkdown(data);
    }
    
    // 不再添加结尾分隔符
    return markdown;
}

// 生成指数分组的Markdown
function generateIndexGroupsMarkdown(indexGroups) {
    let markdown = '';
    
    // 为每个指数创建一个部分
    indexGroups.forEach((group, index) => {
        // 移除一级标题
        markdown += `## **${index + 1}. ${group.index_name} (${group.index_code})**\n`;
        markdown += `|**总规模: ${group.total_scale}亿元 , ETF数量: ${group.etf_count}**|\n`;
        markdown += `|:-----|\n`;
        markdown += `|${getIndexDescription(group.index_code)}|\n\n`;
        
        // 添加ETF表格
        markdown += generateETFTableMarkdown(group.etfs);
        markdown += '\n';
    });
    
    return markdown;
}

// 生成ETF代码搜索的Markdown
function generateETFCodeMarkdown(data) {
    // 移除一级标题和序号，直接从二级标题开始
    let markdown = `## **${data.index_name} (${data.index_code})**\n`;
    markdown += `|**总规模: ${data.total_scale}亿元 , ETF数量: ${data.etf_count}**|\n`;
    markdown += `|:-----|\n`;
    markdown += `|${getIndexDescription(data.index_code)}|\n\n`;
    
    // 添加ETF表格
    markdown += generateETFTableMarkdown(data.results);
    
    return markdown;
}

// 生成通用搜索的Markdown
function generateGeneralMarkdown(data) {
    // 移除一级标题，直接从二级标题开始
    let markdown = `## **相关ETF产品**\n`;
    markdown += `|**总数量: ${data.count}只**|\n`;
    markdown += `|:-----|\n`;
    markdown += `|以下是与"${data.keyword}"相关的ETF产品|\n\n`;
    
    // 添加ETF表格
    markdown += generateETFTableMarkdown(data.results);
    
    return markdown;
}

// 生成ETF表格的Markdown
function generateETFTableMarkdown(etfs) {
    if (!etfs || etfs.length === 0) {
        return '无相关ETF产品';
    }
    
    // 找出交易量最大、规模最大和费率最低的ETF
    let maxVolumeETF = etfs[0];
    let maxScaleETF = etfs[0];
    let minFeeRateETF = etfs[0];
    
    etfs.forEach(etf => {
        if (etf.volume > maxVolumeETF.volume) {
            maxVolumeETF = etf;
        }
        if (etf.scale > maxScaleETF.scale) {
            maxScaleETF = etf;
        }
        if (etf.fee_rate < minFeeRateETF.fee_rate) {
            minFeeRateETF = etf;
        }
    });
    
    // 找出费率最低且交易量最大的ETF
    // 先找出所有费率最低的ETF
    let minFeeRateETFs = etfs.filter(etf => etf.fee_rate === minFeeRateETF.fee_rate);
    
    // 如果有多个费率相同的ETF，选择交易量最大的
    let minFeeMaxVolumeETF = minFeeRateETFs.reduce((max, etf) => 
        etf.volume > max.volume ? etf : max, minFeeRateETFs[0]);
    
    // 确定需要高亮的ETF
    // 在交易量最大、规模最大和费率最低中选择交易量最大的作为高亮ETF
    let volumeRank = [maxVolumeETF];
    if (maxScaleETF.volume > 0 && maxScaleETF !== maxVolumeETF) {
        volumeRank.push(maxScaleETF);
    }
    if (minFeeRateETF.volume > 0 && minFeeRateETF !== maxVolumeETF && minFeeRateETF !== maxScaleETF) {
        volumeRank.push(minFeeRateETF);
    }
    
    // 按交易量排序
    volumeRank.sort((a, b) => b.volume - a.volume);
    
    // 交易量最大的ETF作为高亮ETF
    let highlightETF = volumeRank[0];
    
    // 创建表格头部
    let markdown = '|产品代码|产品简称|管理人|月日均交易量|总规模|管理费率|\n';
    markdown += '|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|\n';
    
    // 添加ETF行
    etfs.forEach(etf => {
        // 处理管理人名称，移除"基金"后缀
        let manager = etf.manager.replace(/基金(管理有限)?公司$|基金$|资产管理$|证券$/, '');
        
        // 使用下划线标记高亮ETF
        let code = (etf === highlightETF || etf === minFeeMaxVolumeETF) ? `==${etf.code}==` : etf.code;
        let volume = etf === maxVolumeETF ? `==${etf.volume.toFixed(2)}==` : etf.volume.toFixed(2);
        let scale = etf === maxScaleETF ? `==${etf.scale.toFixed(2)}==` : etf.scale.toFixed(2);
        let feeRate = etf === minFeeRateETF ? `==${etf.fee_rate.toFixed(2)}%==` : `${etf.fee_rate.toFixed(2)}%`;
        
        markdown += `|${code}|${etf.name}|${manager}|${volume}|${scale}|${feeRate}|\n`;
    });
    
    return markdown;
}

// 获取指数描述（从搜索结果中获取）
function getIndexDescription(indexCode) {
    // 从当前搜索结果中获取指数简介
    const searchResultsData = window.currentSearchResults;
    
    // 检查是否有搜索结果数据
    if (searchResultsData) {
        // 如果是ETF基金代码搜索结果，直接使用index_intro
        if (searchResultsData.search_type === "ETF基金代码" && 
            searchResultsData.index_code === indexCode && 
            searchResultsData.index_intro) {
            return searchResultsData.index_intro;
        }
        
        // 如果是指数名称搜索结果，在index_groups中查找
        if (searchResultsData.search_type === "跟踪指数名称" && 
            searchResultsData.index_groups) {
            // 在指数组中查找匹配的指数代码
            const matchedGroup = searchResultsData.index_groups.find(group => 
                group.index_code === indexCode);
            
            if (matchedGroup && matchedGroup.index_intro) {
                return matchedGroup.index_intro;
            }
        }
    }
    
    // 如果在搜索结果中找不到，则使用默认描述
    return `${indexCode}指数是一个跟踪特定市场或行业的指数，由一系列符合特定条件的股票组成，用于反映该市场或行业的整体表现。`;
}