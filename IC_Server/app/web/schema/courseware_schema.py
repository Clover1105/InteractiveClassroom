from pydantic import BaseModel, Field

# 账号信息参数校验
class CoursewareSchema(BaseModel):
    original_filename: str = Field(..., description="课件原始名称")
    file_path: str = Field(..., description="课件在服务器的路径")
    course_name: str = Field(..., description="课程名")
    chapter_name: str = Field(..., description="章节名")
    id: int = Field(..., description="课件id")

# 单独生成授课脚本的参数
class ScriptGenerateSchema(BaseModel):
    courseware_id: int = Field(..., description="课件id")
    course_name: str = Field(..., description="课程名")
    chapter_name: str = Field(..., description="章节名")
