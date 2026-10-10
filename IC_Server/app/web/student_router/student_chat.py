"""
学生对话业务
职责：
  1. 用户消息、AI回复落库chat_history（所有模式都记录）
  2. 调用student_chat_graph流式生成回复
  3. 每轮结束后异步触发四层记忆更新
"""

import json
# 多线程模块，用来让程序里同时跑多个任务
import threading

from langgraph.errors import GraphRecursionError

from app.web.util.postgres_conn import PostgresConn
from app.web.schema.student_schema import ChatSchema
from app.ai.memory.manager.session_manager import SessionManager

from fastapi.responses import StreamingResponse
from fastapi import Request

class StudentChat:
    def __init__(self, request: Request, chat_schema: ChatSchema):
        # 学生对话智能体（main.py启动时创建，全项目共用一个）
        self.agent = request.app.state.student_agent    # 等价于 -- StudentChatGraph()
        # 获取全局PostgreSQL连接池
        self.pool = PostgresConn().get_pool()
        self.session_id = chat_schema.session_id
        self.user_id = chat_schema.user_id
        self.mode = chat_schema.mode
        self.course_name = chat_schema.course_name
        self.chapter_name = chat_schema.chapter_name
        self.question = chat_schema.question
        self.courseware_id = chat_schema.courseware_id

    # 保存一条消息到PG（历史记录）
    def _save_message(self, role, content):
        # 插入语句
        sql = '''
        INSERT INTO chat_history(session_id, user_id, mode, course_name, chapter_name, role, content)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        '''
        # 执行插入
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        sql,
                        (self.session_id, self.user_id, self.mode,self.course_name, self.chapter_name, role, content)
                    )
            print("【测试】插入数据成功")
        except Exception as e:
            print(f"【测试】保存消息失败: {e}")
            raise

    # 对话入口
    def chat(self):
        print("\n【测试】这里是 -- student_chat.py")
        print(f"【测试】会话：{self.session_id} | 用户：{self.user_id} | 模式：{self.mode}")

        # 获取历史上下文
        history = SessionManager.get_window(self.session_id,6)
        print(f"【测试】获取历史上下文：{history}")

        # 将当前问题存入库中
        self._save_message("user",self.question)

        # 拼接图的状态 -- 状态初始化
        state = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "mode": self.mode,
            "course_name": self.course_name,
            "chapter_name": self.chapter_name,
            "courseware_id": self.courseware_id,
            "question": self.question,
            "history": history,
            "qa_context": "",
            "cw_context": "",
            "graph_context": "",
            "answer": ""
        }

        # 返回结果
        return StreamingResponse(
            self.generate(state),
            media_type="text/event-stream"
        )

    # 流式执行graph：
    #   messages模式 —— 节点内LLM的token实时吐给前端（真流式）
    #   values模式   —— 每个节点执行后的完整state，用于拿到最终answer落库（占位节点没有LLM输出也能拿到）

    def generate(self,state):
        answer = ""

        # 只把这些业务节点里LLM产生的token推给前端（过滤manager等）
        all_nodes = ("normal", "knowledge")

        # "messages" 模式：
        #   -- 拦截图里所有 LLM 调用，把模型生成的 token 逐个流出来。
        #   -- 每个 chunk 是 (消息对象, 元数据)，元数据里包含 langgraph_node 字段，告诉你这个 token 是哪个节点产生的
        #   -- 专门用来做聊天逐字输出
        # "values" 模式：
        #   -- 每执行完一个节点，返回完整的状态快照（包含 session_id、question、answer、qa_context 等所有字段）
        #   -- 用来观察节点执行进度和状态变化。

        # recursion_limit=10 -- 递归超限保护（chat图最长链路为manager->业务节点共2步，10余量充足）

        try:
            result = self.agent.agent.stream(
                state,
                config={"recursion_limit": 10},
                stream_mode=["messages", "values"],
            )
            print(f'【测试】大模型输出结果：{result}')

            # 获取流式结果
            for stream_mode, data in result:
                if stream_mode == "messages":
                    chunk, meta = data
                    text = chunk.content
                    if text and meta.get("langgraph_node") in all_nodes:
                        yield f"data: {json.dumps({'content': text}, ensure_ascii=False)}\n\n"
                else:
                    # values：取最新一次的answer作为完整回复
                    if data.get("answer"):
                        answer = data["answer"]
        except GraphRecursionError:
            # 递归超限 -- 图执行次数超过recursion_limit，降级为友好提示语
            print("【测试】graph递归超限，已降级为提示语")
            answer = "抱歉，本轮对话处理异常，请稍后重试或换个说法。"
            yield f"data: {json.dumps({'content': answer}, ensure_ascii=False)}\n\n"
        except Exception as e:
            # 兜底异常 -- 图内LLM调用失败、节点执行异常等，降级为友好提示语
            print(f"【测试】graph执行异常，已降级为提示语: {e}")
            answer = "抱歉，AI回复生成失败，请稍后重试。"
            yield f"data: {json.dumps({'content': answer}, ensure_ascii=False)}\n\n"

        # 流式输出结束，落库AI回复
        self._save_message("assistant", answer)
        print(f"【测试】回复已生成并落库")

        # 触发四层记忆更新
        # 在对话的主线程之外，悄悄开启一个“后台小助手”，让记忆写入和更新的操作在后台默默运行，绝不拖慢给用户返回回答的速度
        try:
            # 创建后台线程
            threading.Thread(
                # 指定小助手的任务
                target=SessionManager.after_round,
                # 给小助手递参数
                args=(self.session_id, self.user_id, self.mode,
                      self.course_name, self.chapter_name,
                      state["question"], answer),
                # 设置为守护线程 -- 用户退出或主程序崩坏，“后台小助手”会立刻无条件跟着死掉
                daemon=True
            ).start()
            print("【测试】记忆更新任务已后台调度")
        except Exception as e:
            print(f"【测试】记忆调度启动失败: {e}")

        yield "data: end_end\n\n"