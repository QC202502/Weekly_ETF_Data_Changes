with open('blueprints/search_routes.py', 'r') as f:
    lines = f.readlines()
    for i in range(62, 65):
        if i < len(lines):
            print(f'第{i+1}行: |{lines[i]}|')
