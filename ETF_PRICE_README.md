# ETF价格数据获取工具

这个工具用于获取所有ETF的每日收盘价信息，包括代码、场内简称、当日涨跌幅、近五日涨跌幅、年初至今涨跌幅等数据。

## 功能特点

- 获取所有ETF基金列表
- 获取ETF每日价格数据
- 计算当日涨跌幅、近五日涨跌幅、年初至今涨跌幅
- 将数据保存为CSV文件

## 使用方法

### 准备工作

1. 确保已安装所需依赖：
   ```
   pip install -r requirements.txt
   ```

2. 获取Tushare API令牌：
   - 访问 [Tushare官网](https://tushare.pro/) 注册并获取API令牌
   - 设置环境变量：`export TUSHARE_TOKEN=你的令牌`

### 使用命令行工具

```bash
# 基本用法
python get_etf_prices.py -t 你的TUSHARE令牌

# 指定日期范围
python get_etf_prices.py -t 你的TUSHARE令牌 -s 20230101 -e 20231231

# 指定输出文件名
python get_etf_prices.py -t 你的TUSHARE令牌 -o my_etf_data.csv
```

### 参数说明

- `-t, --token`: 指定tushare API令牌
- `-s, --start`: 指定开始日期(格式:YYYYMMDD)
- `-e, --end`: 指定结束日期(格式:YYYYMMDD)
- `-o, --output`: 指定输出文件名

### 测试脚本

还提供了一个测试脚本，可以用来测试ETF价格追踪器的功能：

```bash
python test_etf_tracker.py 你的TUSHARE令牌
```

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