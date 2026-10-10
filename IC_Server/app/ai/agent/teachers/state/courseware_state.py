from typing_extensions import TypedDict

"""
课件节点状态
"""

class CoursewareState(TypedDict):
    # 课件文件在服务器上的绝对路径
    courseware_path: str

    # 课程名称（从上传表单传入）
    course_name: str

    # 章节名称（从上传表单传入）
    chapter_name: str

    # 解析状态标记：pending(待处理) / parsing(处理中) / done(已完成) / failed(失败)
    parse_status: str

    # 文件格式标记：ppt / pptx / pdf
    file_type: str

    # 提取的课件文本内容（全文合并）
    extracted_text: str

    # 按页组织的文本内容：[{"page": 1, "text": "...", "images": ["path1", "path2"]}, ...]
    slide_contents: list[dict]

    # 提取的图片路径列表
    extracted_images: list[str]

    # 临时目录路径（存放提取的图片等中间文件）
    img_temp_dir: str

    # OCR 识别后的文本内容（公式已转 LaTeX）
    ocr_text: str

    # OCR 状态标记：pending / done / failed
    ocr_status: str

    # 向量化状态标记：pending / done / failed
    vectorize_status: str

    # 课件在MySQL中的记录id（用于脚本文件命名）
    courseware_id: int

    # 授课脚本的保存路径
    script_path: str

    # 管理节点的路由决策：generate / skip
    script_mode: str

    # 流程模式标记：parse(解析课件) / script(查看/生成授课脚本)
    mode: str

    # 授课脚本状态标记：pending / exists / done / no_kp / failed
    script_status: str

    # 授课脚本文本内容（manager读文件 或 script节点生成后，放入state供接口返回）
    script_content: str

