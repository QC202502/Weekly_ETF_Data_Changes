with open('blueprints/search_routes.py', 'r') as f:
    lines = f.readlines()
    if len(lines) > 63:
        print(f'第64行: |{lines[63]}|')
