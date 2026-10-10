from typing import TypedDict, List

# 用 total=False，所有字段都是可选的——未注入时为缺失键而不是默认值
class TestState(TypedDict,total=False):
    # 基础上下文
    session_id: str # 会话id
    user_id: str    # 用户标识（名称）
    courseware_id: int  # 课件id
    course_name: str    # 课程名
    chapter_name: str   # 章节名

    # mode 分流 -- start 出题 / finish 收卷
    mode: str

    # start 阶段输出
    questions: List[dict]   # [{"qno":1, "content":"..."}, ...] 共10题

    # finish 阶段输入/输出
    qa_pairs: List[dict]  # [{"qno":1, "question":"...", "answer":"..."}, ...]
    evaluation_md: str  # 最终点评报告内容（Markdown）
    evaluation_path: str  # 落盘路径（前端不可见，便于调试）