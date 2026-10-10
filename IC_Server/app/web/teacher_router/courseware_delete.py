"""
删除课件业务
职责：级联删除该课件的所有数据（互不影响其他课件）
  1. MySQL课件记录（按id）
  2. 上传的原始文件（data/data_download/{uuid}.ext）
  3. 授课脚本（static/md/script_{id}.md）
  4. 学生评价报告（static/evaluation/evaluation_{id}.md）
  5. Chroma向量（data_courseware_chromadb，按source_file=uuid过滤，物理唯一）
  6. Neo4j知识点（按source_file=uuid过滤，DETACH DELETE；Course/Chapter共享节点不删）
"""


from pathlib import Path

from app.ai.util.neo4j_util import Neo4jConn
from app.web.schema.courseware_schema import CoursewareSchema
from app.web.tool.mysql_delete_tool import MySQLDelete
from data.util.chromadb_util import ChromaDB

# 项目根目录
base_dir = Path(__file__).resolve().parents[3]
# 脚本目录
script_dir = base_dir / "static" / "md"
# 评价目录
eval_dir = base_dir / "static" / "evaluation"

# neo4j连接
neo4j = Neo4jConn().get_neo4j_conn()

# 开始删除
class CoursewareDelete:
    def __init__(self,schema: CoursewareSchema) -> None:
        # 课件id
        self.id = schema.id
        # 课件路径
        self.file_path = schema.file_path
        self.course_name = schema.course_name
        self.chapter_name = schema.chapter_name
        # source_file = 上传时生成的uuid文件名（全局唯一，删除过滤的依据）
        self.only_filename = Path(self.file_path).name
        print(f"\n【测试】删除课件：{self.file_path} | {self.only_filename}")

    # 删除MySQL课件记录
    def _del_mysql(self) -> bool:
        try:
            sql = "delete from courseware where id=%s"
            result = MySQLDelete().delete_courseware(sql,self.id)
            return result.get("code") == 200
        except Exception as e:
            print(f"【测试】MySQL删除异常: {e}")
            return False

    # 删除上传的原始文件
    def _del_file(self) -> bool:
        try:
            # 课件在服务器的路径
            path = Path(self.file_path)
            path.unlink(missing_ok=True)
            print(f"【测试】原始文件已删除: {path}")
            return True
        except Exception as e:
            print(f"【测试】原始文件删除失败: {e}")
            return False

    # 删除脚本文件
    def _del_script(self) -> bool:
        try:
            # 脚本文件路径
            path = script_dir / f"script_{self.id}.md"
            path.unlink(missing_ok=True)
            print(f"【测试】脚本文件已删除: {path}")
            return True
        except Exception as e:
            print(f"【测试】脚本文件删除失败: {e}")
            return False

    # 删除评价报告文件
    def _del_eval(self) -> bool:
        try:
            # 评价报告文件路径
            path = eval_dir / f"evaluation_{self.id}.md"
            path.unlink(missing_ok=True)
            print(f"【测试】评价报告文件已删除: {path}")
            return True
        except Exception as e:
            print(f"【测试】评价报告文件删除失败: {e}")
            return False

    # 删除向量化数据
    def _del_chroma(self) -> bool:
        try:
            cw_chroma = ChromaDB().cw_chromadb()
            cw_chroma._collection.delete(where={"source_file": {"$eq": self.only_filename}})
            print(f"【测试】Chroma向量已删除（source_file={self.only_filename}）")
            return True
        except Exception as e:
            print(f"【测试】Chroma向量删除失败: {e}")
            return False

    # 删除结构化数据
    def _del_neo4j(self) -> bool:
        try:
            # 删除知识点
            neo4j.run(
                "MATCH (kp:KnowledgePoint {source_file: $source_file}) DETACH DELETE kp",
                source_file=self.only_filename
            )
            print(f"【测试】Neo4j知识点已删除（source_file={self.only_filename}）")
            return True
        except Exception as e:
            print(f"【测试】Neo4j知识点删除失败: {e}")
            return False


    # 删除课件
    def delete_courseware(self) -> dict:
        print("\n【测试】这里是 -- courseware_delete.py")
        print(f"【测试】删除课件：{self.id} | {self.course_name} / {self.chapter_name}")

        # 收集返回结果
        results = []
        results.append(("MySQL记录", self._del_mysql()))
        results.append(("原始文件", self._del_file()))
        results.append(("授课脚本", self._del_script()))
        results.append(("评价报告", self._del_eval()))
        results.append(("Chroma向量", self._del_chroma()))
        results.append(("Neo4j知识点", self._del_neo4j()))
        print(f"【测试】查看收集的返回结果：{results}")

        # 汇总返回结果
        failed = []
        for name, ok in results:
            if not ok:
                failed.append(name)
        if failed:
            print(f"【测试】部分数据删除失败: {failed}")
            return {"code": 500, "message": f"部分数据删除失败: {', '.join(failed)}"}
        print("【测试】课件及所有相关数据已全部删除")
        return {"code": 200, "message": "课件及所有相关数据已删除"}




