# 连接向量数据库

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_chroma import Chroma
from data.model.chromadb_model import ChromaDBModel


class ChromaDB:
    def __init__(self):
        # 问答 - 向量数据库路径
        self.qa_chromadb_path = os.getenv("QA_CHROMADB_PATH")
        # 问答 - 向量数据集名称
        self.qa_vector_dataset_name = os.getenv("QA_VECTOR_DATASET_NAME")
        # 课件 - 向量数据库路径
        self.cw_courseware_chromadb_path = os.getenv("CW_CHROMADB_PATH")
        # 课件 - 向量数据集名称
        self.cw_vector_dataset_name = os.getenv("CW_VECTOR_DATASET_NAME")
        # 向量化模型
        self.chromadb_model = ChromaDBModel().chromadb_model()

    def qa_chromadb(self):
        return Chroma(
            persist_directory=self.qa_chromadb_path,
            collection_name=self.qa_vector_dataset_name,
            embedding_function=self.chromadb_model,
            collection_metadata = {"hnsw:space": "cosine"}  # 显式指定余弦
        )

    def cw_chromadb(self):
        return Chroma(
            persist_directory=self.cw_courseware_chromadb_path,
            collection_name=self.cw_vector_dataset_name,
            embedding_function=self.chromadb_model,
            collection_metadata={"hnsw:space": "cosine"}  # 显式指定余弦
        )

if __name__ == '__main__':
    chromadb = ChromaDB().qa_chromadb()
    print(chromadb)
    print("【测试】向量数据库连接成功")