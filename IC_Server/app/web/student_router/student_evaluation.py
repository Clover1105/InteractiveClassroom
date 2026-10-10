"""
学生评价查看：读 static/evaluation/evaluation_{courseware_id}.md 最新内容
"""

from pathlib import Path

# 评价文档保存目录
eval_dir = Path(__file__).resolve().parents[3] / "static" / 'evaluation'

class StudentEvaluation:
    def __init__(self) -> None:
        pass

    # 读取最新评价
    def eval_last(self, courseware_id:int) -> dict:
        print(f"\n【测试】这里是 -- student_evaluation.py latest，课件：{courseware_id}")

        md_path = eval_dir / f"evaluation_{courseware_id}.md"

        if not md_path.exists():
            return {
                "code": 500,
                "message": "暂无评价，请先完成测试",
                "data": {"content": ""}
            }

        content = md_path.read_text(encoding="utf-8")
        return {
            "code": 200,
            "message": "获取评价成功",
            "data": {"content": content}
        }
