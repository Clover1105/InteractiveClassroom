from py2neo import Graph
import os
from dotenv import load_dotenv
load_dotenv()

class Neo4jConn:
    def __init__(self) -> None:
        self.host = os.getenv('NEO4J_HOST')
        self.account = os.getenv('NEO4J_ACCOUNT')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.name = os.getenv('NEO4J_NAME')

    def get_neo4j_conn(self) -> Graph:
        return Graph(
            profile=self.host,  # 连接地址
            auth=(self.account, self.password),  # 连接账号和密码
            name=self.name,  # 数据库名称
        )

if __name__ == '__main__':
    neo4j_conn = Neo4jConn()
    print(neo4j_conn.get_neo4j_conn())