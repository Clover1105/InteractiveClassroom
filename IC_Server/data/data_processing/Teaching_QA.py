# 数据向量化

import os
import pandas as pd
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 我们把“标准问题”作为页面内容，把“答案”和其他信息作为元数据存起来
from langchain_core.documents import Document

# 连接向量数据库并写入数据
from data.util.chromadb_util import ChromaDB

class TeachingQA:
    def __init__(self):
        # 读取 Excel 数据
        self.raw_data = os.getenv("RAW_DATA_PATH")
        self.df = self.convert_dataframe()
        self.documents = self.convert_document()

    # 将 Excel 数据转换为 DataFrame 格式
    def convert_dataframe(self):
        # 把 Excel 文件里的指定工作表读取成一个 DataFrame（数据框）对象
        # pandas 本身并不直接解析 .xlsx 文件，它是通过引擎机制（openpyxl）委托第三方库来处理的
        # read_excel -- 专门用来读取 Excel 文件（.xlsx 或 .xls 格式）
        # sheet_name -- 指定要读取的 Excel 工作表名称，默认读取第一个工作表
        df = pd.read_excel(self.raw_data, sheet_name="问答初始数据")

        # 数据清洗：只保留有“标准问题”的行，防止空数据报错
        # dropna -- 删除包含缺失值的行（默认删除所有包含缺失值的行）
        # subset -- 指定要检查的列名列表，默认检查所有列
        # inplace -- 是否在原 DataFrame 上修改，默认返回一个新 DataFrame
        df.dropna(subset=["标准问题(80字以内，不能为空)"], inplace=True)

        # 测试，前10条数据
        # df = df.head(10)

        # 返回数据框
        return df

    # 转换成 LangChain 需要的 Document 格式
    def convert_document(self):
        # 转换为 Document 格式
        documents = []
        # df.iterrows() -- 每次返回一个元组 (索引, 行数据)
        for i, row in self.df.iterrows():
            # 相似问法处理
            similar_questions = []
            similar = ["相似问法1(80字以内)", "相似问法2(80字以内)","相似问法3(80字以内)", "相似问法4(80字以内)","相似问法5(80字以内)", "相似问法6(80字以内)"]
            for s in similar:
                # pd.notna(row[s]) -- 判断这个单元格的值不是空值（Not a Number / Not Available）
                if s in row.index and pd.notna(row[s]):
                    similar_questions.append(str(row[s]))

            # print(f"【测试】第 {i+1} 行的相似问法：\n -- {similar_questions}")

            # 将标准问题和相似问法拼接成一段完整的文本
            page_content = f"标准问题：{str(row['标准问题(80字以内，不能为空)'])}\n"
            if similar_questions:
                page_content += f"相似问法：{'；'.join(similar_questions)}\n"

            # 将文本转换为 Document 格式
            doc = Document(
                page_content=page_content,
                metadata={
                    "answer": str(row["答案(2000字以内，不能为空)"]),
                    "category": str(row["规则分类（30字以内，空为默认分类）"]),
                    "source": "教学问答数据集.xlsx"
                }
            )

            # 添加到列表中
            documents.append(doc)

        # 处理完成，打印，返回
        print(f"【测试】数据处理完成，共加载 {len(documents)} 条问答数据。")
        return documents

    # 将处理好的数据写入向量数据库
    def write_to_chromadb(self):
        print("【测试】正在连接数据库并写入向量...")

        try:
            # 获取数据库实例
            db = ChromaDB().qa_chromadb()

            # 将文档添加到数据库
            # 如果集合已存在，这行代码会追加数据；如果是新的，会创建新集合
            db.add_documents(self.documents)

            print("【测试】数据向量化并存储成功！")
            print(f"【测试】当前数据库中共有 {db._collection.count()} 条数据。")

        except Exception as e:
            print(f"【测试】存入数据库时出错: {e}")



if __name__ == '__main__':
    TeachingQA().write_to_chromadb()

