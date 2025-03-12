import pandas as pd
import glob
from datetime import datetime, timedelta

def load_data():
    """加载并预处理数据"""
    # 动态获取最新数据文件
    files = glob.glob('ETF_基础数据合并_*.csv')
    if not files:
        raise FileNotFoundError("未找到ETF基础数据文件")
    
    # 提取最新文件日期
    filename = sorted(files)[-1]
    date_str = filename.split('_')[-1].split('.')[0]
    
    try:
        current_date = datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        raise ValueError("文件名日期格式应为ETF_基础数据合并_YYYYMMDD.csv")
    
    previous_date = current_date - timedelta(days=7)
    
    # 修正日期格式（保留前导零）
    current_str = current_date.strftime("%m月%d日")
    previous_str = previous_date.strftime("%m月%d日")

    # 读取数据
    result = pd.read_csv(filename, encoding='utf-8-sig')
    
    # 读取ETF指数分类数据
    classification_path = f'/Users/admin/Downloads/ETF-Index-Classification_{date_str}.xlsx'
    try:
        classification_data = pd.read_excel(classification_path, engine='openpyxl')
        print(f"指数分类文件路径: {classification_path}")
        print(f"指数分类文件总行数: {len(classification_data)}")
        
        # 合并分类数据
        if '跟踪指数代码' in result.columns and '跟踪指数代码' in classification_data.columns:
            result = pd.merge(
                result,
                classification_data,
                on='跟踪指数代码',
                how='left'
            )
            print(f"成功合并指数分类数据")
        else:
            print(f"警告: 无法合并指数分类数据，缺少'跟踪指数代码'列")
    except FileNotFoundError:
        print(f"警告: 指数分类文件不存在: {classification_path}，尝试使用固定路径")
        # 尝试使用固定路径
        classification_path = '/Users/admin/Downloads/ETF-Index-Classification_20240307.xlsx'
        try:
            classification_data = pd.read_excel(classification_path, engine='openpyxl')
            print(f"使用固定路径指数分类文件: {classification_path}")
        except:
            print(f"警告: 无法加载指数分类文件")
    
    # 读取商务协议数据
    商务协议_path = f'/Users/admin/Downloads/ETF单产品商务协议{date_str}.xlsx'
    try:
        商务协议 = pd.read_excel(商务协议_path, engine='openpyxl')
        print(f"商务协议文件路径: {商务协议_path}")
        print(f"商务协议文件总行数: {len(商务协议)}")
        
        # 检查商务协议文件中的证券代码列
        if '证券代码' in 商务协议.columns:
            # 确保证券代码列是字符串类型
            商务协议['证券代码'] = 商务协议['证券代码'].astype(str).str.strip()
            唯一代码数量 = len(商务协议['证券代码'].unique())
            print(f"商务协议中唯一证券代码数量: {唯一代码数量}")
        
    except FileNotFoundError:
        print(f"警告: 商务协议文件不存在: {商务协议_path}，尝试使用固定路径")
        # 尝试使用固定路径
        商务协议_path = '/Users/admin/Downloads/ETF单产品商务协议20240307.xlsx'
        try:
            商务协议 = pd.read_excel(商务协议_path, engine='openpyxl')
            print(f"使用固定路径商务协议文件: {商务协议_path}")
            print(f"商务协议文件总行数: {len(商务协议)}")
        except FileNotFoundError:
            raise FileNotFoundError(f"无法找到任何商务协议文件，请确保文件存在于Downloads目录")
    except Exception as e:
        raise Exception(f"读取商务协议文件出错: {str(e)}")

    # 检查商务协议文件中的列
    print(f"商务协议文件列名: {list(商务协议.columns)}")
    
    # 列名映射
    column_mapping = {
        '开始日期': '合作开始日期',
        '结束日期': '合作结束日期',
        '个人分成比例': '分成比例'  # 使用个人分成比例作为分成比例
    }

    # 重命名列
    for old_col, new_col in column_mapping.items():
        if old_col in 商务协议.columns:
            商务协议.rename(columns={old_col: new_col}, inplace=True)
            print(f"已将列 '{old_col}' 重命名为 '{new_col}'")
    
    # 确保分成比例是数值类型
    if '分成比例' in 商务协议.columns:
        商务协议['分成比例'] = pd.to_numeric(商务协议['分成比例'], errors='coerce')
        # 填充缺失值为默认值0.3
        商务协议['分成比例'].fillna(0.3, inplace=True)
    else:
        # 如果没有分成比例列，添加一个默认值为0.3的列
        商务协议['分成比例'] = 0.3
    
    # 确定要合并的列
    merge_columns = ['证券代码', '是否商务品', '产品名称', '基金公司简称', '分成比例']
    
    # 检查可选列是否存在，如果存在则添加到合并列中
    optional_columns = ['合作开始日期', '合作结束日期']
    for col in optional_columns:
        if col in 商务协议.columns:
            merge_columns.append(col)
        else:
            print(f"警告: 商务协议文件中缺少'{col}'列，将使用默认值")
            # 为缺失的列添加默认值
            商务协议[col] = None
    
    # 合并商务协议数据前的处理
    result['证券代码'] = result['证券代码'].astype(str).str.strip()
    商务协议['是否商务品'] = '商务'
    
    # 检查合并前后的商务品数量
    商务品代码集合 = set(商务协议['证券代码'].unique())
    基础数据代码集合 = set(result['证券代码'].unique())
    未匹配商务品 = 商务品代码集合 - 基础数据代码集合
    
    if len(未匹配商务品) > 0:
        print(f"警告: 有 {len(未匹配商务品)} 个商务品在基础数据中未找到匹配项")
        print(f"未匹配的商务品代码: {sorted(list(未匹配商务品))}")
    
    # 合并商务协议数据
    result = result.merge(
        商务协议[merge_columns],
        on='证券代码',
        how='left'
    ).fillna({'是否商务品': '非商务'})
    
    # 打印合并后的商务品数量
    print(f"合并后的商务品数量: {len(result[result['是否商务品'] == '商务']['证券代码'].unique())}")
    
    # 动态生成数值列
    numeric_cols = []
    for metric in ['关注人数', '持仓客户数', '保有金额']:
        current_col = f'{metric}（{current_str}）'
        previous_col = f'{metric}（{previous_str}）'
        
        # 验证列是否存在
        if current_col not in result.columns:
            available_cols = "\n".join(result.columns)
            raise KeyError(f"列名'{current_col}'不存在，可用列：\n{available_cols}")
        if previous_col not in result.columns:
            available_cols = "\n".join(result.columns)
            raise KeyError(f"列名'{previous_col}'不存在，可用列：\n{available_cols}")
        
        numeric_cols.extend([current_col, previous_col])
        result[f'{metric}变动'] = result[current_col] - result[previous_col]

    # 数值类型转换
    result[numeric_cols] = result[numeric_cols].fillna(0).astype(int)
    
    # 计算商务品预期收入
    result['预期年收入(万元)'] = result.apply(
        lambda x: (x[f'保有金额（{current_str}）'] / 1e8) * (x['管理费率[单位]%'] / 100) * 0.3 * 10000 if x['是否商务品'] == '商务' else 0,
        axis=1
    )
    
    # 计算商务品占比
    result['商务品占比'] = result.apply(
        lambda x: 1 if x['是否商务品'] == '商务' else 0,
        axis=1
    )
    
    # 生成正确日期范围（MMDD-MMDD）
    date_range = f"{previous_date.strftime('%m%d')}-{current_date.strftime('%m%d')}"
    
    return result, date_range, current_str, previous_str