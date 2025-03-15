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

// 处理搜索结果的函数
function handleSearchResult(data) {
    console.log("搜索结果:", data);
    const resultsContainer = document.getElementById('search-results');
    
    if (data.error) {
        resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
    }
    
    // 检查是否有结果
    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML = `<div class="alert alert-warning">未找到匹配"${data.keyword}"的ETF产品</div>`;
        return;
    }
    
    // 显示搜索结果
    let html = `<div class="alert alert-success">找到 ${data.count} 个匹配"${data.keyword}"的ETF</div>`;
    
    html += '<div class="list-group">';
    
    data.results.forEach(etf => {
        const businessBadge = etf.is_business 
            ? '<span class="badge bg-danger ms-2">商务品</span>' 
            : '';
            
        html += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-1">${etf.code} ${etf.name}${businessBadge}</h5>
                    <small>规模: ${etf.scale}亿元</small>
                </div>
                <p class="mb-1">管理人: ${etf.manager} | 管理费率: ${etf.fee_rate}%</p>
                <small>跟踪指数: ${etf.index_code} ${etf.index_name}</small>
            </div>
        `;
    });
    
    html += '</div>';
    
    resultsContainer.innerHTML = html;
}

// 修改搜索ETF函数，使用FormData而不是JSON
// 修复搜索ETF函数
function searchETF() {
    // 获取搜索关键词
    const keyword = document.getElementById('search-input').value.trim();
    
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
    
    // 绑定搜索输入框回车事件
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        console.log('找到搜索输入框，绑定回车事件');
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchETF();
            }
        });
    } else {
        console.error('未找到搜索输入框');
    }
    
    // ... 其他初始化代码 ...
});

// 搜索ETF函数
function searchETF() {
    console.log('搜索ETF函数被调用');
    
    // 获取搜索关键词
    const searchInput = document.getElementById('search-input');
    if (!searchInput) {
        console.error('未找到搜索输入框元素');
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
    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML = `<div class="alert alert-warning">未找到匹配"${data.keyword}"的ETF产品</div>`;
        return;
    }
    
    // 显示搜索结果
    let html = `<div class="alert alert-success">找到 ${data.count} 个匹配"${data.keyword}"的ETF</div>`;
    
    html += '<div class="list-group">';
    
    data.results.forEach(etf => {
        const businessBadge = etf.is_business 
            ? '<span class="badge bg-danger ms-2">商务品</span>' 
            : '';
            
        html += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-1">${etf.code} ${etf.name}${businessBadge}</h5>
                    <small>规模: ${etf.scale}亿元</small>
                </div>
                <p class="mb-1">管理人: ${etf.manager} | 管理费率: ${etf.fee_rate}%</p>
                <small>跟踪指数: ${etf.index_code} ${etf.index_name}</small>
            </div>
        `;
    });
    
    html += '</div>';
    
    resultsContainer.innerHTML = html;
}
                                    