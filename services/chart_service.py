import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

def generate_pie_chart(data, column, title, top_n=10):
    """生成饼图"""
    plt.figure(figsize=(10, 6))
    
    # 获取前N个值
    counts = data[column].value_counts().head(top_n)
    
    # 使用简单的标签，避免中文问题
    labels = [f'公司{i+1}' for i in range(len(counts))]
    wedges, texts, autotexts = plt.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90)
    
    # 添加图例，显示实际的公司名称
    plt.legend(wedges, counts.index, title=column, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    plt.title(title)
    plt.axis('equal')
    
    # 将图表转换为base64编码
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    chart = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return chart

def generate_bar_chart(data, group_column, value_column, title, xlabel, ylabel, top_n=10):
    """生成柱状图"""
    plt.figure(figsize=(12, 6))
    
    # 按指定列分组并计算总和
    grouped_data = data.groupby(group_column)[value_column].sum().sort_values(ascending=False).head(top_n)
    
    # 绘制柱状图
    plt.bar(range(len(grouped_data)), grouped_data.values)
    plt.xticks(range(len(grouped_data)), grouped_data.index, rotation=45)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    
    # 将图表转换为base64编码
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    chart = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return chart

def get_scale_column(df):
    """获取基金规模列名"""
    scale_col = '基金规模(合计)[交易日期]S_cal_date(now(),0,D,0)[单位]亿元'
    if scale_col not in df.columns:
        # 尝试查找替代列
        for col in df.columns:
            if '基金规模' in col and '亿元' in col:
                scale_col = col
                break
    return scale_col