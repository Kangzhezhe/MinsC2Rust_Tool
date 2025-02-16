import streamlit as st

VERSION = "2.0"

st.set_page_config(
    page_title=f"MinsC2Rust",
    page_icon=':memo:',
    initial_sidebar_state="expanded",
    layout="wide",
)

intro = f"""
* 团队：MINS 小分队，电子信息与通信学院，华中科技大学\n
* 成员：朱前宇、康哲豪、牟文睿、王祯华\n
* 指导老师：王邦、张小刚\n
* 联系方式：qianyuzhu@hust.edu.cn
"""

release_notes = f"""
在系统编程领域，Rust 因其安全性、性能以及现代语言特性，正逐渐成为替代 C/C++
的热门选择。然而，由于 C/C++ 拥有庞大的存量代码基础，将其完全重写为 Rust 是一
项艰巨的任务。虽然大型语言模型显示出自动化翻译的前景，与基于规则的方法相比能够生
成更自然、更安全的代码，但仍然存在语言差异大、上下文窗口限制、代码存在依赖、编译
错误、工程架构维持等问题。
\n为此，本项目团队提出了一种基于大型语言模型（LLM）的自动化代码转换工具——
MinsC2Rust。该工具通过基于函数转译关系的方案编排、基于函数完整性的代码分割与合
并、基于编译反馈的函数迭代转译策略以及函数去重优化与工程整体结构重构等技术手段，
有效解决了 C 到 Rust 代码转换中的语言差异、上下文窗口限制、代码依赖、编译错误和
性能问题。测试工程结果显示，MinsC2Rust 能够显著提高代码转换的准确性和效率，在给
定的工程文件中，总编译成功率为95.48%，测试函数正确执行率为52.76%，静态断言转译率
为72.50%，动态断言转译率为16.62%，总运行时间为：3h28min40s，为促进 Rust 生态
的发展提供了有力支持。
"""
# End release updates

def draw_main_page():

    st.title(f"欢迎来到MinsC2Rust {VERSION}! :wave:", anchor=False)

    st.caption(intro)

    st.write(release_notes)

draw_main_page()