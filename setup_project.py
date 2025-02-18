import os
import shutil

# 创建项目目录结构
def create_project_structure():
    # 创建主目录
    dirs = [
        'versions',
    ]
    
    for dir in dirs:
        os.makedirs(dir, exist_ok=True)
    
    # 移动现有文件到versions目录
    if os.path.exists('ETF业务周报v1.0.py'):
        shutil.move('ETF业务周报v1.0.py', 'versions/ETF业务周报v1.0.py')
    if os.path.exists('ETF业务周报v1.1.py'):    
        shutil.move('ETF业务周报v1.1.py', 'versions/ETF业务周报v1.1.py')

    # 创建 .gitignore 文件
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write('''# Python
__pycache__/
*.py[cod]
*$py.class

# 数据文件
*.csv
*.xlsx
*.xls

# 生成的报告
*.docx
*.pdf

# 系统文件
.DS_Store
Thumbs.db
''')

if __name__ == '__main__':
    create_project_structure()
    print("项目目录结构创建完成!") 