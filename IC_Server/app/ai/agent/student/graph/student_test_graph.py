"""
学生测试图：manager 统一入口 → start 出题 / finish 收卷 + 评价 → END
"""
from langgraph.graph import StateGraph, START, END
from typing import Any
from app.ai.agent.student.state.test_state import TestState
from app.ai.agent.student.node.test_manager_node import test_manager_node, route_test
from app.ai.agent.student.node.question_node import question_node
from app.ai.agent.student.node.finish_node import finish_node
from app.ai.agent.student.node.evaluation_node import evaluation_node


class StudentTestGraph:
    def __init__(self) -> None:
        self.agent = self.test_agent()

    def test_agent(self) -> Any:
        print("\n【测试】这里是 -- student_test_graph.py")

        graph = StateGraph(TestState)

        # 注册节点
        graph.add_node("manager", test_manager_node)
        graph.add_node("start", question_node)
        graph.add_node("finish", finish_node)
        graph.add_node("evaluation", evaluation_node)

        # 画边
        graph.add_edge(START, "manager")
        graph.add_conditional_edges(
            "manager",
            route_test,
            {"start": "start", "finish": "finish"}
        )
        graph.add_edge("start", END)
        # finish 链路：finish → evaluation → END
        graph.add_edge("finish", "evaluation")
        graph.add_edge("evaluation", END)

        self.agent = graph.compile(debug=True)
        return self.agent

    # 画图
    def draw(self) -> bytes:
        data = self.agent.get_graph().draw_mermaid_png()
        with open("测试评价流程图.png", "wb") as f:
            f.write(data)

if __name__ == '__main__':
    graph = StudentTestGraph()
    graph.draw()
