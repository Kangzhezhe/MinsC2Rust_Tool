import streamlit as st
import os

# 定义输入文件夹路径
input_folder = 'C:/Users/user/Desktop/streamlit1.27/Input'

# 检查文件夹是否存在
if not os.path.exists(input_folder):
    st.error(f"'{input_folder}' 文件夹不存在。")
else:
    # 在侧边栏添加一个标题
    st.sidebar.header("C工程")

    # 创建一个空字典来存储文件夹的状态（是否展开）
    folder_state = {}

    # 初始化session state中的selected_file为空字符串
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = ''

    # 定义一个递归函数来显示文件树
    def display_file_tree(path, prefix=''):
        # 获取当前路径下的文件和文件夹
        items = sorted(os.listdir(path))  # 对文件和文件夹进行排序
        for i, item in enumerate(items):
            # 构造完整的路径
            full_path = os.path.join(path, item)
            # 判断是文件还是文件夹
            if os.path.isdir(full_path):
                # 如果是文件夹，添加一个可折叠的部分
                is_last_item = i == len(items) - 1
                child_prefix = '    ' if not is_last_item else ''
                # 检查文件夹状态，如果未设置，默认为关闭
                if full_path not in folder_state:
                    folder_state[full_path] = False
                # 添加一个可点击的文件夹名，用于切换展开/关闭状态
                folder_state[full_path] = st.sidebar.checkbox(item, value=folder_state[full_path], key=full_path)
                if folder_state[full_path]:
                    # 如果文件夹是展开的，递归显示其内容
                    display_file_tree(full_path, child_prefix)
            else:
                # 如果是文件，添加一个可点击的文件名
                if st.sidebar.button(item, key=full_path):
                    # 当文件被点击时，更新session state中的selected_file
                    st.session_state.selected_file = full_path

    # 从根文件夹开始显示文件树
    display_file_tree(input_folder)

    # 根据session state中的selected_file显示文件内容
    if st.session_state.selected_file:
        selected_file = st.session_state.selected_file
        st.write(f"### {os.path.basename(selected_file)}:")
        try:
            with open(selected_file, 'r', encoding='utf-8') as file:
                content = file.read()
                st.code(content, language='c')  # 使用st.code()高亮显示C语言代码
        except Exception as e:
            st.error(f"无法读取文件 '{selected_file}': {e}")