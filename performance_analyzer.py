import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from base_analyzer import BaseAnalyzer

class PerformanceAnalyzer(BaseAnalyzer):
    """业绩表现分析器"""
    
    def analyze(self):
        """执行业绩表现分析"""
        print("执行业绩表现分析...")
        self.analyze_performance()
        self.analyze_fee_distribution()
        self.analyze_customer_engagement()
        return {
            'performance_data': True if hasattr(self, 'performance_data') else False,
            'fee_stats': True if hasattr(self, 'fee_stats') else False,
            'engagement_data': True if hasattr(self, 'engagement_data') else False
        }
    
    def analyze_performance(self):
        """分析商务品业绩表现"""
        print("分析商务品业绩表现...")
        
        # 检查是否有必要的列
        required_cols = ['关注人数变动', '持仓客户数变动', '保有金额变动']
        for col in required_cols:
            if col not in self.biz_data.columns:
                print(f"警告: 数据中缺少'{col}'列，无法进行业绩表现分析")
                return
        
        # 按变动幅度排序
        attention_top = self.biz_data.sort_values('关注人数变动', ascending=False).head(10)
        holders_top = self.biz_data.sort_values('持仓客户数变动', ascending=False).head(10)
        amount_top = self.biz_data.sort_values('保有金额变动', ascending=False).head(10)
        
        # 绘制关注人数变动Top10
        plt.figure(figsize=(12, 8))
        sns.barplot(x='关注人数变动', y='产品名称', data=attention_top)
        plt.title('关注人数变动Top10商务品')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/关注人数变动Top10.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 绘制持仓客户数变动Top10
        plt.figure(figsize=(12, 8))
        sns.barplot(x='持仓客户数变动', y='产品名称', data=holders_top)
        plt.title('持仓客户数变动Top10商务品')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/持仓客户数变动Top10.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 绘制保有金额变动Top10（百万元）
        plt.figure(figsize=(12, 8))
        amount_top['保有金额变动(百万)'] = amount_top['保有金额变动'] / 1e6
        sns.barplot(x='保有金额变动(百万)', y='产品名称', data=amount_top)
        plt.title('保有金额变动Top10商务品(百万元)')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/保有金额变动Top10.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 保存业绩表现数据
        self.performance_data = pd.DataFrame({
            '关注人数变动Top10': attention_top['产品名称'].values,
            '持仓客户数变动Top10': holders_top['产品名称'].values,
            '保有金额变动Top10': amount_top['产品名称'].values
        })
        self.performance_data.to_csv(f'{self.output_dir}/商务品业绩表现Top10.csv', index=False, encoding='utf-8-sig')
    
    def analyze_fee_distribution(self):
        """分析商务品管理费率分布"""
        print("分析商务品管理费率分布...")
        
        # 检查是否有管理费率列
        if '管理费率[单位]%' not in self.biz_data.columns:
            print("警告: 数据中缺少'管理费率[单位]%'列，无法进行管理费率分析")
            return
        
        # 管理费率分布
        plt.figure(figsize=(12, 8))
        sns.histplot(self.biz_data['管理费率[单位]%'], bins=20, kde=True)
        plt.title('商务品管理费率分布')
        plt.xlabel('管理费率(%)')
        plt.ylabel('数量')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/商务品管理费率分布.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 管理费率与规模的关系
        plt.figure(figsize=(12, 8))
        # 分析商务品业绩表现...
        # 使用 .loc 来避免 SettingWithCopyWarning
        self.biz_data.loc[:, '保有金额(亿元)'] = self.biz_data[f'保有金额（{self.current_date}）'] / 1e8
        
        sns.scatterplot(x='管理费率[单位]%', y='保有金额(亿元)', data=self.biz_data)
        plt.title('商务品管理费率与规模关系')
        plt.xlabel('管理费率(%)')
        plt.ylabel('保有金额(亿元)')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/商务品管理费率与规模关系.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 计算加权平均管理费率
        total_amount = self.biz_data[f'保有金额（{self.current_date}）'].sum()
        if total_amount > 0:
            weighted_fee_rate = (self.biz_data['管理费率[单位]%'] * self.biz_data[f'保有金额（{self.current_date}）']).sum() / total_amount
        else:
            weighted_fee_rate = 0
        
        # 管理费率统计
        self.fee_stats = {
            '平均管理费率(%)': self.biz_data['管理费率[单位]%'].mean(),
            '加权平均管理费率(%)': weighted_fee_rate,
            '中位数管理费率(%)': self.biz_data['管理费率[单位]%'].median(),
            '最高管理费率(%)': self.biz_data['管理费率[单位]%'].max(),
            '最低管理费率(%)': self.biz_data['管理费率[单位]%'].min(),
            '标准差': self.biz_data['管理费率[单位]%'].std()
        }
        
        # 保存管理费率统计数据
        pd.DataFrame([self.fee_stats]).to_csv(f'{self.output_dir}/商务品管理费率统计.csv', index=False, encoding='utf-8-sig')
    
    def analyze_customer_engagement(self):
        """分析商务品客户参与度"""
        print("分析商务品客户参与度...")
        
        # 计算每个商务品的平均关注人数和持仓客户数
        # 使用 .loc 来避免 SettingWithCopyWarning
        self.biz_data.loc[:, '平均关注人数'] = self.biz_data[f'关注人数（{self.current_date}）']
        self.biz_data.loc[:, '平均持仓客户数'] = self.biz_data[f'持仓客户数（{self.current_date}）']
        
        # 关注人数Top10
        attention_top = self.biz_data.sort_values('平均关注人数', ascending=False).head(10)
        
        # 持仓客户数Top10
        holders_top = self.biz_data.sort_values('平均持仓客户数', ascending=False).head(10)
        
        # 绘制关注人数Top10
        plt.figure(figsize=(12, 8))
        sns.barplot(x='平均关注人数', y='产品名称', data=attention_top)
        plt.title('关注人数Top10商务品')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/关注人数Top10.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 绘制持仓客户数Top10
        plt.figure(figsize=(12, 8))
        sns.barplot(x='平均持仓客户数', y='产品名称', data=holders_top)
        plt.title('持仓客户数Top10商务品')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/持仓客户数Top10.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 保存客户参与度数据
        self.engagement_data = pd.DataFrame({
            '关注人数Top10': attention_top['产品名称'].values,
            '持仓客户数Top10': holders_top['产品名称'].values
        })
        self.engagement_data.to_csv(f'{self.output_dir}/商务品客户参与度Top10.csv', index=False, encoding='utf-8-sig')