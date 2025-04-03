/**
 * 主入口文件
 * 负责导入各个模块并初始化应用
 */
import { showLoading, hideLoading, showMessage, showSection } from './modules/utils.js';
import { searchETF, handleSearchResult } from './modules/search.js';
import { loadData, loadOverview, loadBusinessAnalysis, generateReport } from './modules/data.js';
import { initRecommendations, loadRecommendations } from './modules/recommendation.js';
import { generateMarkdown } from './modules/markdown_export.js';

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
    };
    
    console.log('页面元素检查:');
    for (const [id, element] of Object.entries(elements)) {
        console.log(`${id}: ${element ? '存在' : '不存在'}`);
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
    const exportMarkdownButton = document.getElementById('export-markdown-button');
    if (exportMarkdownButton) {
        console.log('找到导出Markdown按钮，绑定点击事件');
        exportMarkdownButton.addEventListener('click', function() {
            // 获取当前搜索结果数据
            const searchResultsData = window.currentSearchResults;
            if (!searchResultsData) {
                showMessage('warning', '没有可导出的搜索结果');
                return;
            }
            
            // 生成Markdown内容
            const markdownContent = generateMarkdown(searchResultsData);
            
            // 显示Markdown模态框
            const markdownModal = new bootstrap.Modal(document.getElementById('markdown-modal'));
            document.getElementById('markdown-content').value = markdownContent;
            markdownModal.show();
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
});