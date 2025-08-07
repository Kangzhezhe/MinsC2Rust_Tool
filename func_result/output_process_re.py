import re
import json

# 正则表达式模式，用于匹配函数名和文件名的基础部分
pattern_func = re.compile(r'^(\w+)\(.*\)$')
pattern_file = re.compile(r'^(.+)\.\w+$')

def extract_function_names(func):
    return pattern_func.match(func).group(1)

def process_file_func_name(json_path, processed_json_path):
    # json.load 加载数据
    with open(json_path, 'r') as file:
        data = json.load(file)

    # 处理数据
    processed_data = {}
    for entry in data:
        for file, functions in entry.items():
            # 使用正则表达式处理文件名
            base_filename = pattern_file.match(file).group(1)
            # 使用正则表达式处理函数名
            processed_functions = [pattern_func.match(func).group(1) for func in functions]
            # 将处理过的文件名和函数名添加到新的字典中
            processed_data[base_filename] = processed_functions
    result = []
    result.append(processed_data)
    # json.dump 将数据写入文件
    with open(processed_json_path, 'w') as json_file:
        json.dump(result, json_file, indent=4)
