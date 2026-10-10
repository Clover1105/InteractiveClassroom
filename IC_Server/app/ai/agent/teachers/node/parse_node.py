"""
课件内容解析节点
职责：
  1. 合并每页文本（原文 + OCR识别结果）
  2. 调用LLM进行结构化解析，提取知识点
  3. 将结构化数据写入Neo4j知识图谱
"""
import os
import json
from app.ai.model.my_model import MyModel
from app.ai.util.neo4j_util import Neo4jConn
from app.ai.agent.teachers.state.courseware_state import CoursewareState

# 读取外部提示词配置文件
from app.ai.prompt.builder_prompt import BuilderPromptYaml

llm = MyModel.get_model()
neo4j = Neo4jConn().get_neo4j_conn()

"""合并每页文本：原文本 + OCR识别结果"""
def _merge_content(slide_contents,ocr_results):
    # 构建OCR结果字典：page_num -> ocr_text
    ocr_dict = {}
    # 判断 ocr 节点的返回结果 self.ocr_results 是不是列表类型
    if isinstance(ocr_results, list):
        for item in ocr_results:
            # 获取图片对应页码
            page = item.get('page')
            if page:
                # 添加字典元素 -- {页码：识别内容}
                # 一页有多个图片时，用换行符拼接，避免覆盖
                existing = ocr_dict.get(page, '')   # 判断该页面是否有图片已经添加了
                current_text = item.get('ocr_text', '') # 获取当前图片的文本
                if existing and current_text:
                    ocr_dict[page] = existing + '\n' + current_text
                elif current_text:
                    ocr_dict[page] = current_text

    # 初始化合并结果列表 -- 存储合并后的每页内容
    merged = []

    # 遍历每一页的文本
    for slide in slide_contents:
        # 获取本页信息
        page_num = slide['page']
        original_text = slide.get('text', '')
        ocr_text = ocr_dict.get(page_num, '')

        # 合并文本
        if ocr_text:
            if original_text:
                combined = original_text + '\n' + ocr_text
            else:
                combined = ocr_text
        else:
            combined = original_text

        if combined:
            lines = combined.split('\n')
            # #过滤掉LaTeX公式标记行（$$...$$）但保留有实际内容的行
            cleaned_lines = [l for l in lines if not l.strip().startswith('$$') or len(l.strip()) > 20]
            combined = '\n'.join(cleaned_lines)

        merged.append({
            'page': f"【第{page_num}页】",
            'text': combined.strip()
        })

    return merged


"""调用LLM并解析返回的JSON知识点"""
def _invoke_and_parse(llm, prompt):
    print(f'\n【调试】Prompt总长度: {len(prompt)} 字符')
    print(f'\n【测试】正在调用LLM解析课件内容...')
    response = llm.invoke(prompt)
    llm_text = response.content

    try:
        # 去除可能的markdown标记
        llm_text = llm_text.strip()
        if llm_text.startswith('```'):
            parts = llm_text.split('```')
            llm_text = parts[1]
            if llm_text.startswith('json'):
                llm_text = llm_text[4:]
        llm_text = llm_text.strip()

        result = json.loads(llm_text)
        kps = result.get('knowledge_points', [])
        print(f'【测试】本块LLM解析完成，提取 {len(kps)} 个知识点')
        return kps
    except json.JSONDecodeError as e:
        print(f'【测试】LLM返回的JSON解析失败: {e}')
        print(f'【测试】原始返回: {llm_text[:500]}')
        return []
    except Exception as e:
        print(f'【测试】LLM调用异常: {e}')
        return []

"""调用LLM进行结构化解析（分块：长课件拆成多次调用，避免LLM概括性总结导致知识点大量丢失）"""
def _parse_with_llm(llm, prompt_template, merged_pages):# merged_pages -- 合并页面
    CHUNK_SIZE = 12  # 每块页数，78页约7次调用；可按效果调整
    all_kps = []
    total_chunks = (len(merged_pages) + CHUNK_SIZE - 1) // CHUNK_SIZE

    for i in range(0, len(merged_pages), CHUNK_SIZE):
        chunk = merged_pages[i:i + CHUNK_SIZE]  # 切片
        chunk_text = '\n'.join([f"{p['page']}\n{p['text']}" for p in chunk])     # 遍历当前块的每个页面 -- 页码\n文本内容

        # 把当前块的文本注入提示词模板的 $content 占位
        prompt = prompt_template.replace('$content', chunk_text)

        print(f"\n【测试】===== 正在解析第 {i // CHUNK_SIZE + 1}/{total_chunks} 块"
                  f"（{chunk[0]['page']} ~ {chunk[-1]['page']}）=====")

        kps = _invoke_and_parse(llm, prompt)
        all_kps.extend(kps) # 把每块的结果累加

    # 按name去重（不同块之间LLM可能重复提取同一概念）
    seen = set()    # 集合，去重
    unique_kps = []
    for kp in all_kps:
        name = kp.get('name', '')
        if name and name not in seen:
            seen.add(name)
            unique_kps.append(kp)

    print(f'【测试】分块解析完成，共提取 {len(all_kps)} 个，去重后 {len(unique_kps)} 个知识点')
    for kp in unique_kps:
        print(f'  - [{kp.get("type")}] {kp.get("name")} (第{kp.get("page")}页)')
    return unique_kps   # 返回去重完成的知识点


"""写入Neo4j"""
def _write_to_neo4j(neo4j, knowledge_points, course_name, chapter_name, source_file):
    # 创建唯一约束（幂等操作）
    try:
        neo4j.run('CREATE CONSTRAINT course_name_unique IF NOT EXISTS FOR (c:Course) REQUIRE c.name IS UNIQUE')
        neo4j.run(
            'CREATE CONSTRAINT chapter_unique IF NOT EXISTS FOR (ch:Chapter) REQUIRE (ch.name, ch.course) IS UNIQUE')
        neo4j.run(
            'CREATE CONSTRAINT kp_unique IF NOT EXISTS '
            'FOR (kp:KnowledgePoint) REQUIRE (kp.name, kp.chapter, kp.course) IS UNIQUE')
    except Exception as e:
        print(f'【测试】创建约束时出错（可能已存在）: {e}')

    # 创建Course节点
    neo4j.run('MERGE (c:Course {name: $name})', name=course_name)

    # 创建Chapter节点并建立关系
    neo4j.run(
        'MERGE (c:Course {name: $course}) '
        'MERGE (c)-[:HAS_CHAPTER]->(ch:Chapter {name: $name, course: $course}) '
        'SET ch.course = $course',
        name=chapter_name,
        course=course_name
    )

    # 写入知识点（按 课程+章节+名称 唯一，避免不同章节同名知识点互相覆盖）
    for kp in knowledge_points:
        neo4j.run(
            'MERGE (ch:Chapter {name: $chapter, course: $course}) '
            'MERGE (kp:KnowledgePoint {name: $name, chapter: $chapter, course: $course}) '
            'MERGE (ch)-[:HAS_KNOWLEDGE_POINT]->(kp) '
            'SET kp.content = $content, kp.type = $type, kp.page = $page, kp.source_file = $source_file',
            chapter=chapter_name,
            course=course_name,
            name=kp.get('name', ''),
            content=kp.get('content', ''),
            type=kp.get('type', 'concept'),
            page=kp.get('page', 0),
            source_file=source_file
        )

    print(f'【测试】已向Neo4j写入 {len(knowledge_points)} 个知识点')

def parse_node(state:CoursewareState):
    print('\n【测试】这里是 -- parse_node.py')
    print(f"【测试】状态：{state}")
    print(f"【测试】状态keys：{list(state.keys())}")
    print(f"【测试】ocr_text是否存在：{'ocr_text' in state}")
    print(f"【测试】ocr_text值：{state.get('ocr_text', 'NOT_FOUND')}")

    # 课件内容
    slide_contents = state.get('slide_contents', [])
    # ocr_node返回的字段名是ocr_text
    ocr_results = state.get('ocr_text', '')
    course_name = state.get('course_name', '')
    chapter_name = state.get('chapter_name', '')

    # 来源文件（优先用独立字段，否则从路径提取）
    courseware_path = state.get('courseware_path', '')
    source_file = os.path.basename(courseware_path)
    print(f'【测试】来源文件: {source_file}')

    # 合并每页文本（原文 + OCR结果）
    merged_pages = _merge_content(slide_contents, ocr_results)

    # 构造提示词模板
    prompt_template = BuilderPromptYaml.get_prompt(
        "parse_node.yaml",
        course_name=course_name,
        chapter_name=chapter_name,
    )

    # 调用LLM结构化解析
    knowledge_points = _parse_with_llm(llm, prompt_template, merged_pages)

    # 降级策略 -- 如果LLM返回0个知识点，逐块用简化prompt重试
    if len(knowledge_points) == 0:
        print('\n【测试】LLM返回0个知识点，尝试简化prompt重试...')
        CHUNK_SIZE = 12
        json_template = '''{"knowledge_points":[{"name":"名称","content":"内容","type":"concept","page":页码}]}'''
        for i in range(0, len(merged_pages), CHUNK_SIZE):
            chunk = merged_pages[i:i + CHUNK_SIZE]
            chunk_text = '\n'.join([f"{p['page']}\n{p['text']}" for p in chunk])
            simple_prompt = (
                f"请从以下课件内容中提取知识点，输出JSON格式。\n"
                f"课程：{course_name}，章节：{chapter_name}\n\n"
                f"课件内容：\n{chunk_text}\n\n"
                f"输出格式：{json_template}"
            )
            knowledge_points.extend(_invoke_and_parse(llm, simple_prompt))

    # 写入Neo4j
    _write_to_neo4j(neo4j, knowledge_points, course_name, chapter_name, source_file)

    print(f'【测试】parse_node 完成，共解析 {len(knowledge_points)} 个知识点')
    return {
        'parse_status': 'done'
    }