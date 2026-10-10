from app.web.util.mysql_conn import MySQLConn

class MySQLUpdate:
    def __init__(self) -> None:
        self.mysql_conn = MySQLConn()

    def update_parse_status(self, sql, status, courseware_id) -> dict:
        print("\n【测试】这里是 -- mysql_update_tool.py")
        conn = None
        cur = None
        try:
            # 每次调用现建连接（对象可安全地被多次调用）
            conn = self.mysql_conn.get_mysql_conn()
            if conn is None:
                print("【测试】获取数据库连接失败")
                return {"code": 500, "message": "数据库连接失败"}
            cur = conn.cursor()
            cur.execute(sql, [status, courseware_id])
            conn.commit()
            print(f"【测试】课件 {courseware_id} 状态更新为 {status}")
            return {"code": 200, "message": "状态更新成功"}
        except Exception as e:
            print(f"【测试】状态更新失败: {e}")
            return {"code": 500, "message": "状态更新失败"}
        finally:
            # 关闭前判断存在性，避免重复关闭报 Already closed
            if cur is not None:
                try:
                    cur.close()
                except Exception:
                    pass
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
