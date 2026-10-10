print("【测试】这里是 -- main.py")

from fastapi import FastAPI
import uvicorn

from contextlib import asynccontextmanager
from app.ai.agent.teachers.graph.courseware_graph import CoursewareGraph
from app.web.util.postgres_conn import PostgresConn
from app.ai.agent.student.graph.student_chat_graph import StudentChatGraph
from app.ai.agent.student.graph.student_test_graph import StudentTestGraph


# 定义异步上下文管理器
@asynccontextmanager
async def content_manager(app: FastAPI):
    # --- 启动阶段 (Startup) ---
    print("【测试】欢迎进入 -- 基于泛雅平台的AI互动智课生成与实时问答系统")
    # 启动课件处理智能体 -- app.state：全局共享命名空间
    app.state.courseware_agent = CoursewareGraph()
    print("【测试】课件处理智能体初始化完成")
    # 学生对话智能体
    app.state.student_agent = StudentChatGraph()
    print("【测试】学生对话智能体初始化完成")
    # 学生测试智能体
    app.state.student_test_agent = StudentTestGraph()
    print("【测试】学生测试智能体初始化完成")
    # 启动PostgreSQL连接池
    app.state.postgres_conn = PostgresConn()
    app.state.postgres_conn.open_pool()
    # yield 之前的代码在服务器启动时执行
    yield
    # yield 之后的代码在服务器关闭时执行
    # --- 关闭阶段 (Shutdown) ---
    # 销毁对象
    app.state.postgres_conn.close_pool()
    app.state.postgres_conn = None
    app.state.courseware_agent = None
    app.state.student_agent = None
    app.state.student_test_agent = None
    print("【测试】系统成功关闭")

app = FastAPI(lifespan=content_manager)

# 跨域配置
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],    # 允许的跨域访问的域名 -- 完整的客户端域名
    allow_credentials=True, # 允许携带cookie
    allow_methods=["*"],    # 允许的跨域访问请求的方法
    allow_headers=["*"],    # 允许的跨域访问请求的头部信息
)


# 注册 -- 注册账号路由
from app.web.system_router.signup_router import signup_router
app.include_router(signup_router,prefix="/account",tags=["account"])

# 注册 -- 发送邮件路由
from app.web.system_router.email_router import email_router
app.include_router(email_router,prefix="/account",tags=["account"])

# 注册 -- 登录路由
from app.web.system_router.login_router import login_router
app.include_router(login_router,prefix="/account",tags=["account"])

# 注册 -- 课件路由
from app.web.teacher_router.courseware_router import courseware_router
app.include_router(courseware_router,prefix="/courseware",tags=["teacher"])

# 注册 -- 学生端路由
from app.web.student_router.student_router import student_router
app.include_router(student_router,prefix="/student",tags=["student"])


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)
