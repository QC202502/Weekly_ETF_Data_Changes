/**
 * 通用工具函数模块
 */

// 显示加载中
export function showLoading() {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        loadingElement.classList.remove('d-none');
    }
    
    // 同时显示状态消息
    const statusMessage = document.getElementById('statusMessage');
    if (statusMessage) {
        statusMessage.textContent = '正在加载，请稍候...';
        statusMessage.style.display = 'block';
    }
}

// 隐藏加载中
export function hideLoading() {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        loadingElement.classList.add('d-none');
    }
    
    // 同时隐藏状态消息
    const statusMessage = document.getElementById('statusMessage');
    if (statusMessage) {
        statusMessage.style.display = 'none';
    }
}

// 显示消息
export function showMessage(type, message) {
    console.log(`显示消息: [${type}] ${message}`);
    
    // 尝试找到正确的消息元素 - 按优先级顺序尝试
    let messageElements = [
        document.getElementById('status-message'),
        document.getElementById('statusMessage'),
        document.getElementById('errorAlert'),
        document.querySelector('.alert'),
        document.querySelector('.status-message')
    ];
    
    // 过滤掉不存在的元素
    messageElements = messageElements.filter(el => el !== null);
    
    // 找不到任何消息元素，创建一个临时的
    if (messageElements.length === 0) {
        console.log('未找到任何消息元素，创建临时消息');
        const tempMessage = document.createElement('div');
        tempMessage.className = `alert alert-${type} position-fixed top-0 start-50 translate-middle-x mt-3`;
        tempMessage.style.zIndex = '9999';
        tempMessage.style.width = '50%';
        tempMessage.style.opacity = '0.9';
        tempMessage.textContent = message;
        document.body.appendChild(tempMessage);
        
        // 3秒后移除
        setTimeout(() => {
            try {
                document.body.removeChild(tempMessage);
            } catch (e) {
                console.error('移除临时消息元素失败:', e);
            }
        }, 3000);
        
        return;
    }
    
    // 使用找到的第一个消息元素
    const messageElement = messageElements[0];
    
    // 设置消息类和内容
    if (messageElement.classList.contains('alert')) {
        // 移除所有可能的alert类型
        messageElement.classList.remove('alert-primary', 'alert-secondary', 'alert-success', 
                                     'alert-danger', 'alert-warning', 'alert-info', 'alert-light', 'alert-dark');
        // 添加当前类型
        messageElement.classList.add(`alert-${type}`);
    } else {
        // 如果不是alert元素，设置完整class
        messageElement.className = `alert alert-${type}`;
    }
    
    // 设置内容和显示
    messageElement.textContent = message;
    messageElement.style.display = 'block';
    
    // 3秒后自动隐藏
    setTimeout(() => {
        messageElement.style.display = 'none';
    }, 3000);
    
    console.log(`消息已显示在元素: ${messageElement.id || 'unknown'}`);
}

// 导航功能
export function showSection(sectionId) {
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

// 显示提示信息
export function showAlert(message, type = 'info') {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) {
        console.error('未找到提示信息容器');
        return;
    }

    const alertClass = {
        'info': 'alert-info',
        'success': 'alert-success',
        'warning': 'alert-warning',
        'error': 'alert-danger'
    }[type] || 'alert-info';

    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    resultsContainer.innerHTML = alertHtml;
}

// 格式化数字
export function formatNumber(value, decimals = 2) {
    if (value === undefined || value === null || isNaN(value)) {
        return '0.00';
    }
    return Number(value).toFixed(decimals);
}