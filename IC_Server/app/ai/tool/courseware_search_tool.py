# 课件库检索（Chroma）

"""
课件库检索 -- 知识源（RAG），不属于用户四层记忆
从 data_courseware_chromadb 中检索与当前问题相关的课程内容
数据由教师端 vectorize_node 写入，本模块只读
"""

from data.util.chromadb_util import ChromaDB

_chromadb = ChromaDB().cw_chromadb()

class CoursewareSearchTool:
    def __init__(self) -> None:
        # 课件库 collection（模块级单例，进程内只初始化一次）
        self.chromadb = _chromadb

    # 检索
    def search(self,
            question: str,
            course_name: str = None,
            chapter_name: str = None,
            k: int = 5
    ):
        # 按问题检索课件库，可选按 course_name/chapter_name 过滤
        # 返回：(拼接文本, docs列表) — 板块5 的 knowledge_node 取拼接文本注入 prompt

        # 拼接 metadata 过滤 -- （若库内 metadata 有这些字段则生效，否则会抛错 → 降级全库）
        where = {}
        if course_name:
            where["course_name"] = course_name
        if chapter_name:
            where["chapter_name"] = chapter_name

        # 筛选课件知识点
        try:
            if where:
                docs = self.chromadb.similarity_search(question, k=k, filter=where)
            else:
                docs = self.chromadb.similarity_search(question, k=k)
        except Exception as e:
            # 降级策略 -- metadata 字段不匹配时降级为全库检索（与 course_node 全库检索 qa 库一致）
            print(f"【测试】课件库 -- 按 metadata 过滤失败，降级全库检索: {e}")
            docs = self.chromadb.similarity_search(question, k=k)

        # 拼接检索文本
        qa_text = "\n\n".join(f"[{i + 1}] {doc.page_content}" for i, doc in enumerate(docs))
        print(f"【测试】课件库 -- 获取到检索文本：{qa_text}")
        return qa_text,docs
