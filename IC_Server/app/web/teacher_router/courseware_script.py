from fastapi import Request

class CoursewareScript:
    def __init__(self, request: Request, courseware_id, course_name, chapter_name) -> None:
        # 课件智能体（与解析共用同一个graph，走manager入口）
        self.agent = request.app.state.courseware_agent
        self.courseware_id = courseware_id
        self.course_name = course_name
        self.chapter_name = chapter_name

    async def get_script(self) -> dict:
        print("\n【测试】这里是 -- courseware_script_get.py")

        # 走管理节点：文件已存在直接返回，不存在则现场生成
        result = await self.agent.run_script(self.course_name, self.chapter_name, self.courseware_id)

        status = result.get('script_status')
        if status in ('exists', 'done'):
            return {
                "code": 200,
                "message": "获取授课脚本成功",
                "data": {
                    "content": result.get('script_content', ''),
                    "script_path": result.get('script_path', ''),
                    # 是否现场生成（前端据此弹"生成完成"提示；exists=文件已有则不弹）??????????????
                    "generated": status == 'done'
                }
            }
        if status == 'no_kp':
            # 知识点为空：课件从未解析过（或解析失败）
            return {"code": 400,
                    "message": "该课件尚未解析，请先点击\"处理\"完成课件解析",
                    "data": None}
        return {"code": 500, "message": "授课脚本获取失败", "data": None}
