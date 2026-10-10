from app.ai.util.neo4j_util import Neo4jConn

class Neo4jSearchTool:
    def __init__(self) -> None:
        # Neo4j连接
        self.neo4j = Neo4jConn().get_neo4j_conn()

    def search_neo4j(self,course_name: str, chapter_name: str) -> str:
        try:
            # 按照章节查找
            # 降级策略 -- 若没有章节按课程查找
            if chapter_name:
                # 查找语句
                query = """
                    MATCH (c:Course {name: $course})-[:HAS_CHAPTER]->(ch:Chapter)
                    WHERE ch.name = $chapter AND ch.course = $course
                    MATCH (ch)-[:HAS_KNOWLEDGE_POINT]->(kp:KnowledgePoint)
                    WHERE kp.course = $course AND kp.chapter = $chapter
                    RETURN DISTINCT kp.name AS name, kp.type AS type, kp.page AS page
                    LIMIT 30
                """
                # 执行查找
                records = self.neo4j.run(query, course=course_name, chapter=chapter_name)
            else:
                # 查找语句
                query = """
                    MATCH (c:Course {name: $course})-[:HAS_CHAPTER]->(ch:Chapter)
                    MATCH (ch)-[:HAS_KNOWLEDGE_POINT]->(kp:KnowledgePoint)
                    WHERE kp.course = $course
                    RETURN DISTINCT kp.name AS name, kp.type AS type, kp.page AS page
                    LIMIT 30
                """
                # 执行查找
                records = self.neo4j.run(query, course=course_name)

            # 拼接知识点
            kn_points = []
            for record in records:
                if record['page'] is not None:
                    page = record['page']
                else:
                    page = "xxx"
                kn_points.append(f"- {record['name']} （{record['type']}，第{page}页）")

            # 返回查询结果
            print(f"【测试】Neo4j -- 查询到 {len(kn_points)} 个知识点")
            return "\n".join(kn_points)
        except Exception as e:
            # 降级策略 -- Neo4j 故障时返回空串，只丢知识点结构这一源，对话/出题继续
            print(f"【测试】Neo4j -- 查询失败，降级为空知识点清单: {e}")
            return ""

    def get_knowledge_points(self,course_name: str, chapter_name: str) -> str:
        try:
            # 按照章节查找
            # 降级策略 -- 若没有章节按课程查找
            if chapter_name:
                # 查找语句
                query = """
                    MATCH (c:Course {name: $course})-[:HAS_CHAPTER]->(ch:Chapter)
                    WHERE ch.name = $chapter AND ch.course = $course
                    MATCH (ch)-[:HAS_KNOWLEDGE_POINT]->(kp:KnowledgePoint)
                    WHERE kp.course = $course AND kp.chapter = $chapter
                    RETURN DISTINCT kp.name AS name
                    LIMIT 30
                """
                # 执行查找
                records = self.neo4j.run(query, course=course_name, chapter=chapter_name)
            else:
                # 查找语句
                query = """
                    MATCH (c:Course {name: $course})-[:HAS_CHAPTER]->(ch:Chapter)
                    MATCH (ch)-[:HAS_KNOWLEDGE_POINT]->(kp:KnowledgePoint)
                    WHERE kp.course = $course
                    RETURN DISTINCT kp.name AS name
                    LIMIT 30
                """
                # 执行查找
                records = self.neo4j.run(query, course=course_name)

            # 返回查询结果
            return "\n".join(f"- {r['name']}" for r in records)
        except Exception as e:
            # 降级策略 -- Neo4j 故障时返回空串，只丢知识点结构这一源，对话/出题继续
            print(f"【测试】Neo4j -- 查询失败，降级为空知识点清单: {e}")
            return ""
