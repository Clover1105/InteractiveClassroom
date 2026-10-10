# psycopg_pool 连接池（全局一份）

"""
-- 历史记录（所有模式的对话消息）
chat_history(id BIGSERIAL PK, session_id VARCHAR, user_id VARCHAR,
             mode VARCHAR, course_name VARCHAR, chapter_name VARCHAR,
             role VARCHAR, content TEXT, create_time TIMESTAMP)

-- 摘要记忆（情况三）
conversation_summary(session_id VARCHAR PK, summary TEXT, update_time TIMESTAMP)

-- 学生长期事实记忆（情况四 -- L3）
student_long_term_memory(id BIGSERIAL PK, user_id VARCHAR,
            content TEXT, fact_type VARCHAR, importance SMALLINT,
            source_session_id VARCHAR, create_time TIMESTAMP, update_time TIMESTAMP)

"""

print("【测试】这里是 -- postgres_conn.py")

import os
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

# 加载环境变量
load_dotenv()

# 建表SQL（幂等，可重复执行）
# chat_history -- 对话历史（会话管理/历史记录用）
# conversation_summary -- 会话摘要记忆（四层记忆的L2层用）
CREATE_TABLE_SQL_LIST = [
    # 对话历史
    '''
    CREATE TABLE IF NOT EXISTS chat_history (
        id BIGSERIAL PRIMARY KEY,
        session_id VARCHAR(64) NOT NULL,
        user_id VARCHAR(64) NOT NULL,
        mode VARCHAR(16) NOT NULL,
        course_name VARCHAR(255) DEFAULT '',
        chapter_name VARCHAR(255) DEFAULT '',
        role VARCHAR(16) NOT NULL,
        content TEXT NOT NULL,
        create_time TIMESTAMP DEFAULT NOW()
    )
    ''',
    'CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id)',
    'CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id)',

    # 摘要记忆
    '''
    CREATE TABLE IF NOT EXISTS conversation_summary (
        session_id VARCHAR(64) PRIMARY KEY,
        summary TEXT,
        update_time TIMESTAMP DEFAULT NOW()
    )
    ''',

    # 人物画像
    '''
    CREATE TABLE IF NOT EXISTS student_profile (
        user_id VARCHAR(64) NOT NULL,
        course_name VARCHAR(255) NOT NULL,
        profile TEXT,
        update_time TIMESTAMP DEFAULT NOW(),
        PRIMARY KEY (user_id, course_name)
    )
    ''',
    'CREATE INDEX IF NOT EXISTS idx_student_profile_user ON student_profile(user_id)',
    
    # 长期记忆 -- 跨会话、跨课程的用户事实（按 user_id 全局）
    '''
    CREATE TABLE IF NOT EXISTS long_memory (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(64) NOT NULL,
        content TEXT NOT NULL,
        create_time TIMESTAMP DEFAULT NOW()
    )
    ''',
    'CREATE INDEX IF NOT EXISTS idx_user_memory_user ON long_memory(user_id)',

]


class PostgresConn:
    # 类级共享连接池 -- 全局唯一
    _pool = None

    def __init__(self) -> None:
        # 从环境变量读取连接串
        self.conninfo = os.getenv("POSTGRESQL_URL")

    # 启动阶段：创建连接池并建表（main.py的lifespan生命周期中调用，只执行一次）
    def open_pool(self) -> ConnectionPool:
        if PostgresConn._pool is None:
            # autocommit=True -- 每条语句自动提交，业务代码无需手动commit
            PostgresConn._pool = ConnectionPool(
                self.conninfo,
                min_size=2,
                max_size=10,
                open=False,
                kwargs={"autocommit": True}
            )
            PostgresConn._pool.open()

            # 建表（幂等）
            self.create_tables()
            print("【测试】PostgreSQL连接池已启动，数据表已就绪")
        return PostgresConn._pool

    # 关闭阶段：销毁连接池（main.py的lifespan中调用）
    def close_pool(self) -> None:
        if PostgresConn._pool is not None:
            PostgresConn._pool.close()
            PostgresConn._pool = None
            print("【测试】PostgreSQL连接池已关闭")

    # 获取连接池（业务代码调用）
    def get_pool(self) -> ConnectionPool:
        if PostgresConn._pool is None:
            raise RuntimeError("PostgreSQL连接池未初始化，请检查服务启动流程")
        return PostgresConn._pool

    # 建表
    def create_tables(self) -> None:
        pool = PostgresConn._pool
        with pool.connection() as conn:
            with conn.cursor() as cur:
                for sql in CREATE_TABLE_SQL_LIST:
                    cur.execute(sql)
