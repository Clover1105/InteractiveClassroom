from datetime import datetime, timezone, timedelta
import os

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import JWTError,jwt

load_dotenv()

# 生成token
def create_token(payload:dict) -> str:
    # payload：用户需要封装进入payload的数据内容，字典格式{k:v}
    copy_payload = payload.copy()
    # 保质期 -- 访问令牌过期时间
    shelf_life = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
    # 到期时间 = 当前时间 + 保质期
    stop_time = datetime.now(timezone.utc)+timedelta(minutes=shelf_life)
    # 将到期时间和token生成时间放入payload中
    copy_payload.update({'exp':stop_time, 'iat':datetime.now(timezone.utc)})
    # 生成token
    token = jwt.encode(
        claims = copy_payload,
        key = os.getenv('SECRET_KEY'),
        algorithm = os.getenv('ALGORITHM')
    )
    # 返回token
    return token

# 验证token
def verify_token(token:str) -> dict:
    try:
        # 解码token -- 验证通过后返回原始的 Pay1oad数据，字典类型
        payload = jwt.decode(
            token = token,
            key = os.getenv('SECRET_KEY'),
            algorithms = [os.getenv('ALGORITHM')]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token错误或已过期，验证失败"
        )

if __name__ == '__main__':
    token = create_token({"user_id": "001", "username": "clover", "identity": "student"})
    print(token)
    print(verify_token(token))
