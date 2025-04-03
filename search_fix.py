#!/usr/bin/env python3
"""
修复search_routes.py文件中的缩进问题
"""

import re

def fix_indentation():
    """修复search_routes.py中的缩进问题"""
    
    # 读取原始文件
    with open('blueprints/search_routes.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复第63行周围的缩进问题
    if len(lines) >= 70:
        # 确保第63行是if语句并且有正确的缩进
        if 'if request.form' in lines[62]:
            lines[62] = '        if request.form and \'code\' in request.form:\n'
    
    # 修复第299行附近的else缩进问题
    found_else_issue = False
    for i in range(290, 310):
        if i < len(lines) and lines[i].strip() == 'else:':
            # 找到孤立的else
            found_else_issue = True
            # 检查上下文并适当缩进
            if 'results = db.general_search(keyword)' in ''.join(lines[i-30:i]):
                lines[i] = '        else:\n'
    
    # 写回修复后的文件
    with open('blueprints/search_routes.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("已尝试修复search_routes.py中的缩进问题")

if __name__ == "__main__":
    fix_indentation() 