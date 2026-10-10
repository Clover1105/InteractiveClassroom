from fastapi import APIRouter
signup_router = APIRouter()

# 账号注册接口
from app.web.schema.account_schema import AccountSchema
from app.web.system_router.add_account import AddAccount
@signup_router.post(
    path="/signup",
    summary="注册账号"
)
def sign_up(account_schema:AccountSchema):
    print("\n【测试】这里是 -- account_router.py")
    print(f"【测试】接收到用户信息（注册账号）：{account_schema}")
    return AddAccount(account_schema).sign_up()


