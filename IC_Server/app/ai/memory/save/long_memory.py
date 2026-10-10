# L3 PG

"""
L3 长期记忆
跨会话、跨课程持久化的用户事实（身份、偏好、背景、说过的重要事情）
存储于 long_memory 表，由 long_agent 每轮抽取写入
"""

from app.web.util.postgres_conn import PostgresConn

# 写入 -- 批量追加该用户的长期事实
def add(user_id: str, facts: list) -> None:
    if not facts:
        return
    pool = PostgresConn().get_pool()
    sql = "INSERT INTO long_memory (user_id, content) VALUES (%s, %s)"
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, [(user_id, f) for f in facts])
        print(f"【测试】L3 -- 写入 {len(facts)} 条长期记忆")
    except Exception as e:
        print(f"【测试】L3 -- 写入长期记忆失败: {e}")
        raise

# 读取 -- 取该用户全部长期记忆（时间正序，最多 limit 条）
def list(user_id: str, limit: int = 20) -> list:
    pool = PostgresConn().get_pool()
    sql = "SELECT content FROM long_memory WHERE user_id = %s ORDER BY id DESC LIMIT %s"
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, limit))
                rows = cur.fetchall()
        # 倒序查出来，翻转回时间正序
        return [r[0] for r in reversed(rows)]
    except Exception as e:
        print(f"【测试】L3 -- 读取长期记忆失败: {e}")
        raise
