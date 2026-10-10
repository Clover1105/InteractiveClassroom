"""
课件向量化节点
职责：
  1. 从Neo4j查询当前章节的所有知识点
  2. 使用本地句子Transformer模型生成向量
  3. 将向量存储到ChromaDB
"""
from dotenv import load_dotenv
from app.ai.util.neo4j_util import Neo4jConn
# 连接向量数据库并写入数据
from data.util.chromadb_util import ChromaDB

from app.ai.agent.teachers.state.courseware_state import CoursewareState

load_dotenv()

neo4j = Neo4jConn().get_neo4j_conn()
# 使用已有的ChromaDB工具类（自动加载模型+连接ChromaDB）
chromadb = ChromaDB()

"""从Neo4j查询当前章节的知识点"""
def _query_knowledge_points(course_name, chapter_name):
    # 找到名为 $course_name 的课程，并顺着 HAS_CHAPTER 关系找到它包含的所有章节
    # 只保留章节名称等于 $chapter_name 的章节节点
    # 从上面找到的章节节点 ch 出发，顺着 HAS_KNOWLEDGE_POINT 关系，找到所有关联的知识点节点
    # 返回知识点的 5 个属性：name（名称）、content（内容）、type（类型）、page（页码）、source_file（来源文件）
    query = '''
        MATCH (c:Course {name: $course_name})-[:HAS_CHAPTER]->(ch:Chapter)
        WHERE ch.name = $chapter_name AND ch.course = $course_name
        MATCH (ch)-[:HAS_KNOWLEDGE_POINT]->(kp:KnowledgePoint)
        WHERE kp.course = $course_name AND kp.chapter = $chapter_name
        RETURN DISTINCT kp.name AS name, kp.content AS content, kp.type AS type,
               kp.page AS page, kp.source_file AS source_file
        '''
    # 获取所有匹配的知识点记录
    results = neo4j.run(
        query,
        course_name=course_name,
        chapter_name=chapter_name
    )

    # 将获取的所有结果，重新整理组合为列表
    knowledge_points = []
    for record in results:
        knowledge_points.append({
            'name': record['name'],
            'content': record['content'],
            'type': record['type'],
            'page': record['page'],
            'source_file': record['source_file']
        })

    print(f'【测试】从Neo4j查询到 {len(knowledge_points)} 个知识点')
    return knowledge_points


"""生成向量并存入ChromaDB"""
def _store_vectors(cw_chroma, knowledge_points, course_name, chapter_name):
    # 替换语义：先删除本章节旧向量，再写入新的（其他课件不受影响）
    cw_chroma._collection.delete(where={
        "$and": [
            {"course_name": {"$eq": course_name}},
            {"chapter_name": {"$eq": chapter_name}}
        ]
    })

    ids = []  # 每条数据的唯一标识
    documents = []  # 原始文本内容（用于向量化和检索）
    metadatas = []  # 元数据字典列表（用于后续检索时过滤，比如按课程名、章节名筛选）

    # 遍历每个知识点 -- 去重
    seen_ids = set()
    for kp in knowledge_points:
        # 拼接文本用于向量化
        text = f"{kp['name']}：{kp['content']}" if kp.get('content') else kp['name']
        # ChromaDB需要唯一ID
        kp_id = f"{course_name}_{kp['name']}_{kp.get('page', 0)}"

        # 跳过重复ID（ChromaDB要求upsert的ID唯一）
        if kp_id in seen_ids:
            print(f'【测试】跳过重复知识点: {kp["name"]} (第{kp.get("page", 0)}页)')
            continue
        seen_ids.add(kp_id)

        ids.append(kp_id)
        documents.append(text)
        metadatas.append({
            'course_name': course_name,
            'chapter_name': chapter_name,
            'type': kp['type'],
            'page': kp['page'],
            'source_file': kp.get('source_file', ''),
            'kp_name': kp['name']
        })

    # #调用langchain_chroma的add_texts方法，内部会自动用HuggingFaceEmbeddings生成向量
    cw_chroma.add_texts(
        texts=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f'【测试】已向ChromaDB写入 {len(ids)} 条向量')


def vectorize_node(state:CoursewareState):
    print('\n【测试】这里是 -- vectorize_node.py')
    print(f"【测试】状态：{state}")

    # 课件信息
    course_name = state.get('course_name', '')
    chapter_name = state.get('chapter_name', '')

    # 从Neo4j查询知识点
    knowledge_points = _query_knowledge_points(course_name, chapter_name)

    if not knowledge_points:
        print('【测试】没有需要向量化的知识点')
        return {
            "vectorize_status": "done"
        }

    # 获取课件ChromaDB客户端
    cw_chroma = chromadb.cw_chromadb()

    # 生成向量并存入ChromaDB
    _store_vectors(cw_chroma, knowledge_points, course_name, chapter_name)

    print(f'【测试】vectorize_node 完成，共向量化 {len(knowledge_points)} 个知识点')

    return {
        "vectorize_status": "done"
    }