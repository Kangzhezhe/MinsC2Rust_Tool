import json
import subprocess
import os
import re

def generate_ctags(c_file, tags_file='tags.json'):
    # 如果标签文件已经存在，删除它
    if os.path.exists(tags_file):
        os.remove(tags_file)
    
    # 生成 ctags 标签文件
    subprocess.run(['ctags', '-R', '--c-kinds=+pxd', '--fields=+S', '--extras=+q', '--output-format=json', '-f', tags_file, c_file], check=True)

def parse_ctags_json(filename, c_file):
    structs = set()
    globals = set()
    macros = set()
    typedefs = set()

    with open(c_file, 'r') as f:
        content = f.read()

    with open(filename, 'r') as f:
        for line in f:
            tag = json.loads(line)
            if 'kind' not in tag:
                continue
            pattern = tag.get('pattern', '').strip('/^$/')
            if tag['kind'] == 'struct':
                match = re.search(re.escape(pattern) + r'[^}]*};', content, re.DOTALL)
                if match:
                    structs.add(match.group(0))
            elif tag['kind'] == 'variable':
                if pattern.endswith(';'):
                    globals.add(pattern)
                else:
                    match = re.search(re.escape(pattern) + r'[^;]*;', content)
                    if match:
                        globals.add(match.group(0))
            elif tag['kind'] == 'macro':
                match = re.search(re.escape(pattern) + r'.*', content)
                if match:
                    macros.add(match.group(0))
            elif tag['kind'] == 'typedef':
                if pattern.endswith(';'):
                    typedefs.add(pattern)
                else:
                    match = re.search(re.escape(pattern) + r'[^;]*;', content)
                    if match:
                        typedefs.add(match.group(0))

    return list(structs), list(globals), list(macros), list(typedefs)

def extract_info_from_c_file(c_file):
    tags_file = 'tags.json'
    generate_ctags(c_file, tags_file)
    structs, globals, macros, typedefs = parse_ctags_json(tags_file, c_file)
    if os.path.exists(tags_file):
        os.remove(tags_file)
    return f"\n\nStructs: {structs}\n\nGlobals: {globals}\n\nMacros: {macros}\n\nTypedefs: {typedefs}"

if __name__ == '__main__':
    # 示例用法
    c_file = '../tmp/test/test-binomial-heap.c'
    
    # 提取信息
    result = extract_info_from_c_file(c_file)
    
    # 打印结果
    print(result)