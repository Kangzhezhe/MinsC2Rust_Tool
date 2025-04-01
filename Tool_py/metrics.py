import ast
import os
import json
import csv
import re
import subprocess
from tqdm import tqdm
from run_tests import run_tests_and_calculate_rates


def get_source_path(source, src_names,output_project_path):
    if source in src_names:
        return f"{output_project_path}/src/{source.replace('-','_')}.rs"
    else:
        return f"{output_project_path}/tests/{source.replace('-','_')}.rs"

def calculate_asserts_count(output_project_path, results, src_names, test_names,output_dir):
    assert_def_path = "assert.rs"
    with open(assert_def_path, 'r') as assert_file:
        assert_content = assert_file.read()
    dynamic_assert_dict = {}
    static_assert_dict = {}
    for source in results.keys():
        if source in test_names:
            test_source_path = get_source_path(source, src_names,output_project_path)

            with open(test_source_path, 'r') as test_file:
                test_content = test_file.read()
            with open(test_source_path, 'w') as test_file:
                test_file.write(assert_content + test_content)

            static_assert_count = len(re.findall(r'assert!', test_content)) + len(re.findall(r'assert_eq!', test_content)) + len(re.findall(r'assert_ne!', test_content))
            static_assert_dict[source] = static_assert_count

            command = f'cd {output_project_path} && RUSTFLAGS=\"-Awarnings\" cargo test  --no-fail-fast --test {source.replace("-","_") } -- --nocapture'
            test_result = subprocess.run(command, shell=True, check=False, text=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output_str = test_result.stdout
            matches = re.findall(r'Total assertions made: (\d+)', output_str)
            if matches:
                max_assertions = max(map(int, matches))
            else:
                max_assertions = 0

            dynamic_assert_dict[source] = max_assertions
            
            with open(test_source_path, 'r') as test_file:
                test_content = test_file.read()
            test_content = test_content.replace(assert_content, '', 1)
            with open(test_source_path, 'w') as test_file:
                test_file.write(test_content)

    # 输出结果到 CSV 文件
    csv_file_path = os.path.join(output_dir, 'asserts_count.csv')
    
    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['Source', 'Static Assert Count', 'Dynamic Assert Count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for source in static_assert_dict.keys():
            writer.writerow({
                'Source': source,
                'Static Assert Count': static_assert_dict[source],
                'Dynamic Assert Count': dynamic_assert_dict.get(source, 0)
            })
    
    print("断言统计已保存到 asserts_count.csv 文件")
    print("\nStatic assert counts:")
    print(static_assert_dict)
    print("\nDynamic assert counts:")
    print(dynamic_assert_dict)


    

def calculate_tests_pass_rates(output_project_path, output_dir,results, sorted_funcs_depth):
    passed_tests, failed_tests, overall_pass_rate, _ = run_tests_and_calculate_rates(output_project_path)
    missing_rates = {}
    pass_fail_counts = {}

    for test_source_name, funcs in tqdm(sorted_funcs_depth.items()):
        pass_counts = 0
        fail_counts = 0
        if test_source_name not in results:
            continue
        for func_name in funcs:
            if func_name in passed_tests:
                pass_counts += 1
            if func_name in failed_tests:
                fail_counts += 1
        total_tests = pass_counts + fail_counts
        missing_rates[test_source_name] = fail_counts / total_tests if total_tests > 0 else 1
        pass_fail_counts[test_source_name] = (pass_counts, total_tests)

    pass_rates = {source: 1 - rate for source, rate in missing_rates.items()}

    print("测试通过率统计已保存到 tests_pass_rates.csv 文件")
    # 打印通过率
    print("\nPass rates:")
    for source, rate in pass_rates.items():
        print(f"{source}: {rate:.2%}")
    
    print(f"\nOverall pass rate: {overall_pass_rate:.2%}")

    # 保存到 CSV 文件
    with open(os.path.join(output_dir, 'tests_pass_rates.csv'), 'w', newline='') as csvfile:
        fieldnames = ['Source', 'Pass Rate', 'Pass Count', 'Total Count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for source, rate in pass_rates.items():
            pass_count, total_count = pass_fail_counts[source]
            writer.writerow({'Source': source, 'Pass Rate': f"{rate:.2%}", 'Pass Count': pass_count, 'Total Count': total_count})

         # 写入整体的通过率
        overall_pass_count = sum(pass_count for pass_count, _ in pass_fail_counts.values())
        overall_total_count = sum(total_tests for _, total_tests in pass_fail_counts.values())
        writer.writerow({'Source': 'Overall', 'Pass Rate': f"{overall_pass_rate:.2%}", 'Pass Count': overall_pass_count, 'Total Count': overall_total_count})


    return pass_rates

def calculate_compile_pass_rates(output_dir, results, sorted_funcs_depth, data_manager):
    missing_rates = {}
    missing_rates_func = {}
    flattened_results = {}
    total_funcs_all = 0
    total_filtered_funcs_all = 0
    missing_count_all = 0
    missing_filtered_count_all = 0

    for source, funcs in results.items():
        for func_name, value in funcs.items():
            flattened_results[func_name] = value

    detailed_data = []  # 用于存储详细数据行

    for test_source_name, funcs in tqdm(sorted_funcs_depth.items()):
        total_funcs = len(funcs)
        total_filtered_funcs = 0
        missing_count = 0
        missing_filtered_count = 0

        if test_source_name not in results:
            continue

        for func_name in funcs:
            if func_name not in flattened_results:
                missing_count += 1
                missing_count_all += 1
                if not func_name.startswith('test_'):
                    missing_filtered_count += 1
                    missing_filtered_count_all += 1
            if not func_name.startswith('test_'):
                total_filtered_funcs += 1
                total_filtered_funcs_all += 1

        total_funcs_all += total_funcs
        pass_count_with_test = total_funcs - missing_count
        pass_count_without_test = total_filtered_funcs - missing_filtered_count

        missing_rates[test_source_name] = missing_count / total_funcs if total_funcs > 0 else 0
        missing_rates_func[test_source_name] = missing_filtered_count / total_filtered_funcs if total_filtered_funcs > 0 else 0

        # 添加详细信息到数据列表
        detailed_data.append({
            'Source': test_source_name,
            'Pass Rate (with test)': 1 - missing_rates[test_source_name],
            'Pass count (with test)': pass_count_with_test,
            'Total count (with test)': total_funcs,
            'Pass Rate (without test)': 1 - missing_rates_func[test_source_name],
            'Pass count (without test)': pass_count_without_test,
            'Total count (without test)': total_filtered_funcs
        })

    all_missing_rates = missing_count_all / total_funcs_all if total_funcs_all > 0 else 0
    all_missing_rates_func = missing_filtered_count_all / total_filtered_funcs_all if total_filtered_funcs_all > 0 else 0

    # 添加总体统计
    detailed_data.append({
        'Source': 'Overall',
        'Pass Rate (with test)': 1 - all_missing_rates,
        'Pass count (with test)': total_funcs_all - missing_count_all,
        'Total count (with test)': total_funcs_all,
        'Pass Rate (without test)': 1 - all_missing_rates_func,
        'Pass count (without test)': total_filtered_funcs_all - missing_filtered_count_all,
        'Total count (without test)': total_filtered_funcs_all
    })

    # 将详细信息写入 CSV 文件
    with open(os.path.join(output_dir, 'compile_pass_rate.csv'), 'w', newline='') as csvfile:
        fieldnames = [
            'Source', 
            'Pass Rate (with test)', 
            'Pass count (with test)', 
            'Total count (with test)', 
            'Pass Rate (without test)', 
            'Pass count (without test)', 
            'Total count (without test)'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in detailed_data:
            writer.writerow({
                'Source': row['Source'],
                'Pass Rate (with test)': f"{row['Pass Rate (with test)']:.2%}",
                'Pass count (with test)': row['Pass count (with test)'],
                'Total count (with test)': row['Total count (with test)'],
                'Pass Rate (without test)': f"{row['Pass Rate (without test)']:.2%}",
                'Pass count (without test)': row['Pass count (without test)'],
                'Total count (without test)': row['Total count (without test)']
            })
    print("编译通过率统计已保存到 compile_pass_rate.csv 文件")
    print("\nPass rates (with test):")
    for source, rate in missing_rates.items():
        print(f"{source}: {1 - rate:.2%}")

    print("\nPass rates for functions (without test):")
    for source, rate in missing_rates_func.items():
        print(f"{source}: {1 - rate:.2%}")

    print(f"\nOverall pass rate (with test): {1 - all_missing_rates:.2%}")
    print(f"Overall pass rate for functions (without test): {1 - all_missing_rates_func:.2%}")



def calculate_retry_pass_rates(output_dir,results,include_dict,once_retry_count_dict,test_names):
    once_pass_rate = {}
    once_pass_counts = {}
    for test_source_name, child_sources in tqdm(include_dict.items()):
        if test_source_name not in test_names or test_source_name not in once_retry_count_dict:
            continue
        
        pass_counts = 0
        fail_counts = 0
        
        source_names = [test_source_name] + child_sources
        for source_name in source_names:
            if source_name not in results or test_source_name not in once_retry_count_dict or source_name not in once_retry_count_dict:
                continue
            for k,v in once_retry_count_dict[source_name].items():
                if v == 0:
                    pass_counts += 1
                else:
                    fail_counts += 1
        total_tests = pass_counts + fail_counts
        once_pass_rate[test_source_name] = pass_counts / total_tests if total_tests > 0 else 0
        once_pass_counts[test_source_name] = (pass_counts, total_tests)

    print("一次编译通过率统计已保存到 once_pass_rates.csv 文件")
    print("\nPass rates:")
    for source, rate in once_pass_rate.items():
        print(f"{source}: {rate:.2%}")
    
    overall_pass_rate = sum(pass_count for pass_count, _ in once_pass_counts.values()) / sum(total_tests for _, total_tests in once_pass_counts.values())
    print(f"\nOverall pass rate: {overall_pass_rate:.2%}")

    # 保存到 CSV 文件
    with open(os.path.join(output_dir,'once_pass_rates.csv'), 'w', newline='') as csvfile:
        fieldnames = ['Source', 'Pass Rate', 'Pass Count', 'Total Count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for source, rate in once_pass_rate.items():
            pass_count, total_count = once_pass_counts[source]
            writer.writerow({'Source': source, 'Pass Rate': f"{rate:.2%}", 'Pass Count': pass_count, 'Total Count': total_count})

        writer.writerow({'Source': 'Overall', 'Pass Rate': f"{overall_pass_rate:.2%}", 'Pass Count': sum(pass_count for pass_count, _ in once_pass_counts.values()), 'Total Count': sum(total_tests for _, total_tests in once_pass_counts.values())})


    return overall_pass_rate

def calculate_loc_statistics(output_dir, results, sorted_funcs_depth, data_manager):
    """
    计算每个源文件的代码行数（LOC）、总代码行数（Total LOC）和行覆盖率（LCov），并打印和保存为 CSV 文件。

    参数:
        output_dir (str): 输出目录。
        results (dict): 包含每个源文件及其函数的结果数据。
        sorted_funcs_depth (dict): 按深度排序的函数依赖关系。
        data_manager (object): 数据管理器，用于获取函数内容和包含关系。

    返回:
        float: 总体代码行数的统计结果。
    """
    detailed_data = []  # 用于存储详细数据行
    total_loc_all = 0
    loc_all = 0
    rust_loc_all = 0

    for test_source_name, funcs in tqdm(sorted_funcs_depth.items()):
        if test_source_name not in results:
            continue

        # 获取包含关系索引（如果需要）
        data_manager.get_include_indices(test_source_name)

        total_loc = 0
        loc = 0
        rust_loc = 0

        for func in funcs:
            func_content, _, _ = data_manager.get_content(func)
            if data_manager.get_result(func,results) != '':
                loc += len(func_content.split('\n'))
                rust_loc += len(data_manager.get_result(func,results).split('\n'))
            total_loc += len(func_content.split('\n'))
        _,before_details = data_manager.get_details(funcs)
        converted_dict = ast.literal_eval(before_details)
        non_function_elements = '\n'.join(converted_dict.values())
        loc += len(non_function_elements.split('\n'))
        total_loc += len(non_function_elements.split('\n'))

        # 累计总 LOC 和总代码行数
        total_loc_all += total_loc
        loc_all += loc
        rust_loc_all += rust_loc

        # 计算行覆盖率（LCov）
        lcov = loc / total_loc if total_loc > 0 else 0

        # 添加详细信息到数据列表
        detailed_data.append({
            'Source': test_source_name,
            'LOC': loc,
            'Total LOC': total_loc,
            'LCov': lcov,
            'Rust LOC': rust_loc
        })

    # 添加总体统计
    overall_lcov = loc_all / total_loc_all if total_loc_all > 0 else 0
    detailed_data.append({
        'Source': 'Overall',
        'LOC': loc_all,
        'Total LOC': total_loc_all,
        'LCov': overall_lcov,
        'Rust LOC': rust_loc_all
    })

    # 打印统计信息
    print("代码行数统计已保存到 loc_statistics.csv 文件")
    print("\nLOC Statistics:")
    for row in detailed_data:
        print(f"{row['Source']}: LOC = {row['LOC']}, Total LOC = {row['Total LOC']}, LCov = {row['LCov']:.2%}, Rust LOC = {row['Rust LOC']}")

    # 保存到 CSV 文件
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'loc_statistics.csv')
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['Source', 'LOC', 'Total LOC', 'LCov', 'Rust LOC']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in detailed_data:
            writer.writerow({
                'Source': row['Source'],
                'LOC': row['LOC'],
                'Total LOC': row['Total LOC'],
                'LCov': f"{row['LCov']:.2%}",
                'Rust LOC': row['Rust LOC']
            })

    print(f"\n统计结果已保存到: {csv_path}")

    return total_loc_all