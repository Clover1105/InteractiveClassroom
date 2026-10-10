"""
知识点提问节点
四源检索：data_qa_chromadb（问答库） + data_courseware_chromadb（课件库） + Neo4j（知识图谱） + 授课脚本（static/md/script_{courseware_id}.md）
四层记忆：L1历史（state传入） + L2会话摘要 + L3长期记忆 + L4学生画像（课件库为知识源，不计入）
"""

from pathlib import Path
from app.ai.agent.student.state.student_state import StudentState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.ai.model.my_model import MyModel
from app.ai.prompt.builder_prompt import BuilderPromptYaml
from app.ai.memory.manager.session_manager import SessionManager
from app.ai.tool.neo4j_search_tool import Neo4jSearchTool
from data.util.chromadb_util import ChromaDB
from app.ai.tool.courseware_search_tool import CoursewareSearchTool


# 授课脚本目录（与教师端script_node的MD_DIR同层）
script_dir = Path(__file__).resolve().parents[5] / "static" / "md"
# 脚本注入上限（字符），防止提示词过长
script_max_len = 8000

# 读取对应课件的授课脚本
def _get_script(courseware_id: int) -> str:
    # 没有选择课件 或 id无效 -- 返回空串，提示词自动跳过这一步
    if not courseware_id:
        print("【测试】脚本 -- 没有选择课件，id无效，跳过脚本检索")
        return ""
    try:
        script_path = script_dir / f"script_{courseware_id}.md"
        if not script_path.exists():
            print(f"【测试】脚本 -- 该课件未生成脚本，脚本不存在，跳过：{script_path}")
            return ""
        # 读取脚本内容
        content = script_path.read_text(encoding="utf-8").strip()
        print(f"【测试】脚本 -- 读取脚本内容：{content}")
        # 超长截断
        if len(content) > script_max_len:
            content = content[:script_max_len] + "\n...（脚本过长，已截断）"
        print(f"【测试】脚本 -- 读取成功，长度 {len(content)} 字符")
        return content
    except Exception as e:
        # 降级策略 -- 脚本读取失败不影响其他源
        print(f"【测试】脚本 -- 读取失败，返回空：{e}")
        return ""

# 知识点提问节点：四源检索（问答库+课件库+Neo4j+脚本）+四层记忆
def knowledge_node(state: StudentState) -> dict:
    print("\n【测试】这里是 -- student/knowledge_node.py")
    print(f"【测试】课程：{state['course_name']} | 章节：{state['chapter_name']}")

    # 获取基本信息
    question = state["question"]
    course_name = state["course_name"]
    chapter_name = state["chapter_name"]

    # 记忆读取
    # -- 摘要
    summary = SessionManager.get_summary(state["session_id"])
    # -- 长期记忆
    facts = SessionManager.get_facts(state["user_id"])
    # -- 画像
    profile = SessionManager.get_profile(state["user_id"], course_name)

    # 检索
    # -- 向量问答库
    docs = ChromaDB().qa_chromadb().similarity_search(question, k=5)
    qa_context = "\n\n".join(f"[{i + 1}] {doc.page_content}" for i, doc in enumerate(docs))
    # -- 向量课件库
    cw_context, _ = CoursewareSearchTool().search(question, course_name, chapter_name, k=5)
    # -- neo4j 知识点
    graph_context = Neo4jSearchTool().search_neo4j(course_name, chapter_name)
    # -- 脚本
    script_context = _get_script(state.get("courseware_id",0))

    # 拼接系统提示词
    sys_prompt = []

    # 主体提示词（角色+回答要求） -- 从yaml读取；六个检索段落按有值动态拼接
    sys_prompt.append(BuilderPromptYaml.get_prompt('knowledge_node.yaml'))

    if script_context:
        sys_prompt.append(f"【授课脚本】（老师本节课的讲稿）\n{script_context}")

    if cw_context:
        sys_prompt.append(f"【课程知识库】（课件知识点检索结果）\n{cw_context}")

    if graph_context:
        scope = f"{course_name} - {chapter_name}" if chapter_name else course_name
        sys_prompt.append(f"【知识点结构】（{scope}）\n{graph_context}")

    if qa_context:
        sys_prompt.append(f"【问答库】（检索结果）\n{qa_context}")

    if summary:
        sys_prompt.append(f"【对话摘要】（本会话此前的讨论要点）\n{summary}")

    if facts:
        sys_prompt.append(f"【长期记忆】（该学生此前说过的重要事实，跨会话有效）\n" + "\n".join(f"- {f}" for f in facts))

    if profile:
        sys_prompt.append(f"【学生画像】（该学生的学习特点）\n{profile}")

    system_prompt = "\n\n".join(sys_prompt)

    # 拼接消息 -- system + L1历史 + 当前问题
    # -- system
    messages = [SystemMessage(content=system_prompt)]
    # -- 历史上下文
    for msg in state.get("history", []):
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    # 当前问题
    messages.append(HumanMessage(content=question))

    # 生成回复
    llm = MyModel.get_model()
    result = llm.invoke(messages)
    print(f"【测试】知识点提问回复内容：{result}")

    # 更新状态
    return {
        "qa_context": qa_context,
        "cw_context": cw_context,
        "graph_context": graph_context,
        "script_context": script_context,
        "answer": result.content
    }



