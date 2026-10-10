"""
课件流程管理节点（统一入口）
职责：根据 mode 字段决定流程走向
  - mode=parse  ：进入课件解析流程（read→ocr→parse→vectorize）
  - mode=script ：查看授课脚本——文件已存在则读出内容直接结束；
                  不存在则交给 script 节点生成
"""
from app.ai.agent.teachers.state.courseware_state import CoursewareState
from app.ai.agent.teachers.node.script_node import MD_DIR


"""条件路由：根据 mode 和 script_status 决定下一个节点"""
def route_manager(state: CoursewareState):
    mode = state.get('mode', 'parse')
    if mode == 'script':
        # 脚本已存在：manager 已读出内容，直接结束
        if state.get('script_status') == 'exists':
            return 'end'
        # 脚本不存在：进入脚本生成节点
        return 'script'
    # 解析课件：进入read节点
    return 'read'


def manager_node(state: CoursewareState):
    print('\n【测试】这里是 -- teacher/manager_node.py')
    mode = state.get('mode', 'parse')
    print(f"【测试】当前模式: {mode}")

    if mode == 'script':
        # 查看脚本：先看文件是否已生成
        courseware_id = state.get('courseware_id', 0)
        script_path = MD_DIR / f"script_{courseware_id}.md"

        if script_path.exists():
            print(f"【测试】脚本已存在，直接返回: {script_path}")
            content = script_path.read_text(encoding='utf-8')
            return {
                "script_status": "exists",
                "script_content": content,
                "script_path": str(script_path)
            }

        print("【测试】脚本不存在，进入脚本生成节点")
        return {"script_status": "pending"}

    # 解析课件模式：不需要做什么，交给路由去 read 节点
    print("【测试】进入课件解析流程")
    return {}