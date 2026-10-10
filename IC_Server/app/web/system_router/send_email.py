from app.web.schema.account_schema import AccountSchema
import random
import os
from email.mime.text import MIMEText
from app.web.util.redis_conn import RedisConn
from app.web.tool.mysql_select_tool import MySQLSelect
import smtplib
import ssl
from dotenv import load_dotenv
load_dotenv()

class SendEmail:
    def __init__(self, account_schema: AccountSchema) -> None:
        # 邮件
        self.sender = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_EMAIL_PASSWORD")
        self.host = os.getenv("EMAIL_HOST")
        self.port = int(os.getenv("EMAIL_PORT"))
        # 账号信息
        self.identity = account_schema.identity
        self.id = account_schema.id
        self.email = account_schema.email
        # 调用
        self.mysql_verify = MySQLSelect()
        self.redis_conn = RedisConn()

    # 生成验证码
    def create_captcha(self) -> str:
        captcha = ""
        for i in range(4):
            captcha += str(random.randint(0, 9))
        return captcha

    # 将验证码存储到redis中
    def save_captcha_to_redis(self,captcha) -> dict:
        try:
            conn = self.redis_conn.get_redis_conn()
            key = f"captcha_{self.identity}_{self.id}"
            conn.delete(key)  # 清除可能存在的旧验证码
            conn.setex(key, 300, captcha)
            self.redis_conn.close_redis_conn(conn)
            return {
                "code": 200,
                "msg": "验证码存储到redis中成功"
            }
        except Exception as e:
            return {
                "code": 500,
                "msg": f"验证码存储到redis中失败：{e}"
            }

    # 生成邮件信息
    def email_message(self,captcha) -> MIMEText:
        # 配置发送信息：发件方、授权码（从.env文件读取）、主题、邮件内容
        sender = self.sender
        subject = "主题为：发送验证码"
        content = f"验证码为：{captcha},请在5分钟内使用"

        # 创建邮件对象 -- 将要发送的信息写在这个对象里面
        message = MIMEText(content, "plain", "utf-8")
        print(f"【测试】创建的邮件对象为：\n{message}")

        # 添加内容在 message对象中
        message["From"] = sender  # 发件人
        message["To"] = self.email  # 收件人
        message["Subject"] = subject  # 主题
        print(f"【测试】添加内容后的邮件对象为：\n{message}")
        return message

    # 发送验证码邮件
    def captcha_email(self) -> dict:
        print("\n【测试】这里是发送邮件 -- UsersService")

        # 验证用户是否存在
        sql_version = f"select id,email from {self.identity} where id = %s"
        result = self.mysql_verify.verify_account(sql_version,self.id)
        print("\n【测试】这里是发送邮件 -- UsersService")
        print(f"【测试】验证用户是否存在结果，查询数据库返回信息：{result}")

        # 如果用户存在，则返回结果
        if result:
            return {
                "code": 500,
                "msg": f"用户 {self.id} 存在，无需注册"
            }

        # 如果用户不存在，则进行以下操作

        # 生成验证码
        captcha = self.create_captcha()
        print(f"【测试】验证码：{captcha}")

        # 将验证码存储到redis中
        save_result = self.save_captcha_to_redis(captcha)
        print(f"【测试】将验证码存储到redis中结果：{save_result}")
        if save_result.get("code") != 200:
            return save_result

        # 发送邮件
        sender = self.sender
        sender_pwd = self.sender_password
        print(f"【调试】程序读到的 sender(发件人) 是: [{sender}]")
        print(f"【调试】程序读到的 email(收件人) 是: [{self.email}]")
        try:
            # 创建 SSL 上下文
            context = ssl.create_default_context()

            # 创建邮件发送服务配置（465 端口必须使用 SMTP_SSL）
            smtp = smtplib.SMTP_SSL(
                host=self.host,
                port=self.port,
                context=context
            )
            print(f"【测试】通过SSL创建邮件发送服务配置：{smtp}")

            # 验证发送方和发送方的授权码是否能对上
            smtp.login(sender, sender_pwd)
            print("【测试】验证发送方和发送方的授权码成功")

            # 发送邮件 -- 方法：sendmail(发送方，接收方，邮件对象)
            message = self.email_message(captcha)
            smtp.sendmail(sender, self.email, message.as_string())
            print(f"【测试】发送邮件成功")

            # 关闭邮件发送服务
            smtp.quit()

            # 返回结果
            return {
                "code": 200,
                "msg": f"发送邮件到 {self.email} 成功",
                "data": self.id
            }

        except Exception as e:
            print(f"【测试】发送邮件失败：{e}")
            return {
                "code": 500,
                "msg": f"发送邮件失败：{e}"
            }

if __name__ == '__main__':
    from app.web.schema.account_schema import AccountSchema
    s = AccountSchema(identity="student", id="001", name="clover", email="2920242909@qq.com", password="123456")
    e = SendEmail(s)
    print(e.captcha_email())
