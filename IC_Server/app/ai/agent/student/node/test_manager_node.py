"""
测试图管理节点：按 state.mode 路由到出题 / 收卷分支
"""
from app.ai.agent.student.state.test_state import TestState


def test_manager_node(state: TestState) -> dict:
    print("\n【测试】这里是 -- student/test_manager_node.py，模式：", state["mode"])
    return {}


def route_test(state: TestState) -> str:
    if state["mode"] == "finish":
        return "finish"
    return "start"
