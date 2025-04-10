/**
 * 推荐功能模块
 */
import { showLoading, hideLoading, showMessage } from './utils.js';
import { searchETF } from './search.js';

// 初始化推荐栏
export function initRecommendations() {
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
export function loadRecommendations() {
    console.log('加载推荐数据');
    const recommendationContainer = document.getElementById('recommendation-container');
    
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
    
    // 更新价格涨幅标签的文本
    const priceReturnTab = document.querySelector('#price-return-tab');
    if (priceReturnTab && recommendations.trade_date) {
        priceReturnTab.textContent = `${recommendations.trade_date}涨幅TOP20`;
    }
    
    // 渲染价格涨幅推荐
    renderRecommendationTable('price-return', recommendations.price_return);
    
    // 渲染自选人数推荐
    renderRecommendationTable('attention', recommendations.attention);
    
    // 渲染持仓客户推荐
    renderRecommendationTable('holders', recommendations.holders);
    
    // 渲染保有金额推荐
    renderRecommendationTable('amount', recommendations.amount);
}

// 渲染推荐表格
function renderRecommendationTable(type, items) {
    const container = document.getElementById(`${type}-recommendations`);
    if (!container) return;
    
    // 如果没有数据，显示提示信息
    if (!items || items.length === 0) {
        container.innerHTML = '<tr><td colspan="4" class="text-center">暂无数据</td></tr>';
        return;
    }
    
    // 清空容器
    container.innerHTML = '';
    
    // 添加推荐项
    items.forEach((item, index) => {
        const row = document.createElement('tr');
        
        // 设置推荐项内容 - 确保ETF代码不包含sh/sz前缀
        let displayCode = item.code;
        if (displayCode.startsWith('sh') || displayCode.startsWith('sz')) {
            displayCode = displayCode.substring(2);
        }
        
        // 准备显示的变化值
        let changeValue = '';
        if (type === 'price-return') {
            changeValue = `${item.change_rate}%`;
        } else if (type === 'attention') {
            changeValue = `+${item.attention_change.toLocaleString()}`;
        } else if (type === 'holders') {
            changeValue = `+${item.holders_change.toLocaleString()}`;
        } else if (type === 'amount') {
            changeValue = `+${item.amount_change.toFixed(2)}亿元`;
        }
        
        // 准备指数信息
        const indexInfo = item.index_code || '未知';
        
        // 设置行内容
        row.innerHTML = `
            <td>${displayCode}</td>
            <td>${item.name}</td>
            <td>${changeValue}</td>
            <td>${indexInfo}</td>
        `;
        
        // 添加数据属性，用于点击搜索
        row.dataset.code = item.code;
        
        // 绑定点击事件 - 点击行时搜索该ETF
        row.addEventListener('click', function() {
            // 处理可能带有sh/sz前缀的ETF代码
            let searchCode = this.dataset.code;
            if (searchCode.startsWith('sh') || searchCode.startsWith('sz')) {
                searchCode = searchCode.substring(2);
            }
            
            // 填充搜索框
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.value = searchCode;
            }
            
            // 触发搜索
            searchETF();
        });
        
        // 添加指针样式，表示可点击
        row.style.cursor = 'pointer';
        
        // 将行添加到表格中
        container.appendChild(row);
    });
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