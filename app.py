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

# --- 页面逻辑 ---

# --- 业务逻辑重写 (接入 KnowledgeManager) ---

def page_file_upload():
    st.header("📂 多模态教学资料上传 (隐私管控版)")
    st.info("支持 PDF, Word, TXT, MD 及视频 (MP4, MOV) 格式。所有内容在入库前均经过本地脱敏。")
    
    show_interception = st.session_state.get("show_interception", False)
    
    # 扩展支持的文件类型
    uploaded_file = st.file_uploader("选择教学素材", type=["pdf", "docx", "txt", "md", "mp4", "mov"])
    
    if uploaded_file:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        
        # 多模态预览窗
        st.divider()
        st.subheader("👁️ 内容预览")
        if file_ext in ["mp4", "mov"]:
            st.video(uploaded_file)
            st.caption(f"🎬 视频预览: {uploaded_file.name}")
        else:
            # 预览文档内容 (前 500 字)
            preview_bytes = uploaded_file.getvalue()
            if file_ext == "pdf":
                # PDF 预览简化处理
                st.write("📄 PDF 文档已就绪，准备解析...")
            else:
                try:
                    preview_text = preview_bytes.decode("utf-8", errors="ignore")[:500]
                    st.text_area("文档预览", preview_text, height=150)
                except Exception:
                    st.write("📄 文档已收录。")

        if st.button("开始 AI 安全解析"):
            import tempfile
            import os
            
            with st.status("正在进行多模态解析...", expanded=True) as status:
                st.write(f"正在读取 {file_ext.upper()} 文件...")
                file_bytes = uploaded_file.getvalue()
                
                try:
                    if file_ext in ["mp4", "mov"]:
                        # 视频处理需要文件路径
                        with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tfile:
                            tfile.write(file_bytes)
                            temp_path = tfile.name
                        
                        st.write(f"🎞️ 正在从视频中提取音频轨道...")
                        # 获取侧边栏选择的模型精度
                        asr_model_size = st.session_state.get("asr_precision", "base")
                        
                        st.write(f"🎙️ 正在使用 {asr_model_size.upper()} 模型进行 ASR 识别 (增强模式)...")
                        # 实际调用 ASR 逻辑
                        processed_chunks = st.session_state.kq_manager.process_video(temp_path, model_size=asr_model_size)
                        os.remove(temp_path)
                        st.write("✅ 语音转文字 (ASR) 完成，已同步执行隐私拦截。")
                    elif file_ext == "docx":
                        processed_chunks = st.session_state.kq_manager.process_docx(file_bytes)
                    elif file_ext in ["txt", "md"]:
                        processed_chunks = st.session_state.kq_manager.process_text(file_bytes)
                    else:
                        processed_chunks = st.session_state.kq_manager.process_pdf(file_bytes)
                    
                    status.update(label="✅ 多模态数据安全解析完成！", state="complete", expanded=False)
                    st.success(f"解析成功！共提取 {len(processed_chunks)} 个安全片段并存入本地知识库。")
                except Exception as e:
                    status.update(label="❌ 解析失败", state="error")
                    st.error(f"解析过程中出现错误: {str(e)}")
                    processed_chunks = []

                if processed_chunks:
                    st.divider()
                    st.subheader("📝 完整解析内容预览")
                    
                    # 组合完整文本用于展示
                    full_content = "\n".join([c["content"] for c in processed_chunks])
                    st.text_area("解析/转写后的安全文本", full_content, height=250)
                    
                    if show_interception:
                        st.subheader("🛡️ 隐私脱敏过程监控 (演示模式)")
                        intercept_count = sum(len(c["logs"]) for c in processed_chunks)
                        if intercept_count > 0:
                            st.warning(f"共检测并拦截了 {intercept_count} 处敏感信息。")
                        else:
                            st.success("未在当前内容中发现敏感信息，数据 100% 安全。")
                            
                        for i, chunk in enumerate(processed_chunks):
                            if chunk["logs"]:
                                with st.expander(f"片段 #{i+1} 脱敏详情"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("**原始内容片段**")
                                        st.caption(chunk["original"])
                                    with col2:
                                        st.markdown("**脱敏后片段**")
                                        st.code(chunk["content"])
                                    st.json(chunk["logs"])

def page_lesson_plan():
    st.header("📝 教案自动生成")
    st.write("基于**已脱敏**的本地知识库内容，安全生成教案大纲。")
    
    topic = st.text_input("请输入教学主题", placeholder="例如：中医基础理论 - 阴阳学说")
    if st.button("生成安全教案"):
        with st.spinner("正在安全检索本地知识库并生成结构化教案..."):
            # 接入 RAG 检索
            context = st.session_state.kq_manager.search(topic)
            if not context:
                st.warning("本地知识库中未找到相关内容，请先上传资料。")
            else:
                # 生成教案
                plan_md = st.session_state.kq_manager.generate_lesson_plan(topic, context)
                st.markdown(plan_md)
                
                st.divider()
                st.subheader("📊 AI 预估教学质量评估 (依据《可行性报告》)")
                scores = st.session_state.kq_manager.calculate_ai_score(plan_md)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("综合预估得分", f"{scores['total']} 分", "+2.5")
                col2.metric("知识点覆盖率", f"{scores['coverage']}%")
                col3.metric("课堂体感指数", f"{scores['vibe_index']}")
                
                st.info("💡 评估算法基于“模块6：AI 教学质量评估”技术预研。")
                st.success("教案大纲及评估已准备就绪。")

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
            with st.spinner("本地检索脱敏数据中..."):
                context = st.session_state.kq_manager.search(prompt)
                if context:
                    aug_prompt = f"背景信息：{ ' '.join(context) }\n\n问题：{prompt}"
                    response = f"根据您的文档，我发现：{context[0][:150]}... (这是基于脱敏上下文的回复)"
                else:
                    response = "抱歉，由于未能在本地知识库中找到脱敏后的参考信息，我无法回答该问题（确保红线安全）。"
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def page_video_center():
    st.header("🎬 AI 视频中心 (数字人课件生成)")
    st.write("基于“模块4：AI 教学视频生成”，将教案一键转化为数字人讲课视频。")
    
    selected_plan = st.selectbox("选择要生成视频的教案", ["中医基础理论 - 阴阳学说", "AI 隐私保护准则"])
    
    if st.button("开始生成数字人课件"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for percent_complete in range(100):
            import time
            time.sleep(0.02) # 模拟处理时间
            progress_bar.progress(percent_complete + 1)
            
            if percent_complete < 30:
                status_text.text("正在合成 AI 语音...")
            elif percent_complete < 60:
                status_text.text("正在进行数字人口型对齐...")
            else:
                status_text.text("正在渲染 1080P 高清成品...")
        
        st.success("生成完成！数字人课件已准备就绪。")
        
        # 使用 placeholder 视频 URL 演示
        # 此处使用一个公开的演示视频或静态占位
        st.video("https://www.w3schools.com/html/mov_bbb.mp4")
        st.caption("演示：数字人老师正在讲解课程内容。")
        
        st.divider()
        st.markdown("#### 🛠️ 技术指标")
        st.code("""
方案: 本地部署 (MuseTalk + GPT-SoVITS)
生成时长: 15s (演示版)
口型同步率: 99.8%
        """, language="yaml")

def page_knowledge_base_browser():
    st.header("🗄️ 知识库概览 (隔离区数据)")
    st.write("展示当前已从本地多模态资料中提取并脱敏的安全知识资产。")
    
    kb = st.session_state.kq_manager.knowledge_base
    if not kb:
        st.warning("知识库当前为空，请前往“文件上传”页面添加教学素材。")
    else:
        st.metric("已收录安全片段", len(kb))
        
        for i, item in enumerate(kb):
            with st.container(border=True):
                st.markdown(f"**安全片段 #{i+1}**")
                st.text(item["content"])
                if item["logs"]:
                    st.caption(f"🛡️ 该片段包含 {len(item['logs'])} 处脱敏拦截操作")
                st.divider()

def page_term_management():
    st.header("📚 术语词库管理 (ASR 纠偏增强)")
    st.write("在此维护行业专业词汇。这些词汇将作为 ASR 解析的语义引导，强制纠正“错别字”（如：托育、婴幼儿）。")
    
    # 增加新术语
    new_term = st.text_input("添加新专业术语", placeholder="输入术语后按回车，例如：分阶段落地")
    if new_term:
        st.session_state.kq_manager.add_term(new_term)
        st.success(f"术语 '{new_term}' 已加入增强词库！")

    st.divider()
    st.subheader("当前词库内容")
    terms = st.session_state.kq_manager.terms
    
    if not terms:
        st.info("当前词库为空。")
    else:
        # 使用标签化展示
        cols = st.columns(4)
        for i, term in enumerate(terms):
            with cols[i % 4]:
                if st.button(f"🗑️ {term}", key=f"term_{i}", help="点击删除"):
                    st.session_state.kq_manager.remove_term(term)
                    st.rerun()
    
    st.divider()
    st.info("💡 提示：词库越精准，Whisper 模型在处理专有名词时的纠错能力越强。")

# --- 主导航 logic ---
def main():
    st.sidebar.title("🚀 nextGenTrain")
    st.sidebar.caption("SmartCourseEngine 重构版 MVP")
    
    # 侧边栏展示机构信息 (脱敏展示)
    db = MockDB()
    config = db.get_institution_config()
    
    st.sidebar.divider()
    # ASR 精度优化配置
    st.sidebar.subheader("⚙️ 演示配置")
    asr_precision_map = {
        "快速 (Tiny)": "tiny",
        "平衡 (Base)": "base",
        "高精度 (Small)": "small",
        "专业 (Medium)": "medium",
        "极致 (Turbo)": "turbo"
    }
    asr_selection = st.sidebar.select_slider(
        "ASR 解析精度",
        options=list(asr_precision_map.keys()),
        value="平衡 (Base)",
        help="精度越高识别越准，但本地解析耗时会相应增加。"
    )
    st.session_state.asr_precision = asr_precision_map[asr_selection]
    
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
        "AI 问答": page_ai_qa,
        "AI 视频中心": page_video_center,
        "知识库概览": page_knowledge_base_browser,
        "术语词库管理": page_term_management
    }
    
    selection = st.sidebar.radio("功能导航", list(menu.keys()))
    
    # 执行选中页面逻辑
    menu[selection]()

if __name__ == "__main__":
    main()
