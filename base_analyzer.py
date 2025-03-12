import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

class BaseAnalyzer:
    def __init__(self, data, date_range, current_date, previous_date):
        self.data = data
        self.date_range = date_range
        self.current_date = current_date
        self.previous_date = previous_date
        self.biz_data = data[data['是否商务品'] == '商务'].copy()
        self.output_dir = 'business_etf_analysis'
        
        # 创建输出目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # 设置绘图风格
        sns.set(style="whitegrid")
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 设置中文字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    def generate_summary_stats(self):
        """生成商务品总体统计"""
        print("生成商务品总体统计...")
        
        # 获取商务品数据
        self.biz_data = self.data[self.data['是否商务品'] == '商务'].copy()
        
        # 确保分成比例是数值类型
        if '分成比例' in self.biz_data.columns:
            self.biz_data['分成比例'] = pd.to_numeric(self.biz_data['分成比例'], errors='coerce')
            # 填充缺失值为默认值0.4
            self.biz_data['分成比例'].fillna(0.4, inplace=True)
        else:
            # 如果没有分成比例列，添加一个默认值为0.4的列
            self.biz_data['分成比例'] = 0.4
        
        # 计算商务品总数
        biz_count = len(self.biz_data['证券代码'].unique())
        
        # 计算商务品总规模（亿元）
        biz_scale = self.biz_data[f'保有金额（{self.current_date}）'].sum() / 1e8
        
        # 计算所有ETF总规模（亿元）
        total_scale = self.data[f'保有金额（{self.current_date}）'].sum() / 1e8
        
        # 计算商务品占比
        biz_percentage = (biz_scale / total_scale) * 100 if total_scale > 0 else 0
        
        # 计算商务品总关注人数
        biz_attention = self.biz_data[f'关注人数（{self.current_date}）'].sum()
        
        # 计算所有ETF总关注人数
        total_attention = self.data[f'关注人数（{self.current_date}）'].sum()
        
        # 计算商务品关注人数占比
        attention_percentage = (biz_attention / total_attention) * 100 if total_attention > 0 else 0
        
        # 计算商务品总持仓客户数
        biz_holders = self.biz_data[f'持仓客户数（{self.current_date}）'].sum()
        
        # 计算所有ETF总持仓客户数
        total_holders = self.data[f'持仓客户数（{self.current_date}）'].sum()
        
        # 计算商务品持仓客户数占比
        holders_percentage = (biz_holders / total_holders) * 100 if total_holders > 0 else 0
        
        # 计算预期年收入 - 修复这里的计算方式
        expected_income = self.biz_data.apply(
            lambda x: (x[f'保有金额（{self.current_date}）'] / 1e8) * (x['管理费率[单位]%'] / 100) * x['分成比例'] * 10000,
            axis=1
        ).sum()
        
        # 创建商务品与非商务品对比数据
        biz_vs_nonbiz = pd.DataFrame([
            {
                '类型': '商务品',
                '数量': biz_count,
                '规模(亿元)': biz_scale,
                '关注人数': biz_attention,
                '持仓客户数': biz_holders
            },
            {
                '类型': '非商务品',
                '数量': len(self.data[self.data['是否商务品'] == '非商务']['证券代码'].unique()),
                '规模(亿元)': total_scale - biz_scale,
                '关注人数': total_attention - biz_attention,
                '持仓客户数': total_holders - biz_holders
            }
        ])
        
        # 绘制商务品与非商务品规模占比饼图
        plt.figure(figsize=(10, 6))
        plt.pie(
            [biz_scale, total_scale - biz_scale],
            labels=['商务品', '非商务品'],
            autopct='%1.1f%%',
            startangle=90,
            shadow=True
        )
        plt.axis('equal')
        plt.title('商务品与非商务品规模占比')
        plt.savefig(f'{self.output_dir}/商务品占比.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 绘制商务品与非商务品客户参与度对比图
        plt.figure(figsize=(12, 8))
        
        # 创建客户参与度对比数据
        engagement_data = pd.DataFrame([
            {'类型': '商务品', '指标': '关注人数', '数值': biz_attention},
            {'类型': '非商务品', '指标': '关注人数', '数值': total_attention - biz_attention},
            {'类型': '商务品', '指标': '持仓客户数', '数值': biz_holders},
            {'类型': '非商务品', '指标': '持仓客户数', '数值': total_holders - biz_holders}
        ])
        
        # 绘制分组柱状图
        sns.barplot(x='指标', y='数值', hue='类型', data=engagement_data)
        plt.title('商务品与非商务品客户参与度对比')
        plt.ylabel('数量')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/商务品与非商务品客户参与度对比.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 计算平均变动
        biz_avg_attention_change = self.biz_data['关注人数变动'].mean()
        nonbiz_avg_attention_change = self.data[self.data['是否商务品'] == '非商务']['关注人数变动'].mean()
        
        biz_avg_holders_change = self.biz_data['持仓客户数变动'].mean()
        nonbiz_avg_holders_change = self.data[self.data['是否商务品'] == '非商务']['持仓客户数变动'].mean()
        
        biz_avg_amount_change = self.biz_data['保有金额变动'].mean() / 1e6  # 转换为百万元
        nonbiz_avg_amount_change = self.data[self.data['是否商务品'] == '非商务']['保有金额变动'].mean() / 1e6
        
        # 创建平均变动对比数据
        change_data = pd.DataFrame([
            {'类型': '商务品', '指标': '平均关注人数变动', '数值': biz_avg_attention_change},
            {'类型': '非商务品', '指标': '平均关注人数变动', '数值': nonbiz_avg_attention_change},
            {'类型': '商务品', '指标': '平均持仓客户数变动', '数值': biz_avg_holders_change},
            {'类型': '非商务品', '指标': '平均持仓客户数变动', '数值': nonbiz_avg_holders_change},
            {'类型': '商务品', '指标': '平均保有金额变动(百万)', '数值': biz_avg_amount_change},
            {'类型': '非商务品', '指标': '平均保有金额变动(百万)', '数值': nonbiz_avg_amount_change}
        ])
        
        # 绘制平均变动对比图
        plt.figure(figsize=(14, 8))
        sns.barplot(x='指标', y='数值', hue='类型', data=change_data)
        plt.title('商务品与非商务品平均变动对比')
        plt.ylabel('变动量')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/商务品与非商务品平均变动对比.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 计算平均管理费率
        avg_fee_rate = self.biz_data['管理费率[单位]%'].mean()
        
        # 计算加权平均管理费率
        total_amount = self.biz_data[f'保有金额（{self.current_date}）'].sum()
        if total_amount > 0:
            weighted_fee_rate = (self.biz_data['管理费率[单位]%'] * self.biz_data[f'保有金额（{self.current_date}）']).sum() / total_amount
        else:
            weighted_fee_rate = 0
        
        # 计算平均分成比例
        if '分成比例' in self.biz_data.columns:
            avg_share_ratio = self.biz_data['分成比例'].mean()
        else:
            avg_share_ratio = 0.4  # 默认值
        
        # 汇总统计数据
        self.summary_stats = {
            'total_count': biz_count,
            'total_scale': biz_scale,
            'all_etf_scale': total_scale,
            'percentage': biz_percentage,
            'total_expected_income': expected_income,
            'avg_fee_rate': avg_fee_rate,
            'weighted_fee_rate': weighted_fee_rate,
            'avg_share_ratio': avg_share_ratio
        }
        
        # 保存统计数据
        pd.DataFrame([self.summary_stats]).to_csv(f'{self.output_dir}/商务品总体统计.csv', index=False, encoding='utf-8-sig')
        
        return self.summary_stats
    
    def analyze(self):
        """执行所有分析"""
        # 子类应该重写此方法
        raise NotImplementedError("子类必须实现analyze方法")