from typing import TypedDict, List

# 学生对话图的状态
class StudentState(TypedDict):
    # 会话基础信息（由web层组装传入）
    session_id: str      # 会话id（前端生成，同一会话内不变）
    user_id: str         # 学生id
    mode: str            # 对话模式：normal普通/course课程/qa知识点
    course_name: str     # 课程名
    chapter_name: str     # 章节名
    question: str        # 学生当前提问
    courseware_id: int  # 课件id

    # 多轮上下文（web层从chat_history表取最近几轮传入，后续由四层记忆模块接管）
    history: List[dict]  # [{"role": "user"|"assistant", "content": "..."}]

    # 各节点产出
    qa_context: str      # 问答库检索内容（course/knowledge节点）
    cw_context: str     # 课件库检索内容（knowledge节点）
    graph_context: str  # Neo4j知识点结构清单（knowledge节点）
    script_context: str  # 授课脚本内容（knowledge节点，源4）
    answer: str  # 最终回答
