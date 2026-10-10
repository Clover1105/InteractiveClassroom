"""
评价节点：把 finish_node 生成的 Markdown 落盘到 static/evaluation/evaluation_{courseware_id}.md
与教师端 script_node 的路径常量计算风格一致
"""
from pathlib import Path

from app.ai.agent.student.state.test_state import TestState

# 评价文档保存目录
eval_dir = Path(__file__).resolve().parents[5] / "static" / 'evaluation'

def evaluation_node(state:TestState) -> dict:
    print("\n【测试】这里是 -- student/evaluation_node.py")

    # 确定目录真实存在
    eval_dir.mkdir(parents=True,exist_ok=True)

    # 基本信息
    courseware_id = state["courseware_id"]
    md_path = eval_dir / f"evaluation_{courseware_id}.md"

    # 写入报告（覆盖，只取最新的一版）
    md_path.write_text(state["evaluation_md"], encoding="utf-8")
    print(f"【测试】点评报告已落盘: {md_path}")

    # 更新状态
    return {
        "evaluation_path": str(md_path)
    }

