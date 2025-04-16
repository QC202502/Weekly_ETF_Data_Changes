/**
 * 新版ETF推荐页面
 */
import { searchETF } from './modules/search.js';
import { initNewRecommendationPage } from './modules/recommendation.js';

// 当DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('新版ETF推荐页面加载完成');
    
    // 初始化推荐页面
    initNewRecommendationPage();
    
    // 绑定搜索表单提交事件
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            searchETF();
        });
    }
    
    // 为搜索按钮单独添加点击事件（有些用户可能直接点击按钮而非提交表单）
    const searchButton = document.querySelector('#search-form button[type="submit"]');
    if (searchButton) {
        searchButton.addEventListener('click', function(e) {
            // 触发表单提交事件
            const searchForm = document.getElementById('search-form');
            if (searchForm) {
                searchForm.dispatchEvent(new Event('submit'));
            }
        });
    }
    
    // 绑定卡片点击事件
    document.querySelectorAll('.recommendation-card').forEach(card => {
        card.addEventListener('click', function() {
            // 提取ETF代码从卡片标题
            const title = this.querySelector('h3').textContent;
            const codeMatch = title.match(/^(\d{6})/);
            
            if (codeMatch && codeMatch[1]) {
                const code = codeMatch[1];
                console.log(`点击ETF卡片: ${code}`);
                
                // 跳转到搜索页面，带上ETF代码参数
                window.location.href = `/?code=${code}`;
            }
        });
    });
    
    // 添加卡片悬停效果
    document.querySelectorAll('.recommendation-card').forEach(card => {
        card.style.cursor = 'pointer';
    });
    
    console.log('新版ETF推荐页面初始化完成');
}); 