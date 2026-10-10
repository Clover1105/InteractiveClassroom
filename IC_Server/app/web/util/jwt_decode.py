from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.web.util.jwt_util import verify_token
from app.web.util.token_blacklist import TokenBlacklist

# 定义 OAuth2 令牌获取端点 -- 创建从请求头获取 token 的对象工具
# FastAPI 自动从请求头 Authorization: Bearer <token> 中提取令牌，缺失/格式错直接401
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="account/login")

# 解码 -- 获取用户信息
# Depends：在进入目标方法之前先执行此拦截，验证token合法性
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    print("【测试】进入方法之前进行验证：")
    # 验证成功：返回原始的 Pay1oad数据；验签失败/已过期：抛出异常 401
    payload = verify_token(token)

    # 黑名单校验
    if TokenBlacklist().verify_token_in_blacklist(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token已失效（已登出），请重新登录",
            headers={"WWW-Authenticate": "Bearer"}
        )

    print(f"【测试】当前用户信息：{payload}")
    return payload

# 判断角色是否被允许访问接口
def is_roles(*allow_roles: list):
    # print(f"【测试】被允许的角色：{allow_roles}")
    def user(now_user: dict = Depends(get_current_user)):
        # 判断用户身份是否在被允许访问该接口的角色列表中
        if now_user.get('identity') in allow_roles[0]:
            return now_user
        else:
            raise HTTPException(
                status_code=403,
                detail="用户身份不被允许访问该接口",
            )
    return user
