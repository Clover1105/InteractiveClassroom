from fastapi import APIRouter

email_router = APIRouter()

from app.web.schema.account_schema import AccountSchema
from app.web.system_router.send_email import SendEmail

@email_router.post(
    path="/email",
    summary="发送验证码邮件"
)
def email(account_schema:AccountSchema):
    print("\n【测试】这里是 -- email_router.py")
    print(f"【测试】接收到用户信息（注册账号）：{account_schema}")
    return SendEmail(account_schema).captcha_email()