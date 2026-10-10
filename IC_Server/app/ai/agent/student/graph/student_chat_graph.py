from typing import Any
from langgraph.graph import StateGraph, START, END
from app.ai.agent.student.state.student_state import StudentState
from app.ai.agent.student.node.manager_node import manager_node, route_chat
from app.ai.agent.student.node.normal_node import normal_node
from app.ai.agent.student.node.knowledge_node import knowledge_node

# 学生对话图：manager统一入口 → 按mode路由 → 业务节点 → END
class StudentChatGraph:
    def __init__(self) -> None:
        self.agent = self.chat_agent()


    def chat_agent(self) -> Any:
        print("\n【测试】这里是 -- student_chat_graph.py")

        graph = StateGraph(StudentState)

        # 注册节点
        graph.add_node("manager", manager_node)
        graph.add_node("normal", normal_node)
        graph.add_node("knowledge", knowledge_node)

        # 画边
        graph.add_edge(START, "manager")
        graph.add_conditional_edges(
            "manager",
            route_chat,
            {"normal": "normal", "knowledge": "knowledge"}
        )
        graph.add_edge("normal", END)
        graph.add_edge("knowledge", END)

        self.agent = graph.compile(debug=True)
        return self.agent

    # 画图
    def draw(self) -> bytes:
        data = self.agent.get_graph().draw_mermaid_png()
        with open("对话流程图.png", "wb") as f:
            f.write(data)

if __name__ == '__main__':
    courseware_graph = StudentChatGraph()
    courseware_graph.draw()
