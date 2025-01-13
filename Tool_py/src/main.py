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


def process_func(test_source_name, func_name, depth, start_time, source_names, funcs_childs, data_manager, results, logger, llm_model, tmp_dir,  all_error_funcs_content, once_retry_count_dict,funcs,lock,params):
    global total_retry_count, total_regenerate_count, total_error_count

    tmp_dir = os.path.join(tmp_dir, test_source_name+'_'+func_name)
    os.makedirs(tmp_dir, exist_ok=True)
    funcs_child = funcs_childs[test_source_name]

    max_history_length = 0
    data_manager.get_include_indices(test_source_name)
    _, _, i = data_manager.get_content(func_name)
    if i != -1 and i in data_manager.include_files_indices:
        source_name = source_names[i]
    else:
        raise ValueError(f"{source_name} is not correct")

    if i == -1 or func_name == 'main' or func_name == 'extra' or func_name in results.get(source_name, {}) or func_name in ['run_test', 'run_tests'] or func_name in all_error_funcs_content.get(source_name, {}):
        shutil.rmtree(tmp_dir)
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
    before_details = data_manager.get_details(child_funs_c_list)
    child_context, child_funs = data_manager.get_child_context(func_name, results, funcs_child)
    child_funs_list = child_funs.strip(',').split(',')
    all_child_func_list = child_funs_list + child_funs_c_list
    debug(f'child_funs_list: {child_funs_list}, child_funs_c_list: {child_funs_c_list}')

    if params['enable_english_prompt']:
        prompt = get_rust_function_conversion_prompt_english(child_funs_c, child_funs, child_context, before_details,source_context)
    else:
        prompt = get_rust_function_conversion_prompt(child_funs_c, child_funs, child_context, before_details,source_context)

    logger.info(f"################################################################################################## Processing func: {func_name}")
    debug(f"Prompt length: {len(prompt)}")
    response = generate_response(prompt, llm_model)
    debug(response)
    text_remove = response.replace("```rust", "").replace("```", "")

    
    max_retries = min(4+depth*2, params['max_retries'])
    template = f"""{child_context}\n\n{text_remove}\n\n{"fn main(){}" if func_name != 'main' else ''}"""
    compile_error1 = ''
    conversation_history = []
    max_history_length = params['max_history_length']
    max_history_limit_tokens = params['max_history_limit_tokens']
    compile_error = ''
    last_compile_error = ''
    max_json_insert_retries = params['max_json_insert_retries']
    if len(child_funs_c_list) > 1:
        max_regenerations = 0
    else:
        max_regenerations = min(2 + depth, params['max_regenerations'])

    retry_count = 0
    regenerate_count = 0

    added_funcs = set()
    all_files = set()
    while 1:
        if retry_count < max_retries:
            with open(os.path.join(tmp_dir,'temp.rs'), 'w') as f:
                f.write(template)
            last_compile_error = compile_error
            compile_error = run_command(f"rustc -Awarnings {os.path.join(tmp_dir,'temp.rs')}")
            delete_file_if_exists('temp')
            compile_error = filter_toolchain_errors(compile_error)
            if compile_error != '' and compile_error1 != '' and last_compile_error == compile_error and retry_count != 0:
                retry_count = max_retries
                continue
            debug("compile_error:", compile_error)
            
            debug('conversation_history len:', len(conversation_history))
            if compile_error:
                retry_count += 1
                with lock:
                    total_retry_count += 1
                if retry_count >= max_retries:
                    continue
                logger.info(f"Compilation failed for {func_name}, retrying... {retry_count}/{max_retries}")
                # history_prompt = "\n".join([f"Prompt: {entry['prompt']}\nResponse: {entry['response']}" for entry in conversation_history])
                if params['enable_english_prompt']:
                    prompt1 = get_error_fixing_prompt_english(template, compile_error)
                else:
                    prompt1 = get_error_fixing_prompt(template, compile_error)
                debug(f"Prompt length: {len(prompt1)}")
                if len(prompt1) < max_history_limit_tokens:
                    i = 0
                    while len(prompt1) < max_history_limit_tokens and i < len(conversation_history):
                        latest_entry = conversation_history[-1 - i]
                        history_prompt = f"Prompt: {latest_entry['prompt']}\nResponse: {latest_entry['response']}\n"
                        prompt1 = history_prompt + prompt1
                        i += 1
                    if i > 0:
                        prompt1 = 'history:\n' + prompt1
                        debug(f"Prompt length after history: {len(prompt1)}")
                response = generate_response(prompt1,llm_model)
                debug(response)
                template = response.replace("```rust", "").replace("```", "")
                
                # 保存对话历史
                conversation_history.append({
                    "prompt": compile_error,
                    "response": response,
                })
                if len(conversation_history) > max_history_length:
                    conversation_history.pop(0)
            else:
                debug(f"Compilation successful for {func_name}!")
                debug("##################################################################################################")

                if all_files == set():
                    for func in all_child_func_list:
                        temp_func = data_manager.get_all_parent_functions(func, funcs_child)
                        if temp_func != set():
                            extended_funcs = [f for f in temp_func if f not in all_child_func_list and data_manager.get_result(f,results) != '']
                            extended_child_funcs = set()
                            for parent_func in extended_funcs:
                                child_funcs = data_manager.get_all_child_functions(parent_func, funcs_child)
                                extended_child_funcs = extended_child_funcs.union(child_funcs)
                            all_child_func_list.extend(extended_funcs)
                            all_child_func_list.extend([func for func in extended_child_funcs if func not in all_child_func_list and data_manager.get_result(func,results) != ''])

                    for func in all_child_func_list:
                        temp_file =data_manager.get_source_name_by_func_name(func)
                        if temp_file != '':
                            all_files.add(temp_file)
                
                all_function_lines = '\n'.join(
                    value
                    for file, source in results.items()
                    if file in data_manager.all_include_files and file not in all_files
                    for key, value in source.items()
                )

                all_function_lines1 = all_function_lines + '\n'.join(
                    value
                    for file, source in results.items()
                    if file in all_files
                    for key, value in source.items()
                    if key != 'extra'
                )+ '\n' + template
                
                non_function_content, function_content_dict, output_content = deduplicate_code(all_function_lines1,tmp_dir)
                if func_name not in function_content_dict:
                    retry_count = max_retries
                    continue
                with open(os.path.join(tmp_dir,'test_source.rs'), 'w') as f:
                    f.write(output_content)
                compile_error1 = run_command(f'rustc -Awarnings {os.path.join(tmp_dir,'test_source.rs')}')
                delete_file_if_exists('test_source')
                if compile_error1:
                    line_numbers = re.findall(r'-->.*:(\d+):\d+', compile_error1)
                    run_command(f"cd ../rust_ast_project/ && cargo run {os.path.join(tmp_dir,'test_source.rs')} {os.path.join(tmp_dir,'definitions.json')}")
                    definitions = read_json_file(os.path.join(tmp_dir,'definitions.json'))
                    line_funcs = get_functions_by_line_numbers(definitions, line_numbers)
                    if len(line_numbers) > len(line_funcs):
                        non_function_content1, _, _ = deduplicate_code(all_function_lines,tmp_dir)
                        template = non_function_content1+'\n'+template
                        all_files = data_manager.all_include_files
                    for func in line_funcs:
                        if func not in child_funs and func != 'main' and func != func_name:
                            if func not in added_funcs:
                                template = template + '\n' + function_content_dict[func]
                                added_funcs.add(func)
                            if func in funcs_child:
                                all_child_funs = data_manager.get_all_child_functions(func, funcs_child)
                                for child_fun in all_child_funs:
                                    if child_fun != func and child_fun in function_content_dict and child_fun not in child_funs:
                                        if child_fun not in added_funcs:
                                            template += function_content_dict[child_fun]
                                            added_funcs.add(child_fun)
                    debug(f"line_number:{line_numbers}, line_funcs:{line_funcs}")
                    debug(f'added_funcs:{added_funcs}')
                    logger.info(f"Compilation failed for processed_all_files.rs, retrying...")
                    retry_count += 1
                    with lock:
                        total_retry_count += 1
                    continue

                all_files = data_manager.all_include_files
                logger.info(f'all_files:{all_files}')
                with open(os.path.join(tmp_dir,'processed_all_files.rs'), 'w') as f:
                    f.write(output_content)
                results_copy = copy.deepcopy(results)
                temp_results = {k: v for k, v in function_content_dict.items() if data_manager.get_source_name_by_func_name(k) in all_files}
                extra_content = '\n'.join(v for k, v in function_content_dict.items() if k not in temp_results and k != 'main')
                for k, v in temp_results.items():
                    _, _, i = data_manager.get_content(k)
                    name = source_names[i]
                    if name not in results_copy:
                        results_copy[name] = {}
                    results_copy[name][k] = v

                if results_copy[source_name].get(func_name, '') == '':
                    results_copy[source_name][func_name] = ''
                results_copy[source_name][func_name] += extra_content

                # if source_name in src_names:
                #     results[source_name]['extra'] = non_function_content

                all_files = data_manager.all_include_files
                logger.info(f"Processing extra insert")
                first_lines = {}
                if results_copy[source_name].get('extra', '') == '':
                    results_copy[source_name]['extra'] = ''
                if len(all_files) > 1:
                    for key, value_dict in results_copy.items():
                        if key in all_files:
                            first_lines[key] = {}
                            for sub_key, sub_value in value_dict.items():
                                if key == source_name and sub_key == func_name or sub_key == 'extra':
                                    first_lines[key][sub_key] = sub_value
                                else:
                                    first_line = sub_value.lstrip().split('\n', 1)[0]
                                    first_lines[key][sub_key] = first_line
                    compile_error2 = ''
                    task_prompt = get_task_prompt(non_function_content, first_lines)
                    debug('non_function_content:', non_function_content)
                    prompt1 = task_prompt
                    retry = 0
                    # data_manager.get_include_indices_with_parent(test_source_name)
                    # all_files = data_manager.all_include_files
                    while True:
                        debug(f"Prompt length: {len(prompt1)}")
                        response = generate_response(prompt1,llm_model,0.2)
                        response = response.replace("```json\n", "").replace("\n```", "").replace("```json", "").replace("```", "")
                        debug(response)
                        try:
                            response_json = json.loads(response)
                            for key, value in response_json.items():
                                if key in results_copy:
                                    results_copy[key]['extra'] = value.get('extra', '')
 
                            compile_error2 = ''
                            for file in all_files:
                                all_child_files = [file]
                                data_manager.get_all_source(file,all_child_files)

                                all_function_lines = '\n'.join(
                                    value
                                    for file, source in results_copy.items()
                                    if file in all_child_files
                                    for key, value in source.items()
                                    if key != 'extra' and key != 'main'
                                )
                                
                                all_function_lines += '\nfn main(){}'
                                output_content = all_function_lines

                                for source in all_child_files:
                                    if 'extra' in results_copy.get(source,[]):
                                        output_content = results_copy[source]['extra'] + '\n' + output_content
                                        

                                with open(os.path.join(tmp_dir,'test_source.rs'), 'w') as f:
                                    f.write(output_content)
                                compile_error2 = run_command(f'rustc -Awarnings {os.path.join(tmp_dir,'test_source.rs')}')

                                delete_file_if_exists('test_source')
                                if compile_error2:
                                    break
                            debug(compile_error2)
                            if compile_error2:
                                retry+=1
                                if retry>=max_json_insert_retries:
                                    logger.info("Failed to parse JSON response, skiping...")
                                    break
                                logger.info(f"Compilation failed for json processed_all_files.rs, retrying...") 
                                prompt1 = get_json_fixing_prompt(task_prompt, response, compile_error2)
                                continue
                        except json.JSONDecodeError as e:
                            retry+=1
                            if retry>=max_json_insert_retries:
                                logger.info("Failed to parse JSON response, skiping...")
                                break
                            logger.info("Failed to parse JSON response, regenerating...")
                            error_position = e.pos if hasattr(e, 'pos') else 'unknown'
                            error_msg = str(e)
                            error_content = response[error_position:min(error_position+20, len(response))]
                            prompt1 = get_json_parsing_fix_prompt(task_prompt, response, error_msg, error_position, error_content)
                            continue
                        break
                elif len(all_files) == 1:
                    results_copy[source_name]['extra'] = non_function_content
                else :
                    raise ValueError("all_files is not correct")

                if retry>=max_json_insert_retries:
                    with lock:
                        total_error_count += 1
                    if source_name not in all_error_funcs_content:
                        all_error_funcs_content[source_name] = {}
                    all_error_funcs_content[source_name][func_name] = output_content + '\n //insert编译报错信息：' + compile_error2
                    shutil.rmtree(tmp_dir)
                    return
                results = results_copy
                if source_name not in once_retry_count_dict:
                    once_retry_count_dict[source_name] = {}
                once_retry_count_dict[source_name][func_name] = retry_count

                break
        else:
            regenerate_count += 1
            if params['enable_multi_models']:
                if regenerate_count == 1:
                    llm_model = 'zhipu'

            if regenerate_count >= max_regenerations:
                logger.warning(f"Failed to compile {func_name} after {regenerate_count} regenerations. Skipping...")
                # total_error_funcs.append(func_name)
                if source_name not in all_error_funcs_content:
                    all_error_funcs_content[source_name] = {}
                all_error_funcs_content[source_name][func_name] = template + '\n //编译报错信息：' + compile_error
                with lock:
                    total_error_count += 1
                break

            logger.info(f"Failed to compile {func_name} after {max_retries} attempts. Regenerating code...")
            debug(f"Prompt length: {len(prompt)}")
            response = generate_response(prompt,llm_model)
            debug(response)
            text_remove = response.replace("```rust", "").replace("```", "")
            template = f"""{child_context}\n\n{text_remove}\n\n{"fn main(){}" if func_name != 'main' else ''}"""

            retry_count = 0
            added_funcs = set()
            all_files = set()
            
            with lock:
                total_regenerate_count += 1
            conversation_history = []
    
    shutil.rmtree(tmp_dir)
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
                update_nested_dict(local_results, updated_results)
                update_nested_dict(local_all_error_funcs_content, updated_all_error_funcs_content)
                update_nested_dict(local_once_retry_count_dict, updated_once_retry_count_dict)
                func_counter += 1

                # 保存检查点
                if func_counter % checkpoint_interval == 0:
                    with lock:
                        update_nested_dict(shared_results, local_results)
                        update_nested_dict(shared_all_error_funcs_content, local_all_error_funcs_content)
                        update_nested_dict(shared_once_retry_count_dict, local_once_retry_count_dict)
                        save_checkpoint(shared_results, shared_once_retry_count_dict, shared_all_error_funcs_content, output_dir)

    # 最后保存一次
    with lock:
        update_nested_dict(shared_results, local_results)
        update_nested_dict(shared_all_error_funcs_content, local_all_error_funcs_content)
        update_nested_dict(shared_once_retry_count_dict, local_once_retry_count_dict)
        save_checkpoint(shared_results, shared_once_retry_count_dict, shared_all_error_funcs_content, output_dir)

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



def parallel_process(sorted_funcs_depth, funcs_childs, source_names, results, data_manager, logger, llm_model, tmp_dir, output_dir, all_error_funcs_content, once_retry_count_dict, test_names, params):
    start_time = time.time()
    
    lock = threading.Lock()
    global total_retry_count, total_regenerate_count, total_error_count

    # 获取每个 test_source_name 的包含列表
    include_lists = {test_name: set(data_manager.get_include_indices(test_name)[1]) for test_name in test_names}

    # 找到可以并行处理的 test_source_name 组
    parallel_groups = []
    while include_lists:
        test_name, include_list = include_lists.popitem()
        group = {test_name}
        group_include_list = include_list.copy()
        to_remove = [test_name]
        for other_test_name, other_include_list in list(include_lists.items()):
            if group_include_list.isdisjoint(other_include_list):
                group.add(other_test_name)
                to_remove.append(other_test_name)
                group_include_list.update(other_include_list)  # 更新 group_include_list 以确保没有交集
        for test_name in to_remove:
            include_lists.pop(test_name, None)
        parallel_groups.append(group)

    # 并行处理每个 test_source_name
    for group in parallel_groups:
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
                    with lock:
                        update_nested_dict(results, updated_results)
                        update_nested_dict(all_error_funcs_content, updated_all_error_funcs_content)
                        update_nested_dict(once_retry_count_dict, updated_once_retry_count_dict)
                        save_checkpoint(results, once_retry_count_dict, all_error_funcs_content, output_dir)

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
    include_dict,all_file_paths = process_files(compile_commands_path, tmp_dir)
    sorted_funcs_depth,funcs_childs,include_dict = clang_callgraph(compile_commands_path,include_dict,all_file_paths)
    logger = logger_init(os.path.join(output_dir,'app.log'))

    test_path = os.listdir(os.path.join(tmp_dir, 'test_json'))
    test_path = [os.path.join(tmp_dir, 'test_json', f) for f in test_path]
    test_names = [os.path.splitext(os.path.basename(f))[0] for f in test_path]
    src_path = os.listdir(os.path.join(tmp_dir, 'src_json'))
    src_path = [os.path.join(tmp_dir, 'src_json', f) for f in src_path]
    src_names = [os.path.splitext(os.path.basename(f))[0] for f in src_path]
    source_path = test_path
    source_path.extend(src_path)

    # source_path = [
    #     os.path.join(tmp_dir,'src_json/compare-int.json'),
    #     os.path.join(tmp_dir,'src_json/compare-pointer.json'),
    #     os.path.join(tmp_dir,'src_json/compare-string.json'),
    #     os.path.join(tmp_dir,'test_json/test-compare-functions.json'),
    #     os.path.join(tmp_dir,'src_json/sortedarray.json'),
    #     os.path.join(tmp_dir,'test_json/test-sortedarray.json'),
    # ]
    # src_names = ['compare-int','compare-pointer','compare-string','sortedarray']
    # test_names = ['test-compare-functions','test-sortedarray']


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
    
    data_manager = DataManager(source_path,include_dict=include_dict)   



    results = {}
    start_time = time.time()
    total_retry_count = 0
    total_regenerate_count = 0
    total_error_count = 0
    total_error_funcs = []
    all_error_funcs_content = defaultdict(dict) 
    once_retry_count_dict = defaultdict(dict)
    results = defaultdict(dict)

    results, once_retry_count_dict, all_error_funcs_content =  load_checkpoint(output_dir, results, once_retry_count_dict, all_error_funcs_content)

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
