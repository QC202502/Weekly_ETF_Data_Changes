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

// 初始化新版推荐页面
export function initNewRecommendationPage() {
    console.log('初始化新版推荐页面');
    
    // 获取推荐数据
    fetch('/recommendations')
        .then(response => {
            console.log('推荐数据响应状态:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('获取到推荐数据:', data);
            
            if (data.error) {
                console.error('获取推荐数据出错:', data.error);
                return;
            }
            
            // 确保返回的数据格式正确
            if (!data.recommendations) {
                console.error('返回的数据格式不正确:', data);
                return;
            }
            
            // 渲染推荐数据
            renderRecommendations(data.recommendations);
        })
        .catch(error => {
            console.error('获取推荐数据出错:', error);
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
    const priceReturnTitle = document.getElementById('price-return-title');
    if (priceReturnTitle && recommendations.trade_date) {
        priceReturnTitle.textContent = `${recommendations.trade_date} 涨幅TOP20 ETF`;
    }
    
    console.log('价格数据:', recommendations.price_return);
    console.log('关注数据:', recommendations.attention);
    console.log('持仓数据:', recommendations.holders);
    
    // 渲染价格排名区域
    renderRecommendationTable(recommendations.price_return || [], 'price-return');
    
    // 渲染关注区域
    renderRecommendationTable(recommendations.attention || [], 'attention');
    
    // 渲染持仓区域
    renderRecommendationTable(recommendations.holders || [], 'holders');
}

// 渲染推荐表格
function renderRecommendationTable(items, type) {
    const container = document.getElementById(`${type}-recommendations`);
    if (!container) {
        console.warn(`未找到容器: ${type}-recommendations`);
        return;
    }
    
    // 如果没有数据，显示提示信息
    if (!items || items.length === 0) {
        container.innerHTML = '<div class="alert alert-info">暂无数据</div>';
        return;
    }
    
    console.log(`渲染 ${type} 表格，数据项:`, items.length);
    
    // 清空容器
    container.innerHTML = '';
    
    // 创建表格
    const table = document.createElement('table');
    table.className = 'table table-hover table-striped';
    
    // 创建表头
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>代码</th>
            <th>名称</th>
            <th>涨幅(%)</th>
            <th>跟踪指数</th>
            <th>基金公司</th>
            <th>规模(亿元)</th>
        </tr>
    `;
    table.appendChild(thead);
    
    // 创建表体
    const tbody = document.createElement('tbody');
    
    // 添加推荐项
    items.forEach((item, index) => {
        const row = document.createElement('tr');
        
        // 设置推荐项内容
        row.innerHTML = `
            <td>${item.code}</td>
            <td>${item.name}</td>
            <td class="${parseFloat(item.change_rate) >= 0 ? 'text-danger' : 'text-success'}">${item.change_rate}</td>
            <td>${item.index_name || item.tracking_index_name || item.index_code || item.tracking_index_code || '-'}</td>
            <td>${item.manager || item.fund_manager || '-'}</td>
            <td>${(item.scale || item.fund_size) ? parseFloat(item.scale || item.fund_size).toFixed(2) : '-'}</td>
        `;
        
        // 添加数据属性，用于点击搜索
        row.dataset.code = item.code;
        
        // 绑定点击事件 - 点击行时搜索该ETF
        row.addEventListener('click', function() {
            // 填充搜索框
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.value = this.dataset.code;
            }
            
            // 触发搜索
            searchETF();
        });
        
        // 添加指针样式，表示可点击
        row.style.cursor = 'pointer';
        
        // 将行添加到表格中
        tbody.appendChild(row);
    });
    
    table.appendChild(tbody);
    container.appendChild(table);
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