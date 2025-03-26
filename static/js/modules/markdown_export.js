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

// 获取指数描述（示例函数，实际应从数据库或API获取）
function getIndexDescription(indexCode) {
    // 这里应该根据指数代码获取实际描述
    // 为了演示，使用一些示例描述
    const descriptions = {
        '000015.SH': '上证红利指数挑选在上证所上市的现金股息率高、分红比较稳定、具有一定规模及流动性的50只股票作为样本，以反映上海证券市场高红利股票的整体状况和走势。',
        '000922.CSI': '中证红利指数根据股息率指标，精选在上海证券交易所和深圳证券交易所上市的现金股息率高、分红比较稳定、具有一定规模及流动性的100只股票作为样本，以反映A股市场高红利股票的整体状况和走势。',
        '000300.SH': '沪深300指数由沪深两市规模大、流动性好、最具代表性的300只股票组成，综合反映中国A股市场上市股票价格的整体表现。',
        '000905.SH': '中证500指数由全部A股中剔除沪深300指数成份股及总市值排名前300名的股票后，总市值排名靠前的500只股票组成，综合反映中国A股市场中小市值公司的股票价格表现。',
        '000852.SH': '中证1000指数从全部A股中剔除市值排名在前1000名的股票后，选取市值排名靠前的1000只股票组成，反映A股市场中小市值公司的股票价格表现。',
        '399006.SZ': '创业板指数由创业板市场规模大、流动性好的100家上市公司组成，反映创业板市场层次的运行情况。',
        '399673.SZ': '创业板50指数由创业板市场规模大、流动性好的50家上市公司组成，反映创业板市场最具代表性的上市公司整体表现。',
        '000688.SH': '科创50指数由科创板市场规模大、流动性好的50家上市公司组成，反映科创板市场最具代表性的上市公司整体表现。',
        '399989.SZ': '中证医疗指数从主营业务属于医疗保健行业的上市公司中，选取规模大、流动性好的100家公司组成，反映医疗保健行业上市公司的整体表现。',
        '000991.SH': '中证消费指数从主营业务属于可选消费或主要消费行业的上市公司中，选取规模大、流动性好的80家公司组成，反映消费类上市公司的整体表现。',
        '000993.SH': '中证信息技术指数从主营业务属于信息技术行业的上市公司中，选取规模大、流动性好的100家公司组成，反映信息技术行业上市公司的整体表现。'
    };
    
    return descriptions[indexCode] || `${indexCode}指数是一个跟踪特定市场或行业的指数，由一系列符合特定条件的股票组成，用于反映该市场或行业的整体表现。`;
}