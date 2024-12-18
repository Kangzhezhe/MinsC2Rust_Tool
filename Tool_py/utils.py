import json
import os
import subprocess
import re
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir,'func_result')))
from extract_rust_func import extract_rust

def debug(*args, **kwargs):
    if 'DEBUG' in os.environ:
        print(*args, **kwargs)

def update_nested_dict(original, updates):
    for key, sub_dict in updates.items():
        if key in original:
            original[key].update(sub_dict)
        else:
            original[key] = sub_dict

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # print("Command output:", result.stdout)
        # print("Command error (if any):", result.stderr)
        return result.stdout
    except subprocess.CalledProcessError as e:
        # print(f"Command '{command}' failed with error: {e.stderr}")
        return e.stderr

def filter_toolchain_errors(compile_error):
    # 使用正则表达式过滤掉工具链的错误信息及其具体内容
    filtered_error = re.sub(r'(?m)^   ::: .*\n(?:.*\n)*', '', compile_error)
    filtered_error = re.sub(r'(?m)^    = note: .*\n(?:.*\n)*', '', filtered_error)
    filtered_error = re.sub(r'(?m)^help: .*\n(?:.*\n)*', '', filtered_error)
    return filtered_error

def run_command_rustc(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Command output:", result.stdout)
        print("Command error (if any):", result.stderr)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with error: {e.stderr}")
        explanations = explain_errors(e.stderr)
        print(explanations)
        return e.stderr + explanations

def explain_errors(stderr, max_length=1000):
    explanations = ""
    # 提取错误代码
    error_codes = set(re.findall(r"error\[\w+\]", stderr))
    for error_code in error_codes:
        code = error_code.strip("error[]")
        explain_command = f"rustc --explain {code}"
        try:
            result = subprocess.run(explain_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            explanation = result.stdout
            # 截断解释内容
            if len(explanation) > max_length:
                explanation = explanation[:max_length] + '... [truncated]'
            explanations += f"\nExplanation for {error_code}:\n{explanation}"
        except subprocess.CalledProcessError as e:
            explanations += f"\nFailed to explain error '{error_code}': {e.stderr}"
    return explanations


def remove_markdown_code_block(text):
    # 创建正则表达式来匹配代码块标记
    text = re.sub(r"```.*?\n", "", text)
    # 去除剩余的代码块结束标记
    text = re.sub(r"```", "", text)
    return text

def traverse_dir(dir_path, header_files, source_files):
    for root, _, files in os.walk(dir_path):
        for file in files:
            path = os.path.join(root, file)
            if file.endswith(".h"):
                with open(path, 'r') as f:
                    header_files[file] = f.read()
            elif file.endswith(".c"):
                with open(path, 'r') as f:
                    source_files[file] = f.read()

def get_filename(filepath):
    """
    获取文件名并去除后缀
    :param filepath: 文件路径
    :return: 去除后缀的文件名
    """
    filename = os.path.basename(filepath)
    filename_without_extension = os.path.splitext(filename)[0]
    return filename_without_extension


def get_functions_by_line_numbers(definitions, line_numbers):
    function_names = set()
    for line in line_numbers:
        line = int(line)
        for func in definitions:
            if func['start_line'] <= line <= func['end_line']:
                function_names.add(func['name'])
    return function_names


def deduplicate_code(all_function_lines,tmp_dir):
    with open(os.path.join(tmp_dir,'test_source.rs'), 'w') as f:
        f.write(all_function_lines)

    json_file_path = os.path.join(tmp_dir,'definitions.json')


    run_command(f"cd ../rust_ast_project/ && cargo run {os.path.join(tmp_dir,'test_source.rs')} {json_file_path}")

    source_file_path = os.path.join(tmp_dir,'test_source.rs')
    output_file_path = os.path.join(tmp_dir,'processed_file.rs')
    non_function_content, function_content_dict= extract_rust(json_file_path, source_file_path, output_file_path)
    non_function_content = ''.join(non_function_content)
    
    non_function_content += '\n'
    output_content = non_function_content + '\n'+'\n'.join(function_content_dict.values())
    return non_function_content, function_content_dict,output_content

def clean_and_validate_json(output):
    # 去除不可见字符
    output = re.sub(r'[\x00-\x1F\x7F]', '', output)

    # 使用正则表达式去除多余的空格和换行符
    output = re.sub(r'\s+', ' ', output).strip()

    # 将单引号替换为双引号
    output = output.replace("'", '"')

    # 尝试修复常见的 JSON 格式问题
    # 确保 key 和 value 是用双引号括起来的
    output = re.sub(r'(\w+)\s*:\s*([^",{}\[\]]+)', r'"\1": "\2"', output)

    try:
        json_obj = json.loads(output)
        return json_obj
    except json.JSONDecodeError:
        return None


def delete_file_if_exists(file_path):
    """
    如果文件存在则删除文件。

    参数:
    file_path (str): 要删除的文件路径。
    """
    if os.path.exists(file_path):
        os.remove(file_path)