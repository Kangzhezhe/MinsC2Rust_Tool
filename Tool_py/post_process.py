import os
import json
import re
from collections import defaultdict
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from parse_config import read_config, setup_project_directories
from models.llm_model import generate_response
from metrics import calculate_compile_pass_rates, calculate_retry_pass_rates, calculate_tests_pass_rates
from merge_c_h import process_files
from utils import run_command
from prompts import generate_extra_prompt,fix_extra_prompt
from logger import logger_init
from clang_callgraph import clang_callgraph
from src.data_manager import DataManager

def post_process(data_manager, output_dir, output_project_path, src_names, test_names, funcs_childs, include_dict, sorted_funcs_depth, llm_model="qwen",eval_only=False):
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

    if not eval_only:
        all_source_names = set()
        for source in results.keys():
            if source in test_names:
                _, all_include_files = data_manager.get_include_indices(source)
                funcs_child = funcs_childs[source]
                for include_file in all_include_files:
                    if include_file in src_names and include_file in results:
                        all_source_names.add(f"pub mod {include_file.replace('-', '_')};")
                        child_source = include_dict.get(include_file, [])
                        post_process_source(data_manager, include_file, child_source, results, src_names, test_names, funcs_child, output_project_path, llm_model)
                with open(f'{output_project_path}/src/lib.rs', 'w') as f:
                    f.write('\n'.join(all_source_names))
                    f.write('\n')
                child_source = include_dict.get(source, [])
                post_process_source(data_manager, source, child_source, results, src_names, test_names, funcs_child, output_project_path, llm_model)
    
    
    test_result = run_command(f'cd {output_project_path} && cargo test --no-fail-fast')
    print(test_result)
    calculate_tests_pass_rates(output_project_path,output_dir, results, sorted_funcs_depth)



def extract_import_errors(log):
    error_codes = ['E0428', 'E0432', 'E0603', 'E0433', 'E0425','E0599', 'E0255']
    pattern = re.compile(r'(error\[(?:' + '|'.join(error_codes) + r')\].*?)(?=error\[E\d+\]|$)', re.DOTALL)
    matches = pattern.findall(log)
    return '\n'.join(matches)

def remove_function_definitions(extra):
    # 正则表达式匹配全局函数定义和声明，包括 pub 和非 pub 的函数，支持可选的泛型参数
    pattern = re.compile(r'^(pub\s+)?fn\s+\w+(\s*<.*?>)?\s*\(.*?\)\s*->\s*[\w:<>]+\s*(\{.*?\}|;)', re.DOTALL | re.MULTILINE)
    return pattern.sub('', extra)

def post_process_source(data_manager, source, child_source, results, src_names, test_names, funcs_child, output_project_path, llm_model="qwen"):
    if source not in results:
        return
    print(f"Processing {source}...")

    def get_source_path(source, src_names):
        if source in src_names:
            return f"{output_project_path}/src/{source.replace('-','_')}.rs"
        else:
            return f"{output_project_path}/tests/{source.replace('-','_')}.rs"

    if os.path.exists(get_source_path(source, src_names)):
        return

    src_output_path = get_source_path(source, src_names)

    def get_content(source, results, with_extra=True):
        if with_extra:
            content = "%s\n" % results[source].get("extra", "")
        else:
            content = ""
        for key, value in results[source].items():
            if key not in ["extra", "main"]:
                if value.startswith("fn"):
                    value = 'pub ' + value
                if key.startswith('test_'):
                    content += "#[test]\n" + "%s\n" % value
                else:
                    content += "%s\n" % value
        content = re.sub(r'\n{3,}', '\n\n', content)
        # updated_content = re.sub(r'(?m)^(fn\s+\w+(\s*<[^>]*>)?\s*\([^)]*\)\s*->\s*[\w:<>]+\s*\{)', r'pub \1', content)

        return content

    content = get_content(source, results)

    if len(child_source) == 0:
        with open(src_output_path, 'w') as file:
            file.write(content)
    
    content = get_content(source, results, with_extra=False)

    if len(child_source) != 0:
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
            prompt_fix = fix_extra_prompt(prompt, response, source, child_source, test_error)
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
                                if sub_key == 'extra' and results[key].get(sub_key, '') != '':
                                    results[key][sub_key] = remove_function_definitions(sub_value)
                                    # results[key][sub_key] = sub_value
                    child_path = get_source_path(key, src_names)
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
                template = generate_response(prompt, llm_model, temperature=0).replace("```rust", "").replace("```", "")
                with open(src_output_path, 'w') as file:
                    file.write(template + content)
                test_error = run_command(f"cd {output_project_path} && RUSTFLAGS=\"-Awarnings\" cargo check --tests")

    run_command(f"rustfmt {src_output_path}")

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
    sorted_funcs_depth,funcs_childs,include_dict,all_pointer_funcs = clang_callgraph(compile_commands_path,include_dict,all_file_paths)
    logger = logger_init(os.path.join(output_dir,'app.log'))

    test_path = os.listdir(os.path.join(tmp_dir, 'test_json'))
    test_path = [os.path.join(tmp_dir, 'test_json', f) for f in test_path]
    test_names = [os.path.splitext(os.path.basename(f))[0] for f in test_path]
    src_path = os.listdir(os.path.join(tmp_dir, 'src_json'))
    src_path = [os.path.join(tmp_dir, 'src_json', f) for f in src_path]
    src_names = [os.path.splitext(os.path.basename(f))[0] for f in src_path]
    source_path = test_path
    source_path.extend(src_path)

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
    
    data_manager = DataManager(source_path,include_dict=include_dict,all_pointer_funcs=all_pointer_funcs) 


    post_process(data_manager, output_dir, output_project_path, src_names, test_names, funcs_childs, include_dict, sorted_funcs_depth, llm_model,eval_only=eval_only)
