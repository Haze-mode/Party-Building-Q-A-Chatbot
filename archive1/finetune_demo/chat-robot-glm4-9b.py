"""
This script creates a Web API demo with transformers backend for the glm-4-9b model,
supporting fine-tuned models (PEFT) and a retrieval-augmented knowledge base.

Usage:
- Run the script to start the Tornado web server on port 6006.
- Send POST/GET requests to /api/chatbot?infos=你的问题 to get responses.

The knowledge base is loaded from the '党建知识库' directory.
"""

import os
import torch
from threading import Thread
from typing import Union
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from peft import AutoPeftModelForCausalLM, PeftModelForCausalLM
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    PreTrainedTokenizerFast,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer,
)
import tornado.web
import tornado.ioloop
from tornado.web import RequestHandler

ModelType = Union[PreTrainedModel, PeftModelForCausalLM]
TokenizerType = Union[PreTrainedTokenizer, PreTrainedTokenizerFast]

# 模型路径：可通过环境变量 MODEL_PATH 指定，默认使用微调后的检查点
MODEL_PATH = os.environ.get('MODEL_PATH', '/root/GLM-4/finetune_demo/output/checkpoint-2950')
# 知识库目录
KB_DIR = "党建知识库"


# -------------------- 知识库加载与检索 --------------------
def load_knowledge_base(directory: str):
    """从目录加载文档并切分成段落"""
    documents = []
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if file.endswith(".txt"):
            loader = TextLoader(path, encoding="utf-8")
        elif file.endswith(".pdf"):
            loader = PyPDFLoader(path)
        elif file.endswith(".docx"):
            loader = Docx2txtLoader(path)
        else:
            continue
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = splitter.split_documents(documents)
    return [doc.page_content for doc in splits]


def build_tfidf_index(knowledge_base):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(knowledge_base)
    return vectorizer, tfidf_matrix


def retrieve(query, vectorizer, tfidf, paragraphs, k=3):
    q_vec = vectorizer.transform([query])
    scores = np.dot(tfidf, q_vec.T).toarray().flatten()
    top_idx = scores.argsort()[-k:][::-1]
    return [paragraphs[i] for i in top_idx]


# -------------------- 模型加载 --------------------
def load_model_and_tokenizer(
    model_dir: Union[str, Path], trust_remote_code: bool = True
) -> tuple[ModelType, TokenizerType]:
    model_dir = Path(model_dir).expanduser().resolve()
    if (model_dir / 'adapter_config.json').exists():
        model = AutoPeftModelForCausalLM.from_pretrained(
            model_dir,
            trust_remote_code=trust_remote_code,
            device_map='auto'
        )
        tokenizer_dir = model.peft_config['default'].base_model_name_or_path
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            trust_remote_code=trust_remote_code,
            device_map='auto'
        )
        tokenizer_dir = model_dir

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_dir,
        trust_remote_code=trust_remote_code,
        encode_special_tokens=True,
        use_fast=False
    )
    return model, tokenizer


# 加载模型和分词器
model, tokenizer = load_model_and_tokenizer(MODEL_PATH, trust_remote_code=True)
model.eval()

# 加载知识库（启动时一次性加载）
print("正在加载党建知识库...")
paragraphs = load_knowledge_base(KB_DIR)
vectorizer, tfidf = build_tfidf_index(paragraphs)
print(f"知识库加载完成，共 {len(paragraphs)} 个段落。")


# -------------------- 自定义停止条件 --------------------
class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        stop_ids = model.config.eos_token_id
        if isinstance(stop_ids, int):
            stop_ids = [stop_ids]
        for stop_id in stop_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False


# 全局对话历史（可按需扩展为按会话存储）
history = []


def chatbot_api(user_input: str) -> str:
    max_length = 8192
    top_p = 0.7
    temperature = 0.9
    stop = StopOnTokens()

    # 1. 检索相关知识
    retrieved = retrieve(user_input, vectorizer, tfidf, paragraphs, k=3)
    context = "\n\n".join(retrieved)

    # 2. 构建对话消息（含系统提示）
    messages = [
        {"role": "system", "content": f"请基于以下已知信息回答问题：\n{context}"}
    ]

    # 追加历史对话
    for user_msg, model_msg in history:
        if user_msg:
            messages.append({"role": "user", "content": user_msg})
        if model_msg:
            messages.append({"role": "assistant", "content": model_msg})
    # 添加当前用户输入
    messages.append({"role": "user", "content": user_input})

    # 准备模型输入
    model_inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt"
    ).to(model.device)

    # 流式输出
    streamer = TextIteratorStreamer(
        tokenizer=tokenizer,
        timeout=60,
        skip_prompt=True,
        skip_special_tokens=True
    )
    generate_kwargs = {
        "input_ids": model_inputs,
        "streamer": streamer,
        "max_new_tokens": max_length,
        "do_sample": True,
        "top_p": top_p,
        "temperature": temperature,
        "stopping_criteria": StoppingCriteriaList([stop]),
        "repetition_penalty": 1.2,
        "eos_token_id": model.config.eos_token_id,
    }

    t = Thread(target=model.generate, kwargs=generate_kwargs)
    t.start()

    # 收集完整回复
    full_response = ""
    for new_token in streamer:
        if new_token:
            full_response += new_token

    # 更新历史记录
    history.append([user_input, full_response.strip()])
    return full_response.strip()


# -------------------- Tornado Web 服务 --------------------
class BaseHandler(RequestHandler):
    """解决跨域请求"""

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET')
        self.set_header('Access-Control-Max-Age', 1000)
        self.set_header('Access-Control-Allow-Headers', '*')


class IndexHandler(BaseHandler):
    def get(self):
        infos = self.get_query_argument("infos")
        print("Q:", infos)
        try:
            result = chatbot_api(user_input=infos)
        except Exception as e:
            print("Error:", e)
            result = "服务器内部错误"
        print("A:", result)
        self.write(result)


if __name__ == '__main__':
    app = tornado.web.Application([(r'/api/chatbot', IndexHandler)])
    app.listen(6006)
    print("党建小助手 Web 服务已启动，监听端口 6006...")
    tornado.ioloop.IOLoop.current().start()