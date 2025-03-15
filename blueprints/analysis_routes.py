from flask import Blueprint, jsonify
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
from docx import Document
import os

# 创建蓝图
analysis_bp = Blueprint('analysis', __name__)

# 从数据蓝图导入全局变量
from blueprints.data_routes import etf_data, business_etfs, current_date_str

@analysis_bp.route('/overview')
def overview():
    """ETF市场概览"""
    if etf_data is None:
        return jsonify({"error": "数据未加载，请先加载数据"})
    
    try:
        # 生成饼图 - 按基金管理人分布
        plt.figure(figsize=(10, 6))

        manager_counts = etf_data['基金管理人'].value_counts().head(10)
        
        # 使用简单的标签，避免中文问题
        labels = [f'公司{i+1}' for i in range(len(manager_counts))]
        wedges, texts, autotexts = plt.pie(manager_counts, labels=labels, autopct='%1.1f%%', startangle=90)
        
        # 添加图例，显示实际的公司名称
        plt.legend(wedges, manager_counts.index, title="基金管理人", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.title('ETF基金管理人分布（Top 10）')
        plt.axis('equal')
        
        # 将图表转换为base64编码
        pie_buffer = io.BytesIO()
        plt.savefig(pie_buffer, format='png', dpi=100, bbox_inches='tight')
        pie_buffer.seek(0)
        pie_chart = base64.b64encode(pie_buffer.getvalue()).decode('utf-8')
        plt.close()
        
        # 生成柱状图 - 按基金规模
        plt.figure(figsize=(12, 6))
        
        # 确保列名存在
        scale_col = '基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'
        if scale_col not in etf_data.columns:
            # 尝试查找替代列
            for col in etf_data.columns:
                if '基金规模' in col and '亿元' in col:
                    scale_col = col
                    break
        
        # 按管理人分组并计算规模总和
        if scale_col in etf_data.columns:
            company_scale = etf_data.groupby('基金管理人')[scale_col].sum().sort_values(ascending=False).head(10)
            
            # 使用条形图而不是company_scale.plot
            plt.bar(range(len(company_scale)), company_scale.values)
            plt.xticks(range(len(company_scale)), company_scale.index, rotation=45)
            plt.title('ETF基金管理人规模排名（Top 10）')
            plt.xlabel('基金管理人')
            plt.ylabel('规模（亿元）')
            plt.tight_layout()
            
            # 将图表转换为base64编码
            company_buffer = io.BytesIO()
            plt.savefig(company_buffer, format='png', dpi=100, bbox_inches='tight')
            company_buffer.seek(0)
            company_chart = base64.b64encode(company_buffer.getvalue()).decode('utf-8')
            plt.close()
        else:
            company_chart = None
        
        # 统计数据
        total_etfs = len(etf_data)
        total_companies = etf_data['基金管理人'].nunique()
        
        # 计算总规模
        if scale_col in etf_data.columns:
            total_scale = etf_data[scale_col].sum()
        else:
            total_scale = None
        
        # 返回结果
        return jsonify({
            "success": True,
            "stats": {
                "total_etfs": total_etfs,
                "total_companies": total_companies,
                "total_scale": round(total_scale, 2) if total_scale is not None else "未知",
                "business_etfs": len(business_etfs)
            },
            "charts": {
                "pie_chart": pie_chart,
                "company_chart": company_chart
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"生成市场概览出错：{str(e)}"})

@analysis_bp.route('/business_analysis')
def business_analysis():
    """商务品分析"""
    if etf_data is None:
        return jsonify({"error": "数据未加载，请先加载数据"})
    
    try:
        # 筛选商务品ETF
        business_df = etf_data[etf_data['证券代码'].isin(business_etfs)]
        
        if business_df.empty:
            return jsonify({"error": "未找到商务品ETF数据"})
        
        # 按管理人分组统计商务品数量
        business_by_company = business_df.groupby('基金管理人').size().sort_values(ascending=False)
        
        # 统计数据
        total_business = len(business_df)
        total_companies = business_df['基金管理人'].nunique()
        
        # 确保列名存在
        scale_col = '基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'
        if scale_col not in business_df.columns:
            # 尝试查找替代列
            for col in business_df.columns:
                if '基金规模' in col and '亿元' in col:
                    scale_col = col
                    break
        
        # 计算总规模
        if scale_col in business_df.columns:
            total_scale = business_df[scale_col].sum()
            # 按管理人分组计算规模
            scale_by_company = business_df.groupby('基金管理人')[scale_col].sum().sort_values(ascending=False)
        else:
            total_scale = None
            scale_by_company = None
        
        # 构建结果
        result = {
            "success": True,
            "stats": {
                "total_business": total_business,
                "total_companies": total_companies,
                "total_scale": round(total_scale, 2) if total_scale is not None else "未知"
            },
            "by_company": []
        }
        
        # 添加公司数据
        for company in business_by_company.index:
            company_data = {
                "company": company,
                "count": int(business_by_company[company])
            }
            
            if scale_by_company is not None and company in scale_by_company:
                company_data["scale"] = round(float(scale_by_company[company]), 2)
            
            result["by_company"].append(company_data)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"商务品分析出错：{str(e)}"})

@analysis_bp.route('/generate_report')
def generate_report():
    """生成报告"""
    if etf_data is None:
        return jsonify({"error": "数据未加载，请先加载数据"})
    
    try:
        # 创建一个简单的Word文档
        doc = Document()
        
        # 添加标题
        doc.add_heading(f'ETF市场周报 ({current_date_str})', 0)
        
        # 添加市场概览
        doc.add_heading('市场概览', level=1)
        doc.add_paragraph(f'截至{current_date_str}，市场上共有{len(etf_data)}只ETF产品，其中商务品{len(business_etfs)}只。')
        
        # 添加商务品分析
        doc.add_heading('商务品分析', level=1)
        business_df = etf_data[etf_data['证券代码'].isin(business_etfs)]
        
        # 按管理人分组统计商务品数量
        business_by_company = business_df.groupby('基金管理人').size().sort_values(ascending=False)
        
        # 添加表格
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        # 添加表头
        header_cells = table.rows[0].cells
        header_cells[0].text = '基金管理人'
        header_cells[1].text = '商务品数量'
        
        # 添加数据行
        for company, count in business_by_company.items():
            row_cells = table.add_row().cells
            row_cells[0].text = company
            row_cells[1].text = str(count)
        
        # 保存文档
        from flask import current_app
        report_filename = f'ETF市场周报_{current_date_str}.docx'
        report_path = os.path.join(current_app.config['UPLOAD_FOLDER'], report_filename)
        doc.save(report_path)
        
        return jsonify({
            "success": True,
            "message": "报告生成成功",
            "report_url": f"/download_report/{report_filename}"
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"生成报告出错：{str(e)}"})