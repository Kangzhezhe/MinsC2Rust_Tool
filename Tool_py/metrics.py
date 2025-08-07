import ast
import os
import json
import csv
import re
import subprocess
from tqdm import tqdm
from run_tests import run_tests_and_calculate_rates
import pandas as pd

def is_test_name_valid(test_source_name, test_names):
    if test_source_name in test_names:
        return True
    # 检查去掉uncovered前缀后的名称
    normalized_name = test_source_name.replace('test_uncovered_', 'test_')
    return normalized_name in test_names

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
    
    print("Assertion statistics have been saved to asserts_count.csv file")
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
        # if test_source_name not in results:
        #     continue
        if not is_test_name_valid(test_source_name, results.keys()):
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

    print("Test pass rate statistics have been saved to tests_pass_rates.csv file")
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

    # 原始数据存储
    raw_data = {}
    
    for test_source_name, funcs in tqdm(sorted_funcs_depth.items()):
        funcs = [f for f in funcs if f != 'main']
        total_funcs = len(funcs)
        total_filtered_funcs = 0
        missing_count = 0
        missing_filtered_count = 0

        if not is_test_name_valid(test_source_name, results.keys()):
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

        # 存储原始数据
        raw_data[test_source_name] = {
            'pass_count_with_test': pass_count_with_test,
            'total_count_with_test': total_funcs,
            'pass_count_without_test': pass_count_without_test,
            'total_count_without_test': total_filtered_funcs
        }

    # 合并 uncovered 数据
    merged_data = {}
    for source, data in raw_data.items():
        if source.startswith('test-uncovered_'):
            # 获取对应的主测试文件名
            main_test = source.replace('test-uncovered_', 'test-')
            if main_test in raw_data:
                # 合并到主测试文件
                if main_test not in merged_data:
                    merged_data[main_test] = raw_data[main_test].copy()
                
                # 数值相加
                merged_data[main_test]['pass_count_with_test'] += data['pass_count_with_test']
                merged_data[main_test]['total_count_with_test'] += data['total_count_with_test']
                merged_data[main_test]['pass_count_without_test'] += data['pass_count_without_test']
                merged_data[main_test]['total_count_without_test'] += data['total_count_without_test']
            else:
                # 如果没有对应的主测试文件，直接添加（去掉 uncovered_ 前缀显示）
                display_name = source.replace('test-uncovered_', 'test-')
                merged_data[display_name] = data
        else:
            # 非 uncovered 文件
            if source not in merged_data:
                merged_data[source] = data

    # 生成最终显示数据
    detailed_data = []
    for source, data in merged_data.items():
        # 计算百分比（用合并后的数值计算）
        pass_rate_with_test = data['pass_count_with_test'] / data['total_count_with_test'] if data['total_count_with_test'] > 0 else 0
        pass_rate_without_test = data['pass_count_without_test'] / data['total_count_without_test'] if data['total_count_without_test'] > 0 else 0
        
        # 显示名称：去掉 test- 前缀
        display_source = source.replace('test-', '') if source.startswith('test-') else source
        
        detailed_data.append({
            'Source': display_source,
            'Pass Rate (with test)': pass_rate_with_test,
            'Pass count (with test)': data['pass_count_with_test'],
            'Total count (with test)': data['total_count_with_test'],
            'Pass Rate (without test)': pass_rate_without_test,
            'Pass count (without test)': data['pass_count_without_test'],
            'Total count (without test)': data['total_count_without_test']
        })

    # 计算 Overall（原有逻辑保持不变）
    all_missing_rates = missing_count_all / total_funcs_all if total_funcs_all > 0 else 0
    all_missing_rates_func = missing_filtered_count_all / total_filtered_funcs_all if total_filtered_funcs_all > 0 else 0

    detailed_data.append({
        'Source': 'Overall',
        'Pass Rate (with test)': 1 - all_missing_rates,
        'Pass count (with test)': total_funcs_all - missing_count_all,
        'Total count (with test)': total_funcs_all,
        'Pass Rate (without test)': 1 - all_missing_rates_func,
        'Pass count (without test)': total_filtered_funcs_all - missing_filtered_count_all,
        'Total count (without test)': total_filtered_funcs_all
    })

    # 保存 CSV 文件
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

    # 打印输出
    print("Compile pass rate statistics have been saved to compile_pass_rate.csv file")
    print("\nPass rates (with test):")
    for row in detailed_data[:-1]:  # 排除 Overall
        print(f"{row['Source']}: {row['Pass Rate (with test)']:.2%}")

    print("\nPass rates for functions (without test):")
    for row in detailed_data[:-1]:  # 排除 Overall
        print(f"{row['Source']}: {row['Pass Rate (without test)']:.2%}")

    print(f"\nOverall pass rate (with test): {1 - all_missing_rates:.2%}")
    print(f"Overall pass rate for functions (without test): {1 - all_missing_rates_func:.2%}")

def calculate_retry_pass_rates(output_dir,results,include_dict,once_retry_count_dict,test_names):
    once_pass_rate = {}
    once_pass_counts = {}
    for test_source_name, child_sources in tqdm(include_dict.items()):
        if not is_test_name_valid(test_source_name, test_names) or test_source_name not in once_retry_count_dict:
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

    print("Once compile pass rate statistics have been saved to once_pass_rates.csv file")
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
    total_func_count = 0
    all_fn_lens = []
    source_data = {}

    for test_source_name, funcs in tqdm(sorted_funcs_depth.items()):
        if not is_test_name_valid(test_source_name, results.keys()):
            continue
        data_manager.get_include_indices(test_source_name)
        
        total_loc = 0
        loc = 0
        rust_loc = 0
        fn_lens = []

        # 处理函数部分
        for func in funcs:
            func_content, _, _ = data_manager.get_content(func)
            fn_len = len(func_content.split('\n'))
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
        
        source_data[test_source_name] = {
            'LOC': loc,
            'Total LOC': total_loc,
            'Rust LOC': rust_loc,
            'Func Count': func_count,
            'Max Fn Len': max_fn,
            'Mean Fn Len': mean_fn,
            'fn_lens': fn_lens
        }

    # 合并 uncovered 数据
    merged_data = {}
    for source, data in source_data.items():
        display_source = source
        if source.startswith('test-uncovered_'):
            display_source = source.replace('test-uncovered_', '')
        elif source.startswith('test-'):
            display_source = source.replace('test-', '')
        
        if display_source in merged_data:
            # 合并数据
            merged_data[display_source]['LOC'] += data['LOC']
            merged_data[display_source]['Total LOC'] += data['Total LOC']
            merged_data[display_source]['Rust LOC'] += data['Rust LOC']
            merged_data[display_source]['Func Count'] += data['Func Count']
            merged_data[display_source]['Max Fn Len'] = max(merged_data[display_source]['Max Fn Len'], data['Max Fn Len'])
            merged_data[display_source]['fn_lens'].extend(data['fn_lens'])
            # 重新计算平均值
            all_lens = merged_data[display_source]['fn_lens']
            merged_data[display_source]['Mean Fn Len'] = sum(all_lens) / len(all_lens) if all_lens else 0
        else:
            merged_data[display_source] = data.copy()

    # 生成详细数据
    for source, data in merged_data.items():
        lcov = data['LOC'] / data['Total LOC'] if data['Total LOC'] else 0
        detailed_data.append({
            'Source': source,
            'LOC': data['LOC'],
            'Total LOC': data['Total LOC'],
            'LCov': lcov,
            'Rust LOC': data['Rust LOC'],
            'Func Count': data['Func Count'],
            'Max Fn Len': data['Max Fn Len'],
            'Mean Fn Len': data['Mean Fn Len']
        })
        
        # 累计全局数据
        total_func_count += data['Func Count']
        all_fn_lens.extend(data['fn_lens'])
        total_loc_all += data['Total LOC']
        loc_all += data['LOC']
        rust_loc_all += data['Rust LOC']

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
    print("\nDataset statistics:")
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
            row_copy = row.copy()
            row_copy['LCov'] = f"{row['LCov']:.1%}"
            row_copy['Mean Fn Len'] = f"{row['Mean Fn Len']:.1f}"
            writer.writerow(row_copy)

    print(f"\nFull statistics have been saved to: {csv_path}")
    return total_loc_all


def merge_results(output_dir):
    import os
    import pandas as pd

    def clean_source_col(df):
        df['Source'] = df['Source'].astype(str).str.replace(r'^test-', '', regex=True)
        return df

    # 拼接各文件路径
    tests_path = os.path.join(output_dir, 'tests_pass_rates.csv')
    compile_path = os.path.join(output_dir, 'compile_pass_rate.csv')
    loc_path = os.path.join(output_dir, 'loc_statistics.csv')
    safety_path = os.path.join(output_dir, 'safety.csv')
    output_path = os.path.join(output_dir, 'test_project', 'metrics.csv')

    # 读取csv并处理Source列
    tests = clean_source_col(pd.read_csv(tests_path))
    compile = clean_source_col(pd.read_csv(compile_path))
    loc = clean_source_col(pd.read_csv(loc_path))
    safety = clean_source_col(pd.read_csv(safety_path))

    # 合并
    df = loc[['Source', 'Total LOC', 'Func Count']].merge(
        compile[['Source', 'Pass Rate (without test)','Total count (with test)', 'Total count (without test)']],
        on='Source', how='left'
    ).merge(
        tests[['Source', 'Pass Count']],
        on='Source', how='left'
    ).merge(
        safety[['Source', 'Safe Loc', 'Safe Ref']],
        on='Source', how='left'
    )

    # 计算 Passed 列
    def calc_passed(row):
        denom = row['Total count (with test)'] - row['Total count (without test)']
        if (
            pd.notnull(row['Pass Count'])
            and pd.notnull(row['Total count (with test)'])
            and pd.notnull(row['Total count (without test)'])
            and denom != 0
        ):
            val = row['Pass Count'] / denom
            return f"{val:.2%}"
        else:
            return None

    df['Passed'] = df.apply(calc_passed, axis=1)

    # 重命名列
    df = df.rename(columns={
        'Total LOC': 'Loc',
        'Func Count': 'Fns',
        'Pass Rate (without test)': 'Compiled',
    })

    # 删除所有关键列都为空的行
    df = df.dropna(subset=['Compiled','Passed', 'Safe Loc', 'Safe Ref'], how='all')

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 保存结果
    df[['Source', 'Loc', 'Fns','Compiled', 'Passed', 'Safe Loc', 'Safe Ref']].to_csv(output_path, index=False)

    print(f"overall metrics have been saved to: {output_path}")