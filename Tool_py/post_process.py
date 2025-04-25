import copy
import os
import json
import re
from collections import defaultdict
import subprocess
import sys

from tqdm import tqdm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from parse_config import read_config, setup_project_directories
from models.llm_model import generate_response
from metrics import calculate_compile_pass_rates, calculate_retry_pass_rates, calculate_tests_pass_rates,calculate_asserts_count,calculate_loc_statistics
from merge_c_h import process_files
from utils import deduplicate_code, run_command, update_test_timeout,parse_and_deduplicate_errors,Memory
from prompts import generate_extra_prompt,fix_extra_prompt, get_json_parsing_fix_prompt
from logger import logger_init
from clang_callgraph import clang_callgraph
from src.data_manager import DataManager

def get_source_path(source, src_names,output_project_path):
    if source in src_names:
        return f"{output_project_path}/src/{source.replace('-','_')}.rs"
    else:
        return f"{output_project_path}/tests/{source.replace('-','_')}.rs"

def process_files_refactoring(data_manager, source, all_include_files, include_dict, results, src_names, test_names, funcs_child, output_project_path, llm_model,check=True):
    for include_file in all_include_files:
        if include_file in src_names and include_file in results:
            child_source = include_dict.get(include_file, [])
            post_process_source(data_manager, include_file, child_source, results, src_names, test_names, funcs_child, output_project_path, llm_model,check=check)
    child_source = include_dict.get(source, [])
    test_error = post_process_source(data_manager, source, child_source, results, src_names, test_names, funcs_child, output_project_path, llm_model,check=check)
    return test_error

def run_tests_and_get_failed_cases(output_project_path, source,funcs_child):
    test_error = run_command(f"cd {output_project_path} && RUSTFLAGS=\"-Awarnings\" cargo test --test {source.replace('-','_')}", check=False)
    pattern = re.compile(r'---- (test_\w+) stdout ----\n(.*?)\n\n', re.DOTALL)
    matches = pattern.findall(test_error)
    failed_tests = {test_case: error_message for test_case, error_message in matches}
    if len(failed_tests) == 0:
        test_error = ''

    depth_cache = {}
    for func in funcs_child:
        calculate_depth(func, funcs_child, depth_cache)
    sorted_tests = sorted(depth_cache.items(), key=lambda x: x[1])
    sorted_failed_tests = {test_case: failed_tests[test_case] for test_case, _ in sorted_tests if test_case in failed_tests}

    return test_error, sorted_failed_tests

def calculate_depth(func, funcs_child, depth_cache, current_path=None):
    if current_path is None:
        current_path = set()
    
    if func in depth_cache:
        return depth_cache[func]
    
    if func in current_path:
        depth_cache[func] = 15
        return 15
    
    if func not in funcs_child or not funcs_child[func]:
        depth_cache[func] = 0
        return 0
    
    current_path.add(func)
    depth = 1 + max(calculate_depth(child, funcs_child, depth_cache, current_path) for child in funcs_child[func])
    current_path.remove(func)
    
    depth_cache[func] = depth
    return depth

def ensure_json_format(json_str):
    retry = 0
    while True:
        try:
            first_brace_index = re.search(r'{', json_str).start()
            json_substr = json_str[first_brace_index:]
            ret = json.loads(json_substr)
            return ret
        except json.JSONDecodeError as e:
            print(f"json decode retrying: {retry}")
            retry += 1
            if retry > 10:
                return None
            error_position = e.pos if hasattr(e, 'pos') else 'unknown'
            error_msg = str(e)
            error_content = json_str[error_position:min(error_position+20, len(json_str))]
            prompt1 = get_json_parsing_fix_prompt("", json_str, error_msg, error_position, error_content)
            json_str = generate_response(prompt1, llm_model, temperature=0).replace("```json\n", "").replace("\n```", "").replace("```json", "").replace("```", "")



# 示例用法
trajectory_memory = Memory(max_size=10, memory_type="Trajectory")


def post_process(data_manager, output_dir, output_project_path, src_names, test_names, funcs_childs, include_dict, sorted_funcs_depth, llm_model="qwen",eval_only=False,test_timeout=60000):
    if os.path.exists(os.path.join(output_dir, 'results.json')):
        with open(os.path.join(output_dir, 'results.json'), 'r') as file:
            results = json.load(file)

    if os.path.exists(os.path.join(output_dir, 'all_error_funcs_content.json')):
        with open(os.path.join(output_dir, 'all_error_funcs_content.json'), 'r') as f:
            all_error_funcs_content = json.load(f)
    
    if os.path.exists(os.path.join(output_dir, 'once_retry_count_dict.json')):
        with open(os.path.join(output_dir, 'once_retry_count_dict.json'), 'r') as f:
            once_retry_count_dict = json.load(f)
    calculate_compile_pass_rates(output_dir, results, sorted_funcs_depth, data_manager)
    calculate_retry_pass_rates(output_dir,results,include_dict,once_retry_count_dict,test_names)
    calculate_loc_statistics(output_dir, results, sorted_funcs_depth, data_manager)
    
    # return

    # 工程结构重构
    if not eval_only:
        all_source_names = set()
        lib_rs_path = f'{output_project_path}/src/lib.rs'
        if os.path.exists(lib_rs_path):
            with open(lib_rs_path, 'r') as f:
                for line in f:
                    all_source_names.add(line.strip())
        for source in results.keys():
            if source in test_names:
                _, all_include_files = data_manager.get_include_indices(source)
                funcs_child = funcs_childs[source]
                for include_file in all_include_files:
                    if include_file in src_names and include_file in results:
                        all_source_names.add(f"pub mod {include_file.replace('-', '_')};")
                        child_source = include_dict.get(include_file, [])
                        post_process_source(data_manager, include_file, child_source, results, src_names, test_names, funcs_child, output_project_path, llm_model)
                with open(lib_rs_path, 'w') as f:
                    f.write('\n'.join(all_source_names))
                    f.write('\n')
                child_source = include_dict.get(source, [])
                post_process_source(data_manager, source, child_source, results, src_names, test_names, funcs_child, output_project_path, llm_model)

    

    # with open(os.path.join(output_dir, 'results.json'), 'w') as f:
    #     json.dump(results, f, indent=4)

    # # TODO:执行测试
    # if not eval_only:
    #     for source in results.keys():
    #         if source in test_names:
    #             print(f"Processing {source}...")
    #             results_copy = copy.deepcopy(results)
    #             _, all_include_files = data_manager.get_include_indices(source)
    #             funcs_child = funcs_childs[source]
    #             print("all_include_files",all_include_files)
    #             print("funcs_child",funcs_child)
    #             process_files_refactoring(data_manager, source, all_include_files, include_dict, results_copy, src_names, test_names, funcs_child, output_project_path, llm_model,check=False)
    #             test_error, failed_tests = run_tests_and_get_failed_cases(output_project_path, source,funcs_child)
    #             if len(failed_tests) == 0:
    #                 continue
    #             all_test_cases = failed_tests.keys()
    #             for test_case in all_test_cases:
    #                 print(f"Processing {source}:{test_case}, remain len(failed_tests): {len(failed_tests)}...")
    #                 if test_case in results_copy[source]:
    #                     test_error = ''

    #                     _, failed_tests = run_tests_and_get_failed_cases(output_project_path, source,funcs_child)
    #                     test_error = failed_tests.get(test_case, '')
    #                     print(test_error)
    #                     retry_count = 0
    #                     while test_error != '' and retry_count < 8: 
    #                         _, child_funs =  data_manager.get_child_context(test_case, results_copy, funcs_child)
    #                         child_funs_list = child_funs.strip(',').split(',')
    #                         child_context_dict = defaultdict(dict)

    #                         for source_name,values in results_copy.items():
    #                             if source_name not in all_include_files:
    #                                 continue
    #                             for func, value in values.items():
    #                                 if func in child_funs_list or func in ['extra',test_case]:
    #                                     child_context_dict[source_name].update({func:value})
                            
    #                         test_case_c, _, _ = data_manager.get_content(test_case)

    #                         prompt = f"""
    #                         请根据Rust测试用例{test_case}的执行错误信息与相关函数上下文，修改相关函数或测试用例，允许改变重写测试用例的逻辑以判断函数的正确性，根据需要在代码中插入打印调试语句输出报错数据
    #                         直接返回修改后的Rust函数，不做任何的解释说明，如果有编译报错则修改对应的函数中的编译报错。
    #                         注意：测试用例{test_case}本身有可能逻辑上有错误导致执行出错，如果发现测试用例本身逻辑错误请修改测试用例判断逻辑。如果多次修改测试用例逻辑仍然无法通过，可以尝试修改函数实现逻辑，如果多次修改函数实现逻辑仍然无法通过，可以尝试修改测试用例逻辑。
    #                           参考与测试用例逻辑等价的C语言代码的实现逻辑：{test_case_c}，如果测试用例逻辑没有问题，则修改函数实现。
    #                         请按照以下思考过程解决问题：首先分析测试用例的执行错误信息，定位到出错的代码行，然后判断测试用例不通过的原因，如果是测试用例本身的不合理请修改测试用例的判断逻辑，如果是函数实现错误请修改函数实现。
    #                         输入上下文格式为json格式，key为文件名，value为函数名和函数内容的字典，返回格式也为json格式但是只返回修改过的元素，不要返回相同的代码，如下所示：
    #                         {{
    #                             "文件名1":{{
    #                                 "extra":"文件额外非函数内容",
    #                                 "函数名1":"函数内容1",
    #                                 "函数名2":"函数内容2"
    #                             }},
    #                             "文件名2":{{
    #                                 "extra":"文件额外非函数内容",
    #                                 "函数名1":"函数内容1",
    #                             }}
    #                             ...
    #                         }}
    #                         返回格式：
    #                         {{
    #                             "需要改动的文件名1":{{
    #                                 "extra":"改动过的文件额外非函数内容",
    #                                 "需要改动的函数名1":"改动过的函数内容1",
    #                                 "需要改动的函数名2":"改动过的函数内容2"
    #                             }},
    #                             ...
    #                         }}

    #                         相关上下文：{json.dumps(child_context_dict)}
    #                         报错信息：{test_error}
    #                         """

    #                         experience = f"""
    #                         以下是你上几轮失败的改错的操作和报错信息，请不要按之前相同的做法进行改错，尝试新的思路改错，避免重复犯错：
    #                         {trajectory_memory.get_latest(5)}
    #                         """

    #                         prompt += experience

    #                         print(f"len of prompt: {len(prompt)}")

    #                         response = generate_response(prompt, llm_model, temperature=0).replace("```json`\n", "").replace("\n```", "").replace("```json`", "").replace("```", "")
    #                         response_dict = ensure_json_format(response)
    #                         print(response_dict)

    #                         results_copy2 = copy.deepcopy(results_copy)
    #                         for key, value in response_dict.items():
    #                             results_copy2[key].update(value)
    #                         test_error1 = process_files_refactoring(data_manager, source, all_include_files, include_dict, results_copy2, src_names, test_names, funcs_child, output_project_path, llm_model,check=False)

    #                         _, failed_tests = run_tests_and_get_failed_cases(output_project_path, source,funcs_child)
    #                         test_error = failed_tests.get(test_case, '')
    #                         test_error += test_error1
    #                         print(test_error)

    #                         if test_error == '':
    #                             results_copy = results_copy2
    #                             break

    #                         # get trajectory
    #                         input_dict = {}
    #                         for key, value in response_dict.items():
    #                             input_dict[key] = {k: results_copy[key][k] for k in value.keys()}

    #                         trajectory_prompt = f"""
    #                         你是一个代码诊断专家，你之前有一个代码的改错任务，但是你改出来的代码仍然有错误存在，
    #                         请你简单对比改错前后代码，描述这一次修改的过程，具体哪个地方的代码前后是怎么改的，报错信息是什么,以便你的之后的改错过程不再犯相同的错误：

    #                         ## 本次改错的输入：
    #                         {input_dict}
    #                         ## 本次改错的输出：
    #                         {response}
    #                         ## 本次改错的报错信息：
    #                         {test_error}
                            
    #                         请按以下步骤思考：
    #                         1. 提取这一轮改错前后的完整语句 （如：这一次我修改/插入/删除了XXX语句...）
    #                         2. 提取这一次的报错信息的关键信息 （如：这一次报错内容是XXX语句，报错内容）

    #                         只返回本次改错过程和报错信息的描述，不要给出下一次修改的建议和分析，避免影响下一次的判断
    #                         用一段话描述但是不能缺少关键语句的详细信息
    #                         返回格式为文本格式，不需要包含代码块，只需要包含文字描述即可。
    #                         """

    #                         print(f"len of trajectory_prompt: {len(trajectory_prompt)}")
    #                         trajectory_response = generate_response(trajectory_prompt, llm_model, temperature=0)
    #                         trajectory_memory.add(trajectory_response)
    #                         print(trajectory_memory.get_context())

    #                         results_copy = results_copy2

    #                         retry_count += 1

    #                     trajectory_memory.clear()
    #                     if len(failed_tests) == 0:
    #                         break
                        
    #             results = results_copy

    print("Running tests...")

    update_test_timeout(f'{output_project_path}/tests', test_timeout)
    run_cargo_test(output_project_path,output_dir)

    calculate_tests_pass_rates(output_project_path,output_dir, results, sorted_funcs_depth)

    print("Calculating asserts count...")
    calculate_asserts_count(output_project_path, results, src_names, test_names,output_dir)
    

def run_cargo_test(output_project_path,output_dir):
    command = f'cd {output_project_path} && cargo test --no-fail-fast'
    test_result = subprocess.run(command, shell=True, check=False, text=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output_str = test_result.stdout
    print(output_str)
    with open(os.path.join(output_dir, 'cargo_test_result.txt'), 'w') as result_file:
        result_file.write(output_str)
    return output_str


def extract_import_errors(log):
    error_codes = ['E0428', 'E0432', 'E0603', 'E0433', 'E0425','E0599', 'E0255']
    pattern = re.compile(r'(error\[(?:' + '|'.join(error_codes) + r')\].*?)(?=error\[E\d+\]|$)', re.DOTALL)
    matches = pattern.findall(log)
    return '\n'.join(matches)

def remove_function_definitions(extra):
    # 正则表达式匹配全局函数定义和声明，包括 pub 和非 pub 的函数，支持可选的泛型参数
    pattern = re.compile(r'^(pub\s+)?fn\s+\w+(\s*<.*?>)?\s*\(.*?\)\s*->\s*[\w:<>]+\s*(\{.*?\}|;)', re.DOTALL | re.MULTILINE)
    return pattern.sub('', extra)


def post_process_source(data_manager, source, child_source, results, src_names, test_names, funcs_child, output_project_path, llm_model="qwen",check=True):
    if source not in results:
        return "source not in results"
    print(f"Processing {source}...")
    
    # if os.path.exists(get_source_path(source, src_names,output_project_path)):
    #     return

    src_output_path = get_source_path(source, src_names,output_project_path)

    def get_content(source, results, with_extra=True):
        if with_extra:
            content = "%s\n" % results[source].get("extra", "")
        else:
            content = ""
        for key, value in results[source].items():
            if key not in ["extra", "main"]:
                if value.lstrip().startswith("fn"):
                    value = 'pub ' + value
                if key.lstrip().startswith('test_'):
                    content += "#[test]\n#[timeout(60000)]\n" + "%s\n" % value
                else:
                    content += "%s\n" % value
        content = re.sub(r'\n{3,}', '\n\n', content).replace(data_manager.comment, '\n')
        # updated_content = re.sub(r'(?m)^(fn\s+\w+(\s*<[^>]*>)?\s*\([^)]*\)\s*->\s*[\w:<>]+\s*\{)', r'pub \1', content)

        return content

    content = get_content(source, results)

    if len(child_source) == 0:
        if  source in test_names:
            content = '\nuse ntest::timeout;\n' + content
        with open(src_output_path, 'w') as file:
            file.write(content)
        return ""
    
    content = get_content(source, results, with_extra=False)
    content = '\nuse ntest::timeout;\n' + content

    with open(src_output_path, 'w') as file:
        file.write(results[source].get("extra", "") + content)
    test_error = run_command(f"cd {output_project_path} && RUSTFLAGS=\"-Awarnings\" cargo check --tests")

    if not check:
        return test_error

    if len(child_source) != 0 and test_error.count("error") > 1:
        all_child_func_list = set()
        for func_name in results[source].keys():
            if func_name != 'extra':
                child_context, child_funs = data_manager.get_child_context(func_name, results, funcs_child)
                child_funs_list = child_funs.strip(',').split(',')
                all_child_func_list.update(child_funs_list)
        all_child_func_list = [func for func in all_child_func_list if func not in results[source].keys()]
        print(all_child_func_list)

        content_temp = ''
        first_lines = defaultdict(dict)
        for child in [source, *child_source]:
            if child in results:
                if "extra" in results[child]:
                    first_lines[child]['extra'] = results[child]["extra"]
                for sub_key, sub_value in results[child].items():
                    if sub_key != 'extra':
                        if child == source:
                            first_line = sub_value.lstrip().split('\n', 1)[0]
                            first_lines[child][sub_key] = first_line
                        else:
                            first_lines[child][sub_key] = f'注意： 该函数已经{child}文件中实现，直接导入，不要重复定义'

        prompt = generate_extra_prompt(first_lines, source, child_source, all_child_func_list)
        
        response = generate_response(prompt, llm_model, temperature=0)
        template = response.replace("```rust", "").replace("```", "")

        with open(src_output_path, 'w') as file:
            file.write(template + content)
        test_error = run_command(f"cd {output_project_path} && RUSTFLAGS=\"-Awarnings\" cargo check --tests")
        attempts = 0
        max_attempts = 10
        regenerations =0
        max_regenerations = 3
        while test_error.count("error") > 1:
            print(test_error)
            prompt_fix = fix_extra_prompt(prompt, response, source, child_source, parse_and_deduplicate_errors(test_error))
            print(f"##################################################################################################")
            print(f"Prompt length: {len(prompt_fix)}")
            response = generate_response(prompt_fix, llm_model, temperature=0)
            response = response.replace("```json\n", "").replace("\n```", "").replace("```json", "").replace("```", "")
            
            print(response)
            try:
                response_json = json.loads(response)
                template = response_json.get(source, {}).get('extra', '')
                for key, value in response_json.items():
                    if key != source and key in first_lines:
                        for sub_key, sub_value in value.items():
                            if sub_key in first_lines[key]:
                                if sub_key == 'extra' and sub_key in results[key]:
                                    # results[key][sub_key] = remove_function_definitions(sub_value)
                                    non_function_content, _,_ =  deduplicate_code(sub_value, tmp_dir)
                                    results[key][sub_key] = non_function_content
                    child_path = get_source_path(key, src_names,output_project_path)
                    with open(child_path, 'w') as file:
                        file.write(get_content(key, results))
            except json.JSONDecodeError as e:
                continue

            with open(src_output_path, 'w') as file:
                file.write(template + content)
            test_error = run_command(f"cd {output_project_path} && RUSTFLAGS=\"-Awarnings\" cargo check --tests")
            attempts += 1

            if attempts >= max_attempts:
                attempts = 0
                regenerations += 1
                if regenerations >= max_regenerations:
                    raise Exception(f"达到最大重试次数，请手动修改{source}文件的编译错误然后重新运行")
                print("Reached maximum attempts, regenerating template.")
                response = generate_response(prompt, llm_model, temperature=0)
                template = response.replace("```rust", "").replace("```", "")
                with open(src_output_path, 'w') as file:
                    file.write(template + content)
                test_error = run_command(f"cd {output_project_path} && RUSTFLAGS=\"-Awarnings\" cargo check --tests")
        results[source]['extra'] = template

    run_command(f"rustfmt {src_output_path}")
    return ""

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python post_process.py <config_path> [--eval-only]")
        sys.exit(1)
    config_path = sys.argv[1]
    eval_only = len(sys.argv) == 3 and sys.argv[2].lower() == '--eval-only'
    cfg = read_config(config_path)
    tmp_dir, output_dir, output_project_path,compile_commands_path,params,excluded_files= setup_project_directories(cfg)

    llm_model = "qwen"

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

    # source_path = [
    #     os.path.join(tmp_dir,'src_json/compare-int.json'),
    #     os.path.join(tmp_dir,'src_json/compare-pointer.json'),
    #     os.path.join(tmp_dir,'src_json/compare-string.json'),
    #     os.path.join(tmp_dir,'test_json/test-compare-functions.json'),
    #     os.path.join(tmp_dir,'src_json/sortedarray.json'),
    #     os.path.join(tmp_dir,'test_json/test-sortedarray.json'),
    #     os.path.join(tmp_dir,'src_json/arraylist.json'),
    #     os.path.join(tmp_dir,'test_json/test-arraylist.json'),
    # ]
    # src_names = ['compare-int','compare-pointer','compare-string','sortedarray','arraylist']
    # test_names = ['test-compare-functions','test-sortedarray','test-arraylist']


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

    post_process(data_manager, output_dir, output_project_path, src_names, test_names, funcs_childs, include_dict, sorted_funcs_depth, llm_model,eval_only=eval_only,test_timeout=params.get('test_timeout',60000))
