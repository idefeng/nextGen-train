import streamlit as st
import pandas as pd
import re

# --- 配置与样式 ---
st.set_page_config(
    page_title="nextGenTrain MVP",
    page_icon="🎓",
    layout="wide",
)

# 自定义 CSS 提升视觉效果 (Vibe Coding: Premium Aesthetics)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stSidebar {
        background-color: #ffffff;
    }
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 隐私规范接口 (Privacy Protection) ---
def mask_sensitive_info(text: str) -> str:
    """
    识别并脱敏敏感信息。在 UI 展示前必须通过此接口。
    简单实现：屏蔽常见姓名、手机号等演示点。
    """
    if not isinstance(text, str):
        return text
    
    # 脱敏手机号 (示例)
    text = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', text)
    
    # 模拟姓名脱敏 (这是一个简单的关键词替换示例)
    sensitive_keywords = ["张三", "李四", "王五"]
    for keyword in sensitive_keywords:
        if keyword in text:
            masked = keyword[0] + "*" * (len(keyword) - 1)
            text = text.replace(keyword, masked)
            
    return text

# --- Mock 数据层 (Data Layer) ---
class MockDB:
    @staticmethod
    def get_institution_config():
        """模拟从 PostgreSQL 读取机构配置"""
        return {
            "name": "博学教育培训中心",
            "admin_contact": "张三 (13812345678)",
            "license_id": "EDU-2026-MOCK-001",
            "region": "华东地区",
            "status": "Active"
        }

# --- 页面逻辑 ---

def page_file_upload():
    st.header("📂 教学资料上传")
    st.info("请上传 PDF、Word 或 PPT 格式的教学素材，系统将自动解析知识点。")
    uploaded_file = st.file_uploader("选择文件", type=["pdf", "docx", "pptx"])
    if uploaded_file:
        st.success(f"成功接收文件: {uploaded_file.name}")
        st.button("开始 AI 解析")

def page_lesson_plan():
    st.header("📝 教案自动生成")
    st.write("基于知识库内容，快速生成符合教学大纲的教案。")
    
    topic = st.text_input("请输入教学主题", placeholder="例如：中医基础理论 - 阴阳学说")
    if st.button("生成教案大纲"):
        with st.spinner("正在检索知识库并生成大纲..."):
            # 模拟生成逻辑
            st.markdown("### 课程大纲 (草稿)")
            st.markdown("1. **教学目标**：掌握阴阳的基本属性及其关系。")
            st.markdown("2. **核心知识点**：对立、互根、消长、转化。")
            st.markdown("3. **教学时长**：45 分钟。")
            st.warning("注：生成的教学内容需经教研员终审（遵守内容红线原则）。")

def page_ai_qa():
    st.header("💬 AI 教学助手")
    st.write("针对教学过程中的细节，与 AI 进行深度问答。")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("有什么我可以帮您的？"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = f"这是关于 '{prompt}' 的模拟回复（内测阶段）。"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- 主导航 logic ---
def main():
    st.sidebar.title("🚀 nextGenTrain")
    st.sidebar.caption("SmartCourseEngine 重构版 MVP")
    
    # 侧边栏展示机构信息 (脱敏展示)
    db = MockDB()
    config = db.get_institution_config()
    
    st.sidebar.divider()
    st.sidebar.markdown(f"**机构名称**: {mask_sensitive_info(config['name'])}")
    st.sidebar.markdown(f"**管理员**: {mask_sensitive_info(config['admin_contact'])}")
    st.sidebar.divider()
    
    menu = {
        "文件上传": page_file_upload,
        "教案生成": page_lesson_plan,
        "AI 问答": page_ai_qa
    }
    
    selection = st.sidebar.radio("功能导航", list(menu.keys()))
    
    # 执行选中页面逻辑
    menu[selection]()

if __name__ == "__main__":
    main()
