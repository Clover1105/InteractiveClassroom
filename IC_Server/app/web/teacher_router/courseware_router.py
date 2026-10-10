from fastapi import APIRouter, UploadFile, File, Form, Query, Request, Depends

# 路由
courseware_router = APIRouter()

# 角色权限中间件
from app.web.util.jwt_decode import is_roles

# 上传课件接口 -- 仅教师
from app.web.teacher_router.courseware_upload import CoursewareUpload

@courseware_router.post(
    path="/upload",
    summary="上传课件"
)
async def upload(
        file: UploadFile = File(..., description="课件文件"),
        course_name: str = Form(..., description="课程名称"),
        chapter_name: str = Form(..., description="章节名称"),
        now_user: dict = Depends(is_roles(["teacher"]))
):
    print("\n【测试】这里是 -- courseware_router.py")
    form_data = {
        "course_name": course_name,
        "chapter_name": chapter_name
    }
    return await CoursewareUpload(file,form_data).save_courseware()



# 获取课件信息列表接口 -- 共用
from app.web.teacher_router.courseware_get import CoursewareGet

@courseware_router.get(
    path='/list',
    summary="获取课件列表"
)
def get_list(now_user: dict = Depends(is_roles(["teacher", "student"]))):
    print("\n【测试】这里是 -- courseware_router.py")
    return CoursewareGet().get_cur_list()



# 解析课件接口 -- 仅教师
from fastapi import Request
from app.web.schema.courseware_schema import CoursewareSchema
from app.web.teacher_router.courseware_parse import CourseWareParse

@courseware_router.post(
    path="/parse",
    summary="解析课件"
)
async def parse(request: Request,courseware_schema:CoursewareSchema,now_user: dict = Depends(is_roles(["teacher"]))):
    print("\n【测试】这里是 -- courseware_router.py")
    return await CourseWareParse(request,courseware_schema).parse_courseware()

# 生成脚本接口 -- 共用
from fastapi import Query
from app.web.teacher_router.courseware_script import CoursewareScript

@courseware_router.get(
    path="/script",
    summary="获取授课脚本")
async def get_script(
        request: Request,
        courseware_id: int = Query(..., description="课件id"),
        course_name: str = Query(..., description="课程名"),
        chapter_name: str = Query(..., description="章节名"),
        now_user: dict = Depends(is_roles(["teacher", "student"]))
):
    print("\n【测试】这里是 -- courseware_router.py")
    return await CoursewareScript(request, courseware_id, course_name, chapter_name).get_script()


# 删除课件接口（级联删除该课件所有数据） -- 仅教师
from app.web.teacher_router.courseware_delete import CoursewareDelete
@courseware_router.post(
    path="/delete",
    summary="删除课件（级联删除解析数据、向量、脚本等）"
)
def delete_courseware(courseware_schema: CoursewareSchema, now_user: dict = Depends(is_roles(["teacher"]))):
    print("\n【测试】这里是 -- courseware_router.py")
    return CoursewareDelete(courseware_schema).delete_courseware()


# 删除授课脚本接口（重新生成 = 先删后调script接口） -- 仅教师
from app.web.schema.courseware_schema import ScriptGenerateSchema
from app.web.teacher_router.courseware_script_delete import CoursewareScriptDelete
@courseware_router.post(
    path="/script/delete",
    summary="删除授课脚本"
)
def delete_script(script_schema: ScriptGenerateSchema, now_user: dict = Depends(is_roles(["teacher"]))):
    print("\n【测试】这里是 -- courseware_router.py")
    return CoursewareScriptDelete(script_schema).del_script()

