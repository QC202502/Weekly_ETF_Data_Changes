#!/usr/bin/env python3

with open('blueprints/search_routes.py', 'r') as f:
    lines = f.readlines()

# 修复问题
for i in range(len(lines)):
    if 'keyword = request.form.get' in lines[i]:
        indent = ' ' * 8  # 8个空格的缩进
        content = lines[i].lstrip()
        lines[i] = indent + content
        print(f"已修复第{i+1}行: {lines[i].rstrip()}")

# 写回文件
with open('blueprints/search_routes.py', 'w') as f:
    f.writelines(lines)

print("修复完成") 