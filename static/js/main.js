/**
 * 主入口文件
 * 负责导入各个模块并初始化应用
 * 版本: 1.0.2 (2025-04-04) - 添加持仓人数和持仓价值支持
 */

// 版本日志
console.log('ETF分析平台 v1.0.2 (2025-04-04) - 添加持仓人数和持仓价值支持');

import { showLoading, hideLoading, showMessage, showSection } from './modules/utils.js';
import { searchETF, handleSearchResult } from './modules/search.js';
import { loadData, loadOverview, loadBusinessAnalysis, generateReport } from './modules/data.js';
import { initRecommendations, loadRecommendations } from './modules/recommendation.js';
import { generateMarkdown } from './modules/markdown_export.js';

// 全局错误处理，捕获JSON解析错误和HTTP错误
window.addEventListener('error', function(event) {
    console.log('捕获到错误:', event.message);
    
    // 捕获JSON解析错误
    if (event.message && event.message.indexOf('SyntaxError') !== -1 && 
        event.message.indexOf('JSON') !== -1) {
        console.error('捕获到JSON解析错误:', event);
        
        // 隐藏原始错误提示
        hideErrorBanner();
        
        // 显示友好的错误提示
        showMessage('warning', '数据加载出错，请刷新页面或点击"刷新数据"按钮');
        
        // 阻止错误显示在控制台
        event.preventDefault();
        return;
    }
    
    // 捕获HTTP 404错误
    if (event.message && 
        (event.message.indexOf('404') !== -1 || 
         event.message.indexOf('HTTP错误') !== -1)) {
        console.error('捕获到HTTP错误:', event);
        
        // 处理HTTP错误
        window.handleHttpError(event.message);
        
        // 阻止错误显示在控制台
        event.preventDefault();
        return;
    }
});

// 隐藏错误提示横幅
function hideErrorBanner() {
    const errorBanners = document.querySelectorAll('.alert-danger');
    errorBanners.forEach(banner => {
        banner.style.display = 'none';
    });
}

// 添加HTTP错误的特殊处理
window.handleHttpError = function(message) {
    console.error('HTTP错误:', message);
    
    // 隐藏可能存在的错误提示
    hideErrorBanner();
    
    // 获取状态区域并更新
    const statusArea = document.getElementById('status-message') || document.getElementById('statusMessage');
    if (statusArea) {
        statusArea.textContent = '';
        statusArea.style.display = 'none';
    }
    
    // 显示友好的错误提示
    showMessage('warning', '服务器连接错误，请确认服务是否正常运行');
}

// 全局变量，用于跟踪当前排序状态
window.currentSortBy = 'total_holding_value'; // 默认与后端一致
window.currentOrder = 'desc'; // 默认与后端一致

// 更新排序指示器的函数
function updateSortIndicators() {
    document.querySelectorAll('.sort-indicator').forEach(indicator => {
        const column = indicator.dataset.column;
        if (column === window.currentSortBy) {
            indicator.innerHTML = window.currentOrder === 'asc' ? '&#9650;' : '&#9660;'; // Up or Down arrow
            indicator.setAttribute('data-active', 'true');
        } else {
            indicator.innerHTML = ''; // Clear other indicators
            indicator.removeAttribute('data-active');
        }
    });
    
    // 高亮当前排序列
    highlightSortColumn();
}

// 表格排序函数
function sortCompanyTable(sortBy) {
    // 获取当前排序方向
    let order;
    
    // 如果点击的是当前排序列，则切换排序方向
    if (sortBy === window.currentSortBy) {
        order = window.currentOrder === 'asc' ? 'desc' : 'asc';
    } else {
        // 如果点击的是新列，默认使用升序
        order = 'asc';
    }
    
    // 发送AJAX请求到后端进行排序
    fetch(`/ajax_sort_company_analytics?sort_by=${encodeURIComponent(sortBy)}&order=${order}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json(); // 服务器返回JSON格式
        })
        .then(data => {
            if (data.error) {
                console.error('排序错误:', data.error);
                return;
            }
            
            // 更新表格内容 - 使用返回的HTML片段
            document.getElementById('company-analytics-tbody').innerHTML = data.html_fragment;
            
            // 更新当前排序状态
            window.currentSortBy = sortBy;
            window.currentOrder = order;
            
            // 更新排序指示器
            updateSortIndicators();
            
            // 重新应用动画和交互效果
            if (typeof reapplyProgressBars === 'function') {
                setTimeout(reapplyProgressBars, 100);
            }
            
            // 根据排序后的公司名称长度重新调整列宽度
            if (typeof adjustCompanyColumnWidth === 'function') {
                setTimeout(adjustCompanyColumnWidth, 150);
            }
            
            if (typeof emergencyFixRatioBars === 'function') {
                setTimeout(emergencyFixRatioBars, 300);
            }
            
            // 应用总管理规模四分位数着色
            if (typeof applyFundSizeQuartileColors === 'function') {
                setTimeout(applyFundSizeQuartileColors, 400);
            }
            
            // 应用总成交额四分位数着色
            if (typeof applyAmountQuartileColors === 'function') {
                setTimeout(applyAmountQuartileColors, 400);
            }
            
            console.log(`表格已按 ${sortBy} ${order === 'asc' ? '升序' : '降序'} 排序`);
        })
        .catch(error => {
            console.error('AJAX请求失败:', error);
        });
}

// 应用公司筛选逻辑
function applyCompanyFilter() {
    const filterInput = document.getElementById('company-filter');
    if (filterInput) {
        const filterText = filterInput.value.toLowerCase().trim();
        const rows = document.querySelectorAll('#company-analytics-tbody tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const companyNameCell = row.querySelector('td:nth-child(2)');
            if (companyNameCell) {
                const companyName = companyNameCell.textContent.toLowerCase();
                if (companyName.includes(filterText) || filterText === '') {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            }
        });
        
        // 更新筛选状态
        const filterCountBadge = document.getElementById('filter-count');
        if (filterCountBadge) {
            filterCountBadge.textContent = filterText ? `${visibleCount} / ${rows.length}` : `全部 ${rows.length}`;
            
            if (visibleCount === 0) {
                filterCountBadge.className = 'status-badge status-badge-danger';
            } else if (visibleCount < rows.length) {
                filterCountBadge.className = 'status-badge status-badge-warning';
            } else {
                filterCountBadge.className = 'status-badge status-badge-success';
            }
        }
    }
}

// 初始化商务品持仓价值相关的交互
function initBusinessValueInteractions() {
    console.log('初始化商务品持仓价值相关交互...');
    
    // 获取所有的商务品持仓价值列
    const holdingValueCells = document.querySelectorAll('.business-value-column');
    const holdingRatioCells = document.querySelectorAll('.business-ratio-column');
    
    // 为商务品持仓价值列添加悬停效果
    holdingValueCells.forEach(cell => {
        cell.addEventListener('mouseenter', () => {
            // 高亮显示该单元格
            cell.classList.add('highlight-hover');
            
            // 获取当前行
            const row = cell.closest('tr');
            if (row) {
                // 高亮显示对应的公司名称单元格
                const companyNameCell = row.querySelector('td:nth-child(2)');
                if (companyNameCell) {
                    companyNameCell.classList.add('highlight-hover');
                }
                
                // 高亮显示对应的商务品持仓价值占比单元格
                const ratioCell = row.querySelector('.business-ratio-column');
                if (ratioCell) {
                    ratioCell.classList.add('highlight-hover');
                }
            }
        });
        
        cell.addEventListener('mouseleave', () => {
            // 移除高亮效果
            cell.classList.remove('highlight-hover');
            
            // 移除其他单元格的高亮效果
            document.querySelectorAll('.highlight-hover').forEach(elem => {
                elem.classList.remove('highlight-hover');
            });
        });
    });
    
    // 也为持仓价值占比列添加相同的悬停效果
    holdingRatioCells.forEach(cell => {
        cell.addEventListener('mouseenter', () => {
            // 高亮显示该单元格
            cell.classList.add('highlight-hover');
            
            // 获取当前行
            const row = cell.closest('tr');
            if (row) {
                // 高亮显示对应的公司名称单元格
                const companyNameCell = row.querySelector('td:nth-child(2)');
                if (companyNameCell) {
                    companyNameCell.classList.add('highlight-hover');
                }
                
                // 高亮显示对应的商务品持仓价值单元格
                const valueCell = row.querySelector('.business-value-column');
                if (valueCell) {
                    valueCell.classList.add('highlight-hover');
                }
            }
        });
        
        cell.addEventListener('mouseleave', () => {
            // 移除高亮效果
            cell.classList.remove('highlight-hover');
            
            // 移除其他单元格的高亮效果
            document.querySelectorAll('.highlight-hover').forEach(elem => {
                elem.classList.remove('highlight-hover');
            });
        });
    });
    
    // 增强进度条动画效果 - 使用交错动画
    function animateProgressBars() {
        const ratioBarFills = document.querySelectorAll('.ratio-bar-fill');
        if (ratioBarFills.length === 0) {
            console.log('未找到比率条元素，无法应用动画');
            return;
        }
        
        console.log(`为${ratioBarFills.length}个进度条应用动画效果`);
        
        // 首先将所有进度条宽度重置为0
        ratioBarFills.forEach(bar => {
            bar.style.width = '0%';
        });
        
        // 然后使用staggered动画，依次显示进度条
        ratioBarFills.forEach((bar, index) => {
            const finalWidth = bar.getAttribute('data-width') || bar.parentElement.getAttribute('data-width');
            
            if (!finalWidth) {
                // 如果没有存储的宽度属性，从内联样式中提取
                const inlineWidth = bar.style.width;
                if (inlineWidth) {
                    // 存储原始宽度值以便动画
                    bar.setAttribute('data-width', inlineWidth);
                } else {
                    console.log(`进度条 #${index+1} 没有有效的宽度值`);
                    return;
                }
            }
            
            // 延迟每个进度条动画，创建瀑布效果
            setTimeout(() => {
                bar.style.width = finalWidth || bar.getAttribute('data-width');
            }, 100 + (index * 20)); // 基础延迟100ms，每个进度条增加20ms
        });
    }
    
    // 在排序操作后重新触发动画
    window.reinitProgressBars = animateProgressBars;
    
    // 执行初始动画
    setTimeout(animateProgressBars, 500);
    
    console.log('商务品持仓价值相关交互已初始化');
}

// 用于高亮当前排序列的函数
function highlightSortColumn() {
    // 清除所有高亮
    document.querySelectorAll('.company-analytics-table th').forEach(th => {
        th.classList.remove('active-sort');
    });
    
    // 添加高亮到当前排序列
    const currentColumn = document.querySelector(`.company-analytics-table th [data-column="${window.currentSortBy}"]`);
    if (currentColumn && currentColumn.parentElement) {
        currentColumn.parentElement.classList.add('active-sort');
        currentColumn.setAttribute('data-active', 'true');
    }
}

// Make sortCompanyTable globally accessible for inline onclick handlers
window.sortCompanyTable = sortCompanyTable;
window.applyCompanyFilter = applyCompanyFilter;
window.highlightSortColumn = highlightSortColumn;

// 初始化商务品持仓价值列动画效果
function initBusinessValueAnimations() {
    console.log('初始化商务品持仓价值列动画效果');
    
    // 获取所有进度条并应用动画
    const progressBars = document.querySelectorAll('.ratio-bar-fill');
    if (progressBars.length > 0) {
        console.log(`找到 ${progressBars.length} 个进度条，应用动画效果`);
        
        // 先将所有进度条设置为宽度0
        progressBars.forEach(bar => {
            const originalWidth = bar.style.width;
            bar.setAttribute('data-width', originalWidth);
            bar.style.width = '0%';
        });
        
        // 然后使用延迟动画依次显示进度条
        setTimeout(() => {
            progressBars.forEach((bar, index) => {
                setTimeout(() => {
                    const targetWidth = bar.getAttribute('data-width');
                    if (targetWidth) {
                        bar.style.width = targetWidth;
                    }
                }, index * 30); // 每个进度条延迟30ms，创建瀑布效果
            });
        }, 300); // 等待300ms后开始动画
    }
    
    // 应用数值高亮效果
    const valueColumns = document.querySelectorAll('.business-value-column .mono-value');
    if (valueColumns.length > 0) {
        console.log(`找到 ${valueColumns.length} 个数值列，应用高亮效果`);
        
        valueColumns.forEach((col, index) => {
            setTimeout(() => {
                col.classList.add('value-changed');
                // 1秒后移除动画类
                setTimeout(() => {
                    col.classList.remove('value-changed');
                }, 1000);
            }, index * 50);
        });
    }
}

// 在表格排序后重新应用动画
function reapplyBusinessAnimations() {
    console.log('重新应用商务品持仓价值列动画效果');
    setTimeout(initBusinessValueAnimations, 100);
}

// 重新应用进度条动画的函数
function reapplyProgressBars() {
    // 先获取所有进度条元素
    const ratioBarFills = document.querySelectorAll('.ratio-bar-fill, .percent-bar-fill');
    
    // 如果找不到元素，退出
    if (ratioBarFills.length === 0) {
        console.log('没有找到进度条元素');
        return;
    }
    
    console.log(`找到 ${ratioBarFills.length} 个进度条元素`);
    
    // 为所有进度条添加data-width属性（如果还没有）
    ratioBarFills.forEach(bar => {
        if (!bar.hasAttribute('data-width')) {
            // 从style.width中提取宽度
            const width = bar.style.width;
            if (width) {
                bar.setAttribute('data-width', width);
            }
        }
    });
    
    // 先将所有进度条宽度重置为0
    ratioBarFills.forEach(bar => {
        // 存储原始宽度（如果还没有存储）
        const originalWidth = bar.style.width;
        if (!bar.hasAttribute('data-width') && originalWidth) {
            bar.setAttribute('data-width', originalWidth);
        }
        // 重置宽度为0
        bar.style.width = '0%';
    });
    
    // 然后延迟依次显示
    setTimeout(() => {
        ratioBarFills.forEach((bar, index) => {
            setTimeout(() => {
                const targetWidth = bar.getAttribute('data-width');
                if (targetWidth) {
                    bar.style.width = targetWidth;
                }
            }, index * 50); // 每个进度条间隔50ms
        });
    }, 300); // 整体延迟300ms
}

// 完全重新初始化表格所有进度条动画效果的函数
function fullResetProgressBars() {
    console.log('执行完全进度条重置操作...');
    
    // 强制暂停一下让DOM更新
    setTimeout(() => {
        // 获取所有进度条容器元素
        const ratioContainers = document.querySelectorAll('.ratio-bar, .percent-bar');
        console.log(`找到 ${ratioContainers.length} 个进度条容器`);
        
        if (ratioContainers.length === 0) return;
        
        // 从ratio-container匹配数据源获取真实数值
        ratioContainers.forEach((container, index) => {
            // 1. 查找该行对应的文本百分比值
            const row = container.closest('tr');
            if (!row) return;
            
            // 判断是哪种类型的进度条
            let percentText = '';
            let percentValue = 0;
            let barFill = container.querySelector('.ratio-bar-fill, .percent-bar-fill');
            
            if (!barFill) {
                console.log(`进度条#${index}没有填充元素`);
                return;
            }
            
            // 查找百分比文本(针对不同类型进度条位置不同)
            if (container.classList.contains('ratio-bar')) {
                // 商务品持仓价值占比
                const valueSpan = row.querySelector('.ratio-value');
                if (valueSpan) {
                    percentText = valueSpan.textContent.trim();
                }
            } else if (container.classList.contains('percent-bar')) {
                // 常规百分比列
                const cell = container.closest('td');
                if (cell) {
                    const valueSpan = cell.querySelector('.percent-value');
                    if (valueSpan) {
                        percentText = valueSpan.textContent.trim();
                    }
                }
            }
            
            // 从文本中提取数值
            if (percentText) {
                percentText = percentText.replace('%', '').trim();
                percentValue = parseFloat(percentText);
                
                if (!isNaN(percentValue)) {
                    console.log(`进度条#${index} 解析到百分比值: ${percentValue}%`);
                    
                    // 临时将宽度设为0
                    barFill.style.width = '0%';
                    
                    // 存储目标宽度到data属性
                    const targetWidth = `${percentValue}%`;
                    barFill.setAttribute('data-width', targetWidth);
                }
            }
        });
        
        // 强制浏览器重绘
        document.body.offsetHeight;
        
        // 开始应用动画，获取所有填充元素
        const barFills = document.querySelectorAll('.ratio-bar-fill, .percent-bar-fill');
        console.log(`准备为${barFills.length}个进度条应用动画效果`);
        
        // 逐个应用动画效果
        setTimeout(() => {
            barFills.forEach((barFill, index) => {
                setTimeout(() => {
                    const targetWidth = barFill.getAttribute('data-width');
                    if (targetWidth) {
                        barFill.style.width = targetWidth;
                        console.log(`进度条#${index}设置宽度为${targetWidth}`);
                    } else {
                        console.log(`进度条#${index}没有目标宽度值`);
                    }
                }, index * 40); // 错开动画时间
            });
        }, 200); // 等待一小段时间后开始动画
    }, 100); // 给DOM更新的时间
}

// 创建一个特别针对商务品持仓价值占比列的修复函数
function fixBusinessRatioProgressBars() {
    console.log('专门修复商务品持仓价值占比进度条...');
    
    // 获取所有商务品持仓价值占比单元格
    const ratioCells = document.querySelectorAll('.business-ratio-column');
    if (ratioCells.length === 0) {
        console.log('未找到商务品持仓价值占比单元格');
        return;
    }
    
    console.log(`找到 ${ratioCells.length} 个商务品持仓价值占比单元格`);
    
    // 处理每个单元格
    ratioCells.forEach((cell, index) => {
        // 查找百分比文本和进度条 - 根据实际HTML结构查找
        const ratioValue = cell.querySelector('.ratio-value');
        const ratioBarContainer = cell.querySelector('.ratio-bar-container');
        const ratioBar = cell.querySelector('.ratio-bar');
        const ratioBarFill = cell.querySelector('.ratio-bar-fill');
        
        if (!ratioValue || !ratioBar || !ratioBarFill) {
            console.log(`单元格 #${index} 缺少必要元素`);
            return;
        }
        
        // 获取百分比值
        const percentText = ratioValue.textContent.trim();
        const percentValue = parseFloat(percentText.replace('%', ''));
        
        if (isNaN(percentValue)) {
            console.log(`单元格 #${index} 无法解析百分比值: ${percentText}`);
            return;
        }
        
        console.log(`商务品单元格 #${index} 解析到百分比值: ${percentValue}%`);
        
        // 确保目标宽度值保存在data属性
        const targetWidth = `${percentValue}%`;
        ratioBarFill.setAttribute('data-width', targetWidth);
        
        // 强制设置宽度0
        ratioBarFill.style.width = '0%';
        
        // 强制重流
        void ratioBarContainer.offsetWidth;
    });
    
    // 强制浏览器重绘
    void document.body.offsetWidth;
    
    // 应用动画效果
    setTimeout(() => {
        const barFills = document.querySelectorAll('.business-ratio-column .ratio-bar-fill');
        
        barFills.forEach((barFill, index) => {
            setTimeout(() => {
                const targetWidth = barFill.getAttribute('data-width');
                if (targetWidth) {
                    console.log(`设置商务品进度条 #${index} 宽度为 ${targetWidth}`);
                    barFill.style.width = targetWidth;
                }
            }, index * 50); // 错开动画
        });
    }, 150);
}

// 添加一个紧急修复函数，直接设置商务品持仓价值占比进度条宽度
function emergencyFixRatioBars() {
    console.log('执行紧急修复：直接设置所有进度条宽度');
    
    // 获取所有占比单元格
    const ratioCells = document.querySelectorAll('.business-ratio-column');
    if (ratioCells.length === 0) {
        console.log('未找到进度条单元格');
        return;
    }
    
    // 遍历每个单元格
    ratioCells.forEach((cell, index) => {
        // 获取值和进度条元素
        const valueSpan = cell.querySelector('.ratio-value');
        const barFill = cell.querySelector('.ratio-bar-fill');
        
        if (!valueSpan || !barFill) return;
        
        // 提取百分比值
        const text = valueSpan.textContent.trim();
        const value = parseFloat(text.replace('%', ''));
        
        if (isNaN(value)) return;
        
        // 直接设置宽度，跳过动画
        const width = `${value}%`;
        console.log(`设置进度条 #${index} 宽度为 ${width}`);
        
        // 立即应用宽度
        barFill.style.width = width;
        barFill.style.transition = 'none'; // 禁用过渡动画
        
        // 确保应用
        void barFill.offsetWidth;
    });
    
    // 完成后恢复过渡动画
    setTimeout(() => {
        document.querySelectorAll('.ratio-bar-fill').forEach(bar => {
            bar.style.transition = '';
        });
        console.log('紧急修复完成，所有进度条已直接设置宽度');
    }, 100);
}

// 将紧急修复函数添加到window对象
window.emergencyFixRatioBars = emergencyFixRatioBars;

// 计算和应用总管理规模的四分位数着色
function applyFundSizeQuartileColors() {
    console.log('应用总管理规模四分位数着色 - 开始');
    console.log(`页面URL: ${window.location.href}`);
    console.log(`文档状态: ${document.readyState}`);
    
    try {
        // 获取所有总管理规模单元格 - 使用多种选择器提高查找可靠性
        let cells = document.querySelectorAll('#company-analytics-tbody tr td.fund-size-cell');
        console.log(`使用class选择器找到 ${cells.length} 个总管理规模单元格`);
        
        if (cells.length === 0) {
            console.log('使用class选择器未找到总管理规模单元格，尝试使用位置选择器');
            // 尝试使用位置选择器（第6列）作为备选
            cells = document.querySelectorAll('#company-analytics-tbody tr td:nth-child(6)');
            console.log(`使用位置选择器找到 ${cells.length} 个总管理规模单元格`);
        }
        
        // 如果仍未找到，尝试最后一种选择器
        if (cells.length === 0) {
            console.log('使用位置选择器仍未找到总管理规模单元格，尝试使用包含"总管理规模"的表头查找');
            // 查找包含"总管理规模"的表头
            const headers = Array.from(document.querySelectorAll('th'));
            const fundSizeHeader = headers.find(th => th.textContent.includes('总管理规模'));
            if (fundSizeHeader) {
                // 找到表头后，获取其索引
                const headerIndex = Array.prototype.indexOf.call(fundSizeHeader.parentNode.children, fundSizeHeader);
                if (headerIndex > 0) {
                    // 根据表头索引获取相应列的单元格
                    cells = document.querySelectorAll(`#company-analytics-tbody tr td:nth-child(${headerIndex + 1})`);
                    console.log(`使用表头查找找到 ${cells.length} 个总管理规模单元格，位于第 ${headerIndex + 1} 列`);
                }
            }
        }
        
        console.log(`找到 ${cells.length} 个总管理规模单元格`);
        
        if (cells.length === 0) {
            console.error('未找到总管理规模单元格，无法应用四分位数着色');
            return;
        }
        
        // 收集所有有效的规模值
        const values = [];
        cells.forEach((cell, index) => {
            try {
                // 尝试从span元素中获取值
                const valueSpan = cell.querySelector('span.fund-size-value');
                let text;
                
                if (valueSpan) {
                    text = valueSpan.textContent.trim();
                    console.log(`单元格 #${index} 中找到span.fund-size-value元素，文本为：${text}`);
                } else {
                    // 如果没有span元素，直接从单元格获取文本
                    text = cell.textContent.trim();
                    console.log(`单元格 #${index} 中未找到span.fund-size-value元素，直接使用单元格文本：${text}`);
                }
                
                const value = parseFloat(text);
                if (!isNaN(value)) {
                    values.push({ cell, value, index, valueSpan });
                    console.log(`单元格 #${index}: ${text} => ${value}亿元`);
                } else {
                    console.log(`单元格 #${index}: 无法解析数值 "${text}"`);
                }
            } catch (error) {
                console.error(`处理单元格 #${index} 时出错:`, error);
            }
        });
        
        // 如果没有有效值，直接返回
        if (values.length === 0) {
            console.error('未找到有效的总管理规模值，无法应用四分位数着色');
            return;
        }
        
        // 排序值以计算四分位数
        values.sort((a, b) => a.value - b.value);
        
        // 打印排序后的值，便于调试
        console.log('排序后的总管理规模值:');
        values.forEach((item, i) => {
            console.log(`#${i} (原始索引: ${item.index}): ${item.value.toFixed(2)}亿元`);
        });
        
        // 计算四分位数
        const q1Index = Math.floor(values.length * 0.25);
        const q2Index = Math.floor(values.length * 0.5);
        const q3Index = Math.floor(values.length * 0.75);
        
        const q1 = values[q1Index].value;
        const q2 = values[q2Index].value;
        const q3 = values[q3Index].value;
        
        console.log(`总管理规模四分位数: Q1=${q1.toFixed(2)}亿, Q2=${q2.toFixed(2)}亿, Q3=${q3.toFixed(2)}亿`);
        console.log(`四分位数阈值: 0-${q1.toFixed(2)}(绿色), ${q1.toFixed(2)}-${q2.toFixed(2)}(蓝色), ${q2.toFixed(2)}-${q3.toFixed(2)}(橙色), ${q3.toFixed(2)}+(红色)`);
        
        // 应用四分位数颜色类
        values.forEach(item => {
            try {
                // 清除单元格上可能存在的任何颜色样式
                if (item.cell) {
                    item.cell.style.removeProperty('color');
                    item.cell.classList.remove('fund-size-q1', 'fund-size-q2', 'fund-size-q3', 'fund-size-q4');
                }
                
                // 选择要应用样式的元素（优先使用span元素）
                const targetElement = item.valueSpan || item.cell;
                
                // 记录元素信息，用于调试
                console.log(`应用颜色到元素:`, targetElement);
                
                // 移除之前可能存在的颜色类
                targetElement.classList.remove('fund-size-q1', 'fund-size-q2', 'fund-size-q3', 'fund-size-q4');
                
                // 根据值添加适当的颜色类
                let colorClass = '';
                let colorValue = '';
                
                if (item.value >= q3) {
                    colorClass = 'fund-size-q4'; // 红色，最高的25%
                    colorValue = '#dc2626';
                } else if (item.value >= q2) {
                    colorClass = 'fund-size-q3'; // 橙色，50%-75%
                    colorValue = '#ea580c';
                } else if (item.value >= q1) {
                    colorClass = 'fund-size-q2'; // 蓝色，25%-50%
                    colorValue = '#0369a1';
                } else {
                    colorClass = 'fund-size-q1'; // 绿色，最低的25%
                    colorValue = '#16a34a';
                }
                
                // 直接添加内联样式，确保颜色应用（最高优先级）
                targetElement.style.setProperty('color', colorValue, 'important');
                targetElement.style.setProperty('font-weight', '600', 'important');
                
                // 同时添加类，以便CSS样式也能应用
                targetElement.classList.add(colorClass);
                
                // 添加data属性，便于调试
                targetElement.setAttribute('data-quartile', colorClass);
                
                console.log(`应用颜色 ${colorClass} (${colorValue}) 到${item.valueSpan ? 'span元素' : '单元格'} #${item.index}，值 ${item.value.toFixed(2)}亿元`);
                
                // 强制触发重排，确保样式应用
                void targetElement.offsetWidth;
            } catch (error) {
                console.error(`为单元格 #${item.index} 应用颜色时出错:`, error);
            }
        });
        
        console.log('总管理规模四分位数着色完成');
    } catch (e) {
        console.error('应用总管理规模四分位数着色函数发生错误:', e);
    }
}

// 计算和应用总成交额的四分位数着色
function applyAmountQuartileColors() {
    console.log('应用总成交额四分位数着色 - 开始');
    
    try {
        // 获取所有总成交额单元格
        let cells = document.querySelectorAll('#company-analytics-tbody tr td.amount-cell');
        console.log(`使用class选择器找到 ${cells.length} 个总成交额单元格`);
        
        if (cells.length === 0) {
            console.log('使用class选择器未找到总成交额单元格，尝试使用位置选择器');
            // 尝试使用位置选择器（第7列）作为备选
            cells = document.querySelectorAll('#company-analytics-tbody tr td:nth-child(7)');
            console.log(`使用位置选择器找到 ${cells.length} 个总成交额单元格`);
        }
        
        // 如果仍未找到，尝试最后一种选择器
        if (cells.length === 0) {
            console.log('使用位置选择器仍未找到总成交额单元格，尝试使用包含"总成交额"的表头查找');
            // 查找包含"总成交额"的表头
            const headers = Array.from(document.querySelectorAll('th'));
            const amountHeader = headers.find(th => th.textContent.includes('总成交额'));
            if (amountHeader) {
                // 找到表头后，获取其索引
                const headerIndex = Array.prototype.indexOf.call(amountHeader.parentNode.children, amountHeader);
                if (headerIndex > 0) {
                    // 根据表头索引获取相应列的单元格
                    cells = document.querySelectorAll(`#company-analytics-tbody tr td:nth-child(${headerIndex + 1})`);
                    console.log(`使用表头查找找到 ${cells.length} 个总成交额单元格，位于第 ${headerIndex + 1} 列`);
                }
            }
        }
        
        console.log(`找到 ${cells.length} 个总成交额单元格`);
        
        if (cells.length === 0) {
            console.error('未找到总成交额单元格，无法应用四分位数着色');
            return;
        }
        
        // 收集所有有效的成交额值
        const values = [];
        cells.forEach((cell, index) => {
            try {
                // 尝试从span元素中获取值
                const valueSpan = cell.querySelector('span.amount-value');
                let text;
                
                if (valueSpan) {
                    text = valueSpan.textContent.trim();
                    console.log(`单元格 #${index} 中找到span.amount-value元素，文本为：${text}`);
                } else {
                    // 如果没有span元素，直接从单元格获取文本
                    text = cell.textContent.trim();
                    console.log(`单元格 #${index} 中未找到span.amount-value元素，直接使用单元格文本：${text}`);
                }
                
                const value = parseFloat(text);
                if (!isNaN(value)) {
                    values.push({ cell, value, index, valueSpan });
                    console.log(`单元格 #${index}: ${text} => ${value}亿元`);
                } else {
                    console.log(`单元格 #${index}: 无法解析数值 "${text}"`);
                }
            } catch (error) {
                console.error(`处理单元格 #${index} 时出错:`, error);
            }
        });
        
        // 如果没有有效值，直接返回
        if (values.length === 0) {
            console.error('未找到有效的总成交额值，无法应用四分位数着色');
            return;
        }
        
        // 排序值以计算四分位数
        values.sort((a, b) => a.value - b.value);
        
        // 打印排序后的值，便于调试
        console.log('排序后的总成交额值:');
        values.forEach((item, i) => {
            console.log(`#${i} (原始索引: ${item.index}): ${item.value.toFixed(2)}亿元`);
        });
        
        // 计算四分位数
        const q1Index = Math.floor(values.length * 0.25);
        const q2Index = Math.floor(values.length * 0.5);
        const q3Index = Math.floor(values.length * 0.75);
        
        const q1 = values[q1Index].value;
        const q2 = values[q2Index].value;
        const q3 = values[q3Index].value;
        
        console.log(`总成交额四分位数: Q1=${q1.toFixed(2)}亿, Q2=${q2.toFixed(2)}亿, Q3=${q3.toFixed(2)}亿`);
        console.log(`四分位数阈值: 0-${q1.toFixed(2)}(绿色), ${q1.toFixed(2)}-${q2.toFixed(2)}(蓝色), ${q2.toFixed(2)}-${q3.toFixed(2)}(橙色), ${q3.toFixed(2)}+(红色)`);
        
        // 应用四分位数颜色类
        values.forEach(item => {
            try {
                // 清除单元格上可能存在的任何颜色样式
                if (item.cell) {
                    item.cell.style.removeProperty('color');
                    item.cell.classList.remove('amount-q1', 'amount-q2', 'amount-q3', 'amount-q4');
                }
                
                // 选择要应用样式的元素（优先使用span元素）
                const targetElement = item.valueSpan || item.cell;
                
                // 记录元素信息，用于调试
                console.log(`应用颜色到元素:`, targetElement);
                
                // 移除之前可能存在的颜色类
                targetElement.classList.remove('amount-q1', 'amount-q2', 'amount-q3', 'amount-q4');
                
                // 根据值添加适当的颜色类
                let colorClass = '';
                let colorValue = '';
                
                if (item.value >= q3) {
                    colorClass = 'amount-q4'; // 红色，最高的25%
                    colorValue = '#dc2626';
                } else if (item.value >= q2) {
                    colorClass = 'amount-q3'; // 橙色，50%-75%
                    colorValue = '#ea580c';
                } else if (item.value >= q1) {
                    colorClass = 'amount-q2'; // 蓝色，25%-50%
                    colorValue = '#0369a1';
                } else {
                    colorClass = 'amount-q1'; // 绿色，最低的25%
                    colorValue = '#16a34a';
                }
                
                // 直接添加内联样式，确保颜色应用（最高优先级）
                targetElement.style.setProperty('color', colorValue, 'important');
                targetElement.style.setProperty('font-weight', '600', 'important');
                
                // 同时添加类，以便CSS样式也能应用
                targetElement.classList.add(colorClass);
                
                // 添加data属性，便于调试
                targetElement.setAttribute('data-quartile', colorClass);
                targetElement.setAttribute('data-value', item.value);
                
                console.log(`应用颜色 ${colorClass} (${colorValue}) 到${item.valueSpan ? 'span元素' : '单元格'} #${item.index}，值 ${item.value.toFixed(2)}亿元`);
                
                // 强制触发重排，确保样式应用
                void targetElement.offsetWidth;
            } catch (error) {
                console.error(`为单元格 #${item.index} 应用颜色时出错:`, error);
            }
        });
        
        console.log('总成交额四分位数着色完成');
    } catch (e) {
        console.error('应用总成交额四分位数着色函数发生错误:', e);
    }
}

// DOMContentLoaded 事件监听器
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，初始化事件监听器');

    // 页面元素检查 (在此处进行，以便后续逻辑使用)
    const elements = {
        'search-button': document.getElementById('search-button'),
        'search-input': document.getElementById('search-input'),
        'searchButton': document.querySelector('#searchButton'), // 兼容旧ID
        'searchInput': document.getElementById('searchInput'), // 兼容旧ID
        'search-results': document.getElementById('search-results'),
        'searchResults': document.getElementById('searchResults'), // 兼容旧ID
        'export-markdown-button': document.getElementById('export-markdown-button'),
        'company-analytics-tbody': document.getElementById('company-analytics-tbody'),
        'recommendation-container': document.getElementById('recommendation-container'),
        'company-filter': document.getElementById('company-filter'),
        'copy-markdown-button': document.getElementById('copy-markdown-button'),
        'load-data-btn': document.getElementById('load-data-btn'),
        'generate-report-btn': document.getElementById('generate-report-btn'),
        'nav-search': document.getElementById('nav-search'),
        'nav-overview': document.getElementById('nav-overview'),
        'nav-business': document.getElementById('nav-business'),
        'nav-report': document.getElementById('nav-report'),
        'markdown-modal': document.getElementById('markdown-modal'), // Markdown模态框本身
        'markdown-content': document.getElementById('markdown-content') // Markdown内容文本域
    };

    console.log('页面元素检查 (main.js DOMContentLoaded):');
    for (const [id, element] of Object.entries(elements)) {
        console.log(`${id}: ${element ? '存在' : '不存在'}`);
    }

    // 确保导出Markdown按钮在页面加载后立即可见 (如果存在)
    if (elements['export-markdown-button']) {
        console.log('初始化Markdown导出按钮，设为可见');
        elements['export-markdown-button'].style.display = 'block';
    }

    // 绑定搜索按钮点击事件
    const searchButton = elements['search-button'] || elements['searchButton'];
    if (searchButton) {
        console.log('找到搜索按钮，绑定点击事件');
        searchButton.addEventListener('click', function() {
            console.log('搜索按钮被点击');
            searchETF();
        });
    } else {
        // console.error('未找到搜索按钮，无法绑定点击事件'); // 在非搜索页面，这是正常的
    }

    // 绑定搜索输入框事件
    const searchInput = elements['search-input'] || elements['searchInput'];
    if (searchInput) {
        console.log('找到搜索输入框，绑定事件');
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                console.log('搜索输入框回车按下');
                e.preventDefault();
                searchETF();
            }
        });
        // 如果搜索框有预填充的值，自动触发搜索
        if (searchInput.value.trim()) {
            console.log("检测到预填充的搜索关键词，自动搜索:", searchInput.value);
            setTimeout(function() {
                searchETF(); // 确保 searchETF 已定义
            }, 1000);
        }
    } else {
        // console.error('未找到搜索输入框，无法绑定事件'); // 在非搜索页面，这是正常的
    }

    // 绑定导出Markdown按钮点击事件
    if (elements['export-markdown-button']) {
        console.log('找到导出Markdown按钮，绑定点击事件');
        elements['export-markdown-button'].addEventListener('click', function() {
            const searchResultsData = window.currentSearchResults;
            if (!searchResultsData) {
                showMessage('warning', '没有可导出的搜索结果');
                return;
            }
            const markdownContent = generateMarkdown(searchResultsData);
            if (elements['markdown-modal'] && elements['markdown-content']) {
                try {
                    const markdownModal = new bootstrap.Modal(elements['markdown-modal']);
                    elements['markdown-content'].value = markdownContent;
                    markdownModal.show();
                    console.log('显示Markdown导出模态框');
                } catch (error) {
                    console.error('打开Markdown模态框失败:', error);
                    showMessage('danger', '打开Markdown导出窗口失败，请检查控制台错误');
                }
            } else {
                console.error('Markdown模态框或内容区域未找到!');
            }
        });
    } else {
        // console.error('未找到导出Markdown按钮'); // 在非相关页面，这是正常的
    }

    // 绑定复制Markdown按钮点击事件
    if (elements['copy-markdown-button']) {
        elements['copy-markdown-button'].addEventListener('click', function() {
            if (elements['markdown-content']) {
                elements['markdown-content'].select();
                document.execCommand('copy');
                showMessage('success', 'Markdown内容已复制到剪贴板');
            }
        });
    }

    // 推荐模块初始化 (特定于首页或包含推荐模块的页面)
    if (elements['recommendation-container']) {
        console.log('main.js: Recommendation container element FOUND. Making it visible, then initializing and loading recommendations.');
        console.log('[main.js] recommendationContainer.innerHTML BEFORE initRecommendations (first 700 chars):', elements['recommendation-container'].innerHTML.substring(0, 700));
        elements['recommendation-container'].style.display = 'block'; // 确保容器可见
        initRecommendations(elements['recommendation-container']); // Pass the container
        console.log('[main.js] recommendationContainer.innerHTML AFTER initRecommendations, BEFORE loadRecommendations (first 700 chars):', elements['recommendation-container'].innerHTML.substring(0, 700));
        loadRecommendations(elements['recommendation-container']); // Pass the container
    } else {
        console.log('main.js: Recommendation container element NOT found. Skipping recommendation load.');
    }
    
    // 基金公司分析表格相关功能初始化
    if (elements['company-analytics-tbody']) {
        console.log('找到公司分析表格 (company-analytics-tbody)，初始化相关功能。');

        // 初始排序指示器
        updateSortIndicators();
        
        // 初始化商务品持仓价值列动画效果
        initBusinessValueAnimations();
        
        // 初始化公司筛选功能
        if (elements['company-filter']) {
            elements['company-filter'].addEventListener('input', applyCompanyFilter);
        }

        // 初始化排序状态 (从HTML或默认值)
        const companyAnalyticsSection = document.getElementById('company-analytics-section');
        if (companyAnalyticsSection) {
            const sortInfoText = companyAnalyticsSection.querySelector('.card-header .text-muted');
            if (sortInfoText && sortInfoText.textContent) {
                const match = sortInfoText.textContent.match(/当前按 (.*?) (升序|降序)排序/);
                if (match && match[1] && match[2]) {
                    const columnDisplayNamesReverse = {
                        '基金公司': 'company_short_name', '产品数量': 'product_count',
                        '商务品数量': 'business_agreement_count', '商务品占比 (%)': 'business_agreement_ratio',
                        '总管理规模 (亿元)': 'total_fund_size', '总成交额 (亿元)': 'total_amount',
                        '总自选热度': 'total_attention_count', '总持仓人数': 'total_holder_count_holders',
                        '持仓自选比 (%)': 'holder_attention_ratio', '总持仓价值 (亿元)': 'total_holding_value'
                    };
                    const matchedSortByDisplay = match[1].trim();
                    window.currentSortBy = columnDisplayNamesReverse[matchedSortByDisplay] || matchedSortByDisplay;
                    window.currentOrder = match[2] === '升序' ? 'asc' : 'desc';
                    console.log(`Initial sort state from HTML: ${window.currentSortBy} ${window.currentOrder}`);
                } else {
                     console.log('Could not parse initial sort state from HTML, using defaults.');
                }
            }
            updateSortIndicators(); // 再次调用以确保基于解析或默认状态更新
        }

        // 初始化商务品持仓价值相关的交互
        initBusinessValueInteractions();
        
        // 添加高亮样式到当前排序列
        highlightSortColumn();
        
        // 初始化进度条动画
        reapplyProgressBars(); // 初始调用
        
        // 给window对象添加相关函数 (仅当表格存在时才有意义)
        window.reapplyProgressBars = reapplyProgressBars;
        window.fullResetProgressBars = fullResetProgressBars;
        window.fixBusinessRatioProgressBars = fixBusinessRatioProgressBars;
        window.emergencyFixRatioBars = emergencyFixRatioBars;
        window.applyFundSizeQuartileColors = applyFundSizeQuartileColors;
        window.applyAmountQuartileColors = applyAmountQuartileColors;
        window.sortCompanyTable = sortCompanyTable; // 表格排序函数
        window.applyCompanyFilter = applyCompanyFilter; // 公司筛选函数
        window.highlightSortColumn = highlightSortColumn; // 高亮排序列函数

        // 初始化时运行一次紧急修复确保进度条显示正确
        setTimeout(emergencyFixRatioBars, 800);
        
        // 应用总管理规模和总成交额四分位数着色 (这些调用现在是条件性的，很好！)
        console.log('准备应用四分位数分区着色 (表格存在)...');
        setTimeout(function() {
            if (typeof applyFundSizeQuartileColors === 'function') applyFundSizeQuartileColors();
            if (typeof applyAmountQuartileColors === 'function') applyAmountQuartileColors();
            console.log('已调用四分位数着色函数 (表格存在)');
        }, 500); // 调整延迟以确保DOM和数据渲染完成

    } else {
        console.log('未找到公司分析表格 (company-analytics-tbody)，跳过相关功能初始化。');
        // 在没有表格的页面，这些函数不应该被全局调用
        // 可以考虑定义一个空的占位函数或者完全不定义，取决于其他模块是否会尝试调用它们
    }

    // 绑定导航事件
    if (elements['nav-search']) {
        elements['nav-search'].addEventListener('click', (e) => {
            // e.preventDefault(); // Removed for MPA navigation
            console.log('[main.js] ETF竞品查询 link clicked. Allowing href navigation.');
            // showSection('section-search'); // Removed for MPA navigation
            // setActiveNav(elements['nav-search']); // Active state will be set on new page load
        });
    }
    if (elements['nav-overview']) {
        elements['nav-overview'].addEventListener('click', (e) => {
            // e.preventDefault(); // Removed for MPA navigation
            console.log('[main.js] 市场概览 link clicked. Allowing href navigation.');
            // showSection('section-overview'); // Removed for MPA navigation
            // setActiveNav(elements['nav-overview']); // Active state will be set on new page load
        });
    }
    if (elements['nav-business']) {
        elements['nav-business'].addEventListener('click', (e) => {
            // e.preventDefault(); // Removed for MPA navigation
            console.log('[main.js] 商务品分析 link clicked. Allowing href navigation.');
            // showSection('section-business'); // Removed for MPA navigation
            // setActiveNav(elements['nav-business']); // Active state will be set on new page load
        });
    }

    // Properly initialize active navigation link based on current URL
    function initializeActiveNavLink() {
        const currentPath = window.location.pathname;
        document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
            link.classList.remove('active'); // Remove from all
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active'); // Add to matching
            }
        });
    }
    initializeActiveNavLink(); // Call on page load and after any AJAX navigation if implemented

    // Example: Re-call initializeActiveNavLink if you implement AJAX content loading that changes "page"
    // window.addEventListener('popstate', initializeActiveNavLink); // For browser back/forward with SPA history

    if (elements['load-data-btn']) {
        elements['load-data-btn'].addEventListener('click', function(e) {
            e.preventDefault();
            if (typeof loadData === 'function') loadData();
        });
    } else {
        // 自动加载数据（如果按钮不存在，也执行一次）
        if (typeof loadData === 'function') {
            console.log('Load data button not found, calling loadData() automatically.');
            loadData();
        }
    }
    
    // 绑定生成报告按钮
    if (elements['generate-report-btn']) {
        elements['generate-report-btn'].addEventListener('click', function(e) {
            e.preventDefault();
            if (typeof generateReport === 'function') generateReport();
        });
    }

    // 隐藏可能存在的解析错误信息
    const errorBanner = document.querySelector('.alert-danger');
    if (errorBanner && errorBanner.textContent.indexOf('SyntaxError') !== -1) {
        errorBanner.style.display = 'none';
        showMessage('info', '系统已就绪，请输入搜索关键词');
    }
    
    // 调整列宽函数，这个可以更通用，但其内部逻辑也应检查元素是否存在
    if (typeof adjustCompanyColumnWidth === 'function') {
        adjustCompanyColumnWidth(); 
    }

    console.log('页面初始化完成，交互功能已加载');
});

// 根据基金公司名称长度动态调整列宽度
function adjustCompanyColumnWidth() {
    const table = document.querySelector('.company-analytics-table');
    if (!table) {
        // console.log('adjustCompanyColumnWidth: .company-analytics-table not found, skipping.');
        return;
    }

    // 使用MutationObserver监听表格DOM变化
    if (typeof MutationObserver !== 'undefined') {
        const observer = new MutationObserver(function(mutations) {
            optimizeColumnWidths();
        });
        
        observer.observe(table, { 
            childList: true, 
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
    }
    
    optimizeColumnWidths();
    
    function optimizeColumnWidths() {
        const tableWidth = table.offsetWidth;
        const thElements = table.querySelectorAll('thead th');
        if (thElements.length === 0) return;

        let totalWidth = 0;
        thElements.forEach(th => {
            totalWidth += th.offsetWidth;
        });
        
        if (totalWidth > tableWidth) {
            console.log(`表格列总宽度(${totalWidth}px)超过表格容器宽度(${tableWidth}px)，尝试优化...`);
            const lessImportantColumns = [2, 3, 4, 7, 8]; 
            lessImportantColumns.forEach(index => {
                if (thElements[index]) {
                    const currentWidth = thElements[index].offsetWidth;
                    if (currentWidth > 100) {
                        const newWidth = Math.floor(currentWidth * 0.9);
                        thElements[index].style.width = `${newWidth}px`;
                    }
                }
            });
        }
        
        const companyColumn = table.querySelector('th:nth-child(2)');
        if (companyColumn) {
            companyColumn.style.width = '80px'; 
        }
    }
    
    window.addEventListener('resize', function() {
        // Check if table still exists before optimizing
        if (document.querySelector('.company-analytics-table')) {
             setTimeout(optimizeColumnWidths, 100);
        }
    });
}