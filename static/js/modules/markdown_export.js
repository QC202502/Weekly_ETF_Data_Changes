/**
 * Markdown导出功能模块
 */

// 生成Markdown内容
export function generateMarkdown(data) {
    console.log('生成Markdown内容:', data);
    console.log('search_type:', data.search_type);
    console.log('是否有index_groups:', data.index_groups ? '是' : '否');
    if (data.index_groups) {
        console.log('index_groups长度:', data.index_groups.length);
    }
    
    if (!data || data.error) {
        return '无法生成Markdown：没有有效的搜索结果';
    }
    
    // 获取数据截止日期，如果存在就使用，否则使用当前日期
    const dataDate = data.data_date || new Date().toISOString().split('T')[0].replace(/-/g, '.');
    
    // 根据搜索类型生成不同的标题和描述
    let title, description;
    let date = new Date().toISOString().split('T')[0]; // 当前日期，格式为YYYY-MM-DD
    let tags = [];
    
    // 添加ETF标签
    tags.push('ETF');
    
    // 如果有关键词，添加到标签
    if (data.keyword) {
        tags.push(data.keyword);
    }
    
    // 根据搜索类型和数据内容生成标题和描述
    if (data.search_type === "ETF基金代码" && data.index_name) {
        // 输入产品代码时
        title = `${data.index_name}，有哪些选择？`;
        description = `目前，全市场共有相关的${data.etf_count}只ETF。哪只规模大？哪只交易量大？哪只费率便宜？这就为你揭晓！`;
    } else if (data.index_groups && data.index_groups.length > 0) {
        // 如果有指数组数据，无论search_type是什么
        const indexCount = data.index_count || data.index_groups.length;
        const totalEtfCount = data.count || data.index_groups.reduce((sum, group) => sum + group.etf_count, 0);
        title = `${data.keyword}相关ETF，有哪些选择？`;
        description = `目前，全市场共有相关的${indexCount}个指数和${totalEtfCount}只ETF。哪只规模大？哪只交易量大？哪只费率便宜？这就为你揭晓！`;
        console.log(`生成指数分组的标题: ${title}`);
        console.log(`指数组数量: ${indexCount}, ETF总数: ${totalEtfCount}`);
    } else {
        // 其他搜索类型
        title = `${data.keyword}相关ETF，有哪些选择？`;
        description = `目前，全市场共有相关的${data.count || 0}只ETF。哪只规模大？哪只交易量大？哪只费率便宜？这就为你揭晓！`;
    }
    
    // 构建Markdown头部
    let markdown = `---\ntitle: ${title}\ndescription: ${description}\ntags: ${tags.join(', ')}\ndate: ${date}\nimage: https://images.unsplash.com/photo-1499750310107-5fef28a66643?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=500&q=80\n\n---\n-\n\n`;
    
    // 如果有关键词，添加关键词为一级标题
    if (data.keyword) {
        markdown += `# ${data.keyword}\n\n`;
    }
    
    // 根据数据内容生成不同的内容
    if (data.index_groups && data.index_groups.length > 0) {
        // 如果有指数组数据，无论search_type是什么
        markdown += generateIndexGroupsMarkdown(data.index_groups);
    } else if (data.search_type === "ETF基金代码" && data.results) {
        markdown += generateETFCodeMarkdown(data);
    } else if (data.results) {
        markdown += generateGeneralMarkdown(data);
    }
    
    // 添加免责声明和数据来源说明，使用动态数据截止日期
    markdown += `\n\n> 数据来源：Wind ${dataDate}。相关内容仅供参考，不作为投资建议，请自行决策，并以基金公告为准。月日均交易量为数据截止日前30日平均日交易量，单位为亿元；总规模为最新基金定期报告中数据，单位为亿元；管理费率单位为 %。`;
    
    return markdown;
}

// 生成指数分组的Markdown
function generateIndexGroupsMarkdown(indexGroups) {
    console.log('生成指数分组的Markdown，组数:', indexGroups.length);
    
    // 调试第一个指数组
    if (indexGroups.length > 0) {
        const firstGroup = indexGroups[0];
        console.log('第一个指数组:', {
            name: firstGroup.index_name,
            code: firstGroup.index_code,
            etf_count: firstGroup.etf_count,
            total_scale: firstGroup.total_scale,
            etfs_length: firstGroup.etfs ? firstGroup.etfs.length : 0
        });
        
        // 调试第一个ETF
        if (firstGroup.etfs && firstGroup.etfs.length > 0) {
            console.log('第一个ETF示例:', firstGroup.etfs[0]);
        }
    }
    
    let markdown = '';
    
    // 对指数组按规模大小排序
    indexGroups.sort((a, b) => b.total_scale - a.total_scale);
    
    // 处理每个指数组
    indexGroups.forEach((group, index) => {
        // 确保总规模是数字类型并有合理默认值
        const totalScale = typeof group.total_scale === 'number' ? group.total_scale : 0;
        
        // 添加带序号的二级标题
        markdown += `## **${index + 1}. ${group.index_name || '未知指数'} (${group.index_code || '无代码'})**\n`;
        markdown += `|**总规模: ${totalScale.toFixed(2)}亿元 , ETF数量: ${group.etf_count || 0}**|\n`;
        markdown += `|:-----|\n`;
        markdown += `|${getIndexDescription(group.index_code, group.index_intro)}|\n\n`;
        
        // 检查是否有ETF数据
        if (!group.etfs || group.etfs.length === 0) {
            markdown += '暂无相关ETF产品数据\n\n';
            return; // 跳过当前循环
        }
        
        // 添加ETF表格
        markdown += `|产品代码|产品简称|管理人|月日均交易量|总规模|管理费率|\n`;
        markdown += `|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|\n`;

        try {
            // 找出总规模最大和交易量最大的ETF
            let maxFundSizeETF = [...group.etfs].sort((a, b) => 
                (Number(b.fund_size || 0) - Number(a.fund_size || 0)))[0] || null;
            
            let maxVolumeETF = [...group.etfs].sort((a, b) => 
                (Number(b.daily_avg_volume || 0) - Number(a.daily_avg_volume || 0)))[0] || null;
            
            // 找出管理费率最低的ETF组
            let minFeeETFs = [...group.etfs].sort((a, b) => 
                (Number(a.management_fee_rate || 0) - Number(b.management_fee_rate || 0)));
            
            // 获取最低费率
            const lowestFee = minFeeETFs.length > 0 ? Number(minFeeETFs[0].management_fee_rate || 0) : 0;
            
            // 筛选所有具有最低费率的ETF
            const lowestFeeETFs = minFeeETFs.filter(etf => 
                Number(etf.management_fee_rate || 0) === lowestFee);
            
            // 在最低费率组中，找出交易量最大的
            let minFeeHighlightETF = lowestFeeETFs.length > 0 ? 
                lowestFeeETFs.sort((a, b) => 
                    Number(b.daily_avg_volume || 0) - Number(a.daily_avg_volume || 0))[0] : 
                (group.etfs.length > 0 ? group.etfs[0] : null);
            
            // 按区间日均成交额从高到低排序后添加ETF
            const sortedETFs = [...group.etfs].sort((a, b) => {
                const volumeA = Number(a.daily_avg_volume || 0);
                const volumeB = Number(b.daily_avg_volume || 0);
                return volumeB - volumeA;
            });
            
            // 简化公司名称的辅助函数
            const simplifyCompany = (company) => {
                if (!company) return '';
                // 删除"基金"及其后面的字符
                return company.replace(/基金.*$/, '');
            };
            
            // 移除代码后缀的辅助函数
            const removeCodeSuffix = (code) => {
                if (!code) return '';
                return code.replace(/\.(SZ|SH|BJ)$/i, '');
            };
            
            // 添加ETF行
            sortedETFs.forEach(etf => {
                try {
                    // 确保所有字段都有合理的默认值
                    const etfSafe = {
                        code: etf.code || '',
                        name: etf.name || '',
                        manager: etf.manager || etf.fund_manager || '',
                        daily_avg_volume: Number(etf.daily_avg_volume || 0),
                        fund_size: Number(etf.fund_size || 0),
                        management_fee_rate: Number(etf.management_fee_rate || 0)
                    };
                    
                    // 检查是否需要高亮
                    const isMinFeeHighlight = minFeeHighlightETF && etf.code === minFeeHighlightETF.code;
                    const isMaxSizeHighlight = maxFundSizeETF && etf.code === maxFundSizeETF.code;
                    const isMaxVolumeHighlight = maxVolumeETF && etf.code === maxVolumeETF.code;
                    
                    // 处理基本字段
                    const displayCode = removeCodeSuffix(etfSafe.code);
                    const code = (isMaxSizeHighlight || isMaxVolumeHighlight || isMinFeeHighlight) ? 
                        `==${displayCode}==` : displayCode;
                    
                    const volume = isMaxVolumeHighlight ? 
                        `==${etfSafe.daily_avg_volume.toFixed(2)}==` : 
                        etfSafe.daily_avg_volume.toFixed(2);
                    
                    const size = isMaxSizeHighlight ? 
                        `==${etfSafe.fund_size.toFixed(1)}==` : 
                        etfSafe.fund_size.toFixed(1);
                        
                    const fee = isMinFeeHighlight ? 
                        `==${etfSafe.management_fee_rate.toFixed(2)}==` : 
                        etfSafe.management_fee_rate.toFixed(2);
                    
                    markdown += `|${code}|${etfSafe.name}|${etfSafe.manager_short || simplifyCompany(etfSafe.manager)}|${volume}|${size}|${fee}|\n`;
                } catch (innerError) {
                    console.error('处理ETF行时出错:', innerError, etf);
                    // 添加错误处理的行，确保不会中断整个表格
                    markdown += `|${etf.code || ''}|${etf.name || ''}|${etf.manager || ''}|0.00|0.0|0.00%|\n`;
                }
            });
        } catch (error) {
            console.error('生成指数组表格时出错:', error, group);
            markdown += '处理ETF数据时出错\n';
        }
        
        markdown += '\n';
    });
    
    return markdown;
}

// 生成ETF代码搜索的Markdown
function generateETFCodeMarkdown(data) {
    // 添加调试信息
    console.log('生成ETF代码Markdown，data对象:', JSON.stringify(data, null, 2));
    console.log('data.index_name:', data.index_name);
    console.log('data.index_code:', data.index_code);
    console.log('data.total_scale:', data.total_scale);
    console.log('data.etf_count:', data.etf_count);
    console.log('data.results长度:', data.results ? data.results.length : 0);
    console.log('data.related_etfs长度:', data.related_etfs ? data.related_etfs.length : 0);
    
    // 检查关键属性是否存在
    if (!data.index_name || !data.index_code || data.total_scale === undefined) {
        console.error('ETF代码Markdown生成失败：缺少必要属性');
        return '无法生成Markdown：数据不完整，缺少指数名称、代码或总规模信息';
    }
    
    // 移除序号，直接从二级标题开始
    let markdown = `## **${data.index_name} (${data.index_code})**\n`;
    markdown += `|**总规模: ${(data.total_scale || 0).toFixed(2)}亿元 , ETF数量: ${data.etf_count || 0}**|\n`;
    markdown += `|:-----|\n`;
    markdown += `|${getIndexDescription(data.index_code, data.index_intro)}|\n\n`;
    
    // 合并主ETF和同指数ETF
    let allETFs = [...(data.results || [])];
    if (data.related_etfs && data.related_etfs.length > 0) {
        allETFs = allETFs.concat(data.related_etfs);
    }
    
    // 按区间日均成交额从高到低排序
    allETFs.sort((a, b) => {
        const volumeA = Number(a.daily_avg_volume || 0);
        const volumeB = Number(b.daily_avg_volume || 0);
        return volumeB - volumeA;
    });
    
    // 添加ETF表格
    markdown += generateETFTableForGroup(allETFs);
    
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
    markdown += generateETFTableForGroup(data.results);
    
    return markdown;
}

// 为指数组生成ETF表格
function generateETFTableForGroup(etfs) {
    if (!etfs || etfs.length === 0) {
        return '暂无相关ETF产品数据\n';
    }
    
    let markdown = '';
    
    // 创建表头
    markdown += `|产品代码|产品简称|管理人|月日均交易量|总规模|管理费率|\n`;
    markdown += `|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|\n`;
    
    // 简化公司名称的辅助函数
    const simplifyCompany = (company) => {
        if (!company) return '';
        // 删除"基金"及其后面的字符
        return company.replace(/基金.*$/, '');
    };
    
    // 移除代码后缀的辅助函数
    const removeCodeSuffix = (code) => {
        if (!code) return '';
        return code.replace(/\.(SZ|SH|BJ)$/i, '');
    };
    
    // 找出总规模最大和交易量最大的ETF
    let maxFundSizeETF = [...etfs].sort((a, b) => 
        (Number(b.fund_size || 0) - Number(a.fund_size || 0)))[0] || null;
    
    let maxVolumeETF = [...etfs].sort((a, b) => 
        (Number(b.daily_avg_volume || 0) - Number(a.daily_avg_volume || 0)))[0] || null;
    
    // 找出管理费率最低的ETF组
    let minFeeETFs = [...etfs].sort((a, b) => 
        (Number(a.management_fee_rate || 0) - Number(b.management_fee_rate || 0)));
    
    // 获取最低费率
    const lowestFee = minFeeETFs.length > 0 ? Number(minFeeETFs[0].management_fee_rate || 0) : 0;
    
    // 筛选所有具有最低费率的ETF
    const lowestFeeETFs = minFeeETFs.filter(etf => 
        Number(etf.management_fee_rate || 0) === lowestFee);
    
    // 在最低费率组中，找出交易量最大的
    let minFeeHighlightETF = lowestFeeETFs.length > 0 ? 
        lowestFeeETFs.sort((a, b) => 
            Number(b.daily_avg_volume || 0) - Number(a.daily_avg_volume || 0))[0] : 
        (etfs.length > 0 ? etfs[0] : null);
    
    // 添加ETF行
    etfs.forEach(etf => {
        // 检查是否需要高亮
        const isMinFeeHighlight = minFeeHighlightETF && etf.code === minFeeHighlightETF.code;
        const isMaxSizeHighlight = maxFundSizeETF && etf.code === maxFundSizeETF.code;
        const isMaxVolumeHighlight = maxVolumeETF && etf.code === maxVolumeETF.code;
        
        // 处理基本字段
        const displayCode = removeCodeSuffix(etf.code);
        // 修改：确保费率最低中交易量最高的产品代码也被高亮
        const code = (isMaxSizeHighlight || isMaxVolumeHighlight || isMinFeeHighlight) ? 
            `==${displayCode}==` : displayCode;
        
        const volume = isMaxVolumeHighlight ? 
            `==${Number(etf.daily_avg_volume || 0).toFixed(2)}==` : 
            Number(etf.daily_avg_volume || 0).toFixed(2);
        
        const size = isMaxSizeHighlight ? 
            `==${Number(etf.fund_size || 0).toFixed(1)}==` : 
            Number(etf.fund_size || 0).toFixed(1);
            
        const fee = isMinFeeHighlight ? 
            `==${Number(etf.management_fee_rate || 0).toFixed(2)}==` : 
            Number(etf.management_fee_rate || 0).toFixed(2);
        
        markdown += `|${code}|${etf.name}|${etf.manager_short || simplifyCompany(etf.manager)}|${volume}|${size}|${fee}|\n`;
    });
    
    return markdown;
}

// 获取指数描述（从搜索结果中获取）
function getIndexDescription(indexCode, indexIntro) {
    console.log('获取指数描述, 指数代码:', indexCode, '传入简介:', indexIntro ? '有' : '无');
    
    // 首先尝试使用传入的指数简介
    if (indexIntro) {
        return indexIntro;
    }
    
    // 从当前搜索结果中获取指数简介
    const searchResultsData = window.currentSearchResults;
    console.log('搜索结果类型:', searchResultsData ? searchResultsData.search_type : '无搜索结果');
    
    // 检查是否有搜索结果数据
    if (searchResultsData) {
        // 如果是ETF基金代码搜索结果，直接使用index_intro
        if (searchResultsData.search_type === "ETF基金代码" && 
            searchResultsData.index_code === indexCode && 
            searchResultsData.index_intro) {
            return searchResultsData.index_intro;
        }
        
        // 如果是指数名称搜索结果，在index_groups中查找
        if (searchResultsData.index_groups) {
            // 在指数组中查找匹配的指数代码
            const matchedGroup = searchResultsData.index_groups.find(group => 
                group.index_code === indexCode);
            
            console.log('匹配的指数组:', matchedGroup ? '找到' : '未找到');
            
            if (matchedGroup && matchedGroup.index_intro) {
                console.log('使用指数组中的简介');
                return matchedGroup.index_intro;
            }
        }
    }
    
    // 如果在搜索结果中找不到，则使用默认描述
    console.log('使用默认描述');
    return `${indexCode}指数是一个跟踪特定市场或行业的指数，由一系列符合特定条件的股票组成，用于反映该市场或行业的整体表现。`;
}