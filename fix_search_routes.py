#!/usr/bin/env python3
"""
修复search_routes.py中的缩进问题
"""

with open('blueprints/search_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 定位并修复第299行附近的else问题
lines = content.splitlines()

# 查看298-300行附近的代码
print("原始第298-300行:")
for i in range(297, 302):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}")

# 修复第299行的else缩进，将其改为在适当的缩进级别
if len(lines) > 298 and lines[298].strip() == 'else:':
    # 获取适当的缩进级别(对应上面的if语句)
    for i in range(298, 0, -1):
        if 'if results:' in lines[i]:
            # 找到匹配的if语句，使用相同的缩进
            indent = lines[i].split('if')[0]
            lines[298] = indent + 'else:'
            break

# 保存修改后的文件
with open('blueprints/search_routes.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("\n修复后的第298-300行:")
for i in range(297, 302):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}")

print("\n修复完成。") 