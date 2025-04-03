/**
 * 主入口文件
 * 负责导入各个模块并初始化应用
 * 版本: 1.0.2 (2025-04-04) - 添加持仓人数和持仓金额支持
 */

// 版本日志
console.log('ETF分析平台 v1.0.2 (2025-04-04) - 添加持仓人数和持仓金额支持');

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

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，初始化事件监听器');
    
    // 检查页面元素，输出调试信息
    const elements = {
        'search-button': document.getElementById('search-button'),
        'search-input': document.getElementById('search-input'),
        'searchButton': document.querySelector('#searchButton'),
        'searchInput': document.getElementById('searchInput'),
        'search-results': document.getElementById('search-results'),
        'searchResults': document.getElementById('searchResults'),
        'export-markdown-button': document.getElementById('export-markdown-button'),
    };
    
    console.log('页面元素检查:');
    for (const [id, element] of Object.entries(elements)) {
        console.log(`${id}: ${element ? '存在' : '不存在'}`);
    }
    
    // 确保导出Markdown按钮在页面加载后立即可见
    if (elements['export-markdown-button']) {
        console.log('初始化Markdown导出按钮，设为可见');
        elements['export-markdown-button'].style.display = 'block';
    }
    
    // 绑定搜索按钮点击事件 - 兼容两种可能的ID
    const searchButton = document.querySelector('#search-button') || document.querySelector('#searchButton');
    if (searchButton) {
        console.log('找到搜索按钮，绑定点击事件');
        searchButton.addEventListener('click', function() {
            console.log('搜索按钮被点击');
            searchETF();
        });
    } else {
        console.error('未找到搜索按钮，无法绑定点击事件');
    }
    
    // 绑定搜索输入框事件 - 兼容两种可能的ID
    const searchInput = document.getElementById('search-input') || document.getElementById('searchInput');
    if (searchInput) {
        console.log('找到搜索输入框，绑定事件');
        // 回车事件
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                console.log('搜索输入框回车按下');
                e.preventDefault();
                searchETF();
            }
        });
    } else {
        console.error('未找到搜索输入框，无法绑定事件');
    }
    
    // 绑定导出Markdown按钮点击事件
    if (elements['export-markdown-button']) {
        console.log('找到导出Markdown按钮，绑定点击事件');
        elements['export-markdown-button'].addEventListener('click', function() {
            // 获取当前搜索结果数据
            const searchResultsData = window.currentSearchResults;
            if (!searchResultsData) {
                showMessage('warning', '没有可导出的搜索结果');
                return;
            }
            
            // 生成Markdown内容
            const markdownContent = generateMarkdown(searchResultsData);
            
            // 显示Markdown模态框
            try {
                const markdownModal = new bootstrap.Modal(document.getElementById('markdown-modal'));
                document.getElementById('markdown-content').value = markdownContent;
                markdownModal.show();
                console.log('显示Markdown导出模态框');
            } catch (error) {
                console.error('打开Markdown模态框失败:', error);
                showMessage('danger', '打开Markdown导出窗口失败，请检查控制台错误');
            }
        });
    } else {
        console.error('未找到导出Markdown按钮');
    }
    
    // 绑定复制Markdown按钮点击事件
    const copyMarkdownButton = document.getElementById('copy-markdown-button');
    if (copyMarkdownButton) {
        copyMarkdownButton.addEventListener('click', function() {
            const markdownContent = document.getElementById('markdown-content');
            markdownContent.select();
            document.execCommand('copy');
            showMessage('success', 'Markdown内容已复制到剪贴板');
        });
    }
    
    // 初始化推荐栏
    initRecommendations();
    
    // 加载推荐数据
    loadRecommendations();
    
    // 绑定导航事件
    document.getElementById('nav-search').addEventListener('click', function(e) {
        e.preventDefault();
        showSection('section-search');
    });
    
    document.getElementById('nav-overview').addEventListener('click', function(e) {
        e.preventDefault();
        showSection('section-overview');
        loadOverview();
    });
    
    document.getElementById('nav-business').addEventListener('click', function(e) {
        e.preventDefault();
        showSection('section-business');
        loadBusinessAnalysis();
    });
    
    document.getElementById('nav-report').addEventListener('click', function(e) {
        e.preventDefault();
        showSection('section-report');
    });
    
    // 绑定加载数据按钮
    document.getElementById('load-data-btn').addEventListener('click', function(e) {
        e.preventDefault();
        loadData();
    });
    
    // 绑定生成报告按钮
    const generateReportBtn = document.getElementById('generate-report-btn');
    if (generateReportBtn) {
        generateReportBtn.addEventListener('click', function(e) {
            e.preventDefault();
            generateReport();
        });
    }
    
    // 如果搜索框有预填充的值，自动触发搜索
    if (searchInput && searchInput.value.trim()) {
        console.log("检测到预填充的搜索关键词，自动搜索:", searchInput.value);
        setTimeout(function() {
            searchETF();
        }, 1000);
    }
    
    // 页面加载完成后自动加载数据
    loadData();
    
    // 隐藏可能存在的错误信息
    const errorBanner = document.querySelector('.alert-danger');
    if (errorBanner && errorBanner.textContent.indexOf('SyntaxError') !== -1) {
        errorBanner.style.display = 'none';
        showMessage('info', '系统已就绪，请输入搜索关键词');
    }
});