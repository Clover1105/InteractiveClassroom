"""
学生测试业务：start 出题、finish 收卷（生成点评报告）
"""

from fastapi import Request
from langgraph.errors import GraphRecursionError

from app.web.util.postgres_conn import PostgresConn

class StudentTest:
    def __init__(self, request: Request, schema):
        # 学生测试智能体
        self.agent = request.app.state.student_test_agent
        # 连接池
        self.pool = PostgresConn().get_pool()
        # 基本信息
        self.session_id = schema.session_id
        self.user_id = schema.user_id
        self.courseware_id = schema.courseware_id
        self.course_name = schema.course_name
        self.chapter_name = schema.chapter_name
        self.questions = getattr(schema, "questions", None)
        self.answers = getattr(schema, "answers", None)

    # 存储测试消息
    def _save_msg(self, role:str, content:str, course_name:str = "") -> None:
        # 插入语句
        sql = "INSERT INTO chat_history(session_id, user_id, mode, course_name, chapter_name, role, content) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        # 执行插入
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (
                        self.session_id, self.user_id, "test",
                        course_name, self.chapter_name, role, content
                    ))
        except Exception as e:
            print(f"【测试】保存测试消息失败: {e}")

    # 同步执行 graph
    # recursion_limit=10 -- 递归超限保护（test图最长链路为manager->finish->evaluation共3步）
    # 异常统一降级返回{}，由调用方判断空结果并给出友好提示
    def _run_graph(self, state: dict) -> dict:
        try:
            return self.agent.agent.invoke(state, config={"recursion_limit": 10})
        except GraphRecursionError as e:
            print(f"【测试】graph递归超限: {e}")
            return {}
        except Exception as e:
            print(f"【测试】graph执行异常: {e}")
            return {}

    # 开始测试，返回10道题
    # 注意：开始时不落库 -- 中途退出测试则完全无痕（未完成不存储）
    def start(self):
        print("\n【测试】这里是 -- student_test.py start")

        # 测试状态初始化
        state = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "courseware_id": self.courseware_id,
            "course_name": self.course_name,
            "chapter_name": self.chapter_name,
            "mode": "start",
            "questions": [],
            "qa_pairs": [],
            "evaluation_md": "",
            "evaluation_path": ""
        }

        # 获取结果
        result = self._run_graph(state)
        print(f"【测试】出题结果: {result}")

        # 降级处理：图执行失败（返回空）时给出友好提示
        if not result or not result.get("questions"):
            return {
                "code": 500,
                "message": "出题失败，请稍后重试",
                "data": {"questions": []}
            }

        # 返回结果
        return {
            "code": 200,
            "message": "测试开始，题目已全部生成",
            "data": {
                "questions": [q["content"] for q in result["questions"]]
            }
        }

    # 收卷：交错落库 + 生成点评报告
    def finish(self):
        print("\n【测试】这里是 -- student_test.py finish")

        # 拼接题目和答案
        qa_pairs = []
        for q,a in zip(self.questions or [], self.answers or []):
            qa_pairs.append({"num":len(qa_pairs)+1, "question":q, "answer":a})

        # 把测试中每道题的答案，以“用户消息”的形式写入数据库
        # 交错落库：按一问一答的顺序存储，保证回看时顺序正确
        # 收卷即存储，测试中途退出则完全无痕
        total = len(qa_pairs)
        for pair in qa_pairs:
            self._save_msg("assistant", f"【练习题 {pair['num']}/{total}】{pair['question']}", course_name=self.course_name)
            self._save_msg("user", f"作答：{pair['answer']}", course_name=self.course_name)

        # 初始化状态
        state = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "courseware_id": self.courseware_id,
            "course_name": self.course_name,
            "chapter_name": self.chapter_name,
            "mode": "finish",
            "questions": [],
            "qa_pairs": qa_pairs,
            "evaluation_md": "",
            "evaluation_path": ""
        }

        # 获取结果
        result = self._run_graph(state)
        print(f"【测试】点评已落盘: {result.get('evaluation_path')}")

        # 降级判断：题目答案已落库，仅点评报告生成失败时如实提示
        if not result or not result.get("evaluation_path"):
            print("【测试】点评报告生成失败")
            return {
                "code": 500,
                "message": "测试已提交，但点评报告生成失败，请稍后重试",
                "data": {"evaluation_path": ""}
            }

        # 返回结果
        return {
            "code": 200,
            "message": "测试完成，点评报告已生成",
            "data": {
                "evaluation_path": result.get("evaluation_path", "")
            }
        }








