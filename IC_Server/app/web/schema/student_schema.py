from pydantic import BaseModel, Field
from typing import List

# 学生对话参数
class ChatSchema(BaseModel):
    session_id: str = Field(..., description="会话id")
    user_id: str = Field(..., description="学生标识（用户名）")
    mode: str = Field(..., description="对话模式：normal/qa")
    course_name: str = Field(default="", description="课程名")
    chapter_name: str = Field(default="", description="章节名")
    question: str = Field(..., description="学生问题")
    courseware_id: int = Field(default=0, description="课件id")

# 开始测试请求体
class TestStartSchema(BaseModel):
    session_id: str = Field(..., description="会话id")
    user_id: str = Field(..., description="学生标识（用户名）")
    courseware_id: int = Field(..., description="课件id")
    course_name: str = Field(default="", description="课程名")
    chapter_name: str = Field(default="", description="章节名")

# 收卷请求体
class TestFinishSchema(BaseModel):
    session_id: str = Field(..., description="会话id")
    user_id: str = Field(..., description="学生标识（用户名）")
    courseware_id: int = Field(..., description="课件id")
    course_name: str = Field(default="", description="课程名")
    chapter_name: str = Field(default="", description="章节名")
    questions: List[str] = []
    answers: List[str] = []