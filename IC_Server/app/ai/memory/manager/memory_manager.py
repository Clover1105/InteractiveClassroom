# 记忆更新调度

"""
记忆更新调度器
每轮对话结束后被调用，按策略决定是否触发长期/摘要/画像更新
四层结构：
  L1 窗口：只读，web 层 get_window 直接用，本模块不更新
  L2 摘要：count > 6 后每轮更新（只覆盖窗口外旧消息）
  L3 长期：每轮抽取本轮事实，写 long_memory 表
  L4 画像：count > 6 且有 course_name 时，从 L3 全部事实提炼
"""

from app.ai.memory.save import window_memory, summary_memory, profile_memory, long_memory
from app.ai.memory.retrieval import summary_agent, profile_agent, long_agent

# 窗口大小（chat_history 计数超过它后，每轮触发摘要/画像更新）
window_size = 6

def after_round(
        session_id: str,
        user_id: str,
        mode: str,
        course_name: str,
        chapter_name: str,
        question: str,
        answer: str
) -> None:
    try:
        # L3 每轮抽取本轮事实写入长期记忆（画像素材也依赖它）
        facts = long_agent.extract(question, answer)    # 调用大模型获取需要记忆的事实
        # 有则加入长期记忆数据表
        if facts:
            long_memory.add(user_id, facts) # 调用添加方法，批量追加

        # 获取当前会话累计消息数 -- 大于6条触发摘要记忆
        count = summary_memory.count(session_id)    # 摘要

        # L2 摘要：count 超过窗口后每轮更新
        if count > window_size:
            # 需要摘要的条数
            older_count = count - window_size
            # 获取窗口外的旧消息，即需要摘要的消息 -- OFFSET跳过n条
            older_messages = window_memory.read(session_id, older_count,offset=window_size)
            # 获取当前会话已经有了的摘要
            old_summary = summary_memory.read(session_id) or ""
            # 生成新的摘要
            new_summary = summary_agent.regenerate(old_summary, older_messages)
            # 写入新的摘要
            summary_memory.write(session_id, new_summary)
            print(f"【测试】L2 摘要已更新（session={session_id}，count={count}）")

        # L4 画像：从 L3 全部长期事实提炼（不再是窗口消息）
        if count > window_size and course_name:
            # 获取当前画像
            old_profile = profile_memory.read(user_id, course_name)
            # 取该用户全部长期记忆
            all_facts = long_memory.list(user_id)
            if all_facts:
                # 生成新的画像
                new_profile = profile_agent.regenerate(old_profile, all_facts)
                # 写入新的画像
                profile_memory.write(user_id, course_name, new_profile)
                print(f"【测试】L4 画像已更新（user={user_id}, course={course_name}）")
    except Exception as e:
        print(f"【测试】记忆更新失败（不影响对话）: {e}")

