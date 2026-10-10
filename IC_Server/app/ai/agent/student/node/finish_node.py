"""
收卷节点：把 10 题 10 答案 + 知识点拼给评价 LLM，
产出 Markdown 点评报告；落盘由 evaluation_node 完成
"""
from app.ai.agent.student.state.test_state import TestState
from app.ai.model.my_model import MyModel
from app.ai.prompt.builder_prompt import BuilderPromptYaml
from app.ai.tool.neo4j_search_tool import Neo4jSearchTool


def finish_node(state:TestState) -> dict:
    print("\n【测试】这里是 -- student/finish_node.py")

    course_name = state["course_name"]
    chapter_name = state["chapter_name"]

    # 获取 neo4j 知识点
    points = Neo4jSearchTool().get_knowledge_points(course_name, chapter_name)

    # 拼接 -- 题目+答案 对照表
    qa_table = ""
    for i, pair in enumerate(state['qa_pairs'],1):
        qa_table += (
            f"\n### 第{i}题：{pair['question']}\n"
            f"**学生回答**：{pair['answer']}\n"
        )

    # 提示词
    sys_prompt = BuilderPromptYaml.get_prompt(
        "evaluation_node.yaml",
        course_name=course_name,
        chapter_name=chapter_name or "（不限定章节）",
        points=points or "（暂无）",
        qa_table=qa_table,
    )

    # 调用大模型生成点评
    llm = MyModel.get_model()
    result = llm.invoke(sys_prompt)

    # 更新状态
    return {
        "evaluation_md": result.content
    }

