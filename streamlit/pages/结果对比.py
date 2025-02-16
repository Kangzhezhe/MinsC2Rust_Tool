import streamlit as st
import os

# 定义输入和输出文件夹路径
input_folder = 'C:/Users/user/Desktop/streamlit1.27/Input'
output_folder = 'C:/Users/user/Desktop/streamlit1.27/Output'

# 检查文件夹是否存在
if not os.path.exists(input_folder):
    st.error(f"'{input_folder}'文件夹不存在。")
if not os.path.exists(output_folder):
    st.error(f"'{output_folder}'文件夹不存在。")

# 创建一个空字典来存储文件夹的状态（是否展开）
folder_state = {}

# 自定义CSS以优化文件树样式并确保文件树置顶
st.markdown("""
<style>
    /* 减小复选框大小 */
    .stCheckbox input[type="checkbox"] {
        transform: scale(0.6);
        margin-right: 2px;
    }

    /* 减小按钮大小并使其紧凑 */
    .stButton>button {
        padding: 1px 4px;
        font-size: 0.7em;
        margin-bottom: 1px;
        line-height: 1.1;
    }

    /* 确保 expander 标题紧凑 */
    .streamlit-expanderHeader {
        font-size: 1.0em;
        padding: 0.25rem 0.5rem;
    }

    /* 减少 expander 内容的内边距 */
    .streamlit-expanderContent {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
    }

    /* 减少元素之间的间距 */
    .stCheckbox, .stButton {
        margin-top: 0;
        margin-bottom: 0;
    }

    /* 确保复选框和按钮在同一行上紧密排列 */
    .stCheckbox label, .stButton button {
        display: block;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* 设置文件树容器的高度并添加滚动条 */
    .file-tree-container {
        max-height: 4px; /* 设置最大高度 */
        overflow-y: auto;  /* 当内容超过最大高度时添加滚动条 */
    }
</style>
""", unsafe_allow_html=True)

# 自定义CSS以调整侧边栏宽度
# st.markdown(
#     """
#     <style>
#     [data-testid="stSidebar"] {
#         min-width: 150px; // 设置最小宽度
#         max-width: 150px; // 设置最大宽度
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )


# 定义一个递归函数来显示文件树并允许选择文件
def display_file_tree(path, prefix='', side='left'):
    items = sorted(os.listdir(path))  # 排序以确保一致的显示顺序
    for i, item in enumerate(items):
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            with st.expander(item):  # 使用 expander 创建可折叠的文件夹
                display_file_tree(full_path, prefix + '--', side)  # 递归调用
        else:
            file_prefix = prefix + item if i == len(items) - 1 else prefix + item
            unique_key = f"{side}_{full_path}"
            if st.button(file_prefix, key=unique_key):
                with open(full_path, 'r') as file:
                    content = file.read()
                if side == 'left':
                    st.session_state['input_file'] = (full_path, content)
                else:
                    st.session_state['output_file'] = (full_path, content)


# 创建四栏布局
col1, col2, col3, col4 = st.columns([1.4, 4, 1.4, 4])

with col1:
    st.write("### C工程")
    with st.container():
        st.markdown('<div class="file-tree-container">', unsafe_allow_html=True)
        display_file_tree(input_folder, side='left')
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    if 'input_file' in st.session_state:
        input_file_path, input_file_content = st.session_state['input_file']
        input_file_name = os.path.basename(input_file_path)
        st.write(f"### {input_file_name}:")
        st.code(input_file_content, language='c')

with col3:
    st.write("### Rust工程")
    with st.container():
        st.markdown('<div class="file-tree-container">', unsafe_allow_html=True)
        display_file_tree(output_folder, side='right')
        st.markdown('</div>', unsafe_allow_html=True)

with col4:
    if 'output_file' in st.session_state:
        output_file_path, output_file_content = st.session_state['output_file']
        output_file_name = os.path.basename(output_file_path)
        st.write(f"### {output_file_name}:")
        st.code(output_file_content, language='rust')