import json
import os

def read_json_file(json_file_path):
    if not os.path.exists(json_file_path):
        return ''
    with open(json_file_path, 'r') as file:
        return json.load(file)

def read_source_file(source_file_path):
    with open(source_file_path, 'r') as file:
        return file.readlines()  # list类型

def write_output_file(output_file_path, content):
    with open(output_file_path, 'w') as file:
        file.writelines(content)

def extract_code_snippet(lines, start_line, end_line):
    return ''.join(lines[start_line - 1:end_line]) + '\n'

def process_definitions(definitions, source_lines, output_file_path):
    seen_functions = {}
    function_content = []
    non_function_content = []
    function_content_dict = {}

    function_lines = set()
    for definition in definitions:
        if definition['type'] == 'Function':
            start_line = definition['start_line']
            end_line = definition['end_line']
            function_lines.update(range(start_line, end_line + 1))

    for i, line in enumerate(source_lines, start=1):
        if i not in function_lines:
            non_function_content.append(line)

    for definition in definitions:
        if definition['type'] == 'Function':
            function_name = definition['name']
            start_line = definition['start_line']
            end_line = definition['end_line']
            # 记录最后一个出现的函数定义
            seen_functions[function_name] = (start_line, end_line)

    # 按 start_line 和 end_line 排序
    sorted_functions = sorted(seen_functions.items(), key=lambda item: (item[1][0], item[1][1]))

    for function_name, (start_line, end_line) in sorted_functions:
        code_snippet = extract_code_snippet(source_lines, start_line, end_line)
        function_content.append(code_snippet)
        function_content_dict[function_name] = code_snippet

    output_content = non_function_content + function_content
    write_output_file(output_file_path, output_content)
    return non_function_content, function_content_dict

def extract_rust(json_path, source_path, output_path):
    definitions = read_json_file(json_path)
    source_lines = read_source_file(source_path)
    return process_definitions(definitions, source_lines, output_path)

if __name__ == '__main__':
    json_file_path = '../rust_ast_project/definitions.json'
    source_file_path = 'test_source.rs'
    output_file_path = 'processed_file.rs'
    extract_rust(json_file_path, source_file_path, output_file_path)