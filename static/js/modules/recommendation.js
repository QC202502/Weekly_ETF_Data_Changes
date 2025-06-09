/**
 * 推荐功能模块
 */
import { showLoading, hideLoading, showMessage } from './utils.js';
import { searchETF } from './search.js';

// 初始化推荐栏
export function initRecommendations(containerElement) {
    console.log('初始化推荐栏 (using provided container)');
    
    if (!containerElement) {
        console.warn('initRecommendations: containerElement is null, skipping init.');
        return;
    }

    // querySelectorAll 将在 containerElement 内部查找，这是正确的，因为tabs是其子元素
    const recommendationTabs = containerElement.querySelectorAll('#recommendation-tabs .nav-link'); 
    if (recommendationTabs.length > 0) {
        recommendationTabs.forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('data-bs-target'); // data-bs-target is like "#price-return-recommendations"
                
                // 移除所有active类
                containerElement.querySelectorAll('#recommendation-tabs .nav-link').forEach(t => {
                    t.classList.remove('active');
                });
                
                // 隐藏所有标签页内容 (tab-pane 也是 containerElement 的子孙)
                containerElement.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.remove('show', 'active');
                });
                
                // 激活当前标签页
                this.classList.add('active');
                const targetPane = containerElement.querySelector(targetId);
                if (targetPane) {
                    targetPane.classList.add('show', 'active');
                }
            });
        });
    }
    
    // 初始化悬浮卡片 (tooltip是独立于containerElement的全局元素)
    const tooltip = document.getElementById('recommendation-tooltip');
    if (tooltip) {
        document.addEventListener('mousemove', function(e) {
            if (tooltip.style.display === 'block') {
                tooltip.style.left = (e.pageX + 15) + 'px';
                tooltip.style.top = (e.pageY + 15) + 'px';
            }
        });
    }
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
export function loadRecommendations(containerElement) {
    console.log('[recommendation.js] loadRecommendations called with containerElement:', containerElement);
    
    if (!containerElement) { 
        console.warn('[recommendation.js] loadRecommendations: containerElement is null. Skipping.');
        return;
    }
    
    fetch('/recommendations')
        .then(response => {
            console.log('[recommendation.js] /recommendations fetch response status:', response.status);
            if (!response.ok) {
                console.error('[recommendation.js] Network response was not ok for /recommendations', response);
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('[recommendation.js] Data received from /recommendations:', JSON.parse(JSON.stringify(data))); // Deep copy for logging
            if (data.error) {
                console.error('[recommendation.js] Error from /recommendations API:', data.error);
                // Potentially update UI to show error
                // For example, for each recommendation type container:
                // const errorMsg = `<div class="alert alert-danger">加载推荐数据失败: ${data.error}</div>`;
                // if (mainContainerElement) {
                //     mainContainerElement.querySelector('#price-return-recommendations').innerHTML = errorMsg;
                //     mainContainerElement.querySelector('#attention-recommendations').innerHTML = errorMsg;
                //     mainContainerElement.querySelector('#holders-recommendations').innerHTML = errorMsg;
                // }
                return;
            }
            if (!data.recommendations) {
                console.error('[recommendation.js] data.recommendations is missing in API response.', data);
                // Update UI to show data format error
                return;
            }
            console.log('[recommendation.js] Calling renderRecommendations with data.recommendations:', JSON.parse(JSON.stringify(data.recommendations)), 'and container:', containerElement);
            renderRecommendations(data.recommendations, containerElement);
        })
        .catch(error => {
            console.error('[recommendation.js] Fetch error for /recommendations:', error);
            // Potentially update UI to show fetch error for all recommendation sections
            // const errorMsg = `<div class="alert alert-danger">加载推荐数据时发生网络错误。</div>`;
            // if (containerElement) { // Use the original containerElement passed to loadRecommendations
            //    containerElement.querySelector('#price-return-recommendations').innerHTML = errorMsg;
            //    containerElement.querySelector('#attention-recommendations').innerHTML = errorMsg;
            //    containerElement.querySelector('#holders-recommendations').innerHTML = errorMsg;
            // }
        });
}

// 渲染推荐数据
function renderRecommendations(recommendationsData, mainContainerElement) {
    console.log('[recommendation.js] renderRecommendations called with recommendationsData:', JSON.parse(JSON.stringify(recommendationsData)), 'and mainContainerElement:', mainContainerElement);
    
    if (mainContainerElement) {
        // console.log('[recommendation.js] Initial mainContainerElement.innerHTML (first 500 chars):', mainContainerElement.innerHTML.substring(0, 500));
    }

    if (!recommendationsData) {
        console.warn('[recommendation.js] renderRecommendations: recommendationsData is null or undefined. Aborting render.');
        return;
    }
    if (!mainContainerElement) {
        console.warn('[recommendation.js] renderRecommendations: mainContainerElement is null or undefined. Aborting render.');
        return;
    }

    // Diagnostic: Check for #price-tab globally and within container
    // const globalPriceTabForDiagnostic = document.getElementById('price-tab');
    // console.log('[recommendation.js] Diagnostic: document.getElementById(\'price-tab\') result:', globalPriceTabForDiagnostic);
    // if (globalPriceTabForDiagnostic && mainContainerElement) {
    //     console.log('[recommendation.js] Diagnostic: mainContainerElement.contains(globalPriceTabForDiagnostic):', mainContainerElement.contains(globalPriceTabForDiagnostic));
    // }
    // Attempt to find #price-tab using querySelector within mainContainerElement for diagnostics
    // const priceTabInContainerForDiagnostic = mainContainerElement.querySelector('#price-tab');
    // console.log('[recommendation.js] Diagnostic: mainContainerElement.querySelector(\'#price-tab\') result:', priceTabInContainerForDiagnostic);


    if (recommendationsData.date_for_title) {
        document.title = `${recommendationsData.date_for_title}涨幅TOP20 - ETF数据分析平台`;
        // const navTabButton = mainContainerElement.querySelector('#price-tab'); // Previous problematic line
        const navTabButton = document.getElementById('price-tab'); // Use global ID lookup
        console.log('[recommendation.js] Found #price-tab for title update (using getElementById):', navTabButton);
        if (navTabButton) {
            // const spanInsideNavTab = navTabButton.querySelector('span#price-return-title'); 
            // querySelector on the button itself should be fine if the button is found
            const spanInsideNavTab = navTabButton.querySelector('span#price-return-title');
            if (spanInsideNavTab) {
                console.log('[recommendation.js] Found span#price-return-title for title update:', spanInsideNavTab);
                spanInsideNavTab.textContent = ` ${recommendationsData.date_for_title}涨幅TOP20`;
            } else {
                console.warn('[recommendation.js] span#price-return-title NOT found inside #price-tab. Updating button innerHTML directly.');
                navTabButton.innerHTML = `<i class="bi bi-graph-up-arrow"></i> ${recommendationsData.date_for_title}涨幅TOP20`;
            }
            // console.log('[recommendation.js] #price-tab after title update query check (mainContainerElement.querySelector):', mainContainerElement.querySelector('#price-tab'));
            console.log('[recommendation.js] #price-tab after title update query check (document.getElementById):', document.getElementById('price-tab'));
        } else {
            console.warn('[recommendation.js] #price-tab button NOT found for title update (using getElementById).');
        }
    }
    
    console.log('[recommendation.js] Price data to render:', recommendationsData.price_return);
    console.log('[recommendation.js] Favorites data to render:', recommendationsData.favorites);
    console.log('[recommendation.js] Attention data to render:', recommendationsData.attention);
    console.log('[recommendation.js] Holders data to render:', recommendationsData.holders);
    
    const priceReturnItems = recommendationsData.price_return || [];
    const favoritesItems = recommendationsData.favorites || [];
    const attentionItems = recommendationsData.attention || [];
    const holdersItems = recommendationsData.holders || [];

    console.log(`[recommendation.js] Rendering price-return with ${priceReturnItems.length} items.`);
    renderRecommendationTable(priceReturnItems, 'price-return', mainContainerElement);
    
    console.log(`[recommendation.js] Rendering favorites with ${favoritesItems.length} items.`);
    renderRecommendationTable(favoritesItems, 'favorites', mainContainerElement);
    
    console.log(`[recommendation.js] Rendering attention with ${attentionItems.length} items.`);
    renderRecommendationTable(attentionItems, 'attention', mainContainerElement);
    
    console.log(`[recommendation.js] Rendering holders with ${holdersItems.length} items.`);
    renderRecommendationTable(holdersItems, 'holders', mainContainerElement);

    // console.log('[recommendation.js] #price-tab after all renderRecommendationTable calls query check (mainContainerElement.querySelector):', mainContainerElement.querySelector('#price-tab'));
    console.log('[recommendation.js] #price-tab after all renderRecommendationTable calls query check (document.getElementById):', document.getElementById('price-tab'));

    // After all tables are rendered, ensure the first tab button is active.
    // The tab click handler in initRecommendations should handle pane visibility.
    console.log('[recommendation.js] Ensuring first tab button is active after rendering all tables.');
    const firstTabButton = document.getElementById('price-tab');
    // const firstTabPane = mainContainerElement.querySelector('#price-return-recommendations'); 
    // No longer directly manipulating firstTabPane's classes here.

    // Deactivate all tab buttons first, then activate the first one.
    // This ensures only one tab button is marked active initially.
    document.querySelectorAll('#recommendation-tabs .nav-link').forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
    });
    
    if (firstTabButton) {
        console.log('[recommendation.js] Setting #price-tab as active.');
        firstTabButton.classList.add('active');
        firstTabButton.setAttribute('aria-selected', 'true');
        
        // Manually trigger a click on the first tab to let Bootstrap handle pane activation
        // This is a more robust way if initRecommendations is set up correctly.
        // However, this might re-trigger loading or other actions if not careful.
        // Let's first see if just setting active on button is enough.
        // Bootstrap might pick up the active button on init/load.

        // If panes are still not showing correctly, we might need to explicitly show the first pane:
        // const firstTabPaneTarget = firstTabButton.getAttribute('data-bs-target');
        // if (firstTabPaneTarget) {
        //     const pane = mainContainerElement.querySelector(firstTabPaneTarget);
        //     if (pane) {
        //          // Hide all panes first
        //          mainContainerElement.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('show', 'active'));
        //          pane.classList.add('show', 'active');
        //          console.log(`[recommendation.js] Explicitly activated pane: ${firstTabPaneTarget}`)
        //     }
        // }

    } else {
        console.warn('[recommendation.js] Could not find #price-tab button to set as active.');
    }
}

// 渲染推荐表格
function renderRecommendationTable(items, type, mainRecContainer) {
    console.log(`[recommendation.js] renderRecommendationTable called for type '${type}' with ${items ? items.length : 'null/undefined'} items. mainRecContainer:`, mainRecContainer);

    if (!mainRecContainer) {
        console.warn(`[recommendation.js] renderRecommendationTable: mainRecContainer is null for type '${type}'. Aborting.`);
        return;
    }

    // const tabContentContainer = mainRecContainer.querySelector('#recommendation-tab-content'); // Original attempt
    const tabContentContainer = document.getElementById('recommendation-tab-content'); // Try global lookup
    console.log(`[recommendation.js] Attempting to find #recommendation-tab-content via document.getElementById. Found:`, tabContentContainer);

    if (!tabContentContainer) {
        console.warn(`[recommendation.js] renderRecommendationTable: Could not find #recommendation-tab-content for type '${type}'. Aborting.`);
        return;
    }

    const paneId = `${type}-recommendations`; // e.g., price-return-recommendations
    // const container = mainRecContainer.querySelector(`.tab-pane#${paneId}`); // Old incorrect attempt
    const container = tabContentContainer.querySelector(`#${paneId}`); // Correct: Find pane by ID within tabContentContainer
    
    // console.log(`[recommendation.js] Attempting to find pane with ID '#${paneId}' inside tabContentContainer. Found:`, container);

    if (!container) {
        console.warn(`[recommendation.js] Pane NOT FOUND with ID '#${paneId}' inside #recommendation-tab-content for type '${type}'.`);
        return;
    }
    
    // Clear previous content, including "加载中..."
    // console.log(`[recommendation.js] Clearing innerHTML of container for type '${type}'. Current content:`, container.innerHTML.substring(0,100));
    container.innerHTML = ''; 

    if (!items || items.length === 0) {
        console.log(`[recommendation.js] No items to render for type '${type}'. Displaying '暂无数据'.`);
        container.innerHTML = '<div class="alert alert-info">暂无数据</div>';
        return;
    }
    
    // console.log(`[recommendation.js] Rendering table for type '${type}' with ${items.length} items into container:`, container);
    
    const tableResponsive = document.createElement('div');
    tableResponsive.className = 'table-responsive';
    
    const table = document.createElement('table');
    table.className = 'table table-hover table-striped';
    
    const thead = document.createElement('thead');
    let headerRow = '<tr>';
    headerRow += '<th>#</th>';
    headerRow += '<th>代码</th>';
    headerRow += '<th>名称</th>';
    
    if (type === 'price-return') {
        headerRow += '<th>涨幅</th>';
    } else if (type === 'favorites') {
        headerRow += '<th>加自选数</th>';
    } else if (type === 'attention') {
        headerRow += '<th>关注人数</th>';
    } else if (type === 'holders') {
        headerRow += '<th>持仓人数</th>';
    }
    
    headerRow += '<th>跟踪指数</th>';
    headerRow += '<th>基金公司</th>';
    headerRow += '<th>类型</th>';
    headerRow += '</tr>';
    
    thead.innerHTML = headerRow;
    table.appendChild(thead);
    
    const tbody = document.createElement('tbody');
    
    items.forEach((item, index) => {
        try { 
            const row = document.createElement('tr');
            
            const code = item.code || 'N/A';
            const name = item.name || '未知名称';
            const trackingIndex = item.tracking_index_name || item.tracking_index_code || '-';
            const manager = item.manager_short || item.fund_manager || '-';
            const isBusiness = typeof item.is_business === 'boolean' ? item.is_business : false;
            const businessText = item.business_text || (isBusiness ? '商务' : '非商务');

            let rankHtml = '';
            if (index < 3) {
                rankHtml = `<span class="rank-badge rank-badge-${index + 1}">${index + 1}</span>`;
            } else {
                rankHtml = `${index + 1}`;
            }
            
            let html = `<td>${rankHtml}</td>`;
            html += `<td>${code}</td>`;
            html += `<td>${name}</td>`;
            
            if (type === 'price-return') {
                const changeVal = item.change_rate;
                const change = Number(changeVal);
                if (isNaN(change)) {
                    html += `<td>-</td>`;
                } else {
                    const colorClass = change >= 0 ? 'text-danger' : 'text-success';
                    const sign = change >= 0 ? '+' : '';
                    html += `<td class="${colorClass}">${sign}${change.toFixed(2)}%</td>`;
                }
            } else if (type === 'favorites') {
                const attentionCount = Number(item.attention_count);
                let attentionColorClass = '';
                let sign = '';
                
                if (!isNaN(attentionCount)) {
                    // 自选变化数，使用正/负标记
                    if (attentionCount > 0) {
                        attentionColorClass = 'text-danger';
                        sign = '+';
                    } else if (attentionCount < 0) {
                        attentionColorClass = 'text-success';
                    }
                }
                
                html += `<td class="favorites-item">
                    <span class="favorites-count ${attentionColorClass}">${sign}${isNaN(attentionCount) ? '-' : attentionCount.toLocaleString()}</span>`;
                
                // If the item has price_change_rate, we'll show it in the same column with the attention count
                if (item.price_change_rate !== undefined) {
                    const change = Number(item.price_change_rate);
                    if (!isNaN(change)) {
                        const colorClass = change >= 0 ? 'positive' : 'negative';
                        const priceSign = change >= 0 ? '+' : '';
                        html += `<span class="price-change ${colorClass}">(${priceSign}${change.toFixed(2)}%)</span>`;
                        
                        // Store price change data as attribute for tooltip
                        row.dataset.priceChange = change.toFixed(2) + '%';
                    }
                }
                html += `</td>`;
            } else if (type === 'attention') {
                const attentionChange = Number(item.attention_change);
                html += `<td class="text-primary">${isNaN(attentionChange) ? '-' : attentionChange.toLocaleString()}</td>`;
            } else if (type === 'holders') {
                const holdersChange = Number(item.holders_change);
                html += `<td class="text-primary">${isNaN(holdersChange) ? '-' : holdersChange.toLocaleString()}</td>`;
            }
            
            html += `<td>${trackingIndex}</td>`;
            html += `<td>${manager}</td>`;
            html += `<td><span class="badge bg-${isBusiness ? 'danger' : 'secondary'}">${businessText}</span></td>`;
            
            row.innerHTML = html;
            
            row.dataset.code = code;
            row.addEventListener('click', function() {
                const searchInput = document.getElementById('search-input');
                if (searchInput && this.dataset.code !== 'N/A') {
                    searchInput.value = this.dataset.code;
                    if (typeof searchETF === 'function') {
                        searchETF();
                    }
                }
            });
            row.style.cursor = (code !== 'N/A' ? 'pointer' : 'default');
            
            tbody.appendChild(row);
        } catch (e) {
            console.error(`[recommendation.js] Error rendering item at index ${index} for type ${type}:`, item, e);
            const errorRow = document.createElement('tr');
            errorRow.innerHTML = `<td colspan="7" class="text-danger text-center">此行数据加载失败</td>`;
            tbody.appendChild(errorRow);
        }
    });
    
    table.appendChild(tbody);
    tableResponsive.appendChild(table);
    container.appendChild(tableResponsive);
    // console.log(`[recommendation.js] Finished rendering table for type '${type}'. Container outerHTML:`, container.outerHTML.substring(0, 200));
    // console.log(`[recommendation.js] For type '${type}', final container.classList:`, container.classList);
    // console.log(`[recommendation.js] For type '${type}', final container.innerHTML (first 300 chars):`, container.innerHTML.substring(0, 300));
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