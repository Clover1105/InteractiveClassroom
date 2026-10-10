# 摘要提取

"""
L2 摘要生成器
根据对话历史 + 原摘要，生成新的会话摘要
"""

from app.ai.model.my_model import MyModel
from app.ai.prompt.builder_prompt import BuilderPromptYaml
from app.ai.memory.manager.builder_prompt import format_messages

# 生成新摘要，覆盖旧摘要
def regenerate(old_summary: str, older_messages: list) -> str:
    # 组装 prompt
    prompt = BuilderPromptYaml.get_prompt(
        "summary_agent.yaml",
        old_summary=old_summary or "（无）",
        older_messages=format_messages(older_messages)
    )
    # 调用LLM生成新摘要
    result = MyModel.get_model().invoke(prompt)
    return result.content.strip()