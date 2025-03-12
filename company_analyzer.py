import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from base_analyzer import BaseAnalyzer

class CompanyAnalyzer(BaseAnalyzer):
    """基金公司分析器"""
    
    def analyze(self):
        """执行基金公司分析"""
        print("执行基金公司分析...")
        self.analyze_by_company()
        return self.company_stats
    
    def analyze_by_company(self):
        """按基金公司分析商务品"""
        print("按基金公司分析商务品...")
        
        # 检查是否有基金公司列
        if '基金公司简称' not in self.biz_data.columns:
            print("警告: 数据中缺少'基金公司简称'列，无法进行基金公司分析")
            return
        
        # 按基金公司分组统计
        company_stats = self.biz_data.groupby('基金公司简称').agg({
            '证券代码': 'count',
            f'保有金额（{self.current_date}）': 'sum',
            '预期年收入(万元)': 'sum'
        }).reset_index()
        
        # 重命名列
        company_stats.columns = ['基金公司', '商务品数量', '保有金额', '预期年收入(万元)']
        
        # 转换保有金额为亿元
        company_stats['商务品规模(亿元)'] = company_stats['保有金额'] / 1e8
        company_stats.drop('保有金额', axis=1, inplace=True)
        
        # 按商务品规模排序
        company_stats = company_stats.sort_values('商务品规模(亿元)', ascending=False)
        
        # 保存基金公司统计数据
        self.company_stats = company_stats
        company_stats.to_csv(f'{self.output_dir}/基金公司商务品统计.csv', index=False, encoding='utf-8-sig')
        
        # 绘制前10家基金公司商务品规模
        top10_companies = company_stats.head(10)
        
        plt.figure(figsize=(12, 8))
        sns.barplot(x='商务品规模(亿元)', y='基金公司', data=top10_companies)
        plt.title('前10家基金公司商务品规模(亿元)')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/前10家公司商务品规模.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 绘制前10家基金公司商务品数量
        plt.figure(figsize=(12, 8))
        sns.barplot(x='商务品数量', y='基金公司', data=top10_companies)
        plt.title('前10家基金公司商务品数量')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/前10家公司商务品数量.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 绘制前10家基金公司预期年收入
        plt.figure(figsize=(12, 8))
        sns.barplot(x='预期年收入(万元)', y='基金公司', data=top10_companies)
        plt.title('前10家基金公司预期年收入(万元)')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/前10家基金公司预期年收入.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"基金公司分析完成，共分析 {len(company_stats)} 家基金公司")