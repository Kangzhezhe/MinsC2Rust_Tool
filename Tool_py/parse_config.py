import configparser
import os
import shutil
import sys

def read_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


config_path = sys.argv[1]
cfg = read_config(config_path)
qwen_api_key = cfg['LLM_API_Keys']['qwen']
zhipu_api_key = cfg['LLM_API_Keys']['zhipu']
deepseek_api_key = cfg['LLM_API_Keys']['deepseek']

os.environ["QWEN_API_KEY"] = qwen_api_key
os.environ["ZHIPU_API_KEY"] = zhipu_api_key
os.environ["DEEPSEEK_API_KEY"] = deepseek_api_key



def setup_project_directories(config):
    tmp_dir = config['Paths']['tmp_dir']
    output_dir = config['Paths']['output_dir']
    output_project_name = config['Paths']['output_project_name']
    compile_commands_path = config['Paths']['compile_commands_path']


    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    output_project_path = os.path.join(output_dir, output_project_name)
    os.makedirs(os.path.join(output_project_path, 'src'), exist_ok=True)
    os.makedirs(os.path.join(output_project_path, 'tests'), exist_ok=True)

    def copy_if_not_exists(src, dst):
        if not os.path.exists(dst):
            shutil.copy(src, dst)

    copy_if_not_exists("../test_project/Cargo.toml", os.path.join(output_project_path, "Cargo.toml"))
    copy_if_not_exists("../test_project/Cargo.lock", os.path.join(output_project_path, "Cargo.lock"))

    params = {key: config.getint('Params', key) for key in config['Params']}
    excluded_files = config['ExcludeFiles']['files'].split(', ')


    enable_english_prompt = config.getboolean('Settings', 'enable_english_prompt')
    enable_multi_models = config.getboolean('Settings', 'enable_multi_models')
    params['enable_english_prompt'] = enable_english_prompt
    params['enable_multi_models'] = enable_multi_models


    return tmp_dir, output_dir, output_project_path ,compile_commands_path ,params,excluded_files
