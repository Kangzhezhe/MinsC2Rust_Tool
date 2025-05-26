import re
import os
import sys
import csv

def calculate_combined_metrics(file_path):
    """
    同时计算安全行比例和引用安全比例
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        code_lines = f.readlines()

    # 预处理：移除注释和字符串内容
    cleaned_lines = []
    for line in code_lines:
        line = re.sub(r'//.*|/\*.*?\*/', '', line)  # 移除行内注释
        line = re.sub(r'"(?:\\"|.)*?"', '""', line)  # 替换双引号字符串
        line = re.sub(r"'(?:\\'|.)*?'", "''", line)  # 替换单引号字符
        cleaned_lines.append(line.strip())

    # 初始化统计变量
    total_lines = 0
    unsafe_line_count = 0
    pending_unsafe = False  # 检测到unsafe但尚未找到{
    unsafe_scope_depth = 0  # 当前unsafe作用域的嵌套深度
    safe_refs = 0
    unsafe_refs = 0

    # 正则表达式模式
    ref_patterns = {
        'safe': re.compile(r'''
            &(?!mut\b)\w+       # 不可变引用 (&T)
            |&\s*mut\s+\w+      # 可变引用 (&mut T)
            |\b(?:Cell|RefCell|String|str|Vec|Box)\b  # 智能指针类型
        ''', re.VERBOSE),
        'unsafe': re.compile(r'\*\w+|\b\*(?:const|mut)\b')
    }

    for line in cleaned_lines:
        if not line:
            continue

        total_lines += 1

        # ===== 安全行统计 =====
        # 检测新的unsafe关键字（仅在非作用域中触发）
        if re.search(r'\bunsafe\b', line) and not pending_unsafe and unsafe_scope_depth == 0:
            pending_unsafe = True

        # 逐字符分析作用域变化
        for char in line:
            if char == '{':
                if pending_unsafe:  # 触发unsafe作用域开始
                    unsafe_scope_depth = 1
                    pending_unsafe = False
                elif unsafe_scope_depth > 0:  # 嵌套作用域
                    unsafe_scope_depth += 1
            elif char == '}' and unsafe_scope_depth > 0:
                unsafe_scope_depth -= 1

        # 统计不安全行
        if unsafe_scope_depth > 0:
            unsafe_line_count += 1

        # ===== 引用统计 =====
        safe_refs += len(ref_patterns['safe'].findall(line))
        unsafe_refs += len(ref_patterns['unsafe'].findall(line))

    # 计算指标
    safe_line_ratio = 1 - (unsafe_line_count / total_lines) if total_lines else 0
    total_refs = safe_refs + unsafe_refs
    ref_ratio = safe_refs / total_refs if total_refs else 0

    return {
        'safe_line_ratio': round(safe_line_ratio, 4),
        'ref_ratio': round(ref_ratio, 4),
        'total_lines': total_lines,
        'unsafe_lines': unsafe_line_count,
        'safe_refs': safe_refs,
        'unsafe_refs': unsafe_refs
    }

def process_directory(directory):
    """
    处理目录下所有.rs文件并汇总统计，返回每个文件的结果列表
    """
    results = []
    total_metrics = {
        'total_lines': 0,
        'unsafe_lines': 0,
        'safe_refs': 0,
        'unsafe_refs': 0
    }

    for root, _, files in os.walk(directory):
        for filename in files:
            if not filename.endswith('.rs'):
                continue

            filepath = os.path.join(root, filename)
            try:
                metrics = calculate_combined_metrics(filepath)
            except Exception as e:
                print(f"处理文件 {filepath} 出错: {str(e)}")
                continue

            results.append({
                'Source': os.path.splitext(os.path.basename(filepath))[0],
                'Safe Loc': f"{metrics['safe_line_ratio']:.2%}",
                'Safe Ref': f"{metrics['ref_ratio']:.2%}"
            })

            total_metrics['total_lines'] += metrics['total_lines']
            total_metrics['unsafe_lines'] += metrics['unsafe_lines']
            total_metrics['safe_refs'] += metrics['safe_refs']
            total_metrics['unsafe_refs'] += metrics['unsafe_refs']

    # 汇总
    safe_line_ratio = 1 - (total_metrics['unsafe_lines'] / total_metrics['total_lines']) if total_metrics['total_lines'] else 0
    total_refs = total_metrics['safe_refs'] + total_metrics['unsafe_refs']
    ref_ratio = total_metrics['safe_refs'] / total_refs if total_refs else 0
    results.append({
        'Source': 'Overall',
        'Safe Loc': f"{safe_line_ratio:.2%}",
        'Safe Ref': f"{ref_ratio:.2%}"
    })
    return results

def process_csv_rows(rows):
    """
    对 rows 进行 hash-functions 和 compare-functions 的合并与平均
    """
    hash_functions_rows = []
    compare_functions_rows = []
    filtered_rows = []

    for row in rows:
        filename = row['Source']
        if filename == 'lib':
            continue  # 删除 'lib' 行
        elif filename in ['hash_pointer', 'hash_int', 'hash_string']:
            hash_functions_rows.append(row)
        elif filename in ['compare_int', 'compare_string', 'compare_pointer']:
            compare_functions_rows.append(row)
        else:
            # 替换文件名中的 '_' 为 '-'
            row['Source'] = filename.replace('_', '-')
            filtered_rows.append(row)

    # 计算 hash-functions 的平均值
    if hash_functions_rows:
        avg_safe_line_ratio = sum(float(row['Safe Loc'].strip('%')) for row in hash_functions_rows) / len(hash_functions_rows)
        avg_ref_safety_ratio = sum(float(row['Safe Ref'].strip('%')) for row in hash_functions_rows) / len(hash_functions_rows)
        filtered_rows.append({
            'Source': 'hash-functions',
            'Safe Loc': f"{avg_safe_line_ratio:.2f}%",
            'Safe Ref': f"{avg_ref_safety_ratio:.2f}%"
        })

    # 计算 compare-functions 的平均值
    if compare_functions_rows:
        avg_safe_line_ratio = sum(float(row['Safe Loc'].strip('%')) for row in compare_functions_rows) / len(compare_functions_rows)
        avg_ref_safety_ratio = sum(float(row['Safe Ref'].strip('%')) for row in compare_functions_rows) / len(compare_functions_rows)
        filtered_rows.append({
            'Source': 'compare-functions',
            'Safe Loc': f"{avg_safe_line_ratio:.2f}%",
            'Safe Ref': f"{avg_ref_safety_ratio:.2f}%"
        })

    return filtered_rows

def write_csv(rows, output_csv):
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Source', 'Safe Loc', 'Safe Ref']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def calculate_safety_metrics(input_path, output_csv):
    rows = []
    if os.path.isfile(input_path):
        metrics = calculate_combined_metrics(input_path)
        rows.append({
            'Source': os.path.splitext(os.path.basename(input_path))[0],
            'Safe Loc': f"{metrics['safe_line_ratio']:.2%}",
            'Safe Ref': f"{metrics['ref_ratio']:.2%}"
        })
    elif os.path.isdir(input_path):
        rows = process_directory(input_path)
    elif input_path.endswith('.csv'):
        # 直接处理已有csv
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                rows.append(row)
    else:
        print(f"无效路径: {input_path}")
        sys.exit(1)

    # 合并 hash-functions 和 compare-functions
    rows = process_csv_rows(rows)
    write_csv(rows, output_csv)
    return rows

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_unsafe.py <file_or_directory> <output_csv>")
        sys.exit(1)
    calculate_safety_metrics(sys.argv[1], sys.argv[2])