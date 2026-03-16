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
