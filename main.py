import os
import sys
import pandas as pd
from data_loader import load_data
from base_analyzer import BaseAnalyzer
from company_analyzer import CompanyAnalyzer
from index_analyzer import IndexAnalyzer
from performance_analyzer import PerformanceAnalyzer
from report_generator import ReportGenerator

def show_version():
    """显示版本信息"""
    print("ETF商务品分析工具 v1.0.0")
    print("作者: 邱超")
    print("日期: 2025年3月")
    print("-" * 50)

def main():
    """主函数"""
    show_version()
    print("开始加载数据...")
    try:
        data, date_range, current_date, previous_date = load_data()
        print(f"数据加载完成，日期范围: {date_range}")
        
        # 创建输出目录
        output_dir = 'business_etf_analysis'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 基础分析
        base = BaseAnalyzer(data, date_range, current_date, previous_date)
        summary_stats = base.generate_summary_stats()
        
        # 获取全市场ETF数量
        # 直接使用指定的ETF数据文件路径
        etf_data_file = '/Users/admin/Downloads/ETF_DATA_20250307.xlsx'
        
        if os.path.exists(etf_data_file):
            try:
                etf_df = pd.read_excel(etf_data_file)
                all_etf_count = len(etf_df)
                print(f"从{etf_data_file}中读取到全市场ETF总数: {all_etf_count}")
                
                # 计算实际占比并更新summary_stats
                if 'total_count' in summary_stats and all_etf_count > 0:
                    business_etf_count = summary_stats['total_count']
                    actual_percentage = (business_etf_count / all_etf_count) * 100
                    summary_stats['percentage'] = actual_percentage
                    summary_stats['all_etf_count'] = all_etf_count
                    print(f"商务品占比: {business_etf_count}/{all_etf_count} = {actual_percentage:.2f}%")
            except Exception as e:
                print(f"读取ETF数据文件失败: {str(e)}")
        else:
            print(f"ETF数据文件不存在: {etf_data_file}")
        
        # 公司分析
        company_analyzer = CompanyAnalyzer(data, date_range, current_date, previous_date)
        company_stats = company_analyzer.analyze()
        
        # 指数分析
        index_analyzer = IndexAnalyzer(data, date_range, current_date, previous_date)
        index_stats = index_analyzer.analyze()
        
        # 业绩表现分析
        performance_analyzer = PerformanceAnalyzer(data, date_range, current_date, previous_date)
        performance_analyzer.analyze()
        
        # 生成报告
        report_generator = ReportGenerator(output_dir, date_range, summary_stats)
        report_path = report_generator.generate_report(index_stats=index_stats, company_stats=company_stats)
        
        print(f"分析完成！报告已保存至: {report_path}")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())