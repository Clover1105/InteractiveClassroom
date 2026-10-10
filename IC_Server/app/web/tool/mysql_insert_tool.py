from app.web.util.mysql_conn import MySQLConn

class MySQLInsert:
    def __init__(self) -> None:
        # 创建全局单例数据库连接对象
        self.mysql_conn = MySQLConn()
        # 创建连接对象
        self.conn = self.mysql_conn.get_mysql_conn()
        # 创建游标对象
        self.cur = self.conn.cursor()

    def insert_account(self,sql,id,name,email,password) -> dict:
        print("\n【测试】这里是 -- mysql_insert_tool.py")
        try:
            # 执行操作
            self.cur.execute(sql,[id,name,email,password])
            # 提交事务
            self.conn.commit()
            print("【测试】注册成功")
            return {
                "code": 200,
                "message": "注册成功"
            }
        except Exception as e:
            print(f"【测试】注册失败：{e}")
            return {"code": 500, "message": "注册失败"}
        finally:
            # 关闭连接
            self.mysql_conn.close_mysql_conn(self.cur, self.conn)

    def insert_courseware(self,sql,original_filename,saved_filename,file_path,course_name,chapter_name,file_size,file_type) -> dict:
        print("\n【测试】这里是 -- mysql_insert_tool.py")
        try:
            # 执行操作
            self.cur.execute(sql,[original_filename,saved_filename,file_path,course_name,chapter_name,file_size,file_type,2])
            # 提交事务
            self.conn.commit()
            print("【测试】数据库添加课件成功")
            return {
                "code": 200,
                "message": "数据库添加课件成功",
                "data": original_filename
            }
        except Exception as e:
            print(f"【测试】数据库添加课件失败：{e}")
            return {"code": 500, "message": "数据库添加课件失败", "data": None}
        finally:
            # 关闭连接
            self.mysql_conn.close_mysql_conn(self.cur, self.conn)