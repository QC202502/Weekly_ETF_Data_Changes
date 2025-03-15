// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 导航切换
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除所有active类
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            
            // 添加active类到当前点击的链接
            this.classList.add('active');
            
            // 隐藏所有内容区域
            document.querySelectorAll('.content-section').forEach(section => {
                section.style.display = 'none';
            });
            
            // 显示对应的内容区域
            if (this.id === 'nav-search') {
                document.getElementById('section-search').style.display = 'block';
            } else if (this.id === 'nav-overview') {
                document.getElementById('section-overview').style.display = 'block';
                loadOverviewData();
            } else if (this.id === 'nav-business') {
                document.getElementById('section-business').style.display = 'block';
                loadBusinessData();
            } else if (this.id === 'nav-report') {
                document.getElementById('section-report').style.display = 'block';
            }
        });
    });
    
    // 加载数据按钮
    document.getElementById('load-data-btn').addEventListener('click', function(e) {
        e.preventDefault();
        loadData();
    });
    
    // 搜索表单提交处理
    document.getElementById('search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        console.log("搜索表单已提交");
        
        // 显示加载状态
        document.getElementById('search-results').innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // 获取表单数据
        const formData = new FormData(this);
        const code = formData.get('code');
        console.log("搜索代码:", code);
        
        // 发送请求
        fetch('/search', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log("收到响应:", response.status);
            return response.json();
        })
        .then(data => {
            handleSearchResult(data);
        })
        .catch(error => {
            console.error('搜索出错:', error);
            document.getElementById('search-results').innerHTML = '<div class="alert alert-danger">搜索请求出错，请查看控制台</div>';
        });
    });
    
    // 如果搜索框有预填充的值，自动触发搜索
    const searchCode = document.getElementById('search-code').value;
    if (searchCode) {
        console.log("检测到URL中的code参数，自动搜索:", searchCode);
        // 延迟一点执行搜索，确保页面已完全加载
        setTimeout(function() {
            // 创建一个FormData对象
            const formData = new FormData();
            formData.append('code', searchCode);
            
            // 显示加载状态
            document.getElementById('search-results').innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
            
            // 发送搜索请求
            fetch('/search', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                handleSearchResult(data);
            })
            .catch(error => {
                console.error('自动搜索出错:', error);
                document.getElementById('search-results').innerHTML = '<div class="alert alert-danger">搜索请求出错，请查看控制台</div>';
            });
        }, 500);
    }
    
    // 页面加载完成后自动加载数据
    loadData();
});

// 加载数据
function loadData() {
    showLoading();
    
    fetch('/load_data')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                document.getElementById('data-status').textContent = '数据已加载';
                showMessage('success', data.message);
            } else {
                document.getElementById('data-status').textContent = '加载失败';
                showMessage('danger', data.message);
            }
        })
        .catch(error => {
            hideLoading();
            document.getElementById('data-status').textContent = '加载出错';
            showMessage('danger', '加载数据出错: ' + error);
        });
}

// 加载市场概览数据
function loadOverviewData() {
    showLoading();
    
    fetch('/overview')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            // 更新统计数据
            document.getElementById('total-etfs').textContent = data.stats.total_etfs;
            document.getElementById('total-companies').textContent = data.stats.total_companies;
            document.getElementById('total-scale').textContent = data.stats.total_scale;
            document.getElementById('business-etfs').textContent = data.stats.business_etfs;
            
            // 更新图表
            if (data.charts.pie_chart) {
                document.getElementById('pie-chart').src = 'data:image/png;base64,' + data.charts.pie_chart;
            }
            
            if (data.charts.company_chart) {
                document.getElementById('company-chart').src = 'data:image/png;base64,' + data.charts.company_chart;
            }
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '加载市场概览出错: ' + error);
        });
}

// 加载商务品分析数据
function loadBusinessData() {
    showLoading();
    
    fetch('/business_analysis')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            // 更新统计数据
            document.getElementById('total-business').textContent = data.stats.total_business;
            document.getElementById('business-companies').textContent = data.stats.total_companies;
            document.getElementById('business-scale').textContent = data.stats.total_scale;
            
            // 更新公司表格
            const tableBody = document.getElementById('business-table');
            tableBody.innerHTML = '';
            
            data.by_company.forEach(company => {
                const row = document.createElement('tr');
                
                const companyCell = document.createElement('td');
                companyCell.textContent = company.company;
                row.appendChild(companyCell);
                
                const countCell = document.createElement('td');
                countCell.textContent = company.count;
                row.appendChild(countCell);
                
                const scaleCell = document.createElement('td');
                scaleCell.textContent = company.scale || '未知';
                row.appendChild(scaleCell);
                
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '加载商务品分析出错: ' + error);
        });
}

// 生成报告
function generateReport() {
    showLoading();
    
    fetch('/generate_report')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            // 显示下载链接
            document.getElementById('report-result').style.display = 'block';
            document.getElementById('download-report-link').href = data.report_url;
            
            showMessage('success', data.message);
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '生成报告出错: ' + error);
        });
}