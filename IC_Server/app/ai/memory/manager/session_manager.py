# 会话管理器

"""
会话记忆（web 层和后续 knowledge_node 都从这里进）
"""
from app.ai.memory.save import window_memory, summary_memory, long_memory, profile_memory
from app.ai.memory.manager import memory_manager

# 对外暴露的四层记忆统一入口 -- 静态方法
class SessionManager:
    # L1 -- 当前轮上下文
    @staticmethod
    def get_window(session_id: str, n: int = 6) -> list:
        try:
            return window_memory.read(session_id,n)
        except Exception as e:
            # 失败降级为空列表，等价于首轮对话
            print(f"【测试】L1 -- 读取失败，降级为空上下文: {e}")
            return []

    # L2 -- 会话摘要
    @staticmethod
    def get_summary(session_id: str) -> str:
        try:
            return summary_memory.read(session_id)
        except Exception as e:
            # 失败降级为空串，等价于本会话无摘要
            print(f"【测试】L2 -- 读取失败，降级为无摘要: {e}")
            return ""

    # L3 -- 长期记忆（该用户的全部长期事实）
    @staticmethod
    def get_facts(user_id: str) -> list:
        try:
            return long_memory.list(user_id)
        except Exception as e:
            # 失败降级为空列表，等价于无长期记忆
            print(f"【测试】L3 -- 读取失败，降级为无长期记忆: {e}")
            return []


    # L4 -- 学生画像
    @staticmethod
    def get_profile(user_id: str, course_name: str) -> str:
        print("\n【调试】L4 -- 开始获取画像")
        try:
            return profile_memory.read(user_id, course_name)
        except Exception as e:
            # 失败降级为空串，等价于无画像
            print(f"【测试】L4 -- 读取失败，降级为无画像: {e}")
            return ""

    # 调度 -- 每轮结束后后台调用，开始写入与更新记忆
    # memory_manager.after_round 内部已有整体 try/except，记忆更新失败不影响对话
    @staticmethod
    def after_round(
            session_id: str,
            user_id: str,
            mode: str,
            course_name: str,
            chapter_name: str,
            question: str,
            answer: str
    ) -> None:
        memory_manager.after_round(
            session_id, user_id, mode,
            course_name, chapter_name,
            question, answer
        )
