from clang_callgraph import get_c_functions_name
from AST_test import content_extract
import sys,os
import configparser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from func_result import output_process_re
from parse_config import read_config
from merge_c_h import process_files

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python makejson.py <config_path>")
        sys.exit(1)
    config_path = sys.argv[1]

    cfg = read_config(config_path)
    src_dir = cfg['Paths']['src_dir']
    test_dir = cfg['Paths']['test_dir']
    func_result_dir = cfg['Paths']['func_result_dir']
    tmp_dir = cfg['Paths']['tmp_dir']
    compile_commands_path = cfg['Paths']['compile_commands_path']

    process_files(compile_commands_path, tmp_dir)

    # 获取函数名称
    get_c_functions_name(src_dir, # 函数内容
                         os.path.join(func_result_dir,'new_src.json'), # 函数名称保存
                         compile_commands_path) # 编译命令路径

    # 函数名正则化
    output_process_re.process_file_func_name(os.path.join(func_result_dir,'new_src.json'), # 未处理json格式
                                             os.path.join(func_result_dir,'new_src_processed.json')) # 正则化处理后文件路径

    # 函数内容分割到json
    content_extract(os.path.join(func_result_dir,'new_src_processed.json'), # 函数名称
                    os.path.join(tmp_dir,"src"), # 函数内容
                    os.path.join(tmp_dir,"src_json"))   # 函数分割保存

    # 获取函数名称
    get_c_functions_name(test_dir, # 函数内容
                         os.path.join(func_result_dir,"new_test.json"), # 函数名称保存
                         compile_commands_path)
    # 函数名正则化
    output_process_re.process_file_func_name(os.path.join(func_result_dir,"new_test.json"), # 未处理json格式
                                             os.path.join(func_result_dir,"new_test_processed.json")) # 正则化处理后文件路径

    # 函数内容分割到json
    content_extract(os.path.join(func_result_dir,"new_test_processed.json"), # 函数名称
                    os.path.join(tmp_dir,"test"), # 函数内容
                    os.path.join(tmp_dir,"test_json"))   # 函数分割保存