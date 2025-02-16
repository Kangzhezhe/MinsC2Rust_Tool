import pandas as pd
import streamlit as st
import os
import json

# 定义错误信息文件夹路径
error_info_folder = 'C:/Users/user/Desktop/streamlit1.27/ErrorInfo'

def list_json_files(startpath):
    """列出给定路径下所有的JSON文件"""
    json_files = []
    for root, dirs, files in os.walk(startpath):
        for file in files:
            if file.endswith('.json'):
                # 构造相对路径
                relative_path = os.path.relpath(os.path.join(root, file), startpath)
                json_files.append(relative_path)
    return json_files

# 检查文件夹是否存在
if not os.path.exists(error_info_folder):
    st.error(f"The folder '{error_info_folder}' does not exist.")
else:
    # 获取文件列表，包括子文件夹中的JSON文件
    json_files = list_json_files(error_info_folder)

    # 如果文件夹为空或没有JSON文件
    if not json_files:
        st.warning("The 'ErrorInfo' folder is empty or contains no JSON files.")
    else:
        # 在侧边栏添加一个标题
        st.sidebar.header("报错信息")

        # 创建一个选择框，让用户选择JSON文件
        selected_file = st.sidebar.selectbox('请选择文件', json_files)

        # 当用户选择了文件后，显示文件内容
        if selected_file:
            file_path = os.path.join(error_info_folder, selected_file)
            file_name = os.path.splitext(selected_file)[0]
            try:
                with open(file_path, 'r', encoding='utf-8') as file:  # 指定UTF-8编码
                    data = json.load(file)

                st.write(f"### {file_name}:")


                def display_value(key, value):
                    """根据值的内容类型选择合适的显示方式，并默认折叠"""
                    rust_keywords = ['fn', 'struct', 'enum', 'impl', 'trait', 'mod', 'use', 'extern', 'pub', 'const',
                                     'static', 'let', 'if', 'else', 'loop', 'while', 'for', 'match', 'unsafe', 'async',
                                     'await', 'dyn']

                    with st.expander(f"点击查看 {key} 的详细信息："):  # 使用 expander 默认折叠内容
                        if isinstance(value, str) and (
                                '\n' in value or any(keyword in value for keyword in rust_keywords)):
                            # 假设包含这些关键词的字符串可能是Rust代码
                            st.code(value, language='rust')  # 指定为Rust代码
                        elif isinstance(value, (dict, list)):
                            st.json(value)
                        else:
                            st.write(value)


                # 根据JSON数据结构选择合适的展示方式
                if isinstance(data, dict):
                    for key, value in data.items():
                        st.markdown(f"**{key}:**")
                        display_value(key, value)
                elif isinstance(data, list):
                    if all(isinstance(item, dict) for item in data):
                        df = pd.DataFrame(data)
                        st.dataframe(df)
                    else:
                        for index, item in enumerate(data, start=1):
                            st.markdown(f"**Item {index}:**")
                            display_value(f"Item {index}", item)
                else:
                    st.write(data)

            except UnicodeDecodeError as e:
                st.error(f"Error reading the file with UTF-8 encoding. Try another encoding. Error: {e}")
            except Exception as e:
                st.error(f"Error reading the file: {e}")