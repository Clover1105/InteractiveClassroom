# L2 PG

"""
L2 会话摘要
存储会话的长期压缩摘要，由 summary_agent 周期性生成
存储于 conversation_summary 表
"""

from app.web.util.postgres_conn import PostgresConn



# 读取摘要 -- 取本会话已有摘要，无则空串
def read(session_id:str) -> str:
    # 连接池
    pool = PostgresConn().get_pool()
    # 查询语句
    sql = "SELECT summary FROM conversation_summary WHERE session_id = %s"
    # 执行查询
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql,(session_id,))
                # 提取出查询结果的一行，列表
                row = cur.fetchone()
        print(f"【测试】L2 -- 读取摘要结果：{row}")
        # 返回结果
        return row[0] if row and row[0] else ""
    except Exception as e:
        print(f"【测试】L2 -- 读取摘要失败: {e}")
        raise

# 写入摘要 -- 覆盖写入本会话摘要（upsert）
def write(session_id: str, summary: str) -> None:
    # 连接池
    pool = PostgresConn().get_pool()
    # 插入语句
    sql = """
          INSERT INTO conversation_summary (session_id, summary, update_time)
          VALUES (%s, %s, NOW()) ON CONFLICT (session_id) DO UPDATE
          SET summary = EXCLUDED.summary, update_time = NOW()
          """
    # 执行插入
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql,(session_id,summary))
        print("【测试】L2 -- 插入摘要成功")
    except Exception as e:
        print(f"【测试】L2 -- 插入摘要失败: {e}")
        raise


# 统计摘要 -- 统计本会话累计消息条数（用于判断是否触发摘要更新）
def count(session_id: str) -> int:
    # 连接池
    pool = PostgresConn().get_pool()
    # 查询语句
    sql = "SELECT COUNT(*) FROM chat_history WHERE session_id = %s"
    # 执行查询
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (session_id,))
                # 提取出查询结果
                row = cur.fetchone()
        print(f"【测试】L2 -- 获取本会话累计消息条数：{row}")
        # 返回结果
        return row[0] if row else 0
    except Exception as e:
        print(f"【测试】L2 -- 查询本会话累计消息条数失败: {e}")
        raise
