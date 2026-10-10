from fastapi import HTTPException, UploadFile
from pathlib import Path
import uuid
from fastapi.responses import JSONResponse
from app.web.tool.mysql_insert_tool import MySQLInsert

class CoursewareUpload:
    def __init__(self,file,form_data) -> None:
        print("\n【测试】这里是 -- courseware_upload.py")

        # 数据库插入对象
        self.mysql_insert = MySQLInsert()

        # 获取上传的文件
        self.file = file
        self.course_name = form_data['course_name']
        self.chapter_name = form_data['chapter_name']

        # 定义文件保存路径（使用绝对路径，避免运行目录变化导致出错）
        self.base_dir = Path(__file__).resolve().parents[3]  # 获取 IC_Server 项目根目录
        self.save_dir = self.base_dir / "data" / "data_download"  # 获取课件存储目录
        self.save_dir.mkdir(parents=True, exist_ok=True)    # 如果目录不存在，自动创建

        # 定义允许上传的文件类型和最大限制（100MB）
        self.allowed_extensions = {".ppt", ".pptx", ".pdf"}  # 允许的文件类型
        self.max_size = 100 * 1024 * 1024  # 最大文件大小（100MB）

        # 测试
        print(f"【测试】上传的文件为: {self.file}")
        print(f"【测试】存储到目录: {self.save_dir}")

        # 生成唯一的文件名、保存路径、后缀
        self.only_filename,self.save_path,self.file_ext = self.get_only_name()

    def get_only_name(self) -> tuple:
        #  校验文件扩展名 -- 获取后缀，转为小写
        file_ext = Path(self.file.filename).suffix.lower()
        print(f"【测试】获取文件扩展名: {file_ext}")

        # 判断文件格式是否正确
        if file_ext not in self.allowed_extensions:
            # 主动抛出一个 HTTP 异常 -- 文件格式不对
            raise HTTPException(status_code=400, detail="仅支持 .ppt, .pptx, .pdf 格式的文件")

        # 生成唯一的文件名（防止重名覆盖，也方便后续数据库管理）
        only_filename = f"{uuid.uuid4().hex}{file_ext}"
        save_path = self.save_dir / only_filename

        # 返回结果
        return only_filename,save_path,file_ext

    # 分块读取并保存文件（防止大文件占满服务器内存）
    async def save_courseware(self) -> JSONResponse:
        try:
            # 前置预判：如果前端传来了文件大小，先直接检查一遍
            if self.file.size is not None and self.file.size > self.max_size:
                raise HTTPException(status_code=400, detail="文件大小不能超过 100MB")

            # 然后再执行边读边写的逻辑（作为双重保险）
            total_size = 0
            with open(self.save_path, "wb") as buffer:
                # := 是“海象运算符” -- 一边读取数据赋值给变量 chunk，一边判断 chunk 是否为空
                # 如果读取到了数据，条件为真，进入循环；如果读取完毕（返回空），条件为假，自动跳出循环
                while chunk := await self.file.read(1024 * 1024):  # 每次读 1MB
                    total_size += len(chunk)
                    if total_size > self.max_size:
                        # 如果超出大小，关闭并删除临时文件
                        buffer.close()  # 手动_提前_强制关闭
                        # unlink() 会删除这个临时文件
                        # missing_ok=True 是一个容错参数，意思是：如果因为某些极端原因该路径下原本就没有文件，删除时也不会报错
                        self.save_path.unlink(missing_ok=True)
                        raise HTTPException(status_code=400, detail="文件大小不能超过 100MB")
                    # 没有异常，安全写入
                    buffer.write(chunk)
            print("【测试】文件保存成功")

            result_save = self.save_mysql()
            print(f"【测试】数据库保存结果：{result_save}")

            return JSONResponse({
                "code": 200,
                "message": "文件上传成功",
            })
        except HTTPException:
            raise  # 重新抛出我们手动抛出的异常
        except Exception as e:
            print(f"【测试】文件保存失败: {e}")
            # 如果发生其他IO异常（不管是文件保存失败还是数据库写入失败），都要尝试清理临时文件
            if self.save_path.exists(): # 判断存储路径是否存在，存在则删除该临时文件
                self.save_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    def save_mysql(self) -> dict:
        sql_insert = f"insert into courseware values(null,%s,%s,%s,%s,%s,now(),%s,%s,%s)"
        file_size = self.file.size if self.file.size is not None else 0
        result = self.mysql_insert.insert_courseware(sql_insert, self.file.filename,self.only_filename,self.save_path,self.course_name,self.chapter_name,file_size,self.file_ext)
        print("\n【测试】这里是 -- courseware_upload.py")
        print(f"【测试】课件存储到数据库结果：{result}")
        return result
