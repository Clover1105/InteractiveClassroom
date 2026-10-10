# 画像提取（结构化输出）

"""
L4 画像更新器
根据 L3 长期记忆事实 + 原画像，由 LLM 生成更新后的学生画像（JSON 格式）
"""

from app.ai.model.my_model import MyModel
from app.ai.prompt.builder_prompt import BuilderPromptYaml

def regenerate(old_profile: str, facts: list) -> str:
    # 组装 prompt --  -- 画像素材改为 L3 长期记忆事实
    prompt = BuilderPromptYaml.get_prompt(
        "profile_agent.yaml",
        old_profile=old_profile or "（无）",
        facts="\n".join(f"- {f}" for f in facts) if facts else "（暂无）"
    )
    # 调用LLM生成新画像
    result = MyModel.get_model().invoke(prompt)
    return result.content.strip()
