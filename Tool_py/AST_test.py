# 导入必要的模块
from collections import defaultdict
from pycparser import parse_file, c_ast
from pycparser.plyparser import ParseError
import json
from ctags_parse import extract_info_from_c_file
import os
from utils import delete_file_if_exists

current_dir = os.path.dirname(os.path.abspath(__file__))
fake_libc_include_path = os.path.abspath(os.path.join(current_dir, '../fake_libc_include'))
print(f"fake_libc_include_path: {fake_libc_include_path}")

# 查找函数调用的访问者类
class FunctionCallVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.function_calls = defaultdict(list)
        self.current_function = None
        self.function_stack = []

    def visit_FuncDef(self, node):
        self.function_stack.append(node.decl.name)
        self.current_function = node.decl.name
        self.generic_visit(node)
        self.function_stack.pop()
        self.current_function = self.function_stack[-1] if self.function_stack else None

    def visit_FuncCall(self, node):
        if isinstance(node.name, c_ast.ID):
            self.function_calls[self.current_function].append(node.name.name)
        self.generic_visit(node)


class FunctionDefVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.functions = set()

    def visit_FuncDef(self, node):
        self.functions.add(node.decl.name)
        self.generic_visit(node)

    def visit_Decl(self, node):
        if isinstance(node.type, c_ast.FuncDecl):
            self.functions.add(node.name)
        self.generic_visit(node)


# 忽略标准库头文件
def parse_c_file(filename):
    try:
        # 使用 parse_file 方法解析文件，并忽略标准库头文件
        # 指定 cpp 路径
        ast = parse_file(filename, use_cpp=True,
                         cpp_path='/usr/bin/cpp',
                         cpp_args=[
                             f'-I{fake_libc_include_path}'
                             ])

        # print("解析成功，生成的 AST 树如下：")
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
                    if content:
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
            result["extra"] = f"{details} extract_info: [{result['extra']}]"
            # 使用 json.dump 将数据写入文件
            os.makedirs(save_json_path, exist_ok=True)
            output_file = f'{save_json_path}/{file_name}.json'
            with open(output_file, 'w') as json_file:
                json.dump(result, json_file, indent=4)

            data[0][file_name] = [key for key in result.keys() if key != 'extra']
    
    with open(func_json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

            


# 文件范围内函数指针依赖访问者
class FileScopeFunctionPointerVisitor(c_ast.NodeVisitor):
    def __init__(self, defined_functions):
        self.defined_functions = defined_functions  # 文件内定义的函数
        self.global_function_pointers = defaultdict(list)  # 每个函数的全局依赖
        self.current_function = None  # 当前函数名
        self.local_symbols = set()  # 当前函数体内定义的局部符号
        self.excluded_functions = ['alloc_test_malloc', 'alloc_test_free', 'alloc_test_calloc', 'alloc_test_strdup', 'alloc_test_realloc','alloc_test_set_limit','alloc_test_get_allocated']
        self.in_function_body = False  # 标志位，表示是否在函数体内

    def visit_FuncDef(self, node):
        """
        处理函数定义，收集函数体内的全局函数依赖。
        """
        self.in_function_body = True  # 进入函数体
        self.current_function = node.decl.name
        self.local_symbols = set()  # 重置局部符号
        self.collect_local_symbols(node.body)  # 收集局部变量
        self.generic_visit(node)  # 遍历函数体
        self.in_function_body = False  # 退出函数体

    def visit_ID(self, node):
        """
        捕获函数体内所有出现的标识符（包括函数指针）。
        """
        if not self.in_function_body or self.current_function is None:
            return

        identifier = node.name
        if (
            identifier
            and identifier not in self.local_symbols  # 排除局部定义
            and identifier in self.defined_functions  # 必须是当前文件定义的
            and identifier != self.current_function  # 排除对自身的调用
            and identifier not in self.excluded_functions  # 排除特定函数
        ):
            self.global_function_pointers[self.current_function].append(identifier)

    def collect_local_symbols(self, node):
        """
        收集函数体内定义的局部变量。
        """
        for child_name, child in node.children():
            if isinstance(child, c_ast.Decl):
                if isinstance(child.type, c_ast.FuncDecl):
                    continue  # 跳过函数声明
                self.local_symbols.add(child.name)
            self.collect_local_symbols(child)


# 获取全局函数指针依赖
def get_global_function_pointer_dependencies(filenames):
    """
    获取函数体内部的全局函数指针依赖（未在函数体内定义，但出现在当前文件内定义的函数）。
    :param filenames: C 文件路径列表
    :return: 字典，键为函数名，值为全局函数指针依赖列表
    """
    dependencies = defaultdict(list)

    for file in filenames:
        ast = parse_c_file(file)

        # 获取定义的函数
        fd_visitor = FunctionDefVisitor()
        fd_visitor.visit(ast)
        defined_functions = fd_visitor.functions

        # 获取函数体内的函数指针依赖
        fc_visitor = FileScopeFunctionPointerVisitor(defined_functions)
        fc_visitor.visit(ast)

        fnc_visitor = FunctionCallVisitor()
        fnc_visitor.visit(ast)

        for func_name, pointers in fc_visitor.global_function_pointers.items():
            filtered_pointers = [pointer for pointer in pointers if pointer not in fnc_visitor.function_calls.get(func_name, [])]
            if filtered_pointers:
                dependencies[func_name] = list(set(filtered_pointers))  # 对依赖去重

    return dependencies

if __name__ == "__main__":
    dependencies = parse_c_file("/home/mins01/exp/time/Output/tmp/src/version-etc.c")