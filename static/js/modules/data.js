/**
 * 数据加载模块
 */
import { showLoading, hideLoading, showMessage } from './utils.js';

// 加载数据
export function loadData() {
    console.log('加载数据...');
    showLoading();
    
    // 更新数据状态显示
    const dataStatus = document.getElementById('data-status');
    if (dataStatus) {
        dataStatus.textContent = '正在加载数据...';
    }
    
    fetch('/load_data')
    .then(response => {
        if (!response.ok) {
            if (response.status === 404) {
                // 特殊处理404错误
                console.error('API端点未找到 (404)，尝试加载本地数据...');
                
                // 如果定义了全局HTTP错误处理函数，则调用它
                if (typeof window.handleHttpError === 'function') {
                    window.handleHttpError('API端点未找到 (404)');
                } else {
                    showMessage('warning', '数据加载失败：API端点未找到，请检查服务是否正常运行');
                }
                
                // 返回一个简单的成功数据，避免中断
                return {
                    message: '使用本地缓存数据',
                    data_date: new Date().toLocaleDateString(),
                    success: false
                };
            }
            throw new Error(`HTTP错误! 状态: ${response.status}`);
        }
        return response.text(); // 先获取文本而不是直接解析JSON
    })
    .then(text => {
        // 如果是对象，说明是我们的错误处理返回的
        if (typeof text === 'object') {
            hideLoading();
            return text;
        }
        
        // 尝试解析JSON
        try {
            const data = JSON.parse(text);
            console.log('数据加载成功:', data);
            hideLoading();
            
            // 更新数据状态
            if (dataStatus) {
                const date = data.data_date || '未知日期';
                dataStatus.textContent = `数据已更新 (${date})`;
                dataStatus.classList.add('text-success');
            }
            
            // 显示成功消息
            showMessage('success', data.message || '数据已成功加载');
            
            return data;
        } catch (e) {
            console.error('JSON解析错误:', e);
            console.error('收到的响应文本:', text);
            hideLoading();
            
            // 更新数据状态
            if (dataStatus) {
                dataStatus.textContent = '数据加载失败';
                dataStatus.classList.add('text-danger');
            }
            
            // 显示友好的错误消息
            showMessage('danger', '数据格式错误，请联系管理员或稍后再试');
            
            throw new Error('JSON解析错误: ' + e.message);
        }
    })
    .catch(error => {
        console.error('加载数据出错:', error);
        hideLoading();
        
        // 更新数据状态
        if (dataStatus) {
            dataStatus.textContent = '数据加载失败';
            dataStatus.classList.add('text-danger');
        }
        
        // 显示错误消息
        showMessage('danger', `加载数据出错: ${error.message}`);
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