def normalize_etf_code(code):
    """
    标准化ETF代码，去除.SH/.SZ后缀
    
    参数:
        code: 原始ETF代码
        
    返回:
        标准化后的ETF代码
    """
    if not code:
        return code
    
    code = str(code).strip()
    # 去除.SH/.SZ后缀
    code = code.replace('.SH', '').replace('.SZ', '')
    # 确保是6位数字
    return code.zfill(6) 