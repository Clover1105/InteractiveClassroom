from typing import Annotated
from fastapi import APIRouter, Depends

login_router = APIRouter()

from app.web.schema.account_schema import AccountSchema
from app.web.system_router.login_account import LoginAccount

@login_router.post(
    path="/login",
    summary="登录账号"
)
def login(account_schema:AccountSchema):
    print("\n【测试】这里是 -- login_router.py")
    print(f"【测试】接收到用户信息（注册账号）：{account_schema}")
    return LoginAccount(account_schema).verify()



# 退出登录接口 -- token加入Redis黑名单，立即失效
from app.web.util.jwt_decode import oauth2_scheme
from app.web.system_router.logout_account import LogoutAccount

@login_router.post(
    path="/logout",
    summary="退出登录（token加入黑名单）"
)
def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    print("\n【测试】这里是 -- login_router.py /logout")
    return LogoutAccount(token).logout()