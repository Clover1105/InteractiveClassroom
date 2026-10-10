from pydantic import BaseModel, Field
from typing import Optional

# 账号信息参数校验
class AccountSchema(BaseModel):
    identity: str = Field(..., description="当前登录身份")
    id: str = Field(..., description="学号或工号")
    name: str = Field(..., description="姓名")
    # 可选
    email: Optional[str] = Field(default=None, description="邮箱")
    password: Optional[str] = Field(default=None, description="密码")
    captcha: Optional[str] = Field(default=None, description="验证码")