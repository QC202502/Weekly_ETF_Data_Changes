/**
 * ETF数据分析平台通用JS
 */
 
// 全局AJAX设置
if (window.jQuery) {
    $.ajaxSetup({
        cache: false
    });
}

// 在文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 页面初始化逻辑可以放在这里
    console.log("ETF数据分析平台已初始化");
    
    // 为ETF对比页面添加超时处理
    if (window.location.pathname.includes('/etf/comparison')) {
        initComparisonPage();
    }
});

// 初始化ETF对比分析页面
function initComparisonPage() {
    console.log("初始化ETF对比分析页面组件");
    
    // 检查所需的DOM元素是否存在
    if (!document.getElementById('uploadBtn')) {
        console.error("页面缺少必要的DOM元素");
        alert("页面加载不完整，请刷新页面重试");
        return;
    }
    
    // 动态获取当前页面正确的主机和端口
    const currentHost = window.location.host;
    const baseUrl = window.location.protocol + '//' + currentHost;
    console.log("当前基础URL:", baseUrl);
    
    // 添加API请求超时处理
    const apiTimeouts = {};
    
    // 拦截所有fetch请求，添加超时处理
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        console.log("发起请求:", url);
        const timeout = 30000; // 30秒超时
        
        // 确保使用正确的域名和端口
        if (url.startsWith('/')) {
            url = baseUrl + url;
        }
        
        return Promise.race([
            originalFetch(url, options),
            new Promise((_, reject) => {
                const id = setTimeout(() => {
                    // 隐藏加载指示器
                    if (document.getElementById('loadingIndicator')) {
                        document.getElementById('loadingIndicator').style.display = 'none';
                    }
                    
                    reject(new Error(`请求超时: ${url}`));
                    alert('请求处理超时，请重试或减少输入的ETF代码数量。');
                }, timeout);
                apiTimeouts[url] = id;
            })
        ]).then(response => {
            if (apiTimeouts[url]) {
                clearTimeout(apiTimeouts[url]);
                delete apiTimeouts[url];
            }
            return response;
        }).catch(error => {
            if (apiTimeouts[url]) {
                clearTimeout(apiTimeouts[url]);
                delete apiTimeouts[url];
            }
            console.error('请求出错:', error);
            throw error;
        });
    };
    
    // 绑定图片上传事件
    const imageUpload = document.getElementById('imageUpload');
    if (imageUpload) {
        // 注意：我们不在这里直接处理图片上传，因为已经在etf_comparison.html中处理了
        // 这里只添加图片优化功能
        imageUpload.addEventListener('change', function(e) {
            console.log("图片上传事件触发 (app.js)");
            // 不做任何处理，让etf_comparison.html中的处理器负责显示预览
        });
    }
}

// 处理图片上传并预处理
function processImageUpload(file) {
    // 验证文件类型
    if (!file.type.match('image.*')) {
        alert('请选择有效的图片文件');
        return;
    }
    
    // 验证文件大小
    if (!validateImageSize(file)) {
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            // 如果图片过大，进行缩放处理
            const maxDimension = 1200; // 最大宽高
            let width = img.width;
            let height = img.height;
            let needsResize = false;
            
            if (width > maxDimension || height > maxDimension) {
                needsResize = true;
                if (width > height) {
                    height = Math.round(height * (maxDimension / width));
                    width = maxDimension;
                } else {
                    width = Math.round(width * (maxDimension / height));
                    height = maxDimension;
                }
            }
            
            // 如果需要调整大小，创建一个canvas来缩放图片
            if (needsResize) {
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                // 转换为更合适的格式 (PNG，质量更高)
                const optimizedDataUrl = canvas.toDataURL('image/png', 0.9);
                
                // 显示处理后的图片
                if (document.getElementById('uploadedImage')) {
                    document.getElementById('uploadedImage').src = optimizedDataUrl;
                    document.getElementById('imagePreview').classList.remove('hidden');
                }
                
                console.log("图片已优化: 原始尺寸 " + img.width + "x" + img.height + 
                          " -> 新尺寸 " + width + "x" + height);
            } else {
                // 不需要调整大小，直接使用原始图片
                if (document.getElementById('uploadedImage')) {
                    document.getElementById('uploadedImage').src = e.target.result;
                    document.getElementById('imagePreview').classList.remove('hidden');
                }
            }
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// 格式化数字，添加千位分隔符
function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) {
        return '-';
    }
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
}

// 格式化百分比
function formatPercent(num) {
    if (num === null || num === undefined || isNaN(num)) {
        return '-';
    }
    return num.toFixed(2) + '%';
}

// 处理API错误
function handleApiError(error, message = '操作失败') {
    console.error(error);
    alert(`${message}: ${error.message || '未知错误'}`);
}

// 限制图片大小
function validateImageSize(file, maxSizeMB = 5) {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
        alert(`图片大小超过${maxSizeMB}MB限制，请选择较小的图片。`);
        return false;
    }
    return true;
}