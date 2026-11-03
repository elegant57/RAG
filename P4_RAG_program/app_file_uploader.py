"""
基于Streamlit 完成 WEB 网页上传服务
Streamlit: 当 WEB 页面元素发生变化，则代码重新执行一遍 -> 状态丢失
"""

import streamlit as st
from knowledge_base import KnowledgeBaseService
import time

# 添加网页标题
st.title('知识库更新服务')

# file_uploader
uploader_file = st.file_uploader(
    '请上传TXT文件',
    type=['txt'],
    accept_multiple_files=False,       # False表示仅接受一个文件的上传
)

if "servuce" not in st.session_state:
    st.session_state['service'] = KnowledgeBaseService()

if uploader_file is not None:
    file_name = uploader_file.name
    file_size = uploader_file.size / 1024
    file_type = uploader_file.type

    st.subheader(f'文件名：{file_name}')
    st.write(f'格式：{file_type} | 大小：{file_size:.2f} KB')

    # getvalue -> bytes -> decode('utf-8')
    text = uploader_file.getvalue().decode('utf-8')
    # st.write(text)
    with st.spinner("载入知识库中..."):     # 在 spinner 内的代码执行过程中，会有一个转圈动画 
        time.sleep(1)
        st.write(st.session_state['service'].uploader_by_str(text, file_name))
