import configparser
import os
import re
import sys
import json
from parse_config import read_config

# 读取文件内容
def read_file(filename):
    with open(filename, 'r') as file:
        return file.readlines()

# 解析 #include 指令并替换为相应的 .h 文件内容，并将结果保存到输出文件
def merge_files(c_filename, output_filename, include_dirs):
    include_pattern = re.compile(r'#include\s+"(.+\.h)"')
    merged_lines = []
    included_files = []

    # 读取 .c 文件内容
    c_file_lines = read_file(c_filename)

    for line in c_file_lines:
        match = include_pattern.match(line)
        if match:
            h_filename = match.group(1)
            h_file_lines = None
            for include_dir in include_dirs:
                h_filepath = os.path.join(include_dir, h_filename)
                if os.path.exists(h_filepath):
                    h_file_lines = read_file(h_filepath)
                    included_files.append(os.path.splitext(os.path.basename(h_filepath))[0])  # 去掉路径和后缀
                    break
            if h_file_lines:
                merged_lines.extend(h_file_lines)
            else:
                print(f"Warning: {h_filename} not found in any include directories.")
                merged_lines.append(include_pattern.sub(f'#include "{h_filename}"', line))
        else:
            merged_lines.append(line)

    # 将合并后的内容写入输出文件
    with open(output_filename, 'w') as output_file:
        output_file.writelines(merged_lines)

    print(f"Merged file saved to {output_filename}")
    return included_files

def read_compile_commands(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def process_files(compile_commands_path, output_dir):
    # 读取 compile_commands.json 文件
    compile_commands = read_compile_commands(compile_commands_path)

    # 存储每个 .c 文件及其包含的 .h 文件的字典
    include_dict = {}
    all_file_paths = []
    excluded_files = {"alloc-testing", "test-alloc-testing", "framework"}

    # 处理每个 .c 文件
    for entry in compile_commands:
        c_filename = entry['file']
        # 确定输出文件的子目录
        if 'src' in c_filename:
            sub_dir = 'src'
        elif 'test' in c_filename:
            sub_dir = 'test'
        else:
            sub_dir = ''

        # 创建输出子目录（如果不存在）
        output_sub_dir = os.path.join(output_dir, sub_dir)
        os.makedirs(output_sub_dir, exist_ok=True)

        output_filename = os.path.join(output_sub_dir, os.path.basename(c_filename))
        include_dirs = [arg[2:] for arg in entry.get('command','').split() if arg.startswith('-I')]

        # 合并文件内容并保存到输出文件
        included_files = merge_files(c_filename, output_filename, include_dirs)
        if output_filename not in all_file_paths:
            all_file_paths.append(output_filename)
        filtered_files = [f for f in included_files if f not in excluded_files]
        key = os.path.splitext(os.path.basename(c_filename))[0]
        if key not in excluded_files:
            include_dict[key] = [f for f in filtered_files if f != key]  # 去掉路径和后缀，并排除与键相同的值

    return include_dict,all_file_paths

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python merge_c_h.py <config_path>")
        sys.exit(1)
    config_path = sys.argv[1]
    cfg = read_config(config_path)
    compile_commands_path = cfg['Paths']['compile_commands_path']
    tmp_dir = cfg['Paths']['tmp_dir']

    # 处理文件并获取包含的 .h 文件字典
    include_dict = process_files(compile_commands_path, tmp_dir)
    # print(json.dumps(include_dict, indent=4))