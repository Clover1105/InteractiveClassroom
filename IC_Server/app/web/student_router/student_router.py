from fastapi import APIRouter, Query, Depends

# 路由
student_router = APIRouter()

# 学生角色权限中间件
from app.web.util.jwt_decode import is_roles

# 学生对话接口
from fastapi import Request
from app.web.schema.student_schema import ChatSchema
from app.web.student_router.student_chat import StudentChat

@student_router.post(
    path="/chat",
    summary="学生对话(SSE流式输出)"
)
def chat(request: Request, chat_schema: ChatSchema, now_user: dict = Depends(is_roles(["student"]))):
    print("\n【测试】这里是 -- student_router.py")
    print(f"【测试】接收到的参数: {chat_schema}")
    return StudentChat(request, chat_schema).chat()

# 历史会话列表接口
from app.web.student_router.student_session import StudentSession

@student_router.get(
    path="/session/list",
    summary="获取学生会话列表"
)
def session_list(user_id: str = Query(..., description="学生标识"), now_user: dict = Depends(is_roles(["student"]))):
    print("\n【测试】这里是 -- student_router.py")
    return StudentSession().get_session_list(user_id)

# 历史会话详情接口
@student_router.get(
    path="/session/detail",
    summary="获取会话消息明细"
)
def session_detail(session_id: str = Query(..., description="会话id"), now_user: dict = Depends(is_roles(["student"]))):
    print("\n【测试】这里是 -- student_router.py")
    return StudentSession().get_session_detail(session_id)


# 开始测试接口 -- 返回10道题
from app.web.schema.student_schema import TestStartSchema
from app.web.student_router.student_test import StudentTest
@student_router.post(
    path="/test/start",
    summary="开始测试：返回10道练习题"
)
def test_start(request: Request, schema: TestStartSchema, now_user: dict = Depends(is_roles(["student"]))):
    print("\n【测试】这里是 -- student_router.py /test/start")
    return StudentTest(request, schema).start()

# 测试完成接口，生成评价报告
from app.web.schema.student_schema import TestFinishSchema
@student_router.post(
    path="/test/finish",
    summary="测试收卷：生成点评报告并落盘"
)
def test_finish(request: Request, schema: TestFinishSchema, now_user: dict = Depends(is_roles(["student"]))):
    print("\n【测试】这里是 -- student_router.py /test/finish")
    return StudentTest(request, schema).finish()

# 查看评价报告接口
from app.web.student_router.student_evaluation import StudentEvaluation
@student_router.get(
    path="/evaluation/latest",
    summary="查看该课件最新测试点评"
)
def evaluation_latest(courseware_id: int, now_user: dict = Depends(is_roles(["student"]))):
    print("\n【测试】这里是 -- student_router.py /evaluation/latest")
    return StudentEvaluation().eval_last(courseware_id)

# 删除历史会话接口
@student_router.delete(
    path="/session",
    summary="删除历史会话（含全部消息和摘要）"
)
def session_delete(session_id: str, now_user: dict = Depends(is_roles(["student"]))):
    print("\n【测试】这里是 -- student_router.py /session DELETE")
    return StudentSession().del_session(session_id)


