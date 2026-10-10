from app.web.schema.account_schema import AccountSchema
from app.web.tool.mysql_insert_tool import MySQLInsert
from app.web.tool.mysql_select_tool import MySQLSelect
from app.web.util.password_util import hash_password
from app.web.util.redis_conn import RedisConn

class AddAccount:
    def __init__(self,account_schema: AccountSchema) -> None:
        self.identity = account_schema.identity
        self.id = account_schema.id
        self.name = account_schema.name
        self.email = account_schema.email
        # 密码加密后入库（数据库只存bcrypt密文，不存明文）
        self.password = hash_password(account_schema.password)
        self.captcha = account_schema.captcha
        self.mysql_verify = MySQLSelect()
        self.mysql_insert = MySQLInsert()
        self.redis_conn = RedisConn()

    def _verify_code(self,captcha):
        try:
            conn = self.redis_conn.get_redis_conn()
            key = f"captcha_{self.identity}_{self.id}"
            real_captcha = conn.get(key)
            if real_captcha == captcha.encode("utf-8"):
                conn.delete(key)
                self.redis_conn.close_redis_conn(conn)
                return {
                    "code": 200,
                    "message": "验证码验证成功"
                }
            elif real_captcha is None:
                self.redis_conn.close_redis_conn(conn)
                return {
                    "code": 500,
                    "message": "验证码已过期或未发送，请重新获取"
                }
            else:
                self.redis_conn.close_redis_conn(conn)
                return {
                    "code": 500,
                    "message": "验证码输入错误"
                }
        except Exception as e:
            return {
                "code": 500,
                "message": f"验证码验证异常：{e}"
            }


    def sign_up(self) -> dict:
        print("\n【测试】这里是注册账号 -- add_account.py")

        if self.identity == "student" or self.identity == "teacher":
            sql_insert = f"insert into {self.identity} values(%s, %s, %s, %s, now())"
            sql_verify = f"select id,name,email from {self.identity} where id = %s"

            # 验证账号是否存在
            result = self.mysql_verify.verify_account(sql_verify,self.id)
            print("【测试】验证账号返回的结果类型：",type(result))  # <class 'dict'> <class 'NoneType'>
            if result:
                return {
                    "code": 500,
                    "message": "账号已存在",
                    "data": result
                }

            # 验证验证码是否正确
            verify_result = self._verify_code(self.captcha)
            if verify_result.get("code") != 200:
                return verify_result
        else:
            return {
                "code": 500,
                "message": "身份错误",
                "data": None
            }
        result = self.mysql_insert.insert_account(sql_insert,self.id,self.name,self.email,self.password)
        return result

if __name__ == '__main__':
    from app.web.schema.account_schema import AccountSchema
    s = AccountSchema(identity="teacher",id="101",name="sang",email="2920242909@qq.com",password="123456")
    a1 = AddAccount(s)
    print(a1.sign_up())
