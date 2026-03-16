import re
import io
from typing import List, Dict, Tuple
import PyPDF2
from langchain_text_splitters import RecursiveCharacterTextSplitter

class PrivacyInterceptor:
    """
    敏感信息拦截器：在数据离开本地环境前进行脱敏处理。
    支持识别：姓名、指纹（模拟格式）、机构隐私。
    """
    def __init__(self, sensitive_keywords: List[str] = None):
        self.sensitive_keywords = sensitive_keywords or []
        # 模拟指纹格式：16进制字符串，长度为 32 或 64
        self.fingerprint_pattern = re.compile(r'\b[a-fA-F0-9]{32,64}\b')
        # 手机号正则
        self.phone_pattern = re.compile(r'(\d{3})\d{4}(\d{4})')
        # 简单中文姓名模式 (姓+1-2个字)
        self.name_pattern = re.compile(r'([张王李赵刘陈杨黄吴周][某]{1,2})|(?<=[：:])([张王李赵刘陈杨黄吴周][^ \n\r\t,，。]{1,2})')

    def intercept(self, text: str) -> Tuple[str, List[Dict]]:
        """
        拦截并替换敏感信息，返回脱敏后的文本和变换日志。
        """
        logs = []
        original_text = text
        
        # 1. 处理机构隐私词
        for word in self.sensitive_keywords:
            if word in text:
                masked = word[0] + "*" * (len(word) - 1)
                text = text.replace(word, masked)
                logs.append({"type": "机构隐私", "original": word, "masked": masked})

        # 2. 处理指纹信息
        fingerprints = self.fingerprint_pattern.findall(text)
        for fp in set(fingerprints):
            masked = fp[:4] + "..." + fp[-4:]
            text = text.replace(fp, masked)
            logs.append({"type": "指纹信息", "original": fp, "masked": masked})

        # 3. 处理手机号
        text = self.phone_pattern.sub(r'\1****\2', text)
        # 注意：正则替换不便记录每个具体的日志，这里仅演示核心逻辑

        # 4. 模拟姓名脱敏 (基于常见姓氏的启发式匹配)
        # 实际生产中应使用 NER 模型，此处为 MVP 逻辑演示
        potential_names = ["张三", "李四", "王五", "赵老师"]
        for name in potential_names:
            if name in text:
                masked = name[0] + "*"
                text = text.replace(name, masked)
                logs.append({"type": "姓名", "original": name, "masked": masked})

        return text, logs

class KnowledgeManager:
    """
    知识库管理模块：负责文档解析、切片、脱敏及检索。
    """
    def __init__(self, institution_name: str = ""):
        self.interceptor = PrivacyInterceptor(sensitive_keywords=[institution_name])
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        self.knowledge_base = [] # 模拟向量库，实际应存储在向量数据库中

    def process_pdf(self, file_bytes: bytes) -> List[Dict]:
        """
        解析 PDF -> 切片 -> 脱敏。
        """
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        return self._process_text_content(full_text)

    def process_docx(self, file_bytes: bytes) -> List[Dict]:
        """
        解析 Docx -> 切片 -> 脱敏。
        """
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = "\n".join([para.text for para in doc.paragraphs])
        return self._process_text_content(full_text)

    def process_text(self, file_bytes: bytes) -> List[Dict]:
        """
        解析 TXT/MD -> 切片 -> 脱敏。
        """
        full_text = file_bytes.decode("utf-8", errors="ignore")
        return self._process_text_content(full_text)

    def process_video(self, file_path: str, model_size: str = "base") -> List[Dict]:
        """
        解析视频 (音频提取 + ASR) -> 切片 -> 脱敏。
        """
        import os
        from moviepy import VideoFileClip
        import whisper
        import tempfile

        # 1. 提取音频
        audio_temp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        try:
            video = VideoFileClip(file_path)
            if video.audio:
                video.audio.write_audiofile(audio_temp, logger=None)
            video.close()
            
            # 2. ASR 语音转文字 (使用缓存的模型)
            if not hasattr(self, "_whisper_models"):
                self._whisper_models = {}
            
            if model_size not in self._whisper_models:
                self._whisper_models[model_size] = whisper.load_model(model_size)
            
            model = self._whisper_models[model_size]
            
            # 增加术语 Prompt 增强
            initial_prompt = "这是一段关于教育培训、AI重构、隐私脱敏和RAG知识库的技术分享。请准确识别专有名词。"
            result = model.transcribe(audio_temp, initial_prompt=initial_prompt)
            full_text = result["text"]
            
            return self._process_text_content(full_text)
        finally:
            if os.path.exists(audio_temp):
                os.remove(audio_temp)

    def _process_text_content(self, full_text: str) -> List[Dict]:
        """
        统一的切片与脱敏流。
        """
        # 1. 文本切片
        chunks = self.splitter.split_text(full_text)
        
        # 2. 逐片脱敏并存入“知识库”
        processed_chunks = []
        for chunk in chunks:
            masked_text, logs = self.interceptor.intercept(chunk)
            processed_chunks.append({
                "original": chunk,
                "content": masked_text,
                "logs": logs
            })
        
        self.knowledge_base.extend(processed_chunks)
        return processed_chunks

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """
        简单的 RAG 检索逻辑 (关键词匹配)。
        """
        results = []
        # 模拟检索：基于关键词出现的频率简单排序
        keywords = query.split()
        scored_chunks = []
        for chunk in self.knowledge_base:
            score = sum(1 for kw in keywords if kw.lower() in chunk["content"].lower())
            if score > 0:
                scored_chunks.append((score, chunk["content"]))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in scored_chunks[:top_k]]

    def generate_lesson_plan(self, topic: str, context: List[str]) -> str:
        """
        模拟 AI 提示词驱动生成结构化教案。
        """
        combined_context = "\n".join(context)
        # 这是一个模拟生成的字符串，实际应由 LLM API 生成
        plan = f"""
# 《{topic}》教学教案 (AI 生成版)

## 🎯 教学目标
1. **理解核心概念**：深入掌握资料中提到的关于“{topic}”的基本定义。
2. **应用案例分析**：能够结合背景信息处理实际问题。
3. **安全准则遵循**：在教学过程中始终贯彻执行隐私保护逻辑。

## 🕸️ 知识点拓扑 (Mermaid)
```mermaid
graph TD
    A[{topic}] --> B[核心要素]
    A --> C[应用场景]
    B --> B1[原理分析]
    B --> B2[脱敏逻辑]
    C --> C1[课堂问答]
    C --> C2[课后评估]
```

## 💬 课堂互动建议
- **提问环节**：询问学生“在实际操作中，如何识别并拦截类似于‘张*’的敏感信息？”
- **讨论课题**：探讨《技术落地方案》中提到的分阶段落地对本课程的意义。
- **实操演练**：使用本地解析器对测试文档进行一次完整的脱敏处理演示。

---
*注：本教案基于脱敏后的本地知识库生成，确保数据合规安全。*
"""
        return plan

    def calculate_ai_score(self, content: str) -> Dict[str, float]:
        """
        模拟依据《可行性报告》指标计算“AI 预估评估分数”。
        """
        # 模拟根据内容长度和关键字密度计算分数
        score = 85.0 + (len(content) % 15)
        return {
            "total": round(min(score, 100.0), 1),
            "attention": round(80.0 + (len(content) % 10), 1),
            "coverage": round(90.0 + (len(content) % 5), 1),
            "vibe_index": 92.5
        }

class MockDB:
    """模拟从 PostgreSQL 读取机构配置"""
    @staticmethod
    def get_institution_config():
        return {
            "name": "博学教育培训中心",
            "admin_contact": "张三 (13812345678)",
            "license_id": "EDU-2026-MOCK-001",
            "region": "华东地区",
            "status": "Active"
        }
