from pathlib import Path

from app.web.schema.courseware_schema import ScriptGenerateSchema

# 获取脚本目录
script_dir = Path(__file__).resolve().parents[3] / "static" / "md"

class CoursewareScriptDelete:
    def __init__(self, schema: ScriptGenerateSchema) -> None:
        self.courseware_id = schema.courseware_id

    def del_script(self) -> dict:
        print("\n【测试】这里是 -- courseware_script_delete.py")

        path = script_dir / f"script_{self.courseware_id}.md"
        existed = path.exists()  # 判断文件是否存在
        path.unlink(missing_ok=True)    # 删除文件，如果文件不存在则不报错
        if existed:
            print(f"【测试】授课脚本已删除: {path}")
            return {"code": 200, "message": "授课脚本已删除"}
        print(f"【测试】授课脚本本就不存在: {path}")
        return {"code": 200, "message": "该课件暂无授课脚本"}


