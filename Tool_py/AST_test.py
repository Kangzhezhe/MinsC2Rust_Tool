# 导入必要的模块
from pycparser import parse_file, c_ast
from pycparser.plyparser import ParseError
import json
from ctags_parse import extract_info_from_c_file
import os
from utils import delete_file_if_exists

current_dir = os.path.dirname(os.path.abspath(__file__))
fake_libc_include_path = os.path.abspath(os.path.join(current_dir, '../fake_libc_include'))
print(f"fake_libc_include_path: {fake_libc_include_path}")


# 忽略标准库头文件
def parse_c_file(filename):
    try:
        # 使用 parse_file 方法解析文件，并忽略标准库头文件
        # 指定 cpp 路径
        ast = parse_file(filename, use_cpp=True,
                         cpp_path='/usr/bin/cpp',
                         cpp_args=f'-I{fake_libc_include_path}')
        print("解析成功，生成的 AST 树如下：")
        return ast
    except ParseError as e:
        print(f"解析错误: {e}")
        exit(1)

# 查找函数定义的访问者类
class FunctionVisitor(c_ast.NodeVisitor):
    def __init__(self, func_signature):
        self.func_signature = func_signature
        self.context = []

    def visit_FuncDef(self, node):
        if self.match_function_signature(node):
            self.context.append(node)
        self.generic_visit(node)

    def match_function_signature(self, node):
        # 获取函数名
        func_name = node.decl.name
        return func_name == self.func_signature

# 获取函数上下文
def get_function_context(ast, func_signature):
    visitor = FunctionVisitor(func_signature)
    visitor.visit(ast)
    return visitor.context

# 获取函数定义的行号
def get_function_lines(node):
    lines = []
    if hasattr(node, 'coord') and node.coord:
        lines.append(node.coord.line)
    for child in node.children():
        lines.extend(get_function_lines(child[1]))
    return lines

# 获取函数定义的起始和结束行号
def get_function_start_end_lines(node):
    start_line = node.coord.line if hasattr(node, 'coord') and node.coord else None
    end_line = max(get_function_lines(node)) if start_line else None
    return start_line, end_line

# 针对src/test文件
def  content_extract(func_json_path, read_c_path, save_json_path):
    with open(func_json_path,"r") as f:
        data = json.load(f)
    for item in data :
        for file_name,funcs in item.items():
            # 文件路径,目前针对arraylist
            filename = f"{read_c_path}/{file_name}.c"
            output_filename = "function_context.txt"
            # 解析文件
            ast = parse_c_file(filename)
            # 将文件包含所有函数分割
            result = {}
            all_function_lines = set()

            # 获取指定函数的上下文
            for func in funcs:
                func_signature = func
                context = get_function_context(ast, func_signature)

                # 获取文件内容
                with open(filename, 'r') as file:
                    file_lines = file.readlines()

                # 将结果写入文件
                with open(output_filename, 'w') as file:
                    for node in context:
                        start_line, end_line = get_function_start_end_lines(node)
                        if start_line and end_line:
                            # 检查最后一行是否以 '}' 结束
                            if not file_lines[end_line - 1].strip().endswith('}'):
                                end_line += 1
                            file.writelines(file_lines[start_line-1:end_line])
                            all_function_lines.update(range(start_line, end_line + 1))

                # 将结果读取成json格式
                with open(output_filename, 'r', encoding='utf-8') as file:
                    content = file.read()
                    result[func_signature] = content
            
            delete_file_if_exists("function_context.txt")

            # 计算extra字段
            extra_content = []
            with open(filename, 'r') as file:
                file_lines = file.readlines()
                for i, line in enumerate(file_lines, start=1):
                    if i not in all_function_lines:
                        extra_content.append(line)

            # 将函数外的内容保存到extra字段
            result["extra"] = ''.join(extra_content)
            details = extract_info_from_c_file(filename)
            result["extra"] = f"details: [{details}], extract_info: [{result['extra']}]"

            # 使用 json.dump 将数据写入文件
            os.makedirs(save_json_path, exist_ok=True)
            output_file = f'{save_json_path}/{file_name}.json'
            with open(output_file, 'w') as json_file:
                json.dump(result, json_file, indent=4)


