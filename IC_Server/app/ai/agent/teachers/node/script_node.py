"""
授课脚本生成节点
职责：
  1. 从Neo4j查询当前章节的所有知识点（没有则提示先解析）
  2. 调用LLM生成授课脚本
  3. 写入 static/md/script_{课件id}.md，内容放入state
"""
from pathlib import Path
from app.ai.model.my_model import MyModel
from app.ai.util.neo4j_util import Neo4jConn
from app.ai.prompt.builder_prompt import BuilderPromptYaml
from app.ai.agent.teachers.state.courseware_state import CoursewareState

llm = MyModel.get_model()
neo4j = Neo4jConn().get_neo4j_conn()

# 项目根目录/static/md —— script_node.py 位于 app/ai/agent/teachers/node/
MD_DIR = Path(__file__).resolve().parents[5] / "static" / "md"


"""从Neo4j查询当前章节的知识点"""
def _query_knowledge_points(course_name, chapter_name):
    query = '''
    MATCH (c:Course {name: $course_name})-[:HAS_CHAPTER]->(ch:Chapter)
    WHERE ch.name = $chapter_name AND ch.course = $course_name
    MATCH (ch)-[:HAS_KNOWLEDGE_POINT]->(kp:KnowledgePoint)
    WHERE kp.course = $course_name AND kp.chapter = $chapter_name
    RETURN DISTINCT kp.name AS name, kp.content AS content, kp.type AS type,
           kp.page AS page, kp.source_file AS source_file
    '''
    results = neo4j.run(query, course_name=course_name, chapter_name=chapter_name)
    return [
        {'name': r['name'], 'content': r['content'], 'type': r['type'],
         'page': r['page'], 'source_file': r['source_file']}
        for r in results
    ]


def script_node(state: CoursewareState):
    print('\n【测试】这里是 -- script_node.py')

    course_name = state.get('course_name', '')
    chapter_name = state.get('chapter_name', '')
    courseware_id = state.get('courseware_id', 0)

    # 1. 知识点不存在：说明课件还没解析过（或解析失败）
    knowledge_points = _query_knowledge_points(course_name, chapter_name)
    if not knowledge_points:
        print('【测试】未查询到知识点，无法生成脚本')
        return {"script_status": "no_kp", "script_content": "", "script_path": ""}

    # 2. 组装知识点清单，构造prompt
    kp_text = '\n'.join(
        f"- [{kp['type']}] {kp['name']}（第{kp['page']}页）：{kp['content']}"
        for kp in knowledge_points
    )
    prompt = BuilderPromptYaml.get_prompt(
        "script_node.yaml",
        course_name=course_name,
        chapter_name=chapter_name,
        knowledge_points=kp_text
    )

    # 3. 调LLM生成脚本
    print(f'【测试】开始生成授课脚本（{len(knowledge_points)}个知识点）...')
    response = llm.invoke(prompt)
    script_content = response.content.strip()

    # 去除LLM可能包裹的```markdown标记
    if script_content.startswith('```'):
        parts = script_content.split('```')
        script_content = parts[1]
        if script_content.startswith('markdown'):
            script_content = script_content[9:]
        script_content = script_content.strip()

    # 4. 写入md文件
    MD_DIR.mkdir(parents=True, exist_ok=True)
    script_path = MD_DIR / f"script_{courseware_id}.md"
    script_path.write_text(script_content, encoding='utf-8')
    print(f'【测试】授课脚本已生成: {script_path}')

    return {
        "script_status": "done",
        "script_content": script_content,
        "script_path": str(script_path)
    }
