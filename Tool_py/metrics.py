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
    
    if sum(total_tests for _, total_tests in once_pass_counts.values()) == 0:
        overall_pass_rate = 0
    else:
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
    计算代码统计指标，包含函数数量、最大函数长度和平均函数长度
    """
    detailed_data = []
    total_loc_all = 0
    loc_all = 0
    rust_loc_all = 0
    total_func_count = 0  # 新增：总函数计数
    all_fn_lens = []      # 新增：存储所有函数长度

    for test_source_name, funcs in tqdm(sorted_funcs_depth.items()):
        # if test_source_name not in results:
        #     continue

        data_manager.get_include_indices(test_source_name)
        
        total_loc = 0
        loc = 0
        rust_loc = 0
        fn_lens = []      # 新增：单文件函数长度记录

        # 处理函数部分
        for func in funcs:
            func_content, _, _ = data_manager.get_content(func)
            fn_len = len(func_content.split('\n'))  # 计算函数长度
            fn_lens.append(fn_len)
            
            if data_manager.get_result(func, results):
                loc += fn_len
                rust_loc += len(data_manager.get_result(func, results).split('\n'))
            total_loc += fn_len

        # 处理非函数部分
        _, before_details = data_manager.get_details(funcs)
        non_function = '\n'.join(ast.literal_eval(before_details).values())
        non_fn_len = len(non_function.split('\n'))
        loc += non_fn_len
        total_loc += non_fn_len

        # 计算统计指标
        func_count = len(funcs)
        max_fn = max(fn_lens) if fn_lens else 0
        mean_fn = sum(fn_lens)/func_count if func_count > 0 else 0
        
        # 累计全局数据
        total_func_count += func_count
        all_fn_lens.extend(fn_lens)
        total_loc_all += total_loc
        loc_all += loc
        rust_loc_all += rust_loc

        # 记录文件数据
        detailed_data.append({
            'Source': test_source_name,
            'LOC': loc,
            'Total LOC': total_loc,
            'LCov': loc / total_loc if total_loc else 0,
            'Rust LOC': rust_loc,
            'Func Count': func_count,       # 新增字段
            'Max Fn Len': max_fn,           # 新增字段
            'Mean Fn Len': mean_fn          # 新增字段
        })

    # 添加全局统计数据
    overall_lcov = loc_all / total_loc_all if total_loc_all else 0
    detailed_data.append({
        'Source': 'Overall',
        'LOC': loc_all,
        'Total LOC': total_loc_all,
        'LCov': overall_lcov,
        'Rust LOC': rust_loc_all,
        'Func Count': total_func_count,
        'Max Fn Len': max(all_fn_lens) if all_fn_lens else 0,
        'Mean Fn Len': sum(all_fn_lens)/total_func_count if total_func_count else 0
    })

    # 打印输出
    print("\n数据集统计信息:")
    header = f"{'Source':<15} | {'LOC':>6} | {'Total':>6} | {'Cov':>6} | {'Rust':>6} | {'Funcs':>5} | {'MaxLen':>6} | {'AvgLen':>6}"
    print(header)
    for row in detailed_data:
        output = f"{row['Source'][:14]:<15} | {row['LOC']:6} | {row['Total LOC']:6} | " \
                f"{row['LCov']:>5.1%} | {row['Rust LOC']:6} | {row['Func Count']:5} | " \
                f"{row['Max Fn Len']:6} | {row['Mean Fn Len']:6.1f}"
        print(output)

    # 保存CSV文件
    csv_path = os.path.join(output_dir, 'loc_statistics.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Source', 'LOC', 'Total LOC', 'LCov', 'Rust LOC', 
            'Func Count', 'Max Fn Len', 'Mean Fn Len'
        ])
        writer.writeheader()
        for row in detailed_data:
            row['LCov'] = f"{row['LCov']:.1%}"
            row['Mean Fn Len'] = f"{row['Mean Fn Len']:.1f}"
            writer.writerow(row)

    print(f"\n完整统计数据已保存至: {csv_path}")
    return total_loc_all