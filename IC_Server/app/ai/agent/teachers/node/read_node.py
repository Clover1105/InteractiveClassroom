import os
import pythoncom
import win32com.client
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pathlib import Path
import pymupdf
from pptx import Presentation
from app.ai.agent.teachers.state.courseware_state import CoursewareState

_img_temp_dir = None
def img_temp(file_name):
    global _img_temp_dir
    if _img_temp_dir is None:
        # 创建临时目录存放提取的图片
        _img_temp_dir = Path(__file__).resolve().parents[5]  # 根目录
        _img_temp_dir = _img_temp_dir / 'static' / 'img' / f"{file_name}"
        _img_temp_dir.mkdir(parents=True, exist_ok=True)
    print(f"【测试】图片临时路径：{_img_temp_dir}")
    return _img_temp_dir

def extract_pptx(file_path, img_temp_dir):
    """提取 PPTX 文件的文本和图片（逐页）"""
    # 使用 python-pptx 库加载一个已有的 .pptx 文件，并返回一个 Presentation 对象，后续通过它来读取或修改 PPT 内容
    prs = Presentation(file_path)
    slide_contents = []
    extracted_images = []

    # prs.slides：获取 PPT 中所有幻灯片的列表 -- slide_num：当前页码；slide：当前页幻灯片对象
    for slide_num, slide in enumerate(prs.slides, 1):
        text = ""   # 当前页文本
        images = [] # 当前页图片

        # 每一个元素（文本框、图片、表格、图表等）在 python-pptx 里都叫 Shape（形状）
        # slide.shapes：获取当前页所有形状的列表 -- shape：当前形状对象
        for shape in slide.shapes:
            # 提取文本
            # .has_text_frame -- 判断这个形状是否包含文本框（文本框、标题框等才有）
            if shape.has_text_frame:
                # .paragraphs -- 获取文本框里的所有段落
                for paragraph in shape.text_frame.paragraphs:
                    # .text.strip() -- 获取段落的文本内容并去除首尾空白，过滤掉空行
                    if paragraph.text.strip():
                        # 将获取的非空文本加入 text 中
                        text += paragraph.text + "\n"

            # 提取图片 -- MSO_SHAPE_TYPE.PICTURE 是一个枚举值
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                # .image -- 只有在确认是图片形状后，才能安全地获取图片对象
                image_blob = shape.image.blob
                # .content_type -- 获取图片的 MIME 类型，比如 "image/png"、"image/jpeg"
                content_type = shape.image.content_type
                # 获取图片后缀
                ext = content_type.split('/')[-1]
                # 统一后缀
                if ext == 'jpeg':
                    ext = 'jpg'

                # 生成图片文件名 -- slide_当前页面_img_图片编号.后缀
                image_filename = f"slide_{slide_num}_img_{len(images)}.{ext}"
                # 拼接完整的保存路径
                image_path = os.path.join(str(img_temp_dir), image_filename)

                # 以二进制写入模式（'wb'）打开文件，把图片的二进制数据写进去，完成图片保存
                with open(image_path, 'wb') as f:
                    f.write(image_blob)

                images.append(image_path)
                extracted_images.append(image_path)

        # 每一页幻灯片的信息
        slide_contents.append({
            'page': slide_num,
            'text': text.strip(),
            'images': images
        })

    return slide_contents, extracted_images

def extract_pdf(file_path, img_temp_dir):
    """提取 PDF 文件的文本和图片（逐页）"""
    # 使用 PyMuPDF（fitz）库打开一个 PDF 文件，并返回一个 Document 对象，后续通过它来读取 PDF 的每一页内容
    doc = pymupdf.open(file_path)
    slide_contents = []
    extracted_images = []

    # 遍历页码，从0开始
    for page_num in range(len(doc)):
        # 获取当前这一页的 Page 对象
        page = doc[page_num]

        # 提取文本，去掉首尾空格
        text = page.get_text().strip()

        # 提取图片 -- 初始化容器
        images = []

        # full=True 表示返回完整信息（包括图片尺寸、颜色空间等）
        image_list = page.get_images(full=True)

        # 遍历当前页的每一张图片
        for img_idx, img in enumerate(image_list):
            # 取元组的第一个元素，即图片的 XREF（交叉引用编号），这是 PDF 内部对图片的唯一标识
            xref = img[0]
            # 根据 XREF 从整个文档中提取图片的完整数据，返回一个字典
            base_image = doc.extract_image(xref)
            # 从字典中取出 'image' 键对应的值，即图片的原始二进制数据
            image_bytes = base_image['image']
            # 从字典中取出 'ext' 键对应的值，即图片的文件扩展名
            image_ext = base_image['ext']

            # 生成图片文件名 -- page_当前页码_img_图片编号.后缀
            image_filename = f"page_{page_num + 1}_img_{img_idx}.{image_ext}"
            # 拼接完整的图片保存路径
            image_path = os.path.join(str(img_temp_dir), image_filename)

            with open(image_path, 'wb') as f:
                f.write(image_bytes)

            images.append(image_path)
            extracted_images.append(image_path)

        slide_contents.append({
            'page': page_num + 1,
            'text': text,
            'images': images
        })

    doc.close()
    return slide_contents, extracted_images

"""使用 libreoffice 将旧版 PPT 转换为 PPTX"""


def extract_ppt(file_path):
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 获取输出目录
    output_dir = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.pptx")

    # 初始化 COM 线程模型，解决 -2147221008 错误
    pythoncom.CoInitialize()

    try:
        # 调用 PowerPoint 应用程序进行转换
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        # 打开 ppt 文件
        presentation = powerpoint.Presentations.Open(file_path)
        # 24 是 PowerPoint 中代表 .pptx 格式的常量
        presentation.SaveAs(output_path, 24)
        presentation.Close()
        powerpoint.Quit()
        return output_path
    finally:
        # 确保无论是否报错，都释放 COM 资源，防止后台残留 PowerPoint 进程
        pythoncom.CoUninitialize()

def read_node(state:CoursewareState):
    print('\n【测试】这里是 -- read_node.py')
    print(f"【测试】状态：{state}")

    # 获取文件路径和基本信息
    file_path = state['courseware_path']
    file_ext = state['file_type']  # 后缀
    file_name = os.path.splitext(os.path.basename(file_path))[0]

    # 图片临时存储路径
    img_temp_dir = img_temp(file_name)

    # 根据文件格式选择提取方式
    # slide_contents = []
    # extracted_images = []

    if file_ext == '.pptx':
        slide_contents, extracted_images = extract_pptx(file_path, img_temp_dir)
    elif file_ext == '.ppt':
        # 旧版 PPT 先用 libreoffice 转成 PPTX，再按 PPTX 处理 -- (file_path, str(temp_dir))
        converted_path = extract_ppt(file_path)
        slide_contents, extracted_images = extract_pptx(converted_path, img_temp_dir)
    elif file_ext == '.pdf':
        slide_contents, extracted_images = extract_pdf(file_path, img_temp_dir)
    else:
        raise ValueError(f"不支持的文件格式: {file_ext}")

    # 4. 合并全文
    full_text = '\n'.join([slide['text'] for slide in slide_contents])

    print(f"【测试】提取完成: {len(slide_contents)}页, {len(extracted_images)}张图片")
    print(f"【测试】slide_contents 示例: {slide_contents[0] if slide_contents else '空'}")

    return {
        'file_type': file_ext.lstrip('.'),
        'extracted_text': full_text,
        'slide_contents': slide_contents,
        'extracted_images': extracted_images,
        'img_temp_dir': str(img_temp_dir)
    }

# if __name__ == '__main__':
#     img_temp_dir = Path(__file__).resolve().parents[5]  # 根目录
#     img_temp_dir = img_temp_dir / 'static' / 'img'
#     print(f"【测试】图片临时路径：{img_temp_dir}")