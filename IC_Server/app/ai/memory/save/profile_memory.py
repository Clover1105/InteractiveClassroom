# L4 Redis

"""
L4 学生画像
每个学生每门课程独立的长期学习画像，由 profile_agent 周期性生成
存储于 student_profile 表
"""

from app.web.util.postgres_conn import PostgresConn

# 读取画像 -- 取该学生该课程已有画像，无则空串
def read(user_id:str, course_name: str) -> str:
    # 连接池
    pool = PostgresConn().get_pool()
    # 查询语句
    sql = "SELECT profile FROM student_profile WHERE user_id = %s AND course_name = %s"
    # 执行查询
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, course_name))
                # 提取出查询结果
                row = cur.fetchone()
        print(f"【测试】L4 -- 获取查询到的数据集结果：{row}")
        # 返回结果
        return row[0] if row and row[0] else ""
    except Exception as e:
        print(f"【测试】L4 -- 查询消息失败: {e}")
        raise

# 写入画像 -- 覆盖写入该学生该课程的画像（upsert）
def write(user_id: str, course_name:str, profile:str) -> None:
    # 连接池
    pool = PostgresConn().get_pool()
    # 插入语句
    sql = """
          INSERT INTO student_profile (user_id, course_name, profile, update_time)
          VALUES (%s, %s, %s, NOW()) ON CONFLICT (user_id, course_name) DO UPDATE
          SET profile = EXCLUDED.profile, update_time = NOW()
          """
    # 执行插入
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, course_name, profile))
        print("【测试】L4 -- 插入画像成功")
    except Exception as e:
        print(f"【测试】L4 -- 插入画像失败: {e}")
        raise