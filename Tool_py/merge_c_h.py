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

def merge_files(c_filename, output_filename, include_dirs):
    include_pattern_local = re.compile(r'#\s*include\s+"(.+\.h)"')
    include_pattern_angle = re.compile(r'#\s*include\s+<(.+\.h)>')
    merged_lines = []
    included_files = set()

    def process_file(filename, include_dirs):
        lines = read_file(filename)
        result_lines = []
        for line in lines:
            match_local = include_pattern_local.match(line)
            match_angle = include_pattern_angle.match(line)
            h_filename = None
            if match_local:
                h_filename = match_local.group(1)
            elif match_angle:
                h_filename = match_angle.group(1)
            if h_filename:
                h_file_lines = None
                h_filepath = None
                for include_dir in include_dirs:
                    h_filepath = os.path.join(include_dir, h_filename)
                    if os.path.exists(h_filepath):
                        if h_filepath not in included_files:
                            included_files.add(h_filepath)
                            h_file_lines = process_file(h_filepath, include_dirs)
                        else:
                            # print(f"Skipping duplicate include: {h_filename}")
                            pass
                        break
                if h_file_lines:
                    result_lines.extend(h_file_lines)
                elif h_filepath and h_filepath not in included_files:
                    # print(f"Warning: {h_filename} not found in any include directories.")
                    result_lines.append(line)
                else:
                    # 已经包含过，跳过
                    pass
            else:
                result_lines.append(line)
        return result_lines

    merged_lines = process_file(c_filename, include_dirs)

    with open(output_filename, 'w') as output_file:
        output_file.writelines(merged_lines)

    print(f"Merged file saved to {output_filename}")
    return [os.path.splitext(os.path.basename(f))[0] for f in included_files]

def read_compile_commands(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def process_compile_commands(compile_commands_path):
    compile_commands = read_compile_commands(compile_commands_path)
    for entry in compile_commands:
        if entry.get('command','') == '' and entry.get('arguments','') != '':
            directory = entry['directory']
            updated_arguments = []
            for arg in entry['arguments']:
                if arg.startswith('-I'):
                    include_path = arg[2:]  # 提取 -I 后的路径
                    if not os.path.isabs(include_path):  # 如果是相对路径
                        absolute_path = os.path.normpath(os.path.join(directory, include_path))
                        updated_arguments.append(f'-I{absolute_path}')
                    else:
                        updated_arguments.append(arg)
                else:
                    updated_arguments.append(arg)
            entry['arguments'] = updated_arguments
            entry['command'] = ' '.join(updated_arguments)

    with open(compile_commands_path, 'w') as file:
        json.dump(compile_commands, file, indent=4)
    return compile_commands

def process_files(compile_commands_path, output_dir, excluded_files = {"alloc-testing", "test-alloc-testing", "framework"}):
    # 读取 compile_commands.json 文件
    compile_commands = process_compile_commands(compile_commands_path)

    # 存储每个 .c 文件及其包含的 .h 文件的字典
    include_dict = {}
    all_file_paths = []
    processed_c_files = set()  # 记录已处理的.c文件基础名称

    # 收集所有包含目录
    all_include_dirs = set()
    for entry in compile_commands:
        include_dirs = {arg[2:] for arg in entry.get('command','').split() if arg.startswith('-I')}
        all_include_dirs.update(include_dirs)

    # 处理每个 .c 文件
    for entry in compile_commands:
        c_filename = entry['file']
        
        # 确定输出文件的子目录：只有以'test-'开头的文件才放入test目录
        if os.path.basename(c_filename).startswith('test-'):
            sub_dir = 'test'
        else:
            sub_dir = 'src'

        # 创建输出子目录（如果不存在）
        output_sub_dir = os.path.join(output_dir, sub_dir)
        os.makedirs(output_sub_dir, exist_ok=True)

        output_filename = os.path.join(output_sub_dir, os.path.basename(c_filename))

        include_dirs = {arg[2:] for arg in entry.get('command','').split() if arg.startswith('-I')}

        # 合并文件内容并保存到输出文件
        included_files = merge_files(c_filename, output_filename, include_dirs)
        
        if output_filename not in all_file_paths:
            all_file_paths.append(output_filename)
        
        filtered_files = [f for f in included_files if f not in excluded_files]
        key = os.path.splitext(os.path.basename(c_filename))[0]
        
        if key not in excluded_files:
            include_dict[key] = [f for f in filtered_files if f != key]
            processed_c_files.add(key)  # 记录已处理的.c文件基础名称

    # 处理独立的.h文件（没有对应.c文件的头文件）
    standalone_h_files = []

    for include_dir in all_include_dirs:
        if os.path.exists(include_dir):
            for root, dirs, files in os.walk(include_dir):
                for filename in files:
                    if filename.endswith('.h'):
                        h_basename = os.path.splitext(filename)[0]
                        
                        # 检查是否有对应的.c文件已经被处理
                        if h_basename not in processed_c_files and h_basename not in excluded_files:
                            h_filepath = os.path.join(root, filename)
                            
                            # 避免重复处理同名的头文件
                            if h_basename not in [os.path.splitext(os.path.basename(f))[0] for f in standalone_h_files]:
                                standalone_h_files.append(h_filepath)

    # 处理独立的.h文件
    for h_filepath in standalone_h_files:
        try:
            filename = os.path.basename(h_filepath)
            h_basename = os.path.splitext(filename)[0]
            
            # 确定输出子目录：只有以'test-'开头的文件才放入test目录
            if filename.startswith('test-'):
                sub_dir = 'test'
            else:
                sub_dir = 'src'
            
            output_sub_dir = os.path.join(output_dir, sub_dir)
            os.makedirs(output_sub_dir, exist_ok=True)
            
            # 创建对应的输出文件名，将.h改为.c
            output_h_filename = os.path.join(output_sub_dir, h_basename + '.c')
            
            # 处理独立的.h文件
            included_files = merge_files(h_filepath, output_h_filename, all_include_dirs)
            
            if output_h_filename not in all_file_paths:
                all_file_paths.append(output_h_filename)
            
            filtered_files = [f for f in included_files if f not in excluded_files]
            include_dict[h_basename] = [f for f in filtered_files if f != h_basename]
            
            print(f"Processed standalone header: {h_filepath} -> {output_h_filename}")
            
        except Exception as e:
            print(f"Warning: Could not process {h_filepath}: {e}")

    return include_dict, all_file_paths

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