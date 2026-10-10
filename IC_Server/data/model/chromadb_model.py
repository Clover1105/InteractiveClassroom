# 向量化模型

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_huggingface import HuggingFaceEmbeddings

class ChromaDBModel:
    def __init__(self):
        self.model_name = os.getenv("VECTORIZE_MODEL_PATH")

    def chromadb_model(self):
        return HuggingFaceEmbeddings(
            model_name=self.model_name,
            # 本地加载
            model_kwargs={
                "device": "cuda",
                "local_files_only": True,
            },
        )