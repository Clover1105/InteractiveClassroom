from passlib.context import CryptContext

# 创建密码加密上下文对象 -- bcrypt 算法
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 加密 -- 注册调用
def hash_password(password) -> str:
    hash_pwd = bcrypt_context.hash(password)
    return hash_pwd

# 验证 -- 登录调用
def verify_password(password, hash_pwd) -> bool:
    try:
        ver_result = bcrypt_context.verify(password, hash_pwd)
        return ver_result
    except Exception as e:
        print(f'【测试】密码验证失败：{e}')
        return False

if __name__ == '__main__':
    hash_password('123456')