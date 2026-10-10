"""
课件处理智能体
文件上传成功后，调用此模块启动后台解析任务
"""
from app.ai.agent.teachers.state.courseware_state import CoursewareState
from langgraph.graph import StateGraph,START,END

from app.ai.agent.teachers.node.read_node import read_node
from app.ai.agent.teachers.node.ocr_node import ocr_node
from app.ai.agent.teachers.node.parse_node import parse_node
from app.ai.agent.teachers.node.vectorize_node import vectorize_node
from app.ai.agent.teachers.node.manager_node import manager_node,route_manager
from app.ai.agent.teachers.node.script_node import script_node

class CoursewareGraph:
    def __init__(self):
        self.agent = self.courseware_agent()


    def courseware_agent(self):
        print("【测试】这里是 -- courseware_graph.py")
        graph = StateGraph(CoursewareState)

        # 添加节点（后续逐步补充）
        graph.add_node("read", read_node)
        graph.add_node("ocr", ocr_node)
        graph.add_node("parse", parse_node)
        graph.add_node("vectorize", vectorize_node)
        graph.add_node("manager", manager_node)
        graph.add_node("script", script_node)

        # 画边（后续逐步补充）
        graph.add_edge(START, "manager")
        # 管理节点条件路由：进解析流程 / 进脚本节点 / 直接结束
        graph.add_conditional_edges(
            "manager", route_manager,
            {"read": "read", "script": "script", "end": END}
        )
        graph.add_edge("read", "ocr")
        graph.add_edge("ocr", "parse")
        graph.add_edge("parse", "vectorize")
        graph.add_edge("vectorize", END)
        graph.add_edge("script", END)

        # 编译
        self.agent = graph.compile(checkpointer=None)
        return self.agent


    # 执行课件处理
    async def run(self, courseware):
        print("【测试】这里是 -- courseware_graph.py")
        print("【测试】获取课件信息：")
        courseware_name = courseware['filename']
        courseware_path = courseware['saved_path']
        course_name = courseware['course_name']
        chapter_name = courseware['chapter_name']
        courseware_ext = courseware['file_ext']
        print(f"【测试】开始处理课件: {courseware_name}")
        # 构建初始状态
        initial_state = {
            "mode": "parse",
            "courseware_path": courseware_path,
            "course_name": course_name,
            "chapter_name": chapter_name,
            "file_type": courseware_ext,
            "courseware_id": courseware.get('id', 0),
            "parse_status": "parsing",
            "vectorize_status": "pending",
            "script_status": "",
            "script_content": "",
            "script_path": "",
        }
        # 执行工作流
        result = await self.agent.ainvoke(initial_state)
        print(f"【测试】课件处理完成: {result}")
        return result

    # 画图
    def draw(self):
        data = self.agent.get_graph().draw_mermaid_png()
        with open("课件处理流程图.png", "wb") as f:
            f.write(data)

    # 查看授课脚本（文件存在则返回内容，不存在则现场生成后返回）
    async def run_script(self, course_name, chapter_name, courseware_id):
        print("【测试】这里是 -- courseware_graph.py run_script")
        initial_state = {
            "mode": "script",  # 脚本模式
            "course_name": course_name,
            "chapter_name": chapter_name,
            "courseware_id": courseware_id,
            "script_status": "",
            "script_content": "",
            "script_path": "",
        }
        result = await self.agent.ainvoke(initial_state)
        print(f"【测试】脚本流程结束: {result.get('script_status')}")
        return result

if __name__ == '__main__':
    courseware_graph = CoursewareGraph()
    courseware_graph.draw()