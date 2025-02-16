import streamlit as st
import pandas as pd
import os

# 定义表文件夹路径
table_folder = 'C:/Users/user/Desktop/streamlit1.27/Table'

def list_csv_files(startpath):
    """列出给定路径下所有的CSV文件"""
    csv_files = []
    for root, dirs, files in os.walk(startpath):
        for file in files:
            if file.endswith('.csv'):
                # 构造相对路径
                relative_path = os.path.relpath(os.path.join(root, file), startpath)
                csv_files.append(relative_path)
    return csv_files


# 检查文件夹是否存在
if not os.path.exists(table_folder):
    st.error(f"'{table_folder}'文件夹不存在。")
else:
    # 获取文件列表，包括子文件夹中的CSV文件
    csv_files = list_csv_files(table_folder)

    # 如果文件夹为空或没有CSV文件
    if not csv_files:
        st.warning("该文件为空。")
    else:
        # 在侧边栏添加一个标题
        st.sidebar.header("结果表格")

        # 创建一个选择框，让用户选择CSV文件
        selected_file = st.sidebar.selectbox('请选择文件', csv_files)

        # 当用户选择了文件后，显示文件内容作为表格
        if selected_file:
            file_path = os.path.join(table_folder, selected_file)
            file_name = os.path.splitext(selected_file)[0]
            try:
                df = pd.read_csv(file_path)
                st.write(f"### {file_name}:")
                st.dataframe(df)  # 使用st.dataframe()来显示DataFrame
            except Exception as e:
                st.error(f"Error reading the file: {e}")