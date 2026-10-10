"""
L1 当前轮上下文（会话窗口）
读取本会话最近的若干条消息，供多轮对话使用
数据来源：chat_history 表（student_chat.py._save_message 写入）
本模块只读，不写
"""
from app.web.util.postgres_conn import PostgresConn

def read(session_id: str, limit: int = 10, offset: int = 0) -> list:
    """
    取本会话最近 limit 条消息，按时间正序返回
    返回：[{"role": "user"|"assistant", "content": "..."}, ...]
    """
    # 连接池
    pool = PostgresConn().get_pool()
    # 查询语句 --  -- 某个会话最近的 N 条消息
    sql = "SELECT role, content FROM chat_history WHERE session_id = %s ORDER BY id DESC LIMIT %s OFFSET %s"
    # 执行查询
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql,(session_id, limit, offset))
                # 提取出查询返回的所有结果行，列表
                rows = cur.fetchall()
        print(f"【测试】L1 -- 查询到 {limit}条 历史上下文：{rows}")
        # 查出来是倒序，翻转回时间正序
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
    except Exception as e:
        print(f"【测试】L1 -- 查询历史上下文失败: {e}")
        raise
