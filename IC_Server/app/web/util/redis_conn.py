import os
import redis
from dotenv import load_dotenv
load_dotenv()

class RedisConn:
    def __init__(self) -> None:
        self.host = os.getenv("REDIS_HOST")
        self.port = os.getenv("REDIS_PORT")
        self.password = os.getenv("REDIS_PASSWORD")
        self.db = os.getenv("REDIS_DB")

    def get_redis_conn(self) -> redis.Redis:
        return redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            # 如果redis无法存入数据，添加下面的配置protocol=2 3 中的一个，应该是2
            # protocol=2,
        )

    def close_redis_conn(self,conn) -> None:
        conn.close()

if __name__ == "__main__":
    r = RedisConn()
    print(r.get_redis_conn())