from typing import Optional
import pymysql
import os
from dotenv import load_dotenv
load_dotenv()

class MySQLConn:
    def __init__(self) -> None:
        self.host = os.getenv("MYSQL_HOST")
        self.port = int(os.getenv("MYSQL_PORT"))
        self.user = os.getenv("MYSQL_USER")
        self.password = os.getenv("MYSQL_PASSWORD")
        self.database = os.getenv("MYSQL_DATABASE")
        self.charset = os.getenv("MYSQL_CHARSET")

    # 获取连接
    def get_mysql_conn(self) -> Optional[pymysql.connections.Connection]:
        try:
            return pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                # # 以 dict 的方式返回查询结果
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            print(f"【测试】获取数据库连接失败：{e}")
            return None

    # 关闭连接
    def close_mysql_conn(self, cur, conn) -> None:
        try:
            if cur is not None:
                cur.close()
        except Exception as e:
            print(f"【测试】关闭cursor异常: {e}")
        try:
            if conn is not None:
                conn.close()
        except Exception as e:
            print(f"【测试】关闭连接异常: {e}")


if __name__ == '__main__':
    conn = MySQLConn()
    result = conn.get_mysql_conn()
    print(result)