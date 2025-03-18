/**
 * 主入口文件
 * 负责导入各个模块并初始化应用
 */
import { showLoading, hideLoading, showMessage, showSection } from './modules/utils.js';
import { searchETF, handleSearchResult } from './modules/search.js';
import { loadData, loadOverview, loadBusinessAnalysis, generateReport } from './modules/data.js';
import { initRecommendations, loadRecommendations } from './modules/recommendation.js';

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
    
    // 绑定搜索输入框事件
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        console.log('找到搜索输入框，绑定事件');
        // 回车事件
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchETF();
            }
        });
    } else {
        console.error('未找到搜索输入框');
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
        searchETF();
    }
    
    // 页面加载完成后自动加载数据
    loadData();
});