with open('blueprints/search_routes.py', 'r') as f:
    lines = f.readlines()

# 找到问题区域并修复
for i in range(290, 310):
    if i < len(lines) and 'else:' in lines[i] and lines[i].startswith('        else:'):
        # 修复缩进
        lines[i] = lines[i].replace('        else:', '            else:')
        print(f'已修复第{i+1}行: {lines[i].strip()}')
        
        # 修复接下来的缩进块
        j = i + 1
        while j < len(lines) and (lines[j].strip() == '' or lines[j].startswith('                ')):
            if lines[j].startswith('                '):
                lines[j] = '            ' + lines[j][16:]
                print(f'已修复第{j+1}行缩进')
            j += 1

# 写回文件
with open('blueprints/search_routes.py', 'w') as f:
    f.writelines(lines)

print('修复完成')
