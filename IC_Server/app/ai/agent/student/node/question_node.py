"""
出题节点：根据课件库 + Neo4j 知识点结构，生成 10 道练习题
"""
import json

from app.ai.agent.student.state.test_state import TestState
from app.ai.tool.courseware_search_tool import CoursewareSearchTool
from app.ai.model.my_model import MyModel
from app.ai.prompt.builder_prompt import BuilderPromptYaml
from app.ai.tool.neo4j_search_tool import Neo4jSearchTool

def question_node(state: TestState) -> dict:
    print("\n【测试】这里是 -- student/question_node.py")

    course_name = state["course_name"]
    chapter_name = state["chapter_name"]

    # 向量课件库
    cw_context, _ = CoursewareSearchTool().search(
        question=f"{course_name} - {chapter_name} 核心考点",
        course_name=course_name,
        chapter_name=chapter_name,
        k=5
    )

    # neo4j 知识点
    kn_points = Neo4jSearchTool().search_neo4j(course_name, chapter_name)

    # 拼接提示词
    sys_prompt = BuilderPromptYaml.get_prompt(
        "question_node.yaml",
        course_name=course_name,
        chapter_name=chapter_name or "（不限定章节）",
        cw_context=cw_context or "（暂无）",
        points=kn_points or "（暂无）",
    )

    user_prompt = (
        "请严格输出 10 道练习题的 JSON 数组，"
        "键名固定为 qno（1~10 的整数）和 content（题目的完整陈述）。"
        "题型覆盖：概念理解 / 方法辨析 / 应用举例 / 知识联系 / 总结反思。"
        "题目应基于以上【课程内容】【知识点结构】，不要超出范围。"
        "只输出 JSON 数组本身，不要任何额外文字。"
    )

    # 调用大模型生成问题
    llm = MyModel.get_model()
    result = llm.invoke(
        [
            ("system", sys_prompt),
            ("user", user_prompt)
        ]
    )

    # 解析回复的JSON格式的结果
    r = result.content.strip()  # 去掉两端的空白字符

    # 去除 Markdown 代码块标记（如 \``json ... ```）并提取纯内容
    if r.startswith("```"):
        r = r.split("```", 2)[1]
        if r.startswith("json"):
            r = r[4:]
        r = r.strip().rstrip("`").strip()

    # 将清洗好的字符串 r 解析成 Python 对象
    ques = json.loads(r)

    # 更新状态
    print(f"【测试】出题成功：{ques}")
    return {
        "questions": ques
    }




