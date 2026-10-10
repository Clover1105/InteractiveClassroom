from datetime import datetime, timezone
from fastapi import HTTPException
from app.web.util.jwt_util import verify_token
from app.web.util.token_blacklist import TokenBlacklist

class LogoutAccount:
    def __init__(self, token: str) -> None:
        self.token = token
        self.token_blacklist = TokenBlacklist()

    def logout(self) -> dict:
        print("\n【测试】这里是 -- logout_account.py")
        try:
            payload = verify_token(self.token)
        except HTTPException:
            # token已过期或非法：本身就无法再使用，无需加黑名单
            return {
                "code": 200,
                "message": "token已失效，直接退出",
                "data": None
            }
        # 剩余有效期（秒）= 到期时间 - 当前时间；至少1秒保证键能写入
        remaining = int(payload.get("exp") - datetime.now(timezone.utc).timestamp())
        remaining = max(remaining, 1)
        # 加入黑名单，TTL=剩余有效期，token过期后黑名单键随之消失
        if self.token_blacklist.add_token_to_blacklist(self.token, remaining):
            return {
                "code": 200,
                "message": "退出登录成功",
                "data": None
            }
        else:
            return {
                "code": 500,
                "message": "退出登录失败，请稍后重试",
                "data": None
            }

