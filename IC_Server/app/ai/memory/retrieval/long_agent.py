# 长期事实抽取

"""
L3 长期记忆抽取器
每轮对话结束后，从本轮 question/answer 中抽取值得长期记住的用户事实
"""

import json

from app.ai.model.my_model import MyModel
from app.ai.prompt.builder_prompt import BuilderPromptYaml

def extract(question: str, answer: str) -> list:
    prompt = BuilderPromptYaml.get_prompt(
        "long_agent.yaml",
        question=question or "（无）",
        answer=answer or "（无）"
    )
    result = MyModel.get_model().invoke(prompt)
    r = result.content.strip()

    # 去除 Markdown 代码块标记
    if r.startswith("```"):
        r = r.split("```", 2)[1]
        if r.startswith("json"):
            r = r[4:]
        r = r.strip().rstrip("`").strip()

    try:
        l = []
        facts = json.loads(r)
        if isinstance(facts, list):
            for f in facts:
                if str(f).strip():
                    l.append(str(f).strip())
        else:
            return []
        return l
    except Exception:
        print(f"【测试】L3 -- 事实解析失败，本轮跳过: {r[:100]}")
        return []
