from app.ai.agent.student.state.student_state import StudentState

# 管理节点：学生对话统一入口，只负责打印和路由
def manager_node(state: StudentState) -> dict:
    print("\n【测试】这里是 -- student/manager_node.py，当前模式：", state["mode"])
    return {}

# 按模式路由到对应业务节点
def route_chat(state: StudentState) -> str:
    mode = state["mode"]
    if mode == "qa":
        return "knowledge"
    return "normal"