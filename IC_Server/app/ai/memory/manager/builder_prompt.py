# 记忆 提示词组装

# 消息列表格式化
def format_messages(messages: list) -> str:
    """
    把消息列表格式化为提示词可读的字符串
    messages: [{"role": "user"|"assistant", "content": "..."}, ...]
    """
    return "\n".join(f"[{m['role']}] {m['content']}" for m in messages)
