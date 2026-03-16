import streamlit as st
import pandas as pd
import re
from knowledge_manager import KnowledgeManager, MockDB

# --- 全局状态初始化 ---
if "kq_manager" not in st.session_state:
    db = MockDB()
    config = db.get_institution_config()
    st.session_state.kq_manager = KnowledgeManager(institution_name=config["name"])
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

# --- 业务逻辑重写 (接入 KnowledgeManager) ---

def page_file_upload():
    st.header("📂 教学资料上传 (隐私管控版)")
    st.info("系统在解析文档后，会自动通过本地“隐私拦截器”进行脱敏，确保敏感数据不离境。")
    
    show_interception = st.session_state.get("show_interception", False)
    
    uploaded_file = st.file_uploader("选择 PDF 教学素材", type=["pdf"])
    if uploaded_file:
        if st.button("开始 AI 安全解析"):
            with st.spinner("解析并拦截敏感信息中..."):
                file_bytes = uploaded_file.read()
                processed_chunks = st.session_state.kq_manager.process_pdf(file_bytes)
                
                st.success(f"解析完成！共切分为 {len(processed_chunks)} 个安全片段并存入本地知识库。")
                
                if show_interception:
                    st.subheader("🛡️ 隐私脱敏过程监控 (演示模式)")
                    for i, chunk in enumerate(processed_chunks[:5]): # 仅展示前5个
                        if chunk["logs"]:
                            with st.expander(f"片段 #{i+1} 脱敏详情"):
                                st.text(f"原始文本推测: {chunk['original'][:100]}...")
                                st.json(chunk["logs"])
                                st.info(f"脱敏后文本: {chunk['content'][:100]}...")

def page_lesson_plan():
    st.header("📝 教案自动生成")
    st.write("基于**已脱敏**的本地知识库内容，安全生成教案大纲。")
    
    topic = st.text_input("请输入教学主题", placeholder="例如：中医基础理论 - 阴阳学说")
    if st.button("生成安全教案"):
        with st.spinner("正在安全检索本地知识库..."):
            # 接入 RAG 检索
            context = st.session_state.kq_manager.search(topic)
            if not context:
                st.warning("本地知识库中未找到相关内容，请先上传资料。")
            else:
                st.markdown("### 依据安全上下文生成的大纲")
                st.markdown("---")
                for i, c in enumerate(context):
                    with st.chat_message("assistant"):
                        st.markdown(f"**参考片段 {i+1}**: {c}")
                
                st.markdown("---")
                st.success("教案大纲已准备就绪。")

def page_ai_qa():
    st.header("💬 AI 教学助手 (RAG 安全增强)")
    st.write("您的提问将经过本地检索，仅将脱敏后的上下文发送给大模型。")
    
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
            # RAG 逻辑
            context = st.session_state.kq_manager.search(prompt)
            if context:
                aug_prompt = f"背景信息：{ ' '.join(context) }\n\n问题：{prompt}"
                response = f"根据您的文档，我发现：{context[0][:150]}... (这是基于脱敏上下文的回复)"
            else:
                response = "抱歉，由于未能在本地知识库中找到脱敏后的参考信息，我无法回答该问题（确保红线安全）。"
            
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
    # 体感优化：脱敏过程演示开关
    show_interception = st.sidebar.toggle("🔬 显示脱敏过程 (演示用)", value=True)
    st.session_state.show_interception = show_interception
    
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
