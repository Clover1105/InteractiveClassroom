import asyncio
from pathlib import Path
from fastapi import Request
from app.web.schema.courseware_schema import CoursewareSchema

from app.web.tool.mysql_update_tool import MySQLUpdate

class CourseWareParse:
    def __init__(self,request:Request,courseware_schema:CoursewareSchema) -> None:
        # 课件智能体
        self.agent = request.app.state.courseware_agent
        # 获取课件信息
        self.save_path = courseware_schema.file_path
        self.course_name = courseware_schema.course_name
        self.chapter_name = courseware_schema.chapter_name
        self.filename = courseware_schema.original_filename
        self.id = courseware_schema.id
        # 修改课件解析状态
        self.mysql_update = MySQLUpdate()
        self.sql_update = "update courseware set parse_status=%s where id=%s"

    # 查找课件信息
    def _get_file(self) -> dict:
        # 获取文件在服务器上的绝对路径（供后续智能体使用）
        # .resolve() -- 把路径解析成绝对路径，同时会解析符号链接（软链接），返回一个新的 Path 对象
        abs_path = str(Path(self.save_path).resolve())
        file_ext = Path(self.save_path).suffix

        print(f"【测试】文件接收成功：{abs_path}")
        print(f"【测试】课程：{self.course_name} | 章节：{self.chapter_name}")

        return {
            "filename": self.filename,
            "saved_path": abs_path,
            "course_name": self.course_name,
            "chapter_name": self.chapter_name,
            "file_ext":file_ext,
            "id": self.id,
        }

    async def parse_courseware(self) -> dict:
        result_file = self._get_file()
        print(f"【测试】获取课件信息结果：{result_file}")

        # 状态 2"未处理"立即置为 0"处理中"
        self.mysql_update.update_parse_status(self.sql_update, 0, self.id)

        # 后台任务：跑完更新状态（成功：1，失败：3）
        asyncio.create_task(self._run_and_update(result_file))

        return {
            "code":200,
            "message":"课件开始处理",
        }

    async def _run_and_update(self, result_file) -> None:
        try:
            await self.agent.run(result_file)
            self.mysql_update.update_parse_status(self.sql_update, 1, self.id)
            print(f"【测试】课件 {self.filename} 处理完成")
        except Exception as e:
            print(f"【测试】课件处理失败: {e}")
            self.mysql_update.update_parse_status(self.sql_update, 3, self.id)