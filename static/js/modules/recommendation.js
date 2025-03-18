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
    
    // 渲染关注人数推荐
    renderRecommendationList('attention', recommendations.attention);
    
    // 渲染持仓客户推荐
    renderRecommendationList('holders', recommendations.holders);
    
    // 渲染保有金额推荐
    renderRecommendationList('amount', recommendations.amount);
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
        
        // 设置推荐项内容
        itemElement.innerHTML = `
            <div class="etf-name">${item.name}</div>
            <div class="etf-code">${item.code}</div>
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
    
    // 移除所有选中状态
    document.querySelectorAll('.recommendation-item').forEach(i => {
        i.classList.remove('selected');
    });
    
    // 添加选中状态
    item.classList.add('selected');
    
    // 填充搜索框
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = code;
    }
    
    // 触发搜索
    searchETF();
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