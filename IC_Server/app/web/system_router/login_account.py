from app.web.schema.account_schema import AccountSchema
from app.web.tool.mysql_select_tool import MySQLSelect
from app.web.util.password_util import verify_password
from app.web.util.jwt_util import create_token

class LoginAccount:
    def __init__(self, account_schema: AccountSchema) -> None:
        self.id = account_schema.id # 学号或工号
        self.password = account_schema.password
        self.identity = account_schema.identity
        self.mysql_verify = MySQLSelect()

    # 验证登录信息
    def verify(self) -> dict:
        print("\n【测试】这里是 -- login_account.py")
        sql_verify = f"select id,name,password from {self.identity} where id = %s"
        result = self.mysql_verify.verify_account(sql_verify,self.id)
        print("\n【测试】这里是 -- login_account.py")
        if result:
            # 密码对比 -- 明文 vs 数据库bcrypt密文
            if result["id"] == self.id and verify_password(self.password, result["password"]):
                # 登录成功，生成JWT令牌（payload封装学号/工号、姓名、身份角色）
                token = create_token({
                    "id": self.id,
                    "name": result["name"],
                    "identity": self.identity
                })
                return {
                    "code": 200,
                    "message": "登录成功",
                    "data": result['name'],
                    "token": token
                }
            else:
                return {
                    "code": 500,
                    "message": "账号或密码错误",
                    "data": None
                }
        else:
            return {
                "code": 500,
                "message": "账号不存在，请注册后重新登录！",
                "data": None
            }

if __name__ == '__main__':
    from app.web.schema.account_schema import AccountSchema
    s = AccountSchema(identity="student", id="001", name="", email="", password="123456")
    e = LoginAccount(s)
    print(e.verify())
