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
    console.log(`[utils.js] showSection called with: ${sectionId}`);
    // 隐藏所有主要内容区域 (content-section)
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
        // console.log(`[utils.js] Hiding section: ${section.id}`);
    });
    
    // 显示选中的主要内容区域
    const selectedSection = document.getElementById(sectionId);
    if (selectedSection) {
        selectedSection.style.display = 'block';
        // console.log(`[utils.js] Showing section: ${selectedSection.id}`);
    } else {
        console.error(`[utils.js] Element with ID ${sectionId} not found. Falling back to overview.`);
        const overviewSection = document.getElementById('section-overview');
        if(overviewSection) {
            overviewSection.style.display = 'block';
            // console.log('[utils.js] Fallback: Showing section-overview');
        }
    }

    // 控制基金公司分析概览表格的显示
    const companyAnalyticsSection = document.getElementById('company-analytics-section');
    if (companyAnalyticsSection) {
        if (sectionId === 'section-overview') {
            companyAnalyticsSection.style.display = ''; // 或者 'block'
            console.log('[utils.js] Displaying company-analytics-section for section-overview');
        } else {
            companyAnalyticsSection.style.display = 'none';
            console.log(`[utils.js] Hiding company-analytics-section for ${sectionId}`);
        }
    }
    
    // 更新导航项的激活状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // 激活对应的导航项 (处理 nav-id 可能不完全匹配 sectionId 的情况)
    const navItemId = sectionId.startsWith('section-') ? sectionId.substring('section-'.length) : sectionId;
    const activeNavLink = document.querySelector(`#nav-${navItemId}`);
    if (activeNavLink) {
        activeNavLink.classList.add('active');
    } else {
        // Fallback or default active nav item if specific one not found (e.g. for root path)
        const overviewNav = document.getElementById('nav-overview');
        if(overviewNav) {
           overviewNav.classList.add('active'); 
           // console.log('[utils.js] Fallback: Activating nav-overview');
        }
    }
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