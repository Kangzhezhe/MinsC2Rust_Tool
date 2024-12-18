#!/usr/bin/env python3

from pprint import pprint
import re
from clang.cindex import CursorKind, Index, CompilationDatabase
from collections import defaultdict
import sys
import json
import yaml
import graphviz
import os

"""
Dumps a callgraph of a function in a codebase
usage: callgraph.py file.cpp|compile_commands.json [-x exclude-list] [extra clang args...]
The easiest way to generate the file compile_commands.json for any make based
compilation chain is to use Bear and recompile with `bear make`.

When running the python script, after parsing all the codebase, you are
prompted to type in the function's name for which you wan to obtain the
callgraph
"""

CALLGRAPH = defaultdict(list)
FULLNAMES = defaultdict(set)
FILE_FUNCTIONS = defaultdict(set)


def get_diag_info(diag):
    return {
        'severity': diag.severity,
        'location': diag.location,
        'spelling': diag.spelling,
        'ranges': list(diag.ranges),
        'fixits': list(diag.fixits)
    }


def fully_qualified(c):
    if c is None:
        return ''
    elif c.kind == CursorKind.TRANSLATION_UNIT:
        return ''
    else:
        res = fully_qualified(c.semantic_parent)
        if res != '':
            return res + '::' + c.spelling
        return c.spelling


def fully_qualified_pretty(c):
    if c is None:
        return ''
    elif c.kind == CursorKind.TRANSLATION_UNIT:
        return ''
    else:
        res = fully_qualified(c.semantic_parent)
        if res != '':
            return res + '::' + c.displayname
        return c.displayname


def is_excluded(node, xfiles, xprefs):
    if not node.extent.start.file:
        return False

    for xf in xfiles:
        if node.extent.start.file.name.startswith(xf):
            return True

    fqp = fully_qualified_pretty(node)

    for xp in xprefs:
        if fqp.startswith(xp):
            return True

    return False


def show_info(node, xfiles, xprefs, cur_fun=None):
    if node.kind == CursorKind.FUNCTION_TEMPLATE:
        if not is_excluded(node, xfiles, xprefs):
            cur_fun = node
            FULLNAMES[fully_qualified(cur_fun)].add(
                fully_qualified_pretty(cur_fun))
            FILE_FUNCTIONS[node.location.file.name].add(fully_qualified_pretty(cur_fun))

    if node.kind == CursorKind.CXX_METHOD or \
            node.kind == CursorKind.FUNCTION_DECL:
        if not is_excluded(node, xfiles, xprefs):
            cur_fun = node
            FULLNAMES[fully_qualified(cur_fun)].add(
                fully_qualified_pretty(cur_fun))
            FILE_FUNCTIONS[node.location.file.name].add(fully_qualified_pretty(cur_fun))

    if node.kind == CursorKind.CALL_EXPR:
        if node.referenced and not is_excluded(node.referenced, xfiles, xprefs):
            CALLGRAPH[fully_qualified_pretty(cur_fun)].append(node.referenced)

    for c in node.get_children():
        show_info(c, xfiles, xprefs, cur_fun)


def pretty_print(n):
    v = ''
    if n.is_virtual_method():
        v = ' virtual'
    if n.is_pure_virtual_method():
        v = ' = 0'
    return fully_qualified_pretty(n) + v

def generate_dot(fun_name, so_far, depth=0, dot=None):
    if dot is None:
        dot = graphviz.Digraph(comment='Call Graph')
    if depth >= 15:
        dot.node('too_deep', '...<too deep>...')
        return dot
    if fun_name in CALLGRAPH:
        for f in CALLGRAPH[fun_name]:
            if pretty_print(f) in so_far:
                continue
            so_far.append(pretty_print(f))
            print('  ' * (depth + 1) + pretty_print(f))
            dot.node(pretty_print(f), pretty_print(f))
            dot.edge(fun_name, pretty_print(f))
            if fully_qualified_pretty(f) in CALLGRAPH:
                generate_dot(fully_qualified_pretty(f), list(), depth + 1, dot)
            else:
                generate_dot(fully_qualified(f), list(), depth + 1, dot)
    return dot





def read_compile_commands(filename):
    if filename.endswith('.json'):
        with open(filename) as compdb:
            return json.load(compdb)
    else:
        return [{'command': '', 'file': filename}]




def read_args(args):
    db = None
    clang_args = []
    excluded_prefixes = []
    excluded_paths = []
    config_filename = None
    lookup = None
    i = 0
    while i < len(args):
        if args[i] == '-x':
            i += 1
            excluded_prefixes += args[i].split(',')
        elif args[i] == '-p':
            i += 1
            excluded_paths += args[i].split(',')
        elif args[i] == '--cfg':
            i += 1
            config_filename = args[i]
        elif args[i] == '--lookup':
            i += 1
            lookup = args[i]
        # elif args[i][0] == '-':
        #     clang_args.append(args[i])
        else:
            db = args[i]
        i += 1

    if len(excluded_paths) == 0:
        excluded_paths.append('/usr')
    excluded_prefixes.append('alloc_test')
    return {
        'db': db,
        'clang_args': clang_args,
        'excluded_prefixes': excluded_prefixes,
        'excluded_paths': excluded_paths,
        'config_filename': config_filename,
        'lookup': lookup,
        'ask': (lookup is None)
    }


def load_config_file(cfg):
    if cfg['config_filename']:
        with open(cfg['config_filename'], 'r') as yamlfile:
            data = yaml.load(yamlfile, Loader=yaml.FullLoader)
            cfg['clang_args'] += data['clang_args']
            cfg['excluded_prefixes'] += data['excluded_prefixes']
            cfg['excluded_paths'] += data['excluded_paths']


def keep_arg(x) -> bool:
    keep_this = x.startswith('-I') or x.startswith('-std=') or x.startswith('-D')
    return keep_this


def analyze_source_files(cfg):
    print('reading source files...')
    for cmd in read_compile_commands(cfg['db']):
        index = Index.create()
        c = [
            x for x in cmd['command'].split()
            if keep_arg(x)
        ] + cfg['clang_args']
        tu = index.parse(cmd['file'], c)
        print(cmd['file'])
        if not tu:
            print("unable to load input")

        for d in tu.diagnostics:
            if d.severity == d.Error or d.severity == d.Fatal:
                print(' '.join(c))
                pprint(('diags', list(map(get_diag_info, tu.diagnostics))))
                return
        show_info(tu.cursor, cfg['excluded_paths'], cfg['excluded_prefixes'])


def print_callgraph(fun):
    if fun in CALLGRAPH:
        print(fun)
        dot = generate_dot(fun, list())
        # dot.render('callgraph', format='png', cleanup=True)
    else:
        print('matching:')
        for f, ff in FULLNAMES.items():
            if f.startswith(fun):
                for fff in ff:
                    print(fff)

def func_match(fun):
    fs = []
    for f, ff in FULLNAMES.items():
        if f ==fun:
            for fff in ff:
                fs.append(fff)
    return fs

def ask_and_print_callgraph():
    while True:
        fun = input('> ')
        if not fun:
            break
        print_callgraph(fun)


def get_c_filenames(directory):
    # 创建一个空列表来保存文件名
    c_filenames = []

    # 遍历给定目录中的所有文件和子目录
    for filename in os.listdir(directory):
        # 检查文件是否是.c文件
        if filename.endswith('.c'):
            # 去掉.c后缀并添加到列表中
            c_filenames.append(os.path.splitext(filename)[0])
            # c_filenames = [s.replace("-","_") for s in c_filenames]
    print(c_filenames)
    return c_filenames

def get_c_filepaths(directory_path):
    c_filepaths = []
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith('.c'):
                # 使用 os.path.abspath 获取绝对路径
                abs_path = os.path.abspath(os.path.join(root, filename))
                c_filepaths.append(abs_path)
    return c_filepaths

def get_c_functions_name(c_path, unprocess_path,compile_commands_path):
    #找到文件夹下的所有的.c文件
    # filenames = get_c_filenames("/home/mins01/project/c-algorithms/src")
    # #将文件的所有函数合成json格式
    if len(sys.argv) < 2:
        print('usage: ' + sys.argv[0] +
              '[extra clang args...]')
        return
    cfg = read_args(sys.argv)
    cfg['db'] = compile_commands_path
    load_config_file(cfg)
    analyze_source_files(cfg)
    filepaths =  get_c_filepaths(c_path)
    results = []
    for file in filepaths:
        functions_list = list(FILE_FUNCTIONS[file])
        results.append({os.path.basename(file):functions_list})
    # 指定要保存的文件名
    # 使用 json.dump 将数据写入文件
    with open(unprocess_path, 'w') as json_file:
        json.dump(results, json_file, indent=4)

def get_func_depth(fun_name, so_far, depth=0, funcs_depth = {}):
    if depth >= 15:
        return 
    if fun_name in CALLGRAPH:
        for f in CALLGRAPH[fun_name]:
            if pretty_print(f) in so_far:
                continue
            so_far.append(pretty_print(f))
            print('  ' * (depth + 1) + pretty_print(f))
            if funcs_depth.get(pretty_print(f)) is None:
                funcs_depth[pretty_print(f)] = depth+1
            else :
                if funcs_depth[pretty_print(f)] < depth+1:
                    funcs_depth[pretty_print(f)] = depth+1
            if fully_qualified_pretty(f) in CALLGRAPH:
                get_func_depth(fully_qualified_pretty(f), list(), depth + 1,funcs_depth)
            else:
                get_func_depth(fully_qualified(f), list(), depth + 1,funcs_depth)

pattern_func = re.compile(r'^(\w+)\(.*\)$')
pattern_file = re.compile(r'^(.+)\.\w+$')

def extract_function_names(func):
    if pattern_func.match(func) is None:
        return None
    else:
        return pattern_func.match(func).group(1)
    
def clang_callgraph(compile_commands_path ,include_dirs = None):
    if len(sys.argv) < 2:
        print('usage: ' + sys.argv[0] +
              '[extra clang args...]')
        return
    cfg = read_args(sys.argv)
    cfg['db'] = compile_commands_path
    load_config_file(cfg)
    analyze_source_files(cfg)
    
    with open('../func_result/new_test_processed.json', 'r') as json_file:
        data = json.load(json_file)[0]

    with open('../func_result/new_src_processed.json', 'r') as json_file:
        data_src = json.load(json_file)[0]


    
    def get_all_funcs(source_name, include_dirs, data_src, all_funcs):
        child_source = include_dirs.get(source_name, [])
        for source in child_source:
            all_funcs += data_src.get(source, [])
            get_all_funcs(source, include_dirs, data_src, all_funcs)

    def func_avaliabe(func, source_name, include_dirs=include_dirs, data=data, data_src=data_src):
        all_funcs = data.get(source_name, []).copy()
        get_all_funcs(source_name, include_dirs, data_src, all_funcs)
        return func in all_funcs

        
    result_funcs_depth = {}
    result_funcs_child = {}
    for source_name, value in data.items():
        funcs_depth = {}
        funcs_child = defaultdict(set)
        for func in value:
            matchs = func_match(func)
            for match in matchs:
                if funcs_depth.get(match) is None:
                    funcs_depth[match] = 0
                    print_callgraph(match)
                    get_func_depth(match, list(),  funcs_depth = funcs_depth)
        

        for func, depth in funcs_depth.items():
            if extract_function_names(func) and func_avaliabe(extract_function_names(func),source_name):
                for child in CALLGRAPH[func]:
                    if extract_function_names(pretty_print(child)) and func_avaliabe(extract_function_names(pretty_print(child)),source_name):
                        funcs_child[func].add(pretty_print(child)) 
        
        sorted_funcs_depth = dict(sorted(funcs_depth.items(), key=lambda item: item[1], reverse=True))
        sorted_funcs_depth = {extract_function_names(k): v for k, v in sorted_funcs_depth.items() if extract_function_names(k) and func_avaliabe(extract_function_names(k),source_name)}
        funcs_child = {
            extract_function_names(k): [extract_function_names(v) for v in vs if extract_function_names(v)]
            for k, vs in funcs_child.items() if extract_function_names(k)
        }
        result_funcs_depth[source_name] = sorted_funcs_depth
        result_funcs_child[source_name] = funcs_child

    flattened_funcs_child = {}
    for source, funcs in result_funcs_child.items():
        for func_name, children in funcs.items():
            flattened_funcs_child[func_name] = children

    all_data = data.copy() 
    all_data.update(data_src)
    for file,file_childs in include_dirs.items():
        funcs = all_data.get(file, [])
        all_childs = set()
        for func in funcs:
            if func in flattened_funcs_child:
                all_childs.update(flattened_funcs_child[func])
        excluded_childs = set()
        for child in file_childs:
            all_funcs = all_data.get(child, [])
            if set(all_funcs).isdisjoint(set(all_childs)):
                excluded_childs.add(child)
        include_dirs[file] = [child for child in file_childs if child not in excluded_childs]
                

    # if cfg['lookup']:
    #     print_callgraph(cfg['lookup'])
    # if cfg['ask']:
    #     ask_and_print_callgraph()
    return result_funcs_depth,result_funcs_child,include_dirs
if __name__ == '__main__':
    clang_callgraph()