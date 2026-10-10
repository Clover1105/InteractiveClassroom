from typing import Optional
from app.web.util.mysql_conn import MySQLConn

class MySQLSelect:
    def __init__(self) -> None:
        # 创建全局单例数据库连接对象
        self.mysql_conn = MySQLConn()
        # 创建连接对象
        self.conn = self.mysql_conn.get_mysql_conn()
        # 创建游标对象
        self.cur = self.conn.cursor()

    def verify_account(self,sql:str,id:str) -> Optional[dict]:
        print("\n【测试】这里是 -- mysql_select_tool.py")
        # 执行 sql
        self.cur.execute(sql,id)
        # 获取结果
        result = self.cur.fetchone()
        print(f"【测试】数据库查询结果：{result}")
        # 关闭连接
        self.mysql_conn.close_mysql_conn(self.cur,self.conn)
        return result

    def select_courseware(self,sql:str) -> list:
        print("\n【测试】这里是 -- mysql_select_tool.py")
        # 执行 sql
        self.cur.execute(sql)
        # 获取结果
        result = self.cur.fetchall()
        print(f"【测试】数据库查询结果：{result}")
        # 关闭连接
        self.mysql_conn.close_mysql_conn(self.cur, self.conn)
        return result

if __name__ == '__main__':
    sql = "select id,name,email from student where id = %s"
    result = MySQLSelect().verify_account(sql,"001")
    print(result)