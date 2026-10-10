from app.web.util.redis_conn import RedisConn

class TokenBlacklist:
    def __init__(self) -> None:
        self.redis_conn = RedisConn()

    # 未过期，退出登录 -- 添加token到黑名单
    def add_token_to_blacklist(self, token: str, remaining_seconds: int) -> bool:
        try:
            conn = self.redis_conn.get_redis_conn()
            conn.setex(f"token_blacklist:{token}", remaining_seconds, "1")
            self.redis_conn.close_redis_conn(conn)
            return True
        except Exception as e:
            print(f"【测试】添加token到黑名单失败：{e}")
            return False

    # 登录时，验证token是否在黑名单里面
    def verify_token_in_blacklist(self, token: str) -> bool:
        try:
            conn = self.redis_conn.get_redis_conn()
            result = conn.exists(f"token_blacklist:{token}")
            self.redis_conn.close_redis_conn(conn)
            return bool(result)
        except Exception as e:
            print(f"【测试】验证token是否在黑名单，查询异常，降级放行：{e}")
            return False
