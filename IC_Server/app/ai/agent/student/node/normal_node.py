from app.ai.agent.student.state.student_state import StudentState
from app.ai.model.my_model import MyModel
from app.ai.prompt.builder_prompt import BuilderPromptYaml
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.ai.memory.manager.session_manager import SessionManager



# 普通对话节点：不检索任何数据集，直接结合历史多轮回答
def normal_node(state:StudentState) -> dict:
    print("\n【测试】这里是 -- student/normal_node.py")

    # 读 L2 摘要 / L3 长期记忆 / L4 画像（normal 模式可能没有 course_name，profile 自动降级为空）
    summary = SessionManager.get_summary(state["session_id"])
    course_name = state.get("course_name", "")
    facts = SessionManager.get_facts(state["user_id"])  # l3
    profile = SessionManager.get_profile(state["user_id"], course_name) if course_name else ""

    # 提示词
    system_prompt = BuilderPromptYaml.get_prompt(
        'normal_node.yaml',
        summary=summary or "（暂无）",
        facts="\n".join(f"- {f}" for f in facts) if facts else "（暂无）",
        profile=profile or "（暂无）",
    )


    # 拼接消息 -- system + 历史对话 + 当前问题
    # system
    messages = [SystemMessage(content=system_prompt)]
    # 历史对话
    for msg in state.get("history",[]):
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    # 当前问题
    messages.append(HumanMessage(content=state["question"]))

    # 生成回复
    llm = MyModel.get_model()
    result = llm.invoke(messages)
    print(f"【测试】普通对话回复内容：{result}")

    return {"answer":result.content}
