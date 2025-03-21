# ETF价格数据获取工具

这个工具用于获取所有ETF的每日收盘价信息，包括代码、场内简称、当日涨跌幅、近五日涨跌幅、年初至今涨跌幅等数据。

## 功能特点

- 获取所有ETF基金列表
- 获取ETF每日价格数据
- 计算当日涨跌幅、近五日涨跌幅、年初至今涨跌幅
- 将数据保存为CSV文件
- 支持获取特定日期的ETF数据

## 使用方法

### 准备工作

1. 确保已安装所需依赖：
   ```
   pip install -r requirements.txt
   ```

### 使用命令行工具

```bash
# 基本用法 - 获取ETF数据
python get_etf_prices_akshare_fixed.py

# 指定日期范围
python get_etf_prices_akshare_fixed.py -s 2025-01-01 -e 2025-12-31

# 指定输出文件名
python get_etf_prices_akshare_fixed.py -o my_etf_data.csv

# 获取所有ETF数据
python get_etf_prices_akshare_fixed.py -a

# 获取指定数量的ETF数据
python get_etf_prices_akshare_fixed.py -n 10

# 获取特定日期的ETF数据
python get_etf_data_20250319.py
```

### 参数说明

#### get_etf_prices_akshare_fixed.py
- `-s, --start`: 指定开始日期(格式:YYYY-MM-DD)
- `-e, --end`: 指定结束日期(格式:YYYY-MM-DD)
- `-o, --output`: 指定输出文件名
- `-n, --number`: 要获取的ETF数量，默认为5
- `-a, --all`: 获取所有ETF数据
- `-p, --proxy`: 启用代理功能
- `-r, --retries`: 最大重试次数，默认为3
- `--no-proxy`: 禁用所有代理设置
- `-d, --debug`: 启用调试模式

#### get_etf_data_20250319.py
这个脚本专门用于获取2025年3月19日的ETF数据，不需要额外参数。

## 数据说明

生成的CSV文件包含以下字段：

- `TS代码`: ETF的TS代码
- `代码`: ETF代码
- `场内简称`: ETF名称
- `交易日期`: 数据日期
- `收盘价`: ETF收盘价
- `当日涨跌幅(%)`: 当日涨跌幅
- `近五日涨跌幅(%)`: 近五日涨跌幅
- `年初至今涨跌幅(%)`: 年初至今涨跌幅

## 数据存储

数据默认保存在项目的`data`目录下，文件名格式为`ETF_价格数据_YYYYMMDD.csv`。

## 关于AKShare

AKShare是一个开源的金融数据接口库，可以免费获取ETF数据，不需要特殊权限。本工具使用AKShare替代了原来的Tushare API，以便更方便地获取ETF数据。