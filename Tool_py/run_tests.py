import re
import subprocess

# 解析测试输出
def parse_test_output(output):
    passed_tests = []
    failed_tests = []
    total_passed = 0
    total_failed = 0

    # 匹配测试结果
    test_result_pattern = re.compile(r'test (\S+) \.\.\. (ok|FAILED)')
    overall_result_pattern = re.compile(r'test result: (ok|FAILED)\. (\d+) passed; (\d+) failed;')

    for line in output.split('\n'):
        result_match = test_result_pattern.search(line)
        if result_match:
            test_name, result = result_match.groups()
            if result == 'ok':
                passed_tests.append(test_name)
                total_passed += 1
            else:
                failed_tests.append(test_name)
                total_failed += 1

        overall_result_match = overall_result_pattern.search(line)
        if overall_result_match:
            overall_result, passed, failed = overall_result_match.groups()
            total_passed += int(passed)
            total_failed += int(failed)

    return passed_tests, failed_tests, total_passed, total_failed

# 计算通过率和错误率
def calculate_rates(total_passed, total_failed):
    overall_pass_rate = total_passed / (total_passed + total_failed) if (total_passed + total_failed) > 0 else 0
    overall_fail_rate = total_failed / (total_passed + total_failed) if (total_passed + total_failed) > 0 else 0
    return overall_pass_rate, overall_fail_rate

def run_tests_and_calculate_rates(output_project_path):
    test_output = subprocess.run(f"cd {output_project_path} && cargo test --no-fail-fast", shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
    print(test_output)

    # 解析测试输出
    passed_tests, failed_tests, total_passed, total_failed = parse_test_output(test_output)

    # 调试信息
    # print("Passed Tests:", passed_tests)
    # print("Failed Tests:", failed_tests)
    # print("Total Passed:", total_passed)
    # print("Total Failed:", total_failed)

    # 计算通过率和错误率
    overall_pass_rate, overall_fail_rate = calculate_rates(total_passed, total_failed)

    # # 打印结果
    # print(f"\nOverall pass rate: {overall_pass_rate:.2%}")
    # print(f"Overall fail rate: {overall_fail_rate:.2%}")

    return passed_tests, failed_tests,overall_pass_rate, overall_fail_rate

if __name__ == "__main__":
    run_tests_and_calculate_rates()