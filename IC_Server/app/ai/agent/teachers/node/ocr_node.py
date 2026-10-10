import os
# 使用 PaddleOCR 替代 pix2text，彻底摆脱 pix2text 的依赖链
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    PaddleOCR = None

from app.ai.agent.teachers.state.courseware_state import CoursewareState

# 全局OCR引擎实例（避免每次识别都重新加载模型）
_ocr_engine = None

def get_ocr_engine():
    """懒加载PaddleOCR引擎"""
    global _ocr_engine
    if _ocr_engine is None:
        if not PADDLEOCR_AVAILABLE:
            raise ImportError(
                "PaddleOCR 未安装，请执行: pip install paddleocr paddlepaddle"
            )
        # use_angle_cls=True 开启文字方向分类器（处理倾斜文字）
        # det_db_box_thresh=0.3 降低检测阈值，提高召回率
        # use_gpu=False 强制CPU模式，避免CUDA版本冲突
        _ocr_engine = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            det_db_box_thresh=0.3,
            device='CPU',
        )
    return _ocr_engine

def ocr_node(state:CoursewareState):
    print('\n【测试】这里是 -- ocr_node.py')
    print(f"【测试】状态：{state}")

    # 页面信息
    slide_contents = state.get('slide_contents', [])
    # 识别结果
    ocr_results = []

    if not slide_contents:
        print("【测试】没有课件内容，跳过 OCR")
        return {
            'ocr_status': 'done',
            'ocr_text': ""
        }

    # 获取OCR引擎
    try:
        ocr_engine = get_ocr_engine()
    except ImportError as e:
        print(f"【测试】PaddleOCR 初始化失败: {e}")
        print("【测试】请执行: pip install paddleocr paddlepaddle")
        return {
            'ocr_status': 'error',
            'ocr_text': f'PaddleOCR未安装: {e}'
        }

    for slide in slide_contents:
        page_num = slide['page']
        images = slide.get('images', [])
        if not images:
            continue

        for img_path in images:
            print(f"【测试】正在识别: 第{page_num}页 - {os.path.basename(img_path)}")
            try:
                # PaddleOCR 返回结构: [[box, (text, confidence)], ...]
                result = ocr_engine.ocr(img_path, cls=True)

                # 提取文本内容
                texts = []
                if result and result[0]:
                    for line in result[0]:
                        # line 结构: [[x1,y1],[x2,y2],[x3,y3],[x4,y4], (text, confidence)]
                        text = line[1][0]
                        texts.append(text)

                ocr_text = '\n'.join(texts) if texts else ''

                ocr_results.append({
                    'page': page_num,
                    'image_path': img_path,
                    'ocr_text': ocr_text
                })
                print(f"【测试】识别结果(前100字): {ocr_text[:100]}...")
            except Exception as e:
                print(f"【测试】识别失败: {img_path}, 错误: {e}")
                ocr_results.append({
                    'page': page_num,
                    'image_path': img_path,
                    'ocr_text': f'[OCR失败: {e}]'
                })

    print(f"【测试】OCR 完成，共识别 {len(ocr_results)} 张图片")

    return {
        'ocr_text': ocr_results,
        'ocr_status': 'done',
    }