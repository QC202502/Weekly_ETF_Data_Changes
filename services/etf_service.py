def get_manager_short(full_name):
    """基金管理人简称提取"""
    special_mapping = {
        '汇添富基金管理有限公司': '汇添富',
        '易方达基金管理有限公司': '易方达',
        '华夏基金管理有限公司': '华夏',
        '南方基金管理股份有限公司': '南方',
        '嘉实基金管理有限公司': '嘉实'
    }
    if full_name in special_mapping:
        return special_mapping[full_name]

    patterns = ['基金管理有限公司', '基金管理公司', '基金', '管理有限公司', '股份有限公司']
    for pattern in patterns:
        if pattern in full_name:
            return full_name.split(pattern)[0]

    return full_name[:4] if len(full_name) >= 4 else full_name

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

def get_management_fee(row):
    """获取正确的管理费率"""
    management_fee = None
    for col in row.index:
        if '管理费率' in col and '托管' not in col:
            if pd.notna(row[col]):
                management_fee = row[col]
                break
    return management_fee

def get_trading_volume(row):
    """获取交易额"""
    volume = None
    for col in row.index:
        if '交易额' in col or '日均' in col:
            if pd.notna(row[col]):
                volume = row[col]
                break
    return volume