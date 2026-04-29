"""
知识库管理模块 - FAISS向量检索版本
提供文档加载、分割和基于FAISS的语义检索功能
"""
import os
import logging
from typing import List, Optional
import numpy as np

# FAISS相关导入
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    faiss = None
    SentenceTransformer = None

from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings

logger = logging.getLogger(__name__)


def load_documents(directory: str) -> List[str]:
    """
    从目录加载所有支持格式的文档，返回段落列表
    
    Args:
        directory: 文档目录路径
        
    Returns:
        文档段落列表
        
    Raises:
        FileNotFoundError: 目录不存在
        Exception: 文档加载失败
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"知识库目录不存在: {directory}")
    
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"路径不是目录: {directory}")
    
    documents = []
    loaded_files = 0
    skipped_files = 0
    
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        
        # 跳过非文件
        if not os.path.isfile(path):
            continue
        
        try:
            loader = None
            
            if file.endswith(".txt"):
                loader = TextLoader(path, encoding="utf-8")
            elif file.endswith(".pdf"):
                loader = PyPDFLoader(path)
            elif file.endswith(".docx"):
                loader = Docx2txtLoader(path)
            else:
                skipped_files += 1
                logger.debug(f"跳过不支持的文件格式: {file}")
                continue
            
            docs = loader.load()
            documents.extend(docs)
            loaded_files += 1
            logger.debug(f"已加载文件: {file} ({len(docs)} 个文档)")
            
        except Exception as e:
            logger.error(f"加载文件失败 {file}: {e}")
            continue
    
    if not documents:
        logger.warning(f"目录中没有找到可加载的文档: {directory}")
        return []
    
    # 文档分割
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.kb.chunk_size,
        chunk_overlap=settings.kb.chunk_overlap
    )
    splits = splitter.split_documents(documents)
    paragraphs = [doc.page_content for doc in splits]
    
    logger.info(
        f"文档加载完成: {loaded_files} 个文件, "
        f"{skipped_files} 个跳过, "
        f"共 {len(paragraphs)} 个段落"
    )
    
    return paragraphs


class KnowledgeBaseFAISS:
    """基于FAISS的知识库检索类，使用语义向量检索"""
    
    def __init__(self, kb_dir: Optional[str] = None, model_name: str = None):
        """
        初始化FAISS知识库
        
        Args:
            kb_dir: 知识库目录路径，None则使用配置默认值
            model_name: Embedding模型名称，默认使用多语言MiniLM模型
        """
        if not HAS_FAISS:
            raise ImportError(
                "FAISS未安装，请运行: pip install faiss-cpu sentence-transformers\n"
                "如果使用GPU: pip install faiss-gpu"
            )
        
        self.kb_dir = kb_dir or settings.kb.directory
        self.paragraphs: List[str] = []
        self.embeddings = None
        self.index = None
        self.is_loaded = False
        
        # 初始化Embedding模型
        self.model_name = model_name or 'paraphrase-multilingual-MiniLM-L12-v2'
        logger.info(f"正在加载Embedding模型: {self.model_name}")
        self.embedding_model = SentenceTransformer(self.model_name)
        logger.info("✓ Embedding模型加载完成")
        
        # 自动加载知识库
        try:
            self.reload()
        except Exception as e:
            logger.error(f"知识库初始化失败: {e}")
            raise
    
    def reload(self, kb_dir: Optional[str] = None):
        """
        重新加载知识库目录中的文档并重新建立FAISS索引
        
        Args:
            kb_dir: 可选的新目录路径
            
        Raises:
            Exception: 加载或索引失败
        """
        if kb_dir:
            self.kb_dir = kb_dir
        
        logger.info(f"开始重新加载知识库: {self.kb_dir}")
        
        try:
            # 加载文档
            self.paragraphs = load_documents(self.kb_dir)
            
            if not self.paragraphs:
                logger.warning("知识库为空，无法建立索引")
                self.is_loaded = False
                return
            
            # 生成文本嵌入向量
            logger.info(f"正在生成 {len(self.paragraphs)} 个段落的嵌入向量...")
            self.embeddings = self.embedding_model.encode(
                self.paragraphs, 
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            # 构建FAISS索引
            dimension = self.embeddings.shape[1]
            logger.info(f"向量维度: {dimension}, 正在构建FAISS索引...")
            
            # 使用L2距离的平坦索引（适合小规模数据）
            # 对于大规模数据，可以使用 IndexIVFFlat 或 IndexHNSW
            self.index = faiss.IndexFlatL2(dimension)
            
            # 添加向量到索引
            self.index.add(self.embeddings.astype('float32'))
            
            self.is_loaded = True
            logger.info(
                f"✓ 知识库加载完成: {len(self.paragraphs)} 个段落, "
                f"向量维度: {dimension}"
            )
            
        except Exception as e:
            logger.error(f"知识库重载失败: {e}", exc_info=True)
            self.is_loaded = False
            raise
    
    def retrieve(self, query: str, k: Optional[int] = None) -> List[str]:
        """
        根据查询语句返回最相关的k个段落（语义检索）
        
        Args:
            query: 查询文本
            k: 返回段落数量，None则使用配置默认值
            
        Returns:
            相关段落列表（按相关性降序）
            
        Raises:
            RuntimeError: 知识库未加载
            ValueError: 查询为空
        """
        if not self.is_loaded:
            raise RuntimeError("知识库未加载，请先调用reload()")
        
        if not query or not query.strip():
            raise ValueError("查询文本不能为空")
        
        if k is None:
            k = settings.retrieval.k
        
        try:
            # 将查询转换为向量
            query_embedding = self.embedding_model.encode([query])
            
            # 在FAISS索引中搜索最相似的k个向量
            k = min(k, len(self.paragraphs))  # 确保不超过总段落数
            distances, indices = self.index.search(
                query_embedding.astype('float32'), 
                k
            )
            
            # 获取结果段落
            results = [self.paragraphs[i] for i in indices[0]]
            
            # 记录相似度分数（L2距离越小越相似）
            logger.debug(
                f"检索结果 - 查询: {query[:30]}..., "
                f"距离分数: {distances[0]}"
            )
            
            if not results:
                logger.warning(f"未找到与查询相关的段落: {query[:50]}...")
            
            return results
            
        except Exception as e:
            logger.error(f"检索失败: {e}", exc_info=True)
            raise RuntimeError(f"知识库检索出错: {e}")
    
    def get_stats(self) -> dict:
        """
        获取知识库统计信息
        
        Returns:
            包含统计信息的字典
        """
        return {
            'kb_dir': self.kb_dir,
            'paragraph_count': len(self.paragraphs),
            'is_loaded': self.is_loaded,
            'embedding_model': self.model_name,
            'vector_dimension': self.embeddings.shape[1] if self.embeddings is not None else 0,
            'index_type': 'IndexFlatL2',
        }
    
    def save_index(self, index_path: str):
        """
        保存FAISS索引到磁盘
        
        Args:
            index_path: 索引文件路径
        """
        if not self.is_loaded:
            raise RuntimeError("知识库未加载，无法保存索引")
        
        faiss.write_index(self.index, index_path)
        logger.info(f"FAISS索引已保存到: {index_path}")
    
    def load_index(self, index_path: str, paragraphs_path: str):
        """
        从磁盘加载FAISS索引
        
        Args:
            index_path: 索引文件路径
            paragraphs_path: 段落文本文件路径（JSON格式）
        """
        import json
        
        self.index = faiss.read_index(index_path)
        
        with open(paragraphs_path, 'r', encoding='utf-8') as f:
            self.paragraphs = json.load(f)
        
        self.is_loaded = True
        logger.info(f"FAISS索引已从 {index_path} 加载")
    
    def __len__(self) -> int:
        """返回段落数量"""
        return len(self.paragraphs)


# 为了向后兼容，保留原来的类名指向
if HAS_FAISS:
    KnowledgeBase = KnowledgeBaseFAISS
else:
    # 如果FAISS不可用，回退到原来的TF-IDF实现
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    class KnowledgeBaseTFIDF:
        """基于TF-IDF的知识库检索类（后备方案）"""
        
        def __init__(self, kb_dir: Optional[str] = None):
            self.kb_dir = kb_dir or settings.kb.directory
            self.paragraphs: List[str] = []
            self.vectorizer: Optional[TfidfVectorizer] = None
            self.tfidf_matrix = None
            self.is_loaded = False
            
            try:
                self.reload()
            except Exception as e:
                logger.error(f"知识库初始化失败: {e}")
                raise
        
        def reload(self, kb_dir: Optional[str] = None):
            if kb_dir:
                self.kb_dir = kb_dir
            
            logger.info(f"开始重新加载知识库: {self.kb_dir}")
            
            try:
                self.paragraphs = load_documents(self.kb_dir)
                
                if not self.paragraphs:
                    logger.warning("知识库为空，无法建立索引")
                    self.is_loaded = False
                    return
                
                logger.info("正在建立TF-IDF索引...")
                self.vectorizer = TfidfVectorizer()
                self.tfidf_matrix = self.vectorizer.fit_transform(self.paragraphs)
                
                self.is_loaded = True
                logger.info(
                    f"知识库加载完成: {len(self.paragraphs)} 个段落, "
                    f"词汇表大小: {len(self.vectorizer.vocabulary_)}"
                )
                
            except Exception as e:
                logger.error(f"知识库重载失败: {e}", exc_info=True)
                self.is_loaded = False
                raise
        
        def retrieve(self, query: str, k: Optional[int] = None) -> List[str]:
            if not self.is_loaded:
                raise RuntimeError("知识库未加载，请先调用reload()")
            
            if not query or not query.strip():
                raise ValueError("查询文本不能为空")
            
            if k is None:
                k = settings.retrieval.k
            
            try:
                query_vec = self.vectorizer.transform([query])
                scores = np.dot(self.tfidf_matrix, query_vec.T).toarray().flatten()
                
                k = min(k, len(self.paragraphs))
                top_indices = scores.argsort()[-k:][::-1]
                
                results = [
                    self.paragraphs[i] 
                    for i in top_indices 
                    if scores[i] > 0
                ]
                
                if not results:
                    logger.warning(f"未找到与查询相关的段落: {query[:50]}...")
                
                return results
                
            except Exception as e:
                logger.error(f"检索失败: {e}", exc_info=True)
                raise RuntimeError(f"知识库检索出错: {e}")
        
        def get_stats(self) -> dict:
            return {
                'kb_dir': self.kb_dir,
                'paragraph_count': len(self.paragraphs),
                'is_loaded': self.is_loaded,
                'vocabulary_size': len(self.vectorizer.vocabulary_) if self.vectorizer else 0,
            }
        
        def __len__(self) -> int:
            return len(self.paragraphs)
    
    KnowledgeBase = KnowledgeBaseTFIDF
