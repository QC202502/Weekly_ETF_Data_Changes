/**
 * 通用工具函数模块
 */

// 显示加载中
export function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

// 隐藏加载中
export function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// 显示消息
export function showMessage(type, message) {
    const messageElement = document.getElementById('status-message');
    messageElement.className = `alert alert-${type} status-message`;
    messageElement.textContent = message;
    messageElement.style.display = 'block';
    
    // 3秒后自动隐藏
    setTimeout(() => {
        messageElement.style.display = 'none';
    }, 3000);
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