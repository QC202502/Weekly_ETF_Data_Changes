import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob
from datetime import datetime

class IndexAnalyzer:
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
        
        # 尝试加载指数分类数据
        self.load_index_classification()
    
    def load_index_classification(self):
        """加载指数分类数据"""
        # 尝试从文件名获取日期
        files = glob.glob('ETF_基础数据合并_*.csv')
        if files:
            filename = sorted(files)[-1]
            date_str = filename.split('_')[-1].split('.')[0]
        else:
            date_str = "20240307"

        # 定义可能的分类文件路径
        paths_to_try = [
            f'/Users/admin/Downloads/ETF-Index-Classification_{date_str}.xlsx',
            '/Users/admin/Downloads/ETF-Index-Classification_20240307.xlsx'
        ]
        
        # 尝试加载任一路径的文件
        classification_data = None
        for path in paths_to_try:
            try:
                classification_data = pd.read_excel(path, engine='openpyxl')
                print(f"成功加载指数分类文件: {path}")
                print(f"指数分类文件总行数: {len(classification_data)}")
                print(f"分类文件列名: {classification_data.columns.tolist()}")
                break  # 成功加载后跳出循环
            except Exception as e:
                print(f"无法加载文件 {path}: {str(e)}")
        
        # 如果没有成功加载任何文件，直接返回
        if classification_data is None:
            print("警告: 无法加载任何指数分类文件")
            return
        
        # 检查是否有必要的列并合并数据
        if '跟踪指数代码' in classification_data.columns and '跟踪指数代码' in self.data.columns:
            # 确保代码列是字符串类型
            classification_data['跟踪指数代码'] = classification_data['跟踪指数代码'].astype(str).str.strip()
            self.data['跟踪指数代码'] = self.data['跟踪指数代码'].astype(str).str.strip()
            
            # 合并前打印一些信息，帮助调试
            print(f"原始数据中跟踪指数代码的唯一值数量: {self.data['跟踪指数代码'].nunique()}")
            print(f"分类数据中跟踪指数代码的唯一值数量: {classification_data['跟踪指数代码'].nunique()}")
            
            # 合并数据
            self.data = pd.merge(self.data, classification_data, on='跟踪指数代码', how='left')
            self.biz_data = self.data[self.data['是否商务品'] == '商务'].copy()
            print("成功合并指数分类数据")
            
            # 检查分类列
            classification_columns = ['一级分类', '二级分类', '三级分类', '指数类型']
            available_columns = [col for col in classification_columns if col in self.data.columns]
            print(f"可用的分类列: {available_columns}")
            
            if not available_columns:
                print("警告: 合并后没有找到标准分类列，尝试查找其他分类列...")
                possible_columns = [col for col in classification_data.columns if '分类' in col or '类型' in col]
                if possible_columns:
                    print(f"找到可能的分类列: {possible_columns}")
                    # 将这些列添加到数据中
                    for col in possible_columns:
                        if col not in self.data.columns:
                            mapping = dict(zip(classification_data['跟踪指数代码'], classification_data[col]))
                            self.data[col] = self.data['跟踪指数代码'].map(mapping)
                            self.biz_data[col] = self.biz_data['跟踪指数代码'].map(mapping)
                    
                    # 重新检查分类列
                    classification_columns = ['一级分类', '二级分类', '三级分类', '指数类型'] + possible_columns
                    available_columns = [col for col in classification_columns if col in self.data.columns]
                    print(f"更新后可用的分类列: {available_columns}")
        else:
            print("警告: 缺少'跟踪指数代码'列，无法合并分类数据")

    def analyze(self):
        """分析指数相关数据"""
        print("开始分析指数数据...")
        
        # 检查是否有指数分类列
        classification_columns = ['一级分类', '二级分类', '三级分类', '指数类型']
        available_columns = [col for col in classification_columns if col in self.data.columns]
        
        if not available_columns:
            print("警告: 没有找到指数分类列，无法进行指数分类分析")
            return {}
        
        # 分析结果存储
        index_stats = {}
        
        # 按照指数分类统计ETF数量
        for col in available_columns:
            # 跳过空值
            valid_data = self.biz_data[~self.biz_data[col].isna()]
            
            if len(valid_data) == 0:
                print(f"警告: 在'{col}'列中没有有效数据")
                continue
                
            # 按分类统计ETF数量
            category_counts = valid_data[col].value_counts().reset_index()
            category_counts.columns = [col, 'ETF数量']
            
            # 计算占比
            total = category_counts['ETF数量'].sum()
            category_counts['占比'] = category_counts['ETF数量'] / total * 100
            category_counts['占比'] = category_counts['占比'].round(2).astype(str) + '%'
            
            # 保存结果
            index_stats[col] = category_counts
            
            # 绘制饼图
            plt.figure(figsize=(12, 8))
            plt.pie(
                category_counts['ETF数量'],
                labels=category_counts[col],
                autopct='%1.1f%%',
                startangle=90,
                shadow=True
            )
            plt.axis('equal')  # 确保饼图是圆的
            plt.title(f'商务品ETF按{col}分布')
            
            # 保存图表
            chart_path = os.path.join(self.output_dir, f'index_category_{col}.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"已生成{col}分布图表: {chart_path}")
            
            # 如果分类数量较多，也生成条形图
            if len(category_counts) > 5:
                plt.figure(figsize=(14, 8))
                sns.barplot(x='ETF数量', y=col, data=category_counts.sort_values('ETF数量', ascending=False))
                plt.title(f'商务品ETF按{col}分布')
                plt.tight_layout()
                
                # 保存图表
                chart_path = os.path.join(self.output_dir, f'index_category_{col}_bar.png')
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                print(f"已生成{col}条形图表: {chart_path}")
        
        # 分析指数表现
        if '跟踪指数代码' in self.data.columns and '最新单位净值' in self.data.columns:
            # 按指数代码分组计算平均净值
            index_performance = self.biz_data.groupby('跟踪指数代码')['最新单位净值'].mean().reset_index()
            index_performance.columns = ['跟踪指数代码', '平均净值']
            
            # 如果有指数名称，添加到结果中
            if '跟踪指数名称' in self.biz_data.columns:
                # 创建指数代码到名称的映射
                index_name_map = dict(zip(self.biz_data['跟踪指数代码'], self.biz_data['跟踪指数名称']))
                index_performance['跟踪指数名称'] = index_performance['跟踪指数代码'].map(index_name_map)
                
                # 调整列顺序
                index_performance = index_performance[['跟踪指数代码', '跟踪指数名称', '平均净值']]
            
            # 按平均净值排序
            index_performance = index_performance.sort_values('平均净值', ascending=False)
            
            # 保存结果
            index_stats['指数表现'] = index_performance
            
            # 绘制前10名指数的条形图
            top_indices = index_performance.head(10)
            
            plt.figure(figsize=(14, 8))
            if '跟踪指数名称' in top_indices.columns:
                sns.barplot(x='平均净值', y='跟踪指数名称', data=top_indices)
                plt.title('商务品ETF跟踪指数表现Top10')
            else:
                sns.barplot(x='平均净值', y='跟踪指数代码', data=top_indices)
                plt.title('商务品ETF跟踪指数表现Top10')
            
            plt.tight_layout()
            
            # 保存图表
            chart_path = os.path.join(self.output_dir, 'index_performance_top10.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"已生成指数表现Top10图表: {chart_path}")
        
        print("指数数据分析完成")
        return index_stats