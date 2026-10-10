"""
学生历史会话业务
职责：查询PG中chat_history表，聚合出会话列表和会话消息明细
"""
from psycopg.rows import dict_row

from app.web.util.postgres_conn import PostgresConn

# 模式显示文本
def get_mode_text(mode) -> str:
    if mode == 'test': return '测试'
    if mode == 'qa': return '知识点提问'
    return '普通对话'

# 会话标题拼接
def get_title(course_name, chapter_name) -> str:   # 课程、章节
    if not course_name:
        return '普通对话'
    if chapter_name:
        return f"{course_name} / {chapter_name}"
    return course_name


class StudentSession:
    def __init__(self) -> None:
        # 获取全局PostgreSQL连接池
        self.pool = PostgresConn().get_pool()

    # 查询会话列表：按session_id聚合chat_history，一个会话一行
    def get_session_list(self, user_id) -> dict:
        print("\n【测试】这里是 -- student_session.py")
        sql = '''
        SELECT session_id, MIN(mode) AS mode, MAX(course_name) AS course_name, MAX(chapter_name) AS chapter_name,
               COUNT(*) AS msg_count, MIN(create_time) AS start_time, MAX(create_time) AS last_time
        FROM chat_history WHERE user_id = %s GROUP BY session_id ORDER BY last_time DESC
        '''
        # 执行sql（row_factory=dict_row -- 查询结果转字典，免手动拼装）
        results = self._query_all(sql, (user_id,))

        # 组装前端需要的字段
        session_list = []
        for row in results:
            session_list.append({
                'session_id': row['session_id'],
                'time': row['last_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'title': get_title(row['course_name'], row['chapter_name']),
                'mode': row['mode'],
                'modeText': get_mode_text(row['mode']),
                'msg_count': row['msg_count'],
                'selectedCourse': row['course_name'],
                'selectedChapter': row['chapter_name'],
            })

        print(f"【测试】查询到 {len(session_list)} 个会话")
        return {
            "code": 200,
            "message": "获取会话列表成功",
            "data": session_list
        }

    # 查询会话详情：按时间正序返回该会话的所有消息
    def get_session_detail(self, session_id) -> dict:
        print("\n【测试】这里是 -- student_session.py")
        sql = 'SELECT role, content, create_time FROM chat_history WHERE session_id = %s ORDER BY id'
        results = self._query_all(sql, (session_id,))

        messages = []
        for row in results:
            messages.append({
                'role': row['role'],
                'content': row['content'],
                'time': row['create_time'].strftime("%Y-%m-%d %H:%M:%S")
            })

        print(f"【测试】会话 {session_id} 共 {len(messages)} 条消息")
        return {
            "code": 200,
            "message": "获取会话详情成功",
            "data": {"session_id": session_id, "messages": messages}
        }

    # 执行查询的内部通用方法
    def _query_all(self, sql, params) -> list:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    # 删除会话：删除该会话的全部消息和摘要
    def del_session(self, session_id) -> dict:
        print("\n【测试】这里是 -- student_session.py delete_session")
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM chat_history WHERE session_id = %s", (session_id,))
                # 摘要删除单独容错 -- 不是每个会话都生成过摘要，失败不影响会话删除
                try:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM conversation_summary WHERE session_id = %s", (session_id,))
                except Exception as e:
                    print(f"【测试】摘要删除失败: {e}")
                conn.commit()
            print(f"【测试】会话 {session_id} 及其摘要已删除")
            return {"code": 200, "message": "删除会话成功"}
        except Exception as e:
            print(f"【测试】删除会话失败: {e}")
            return {"code": 500, "message": "删除会话失败"}

