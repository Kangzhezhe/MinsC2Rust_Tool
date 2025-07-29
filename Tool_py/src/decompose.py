import multiprocessing
import os
import time
import re
import asyncio
from collections import defaultdict
import concurrent.futures
import threading
import json
import shutil
import sys
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from parse_config import read_config,setup_project_directories
from clang_callgraph import clang_callgraph
import shutil
import copy
from extract_rust_func import read_json_file
from merge_c_h import process_files
from logger import logger_init
from utils import *
from data_manager import DataManager
from models.llm_model import generate_response
from metrics import calculate_compile_pass_rates,calculate_retry_pass_rates
from prompts import *

total_retry_count = 0
total_regenerate_count = 0
total_error_count = 0

def extract_includes(text):
    # 使用正则表达式匹配 #include<> 语句
    includes = re.findall(r'#include\s*<[^>]+>', text)
    return "\n".join(includes)

def extract_function_declarations(code):
    # 改进的正则表达式，确保匹配的是函数定义
    function_pattern = re.compile(
        r'^\s*(?P<return_type>\w[\w\s\*]*)\s+(?P<name>\w+)\s*\((?P<params>[^\)]*)\)\s*\{',
        re.MULTILINE
    )
    
    declarations = []
    for match in function_pattern.finditer(code):
        return_type = match.group('return_type').strip()
        name = match.group('name').strip()
        params = match.group('params').strip()
        declarations.append(f"{return_type} {name}({params});")
    
    return "\n".join(declarations)


def process_func(test_source_name, func_name, depth, start_time, source_names, funcs_childs, data_manager, results, logger, llm_model, tmp_dir,  all_error_funcs_content, once_retry_count_dict,funcs,lock,params):
    global total_retry_count, total_regenerate_count, total_error_count

    tmp_dir = os.path.join(tmp_dir, 'units',test_source_name.replace('-','_'))
    os.makedirs(tmp_dir, exist_ok=True)
    funcs_child = funcs_childs[test_source_name]

    max_history_length = 0
    data_manager.get_include_indices(test_source_name)
    _, _, i = data_manager.get_content(func_name)
    if i != -1 and i in data_manager.include_files_indices:
        source_name = source_names[i]
    else:
        raise ValueError(f"{func_name} is not correct")
        # logger.info(f"{func_name} is not correct")
        # shutil.rmtree(tmp_dir)
        # return

    if i == -1 or func_name == 'main' or func_name == 'extra' or func_name in results.get(source_name, {}) or func_name in ['run_test', 'run_tests'] or func_name in all_error_funcs_content.get(source_name, {}):
        return

    if func_name.startswith('test_'):
        if os.path.exists(os.path.join(tmp_dir, f'{func_name}.c')):
            os.remove(os.path.join(tmp_dir, f'{func_name}.c'))
        return

    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    logger.info(f"Total time taken for conversion: {int(hours):02}:{int(minutes):02}:{int(seconds):02} seconds, Total retry count: {total_retry_count}, Total regenerate count: {total_regenerate_count}, Total error count:{total_error_count}")

    with lock:
        if source_name not in results:
            results[source_name] = {}

    source_context, child_funs_c, sourc_extra = data_manager.get_child_context_c(func_name, results, funcs_child)

    child_funs_c_list = child_funs_c.strip(',').split(',')
    names_list,before_details,raw_details = data_manager.get_details(child_funs_c_list,True)
    before_details1 = extract_related_items(source_context,before_details,names_list,not_found=True)
    target_str = extract_related_items(before_details1,before_details,names_list,not_found=True)
    # debug(f"before_details: {target_str}")

    all_child_files = [source_name]
    data_manager.get_all_source(source_name, all_child_files)

    includes = extract_includes(raw_details)

    declarations = extract_function_declarations(source_context)

    function_unit = includes + '\n' +  target_str + "\n" +declarations+ '\n' + source_context
    
    file_path = os.path.join(tmp_dir, f'{func_name}.c')

    # 如果文件已存在，先尝试编译
    if os.path.exists(file_path):
        compile_error = run_command(f"gcc -o temp -c {file_path}")
        delete_file_if_exists('temp')
        if not compile_error:  # 如果编译通过，跳过处理
            print(f"文件 {file_path} 已存在且编译通过，跳过处理。")
            return results, all_error_funcs_content, once_retry_count_dict

    # 写入文件
    with open(file_path, 'w') as f:
        f.write(function_unit)

    compile_error = run_command(f"gcc -o temp -c {file_path}")
    delete_file_if_exists('temp')
    print(f"{function_unit}\n{compile_error}")
    
    max_retry = 5
    retry = 0
    while compile_error and retry < max_retry:
        prompt = f"""
        你是一个C语言专家，帮我修改以下c语言文件的编译错误，直接返回修改后的c语言完整代码，不要添加任何其他内容。
        改错内容包括：移动代码定义顺序，修改编译报错，将free malloc等内存分配函数替换为malloc，calloc等系统库函数，比如将用户#define 的malloc语句删去
        编译错误如下：
        {compile_error}
        下面是代码：
        {function_unit}
        """
        print("len of prompt:", len(prompt))
        response = generate_response(prompt,llm_model=llm_model)
        text_remove = response.replace("```c", "").replace("```", "")
        function_unit = text_remove
        with open(file_path, 'w') as f:
            f.write(function_unit)
        compile_error = run_command(f"gcc -o temp -c {file_path}")
        delete_file_if_exists('temp')
        print(f"{function_unit}\n{compile_error}")
        retry += 1

    return  results, all_error_funcs_content, once_retry_count_dict

def process_test_source_name(test_source_name, funcs, source_names, funcs_childs, data_manager, shared_results, shared_all_error_funcs_content, shared_once_retry_count_dict, logger, llm_model, tmp_dir, start_time, lock, output_dir, params):
    if test_source_name not in source_names:
        return

    checkpoint_interval = params['checkpoint_interval']
    func_counter = 0

    local_results = copy.deepcopy(shared_results)
    local_all_error_funcs_content = copy.deepcopy(shared_all_error_funcs_content)
    local_once_retry_count_dict = copy.deepcopy(shared_once_retry_count_dict)


    with tqdm(funcs.items(), desc=f"{test_source_name}") as pbar:
        for func_name, depth in pbar:
            pbar.set_postfix(func_name=func_name) 

            result = process_func(
                test_source_name, func_name, depth, start_time, source_names, funcs_childs, copy.deepcopy(data_manager), local_results, logger, llm_model, tmp_dir, local_all_error_funcs_content, local_once_retry_count_dict, funcs, lock, params
            )
            if result is not None:
                updated_results, updated_all_error_funcs_content, updated_once_retry_count_dict = result
                func_counter += 1


    return local_results, local_all_error_funcs_content, local_once_retry_count_dict


def save_checkpoint(results, once_retry_count_dict, all_error_funcs_content, output_dir):
    with open(os.path.join(output_dir, 'results.json'), 'w') as f:
        json.dump(results, f, indent=4)
    with open(os.path.join(output_dir, 'once_retry_count_dict.json'), 'w') as f:
        json.dump(once_retry_count_dict, f, indent=4)
    with open(os.path.join(output_dir, 'all_error_funcs_content.json'), 'w') as f:
        json.dump(all_error_funcs_content, f, indent=4, ensure_ascii=False)

    global total_retry_count, total_regenerate_count, total_error_count
    checkpoint = {
        'total_retry_count': total_retry_count,
        'total_regenerate_count': total_regenerate_count,
        'total_error_count': total_error_count
    }
    with open(os.path.join(output_dir, 'checkpoint.json'), 'w') as f:
        json.dump(checkpoint, f, indent=4, ensure_ascii=False)

    
def load_checkpoint(output_dir, results={}, once_retry_count_dict={}, all_error_funcs_content={}):
    if os.path.exists(os.path.join(output_dir,'results.json')):
        with open(os.path.join(output_dir,'results.json'), 'r') as file:
            results = json.load(file)
    if os.path.exists(os.path.join(output_dir,'all_error_funcs_content.json')):
        with open(os.path.join(output_dir,'all_error_funcs_content.json'), 'r') as f:
            all_error_funcs_content = json.load(f)
    if os.path.exists(os.path.join(output_dir,'once_retry_count_dict.json')):
        with open(os.path.join(output_dir,'once_retry_count_dict.json'), 'r') as f:
            once_retry_count_dict = json.load(f)

    global total_retry_count, total_regenerate_count, total_error_count
    checkpoint_path = os.path.join(output_dir, 'checkpoint.json')
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r') as f:
            checkpoint = json.load(f)
            total_retry_count = checkpoint['total_retry_count']
            total_regenerate_count = checkpoint['total_regenerate_count']
            total_error_count = checkpoint['total_error_count']
            return results, once_retry_count_dict, all_error_funcs_content
    return {}, {}, {}


def get_parallel_groups(test_names, data_manager,sorted_funcs_depth,funcs_childs):
    # 获取每个 test_source_name 的包含列表
    include_lists_without_fn_pointer = {test_name: set(data_manager.get_include_indices(test_name, without_fn_pointer=True)[1]) for test_name in test_names}
    include_lists = {test_name: set(data_manager.get_include_indices(test_name)[1]) for test_name in test_names}
    difference_values = {}
    for test_name, include_list in include_lists.items():
        if test_name in include_lists_without_fn_pointer:
            difference = include_list - include_lists_without_fn_pointer[test_name]
            if difference:
                difference_values[test_name] = difference
            else:
                difference_values[test_name] = set()

    # 计算所有差异值的并集
    all_difference_values = set().union(*difference_values.values())

    # 初始化两个集合
    set1 = {}
    set2 = {}

    # 复制 difference_values 以便操作
    remaining_values = difference_values.copy()

    # 贪心算法：优先选择包含最多 all_difference_values 元素的项
    while all_difference_values:
        best_test_name = None
        best_value = set()
        for test_name, value in remaining_values.items():
            intersection = value & all_difference_values
            if len(intersection) > len(best_value):
                best_test_name = test_name
                best_value = value

        if best_test_name:
            set1[best_test_name] = best_value
            all_difference_values -= best_value
            del remaining_values[best_test_name]
        else:
            break

    # 将剩余的项放入 set2
    set2 = remaining_values

    print("Set 1:", set1)
    print("Set 2:", set2)

    # 找到可以并行处理的 test_source_name 组
    def process_keys(keys, include_lists_without_fn_pointer):
        parallel_groups = []
        for key in keys:
            if key in include_lists_without_fn_pointer:
                include_list = include_lists_without_fn_pointer.pop(key)
                group = {key}
                group_include_list = include_list.copy()
                to_remove = [key]
                for other_test_name, other_include_list in list(include_lists_without_fn_pointer.items()):
                    if group_include_list.isdisjoint(other_include_list):
                        group.add(other_test_name)
                        to_remove.append(other_test_name)
                        group_include_list.update(other_include_list)  # 更新 group_include_list 以确保没有交集
                for test_name in to_remove:
                    include_lists_without_fn_pointer.pop(test_name, None)
                parallel_groups.append(group)
        return parallel_groups

    # 处理 set1 和 set2 的键
    parallel_groups_set1 = process_keys(set1.keys(), {k: v for k, v in include_lists_without_fn_pointer.items() if k in set1.keys()})
    parallel_groups_set2 = process_keys(set2.keys(), {k: v for k, v in include_lists_without_fn_pointer.items() if k in set2.keys()})

    # 合并结果
    parallel_groups = parallel_groups_set1 + parallel_groups_set2

    print("Parallel Groups:", parallel_groups)
    for k,vs in set1.items():
        for v in vs:
            index = data_manager.get_index_by_source_name(v)
            funcs = list(data_manager.data[index].keys())
            for f in funcs :
                if f != 'extra' and f in data_manager.all_pointer_funcs and f not in sorted_funcs_depth[k]:
                    max_value = max(sorted_funcs_depth[k].values())
                    sorted_funcs_depth[k] = dict([(f, max_value)] + list(sorted_funcs_depth[k].items()))
           
    return parallel_groups

def parallel_process(sorted_funcs_depth, funcs_childs, source_names, results, data_manager, logger, llm_model, tmp_dir, output_dir, all_error_funcs_content, once_retry_count_dict, test_names, params):
    start_time = time.time()
    
    lock = threading.Lock()
    global total_retry_count, total_regenerate_count, total_error_count

    parallel_groups = get_parallel_groups(test_names, data_manager,sorted_funcs_depth,funcs_childs)
    merged_set = set.union(*parallel_groups)

    # 并行处理每个 test_source_name
    for group in [merged_set]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=params['num_threads']) as executor:
            futures = []
            for test_source_name in group:
                future = executor.submit(process_test_source_name, test_source_name, sorted_funcs_depth[test_source_name], source_names, funcs_childs, data_manager, results, all_error_funcs_content, once_retry_count_dict, logger, llm_model, tmp_dir, start_time, lock, output_dir, params)
                futures.append(future)

            # 等待所有任务完成并更新结果
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result is not None:
                    updated_results, updated_all_error_funcs_content, updated_once_retry_count_dict = result

    return results, once_retry_count_dict, all_error_funcs_content, total_retry_count, total_regenerate_count, total_error_count


async def main():
    if len(sys.argv) != 2:
        print("Usage: python main_multi.py <config_path>")
        sys.exit(1)
    config_path = sys.argv[1]
    cfg = read_config(config_path)
    tmp_dir, output_dir, output_project_path,compile_commands_path,params,excluded_files= setup_project_directories(cfg)

    # llm_model = "local"
    llm_model = "qwen"
    # llm_model = "zhipu"
    # llm_model = "deepseek"
    # llm_model = "gpt4o"
    # llm_model = "claude"
    include_dict,all_file_paths = process_files(compile_commands_path, tmp_dir)
    test_path = os.listdir(os.path.join(tmp_dir, 'test_json'))
    test_path = [os.path.join(tmp_dir, 'test_json', f) for f in test_path]
    test_names = [os.path.splitext(os.path.basename(f))[0] for f in test_path]
    src_path = os.listdir(os.path.join(tmp_dir, 'src_json'))
    src_path = [os.path.join(tmp_dir, 'src_json', f) for f in src_path]
    src_names = [os.path.splitext(os.path.basename(f))[0] for f in src_path]
    source_path = test_path
    source_path.extend(src_path)

    has_test = (cfg['Paths'].get('test_dir','') != '')
    if not has_test:
        for test_name in test_names:
            include_dict[test_name]=src_names

    sorted_funcs_depth,funcs_childs,include_dict,include_dict_without_fn_pointer,all_pointer_funcs = clang_callgraph(compile_commands_path,include_dict,all_file_paths,has_test=has_test)
    logger = logger_init(os.path.join(output_dir,'app.log'))

    if not has_test:
        for test_name in test_names:
            include_dict[test_name]=src_names


    files_to_remove = []
    
    for file in excluded_files:
        if file in src_names:
            files_to_remove.append(os.path.join(tmp_dir, f'src_json/{file}.json'))
        elif file in test_names:
            files_to_remove.append(os.path.join(tmp_dir, f'test_json/{file}.json'))


    for file in files_to_remove:
        if file in source_path:
            source_path.remove(file)
    source_names = [os.path.splitext(os.path.basename(f))[0] for f in source_path]

    data = []
    for f in source_path:
        with open(f, 'r') as file:
            data.append(json.load(file))

    data_manager = DataManager(source_path,include_dict=include_dict,all_pointer_funcs=all_pointer_funcs,include_dict_without_fn_pointer=include_dict_without_fn_pointer,has_test=has_test)   

    results = {}
    start_time = time.time()
    total_retry_count = 0
    total_regenerate_count = 0
    total_error_count = 0
    total_error_funcs = []
    all_error_funcs_content = defaultdict(dict) 
    once_retry_count_dict = defaultdict(dict)
    results = defaultdict(dict)

    data_manager = DataManager(source_path,include_dict=include_dict,all_pointer_funcs=all_pointer_funcs,include_dict_without_fn_pointer=include_dict_without_fn_pointer,has_test=has_test)   


    results = {}
    start_time = time.time()
    total_retry_count = 0
    total_regenerate_count = 0
    total_error_count = 0
    total_error_funcs = []
    all_error_funcs_content = defaultdict(dict) 
    once_retry_count_dict = defaultdict(dict)
    results = defaultdict(dict)



    results,once_retry_count_dict,all_error_funcs_content,total_retry_count, total_regenerate_count, total_error_count = parallel_process(
        sorted_funcs_depth, funcs_childs, source_names, results, data_manager, logger, llm_model, tmp_dir, output_dir,all_error_funcs_content,once_retry_count_dict,test_names,params
    )


    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    logger.info(f"Total time taken for conversion :{int(hours):02}:{int(minutes):02}:{int(seconds):02} seconds, Total retry count: {total_retry_count}, Total regenerate count: {total_regenerate_count},Total error count:{total_error_count}, Total error funcs:{total_error_funcs}") 

    calculate_compile_pass_rates(output_dir, results, sorted_funcs_depth, data_manager)
    calculate_retry_pass_rates(output_dir,results,include_dict,once_retry_count_dict,test_names)

    # post_process(data_manager, output_dir, output_project_path, src_names, test_names, funcs_childs, include_dict, sorted_funcs_depth, llm_model)


if __name__ == "__main__":
    asyncio.run(main())
