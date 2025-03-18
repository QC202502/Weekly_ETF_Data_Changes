/**
 * 数据加载模块
 */
import { showLoading, hideLoading, showMessage } from './utils.js';

// 加载数据
export function loadData() {
    showLoading();
    
    fetch('/load_data')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            showMessage('success', data.message);
            
            // 更新数据状态
            document.getElementById('data-status').textContent = `数据日期: ${data.date_range}`;
        })
        .catch(error => {
            hideLoading();
            document.getElementById('data-status').textContent = '加载出错';
            showMessage('danger', '加载数据出错: ' + error);
        });
}

// 加载市场概览数据
export function loadOverview() {
    showLoading();
    
    fetch('/overview')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            // 更新基本统计数据
            document.getElementById('total-etfs').textContent = data.total_etfs;
            document.getElementById('total-companies').textContent = data.total_companies;
            document.getElementById('total-scale').textContent = data.total_scale;
            document.getElementById('business-etfs').textContent = data.business_etfs;
            
            // 更新图表
            document.getElementById('pie-chart').src = data.pie_chart;
            document.getElementById('company-chart').src = data.company_chart;
            
            // 更新商务品表格
            const tableBody = document.getElementById('business-table');
            tableBody.innerHTML = '';
            
            data.business_companies.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.company || '-'}</td>
                    <td>${item.count || '-'}</td>
                    <td>${item.scale || '-'}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '加载市场概览数据出错: ' + error);
        });
}

// 加载商务品分析数据
export function loadBusinessAnalysis() {
    showLoading();
    
    fetch('/business_analysis')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            // 更新基本统计数据
            document.getElementById('total-business').textContent = data.total_business;
            document.getElementById('business-companies').textContent = data.business_companies_count;
            document.getElementById('business-scale').textContent = data.total_scale;
            
            // 更新商务品表格
            const tableBody = document.getElementById('business-table');
            tableBody.innerHTML = '';
            
            if (data.companies && data.companies.length > 0) {
                data.companies.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.company || '-'}</td>
                        <td>${item.count || '-'}</td>
                        <td>${item.scale || '-'}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '加载商务品分析数据出错: ' + error);
        });
}

// 生成报告
export function generateReport() {
    showLoading();
    
    fetch('/generate_report')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showMessage('danger', data.error);
                return;
            }
            
            showMessage('success', data.message);
            
            // 显示下载链接
            document.getElementById('report-result').style.display = 'block';
            document.getElementById('download-report-link').href = data.report_url;
        })
        .catch(error => {
            hideLoading();
            showMessage('danger', '生成报告出错: ' + error);
        });
}