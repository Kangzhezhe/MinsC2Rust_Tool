import json
from clang_callgraph import get_c_functions_name
from AST_test import content_extract
import sys,os
import configparser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from func_result import output_process_re
from parse_config import read_config
from merge_c_h import process_files
import shutil

def clear_directory(directory_path):
    """清空指定目录的内容，但保留目录本身。"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)  # 如果目录不存在，则创建
    else: 
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # 删除文件或符号链接
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # 删除子目录

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python makejson.py <config_path>")
        sys.exit(1)
    config_path = sys.argv[1]

    cfg = read_config(config_path)
    src_dir = cfg['Paths'].get('src_dir','')
    test_dir = cfg['Paths'].get('test_dir','')
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

    if test_dir != '':
        # 获取函数名称
        get_c_functions_name(test_dir, # 函数内容
                            os.path.join(func_result_dir,"new_test.json"), # 函数名称保存
                            compile_commands_path,
                            is_test=True) # 编译命令路径
        # 函数名正则化
        output_process_re.process_file_func_name(os.path.join(func_result_dir,"new_test.json"), # 未处理json格式
                                                os.path.join(func_result_dir,"new_test_processed.json")) # 正则化处理后文件路径

        # 函数内容分割到json
        content_extract(os.path.join(func_result_dir,"new_test_processed.json"), # 函数名称
                        os.path.join(tmp_dir,"test"), # 函数内容
                        os.path.join(tmp_dir,"test_json"))   # 函数分割保存

    else:
        with open(os.path.join(func_result_dir,'new_src_processed.json'), 'r') as json_file:
            data_src = json.load(json_file)[0]

        contains_main = {key: value for key, value in data_src.items() if 'main' in value}
        not_contains_main = {key: value for key, value in data_src.items() if 'main' not in value}

        with open(os.path.join(func_result_dir,'new_src_processed.json'), 'w') as json_file:
            json.dump([not_contains_main], json_file, indent=4)

        with open(os.path.join(func_result_dir,'new_test_processed.json'), 'w') as json_file:
            json.dump([contains_main], json_file, indent=4)


        clear_directory(os.path.join(tmp_dir, 'src_json'))
        clear_directory(os.path.join(tmp_dir, 'test_json'))


        content_extract(os.path.join(func_result_dir,'new_src_processed.json'), # 函数名称
                    os.path.join(tmp_dir,"src"), # 函数内容
                    os.path.join(tmp_dir,"src_json"))   # 函数分割保存
        
        content_extract(os.path.join(func_result_dir,'new_test_processed.json'), # 函数名称
                    os.path.join(tmp_dir,"src"), # 函数内容
                    os.path.join(tmp_dir,"test_json"))   # 函数分割保存
