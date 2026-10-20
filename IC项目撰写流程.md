# 面向高校课堂的 AI 互动智课系统

> 顺序即开发顺序：先让一个空项目跑起来，再一个模块一个模块地加业务，每个模块都先写服务端、再写客户端、最后验证。文中代码取自仓库当前实现，个别地方为便于阅读做了删减（会标注）。
>
> 约定：每一步都按「做什么 → 为什么 → 代码 → 怎么验证」四段写。

---

## 一、创建项目

### （一）目录结构

动手写代码之前，先把"哪些东西放哪里"定下来。这个项目的目录是按**职责**切的，不是按文件类型切的：

```
InteractiveClassroom/
├── IC_Server/                 后端（一个独立进程）
│   ├── main.py                入口
│   ├── app/
│   │   ├── web/               接口层（对外的 HTTP）
│   │   │   ├── system_router/ 账号相关
│   │   │   ├── teacher_router/课件相关
│   │   │   ├── student_router/学生相关
│   │   │   ├── schema/        入参模型
│   │   │   ├── tool/          数据库读写工具
│   │   │   └── util/          鉴权、连接、密码
│   │   └── ai/                AI 层
│   │       ├── agent/         两个智能体（教师端解析、学生端对话测试）
│   │       ├── memory/        四层记忆
│   │       ├── tool/          检索工具
│   │       ├── prompt/        YAML 提示词
│   │       └── model/         大模型单例
│   ├── data/                  数据集、向量库、模型
│   └── static/                图片、脚本、评价报告
└── IC_Client/                 前端（Vue3 + Vite）
    └── src/
        ├── components/        页面
        ├── router/            路由
        └── main.js            全局配置
```

**为什么要先定结构**：后面每加一个功能，都能直接回答"代码写在哪"。做课件解析就进 `ai/agent/teachers`，做学生对话就进 `ai/agent/student`，写接口就进 `web/*_router`，不会出现"这个文件到底该放哪"的犹豫。

### （二）后端 Server

#### 1. 新建项目

打开 PyCharm → New Project，选择 `G:\GitHub\InteractiveClassroom\IC_Server`，解释器选已建好的 conda 环境（见下一节）。项目建好后目录是空的，只多一个 `.idea/`。

![image-20261020151848845](项目撰写流程.assets/image-20261020151848845.png)

#### 2. 创建虚拟环境

```cmd
# 环境检测
conda --version

# 创建（本机实际使用 Python 3.12）
conda create -n agent_env python=3.12 -y
conda activate agent_env
```

**为什么必须建虚拟环境**：这个项目要装 `paddleocr`、`torch`、`chromadb` 这类对 numpy / CUDA 版本极其敏感的重依赖。装在全局环境里，任何一次 `pip install` 都可能把别的项目的依赖顶掉；装进独立环境，坏了就 `conda env remove -n agent_env` 重建，成本只有几分钟。

#### 3. 安装依赖

项目没有提交 `requirements.txt`（这是后来要补的），实际是边写边装的。装完之后的核心依赖清单：

| 类别 | 包 |
| --- | --- |
| Web 框架 | `fastapi` `uvicorn` `pydantic` |
| 配置 | `python-dotenv` `pyyaml` |
| 存储驱动 | `pymysql` `redis` `psycopg[binary]` `psycopg_pool` `py2neo` |
| 数据处理 | `pandas` `openpyxl` |
| RAG 链路 | `langchain-core` `langchain-openai` `langchain-chroma` `langchain-huggingface` `chromadb` |
| 文档解析 | `python-pptx` `pymupdf` `pywin32` `paddleocr` `paddlepaddle` |
| 安全 | `passlib[bcrypt]` `python-jose[cryptography]` |

```cmd
pip install fastapi uvicorn pydantic python-dotenv pyyaml ^
    pymysql redis "psycopg[binary]" psycopg_pool py2neo ^
    pandas openpyxl langchain-core langchain-openai langchain-chroma ^
    langchain-huggingface chromadb python-pptx pymupdf pywin32 ^
    passlib[bcrypt] python-jose[cryptography] ^
    -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> `pywin32` 只在 Windows 上需要，用于把老版 `.ppt` 转成 `.pptx`（第 6 章会用到）。

**验证**：

```cmd
python -c "import fastapi, chromadb, langchain_chroma, pymysql; print('ok')"
```

#### 4. 写出第一个能跑的 `main.py`

不要一上来就写全量路由。先写一个只有 FastAPI 和 uvicorn 的最小版本：

```python
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/ping")
def ping():
    return {"code": 200, "message": "pong"}

if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)
```

**验证**：运行 `python main.py`，浏览器打开 `http://localhost:8000/docs`，能看到 `/ping` 并可点 "Try it out" 返回 pong。

这一步的意义是**先把"进程能起来、端口能通、文档能打开"三件事确认掉**。后面加功能时如果崩了，就能排除环境和框架的问题。

### （三）前端 Client

#### 1. 脚手架生成项目

```cmd
cd G:\GitHub\InteractiveClassroom
npm create vite@latest IC_Client -- --template vue
```

![image-20261020152207917](项目撰写流程.assets/image-20261020152207917.png)

执行过程中：是否安装包填 `y`，包名直接回车，确认安装填 `y`。

![是否安装依赖包](项目撰写流程.assets/image-20261020152344233.png)

![确认包名与安装](项目撰写流程.assets/image-20261020152423878.png)

生成完进入目录、装依赖、跑起来：

```cmd
cd IC_Client
npm install
npm run dev
```

创建成功后，Vite 会给出本地地址，打开能看到默认页面：

![脚手架创建成功](项目撰写流程.assets/image-20261020152450108.png)

![打开客户端项目并配置启动](项目撰写流程.assets/image-20261020152505055.png)

#### 2. 把端口固定成 8080

Vite 默认 5173，而后面后端 CORS 只放行 8080。与其改后端白名单，不如把前端口固定下来——**跨域配置里写死的端口就是契约**，前后端必须一致。

`vite.config.js`

```js
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  // 设置启动的端口号 -- 默认5173，这里改成 8080 与后端 CORS 对齐
  server: {
    host: 'localhost',
    port: 8080,
    open: true // 启动时自动打开浏览器
  }
})
```

#### 3. 清理脚手架

删掉 `HelloWorld.vue` 和示例样式，`App.vue` 先只留一个空壳，后面按页面逐步往里加：

```vue
<script setup>
</script>

<template>
  <div>
    <!-- 后面换成 <router-view /> -->
  </div>
</template>
```

**验证**：`npm run dev`，打开 `http://localhost:8080`，页面白屏但控制台无报错。

---

## 二、准备工作

### （一）配置中心：先有 `.env`，再有代码

**做什么**：把所有"会变的东西"（路径、连接串、密钥、模型名）抽到环境变量里，代码只读不写死。

**为什么**：这个项目的配置项有三十多个——向量库路径、模型路径、四个数据库的连接串、JWT 密钥。写死在代码里，换一台机器就要改十几处；抽到 `.env` 后，换机器只需要换一个文件。

`IC_Server/.env`（真实值填进去，`.env.example` 留空提交）

```ini
# 向量化相关配置
VECTORIZE_MODEL_PATH=D:\models\bge-large-zh-v1.5

# 问答 -- 向量数据库路径、数据集名称、原始数据路径
QA_CHROMADB_PATH=G:\GitHub\InteractiveClassroom\IC_Server\data\data_qa_chromadb
QA_VECTOR_DATASET_NAME=teach_qa
RAW_DATA_PATH=G:\GitHub\InteractiveClassroom\IC_Server\data\data_download\教学问答数据集.xlsx

# 课件 -- 向量数据库路径、数据集名称
CW_CHROMADB_PATH=G:\GitHub\InteractiveClassroom\IC_Server\data\data_courseware_chromadb
CW_VECTOR_DATASET_NAME=courseware

# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=******
MYSQL_DATABASE=interactiveclassroom
MYSQL_CHARSET=utf8mb4

# PostgreSQL
POSTGRESQL_URL=postgresql://postgres:******@localhost:5432/interactiveclassroom

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Neo4j
NEO4J_HOST=neo4j://127.0.0.1:7687
NEO4J_ACCOUNT=neo4j
NEO4J_PASSWORD=******
NEO4J_NAME=courseware

# 大模型
MODEL_ONLINE_NAME=qwen-plus
DASHSCOPE_API_KEY=sk-******
MODEL_LOCAL_NAME=qwen2.5:7b
LOCAL_URL=http://localhost:11434/v1

# JWT
SECRET_KEY=用-secrets.token_urlsafe(32)-生成
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720

# 记忆窗口
WINDOW_MEMORY_ROUND=4
WINDOW_MEMORY_EXPIRE_TIME=300
```

**验证**：

```python
# 临时脚本，确认配置能读到
from dotenv import load_dotenv
import os
load_dotenv()
print(os.getenv("MYSQL_DATABASE"), os.getenv("MODEL_ONLINE_NAME"))
```

能打印出 `interactiveclassroom qwen-plus` 即通过。

> 踩过的坑：`.env.example` 里漏掉了 `MYSQL_HOST`，但 `mysql_conn.py` 要读它，新环境启动时会直接 `int(None)` 报错。模板文件要么和代码对齐，要么干脆用代码里出现的变量名反向生成。

### （二）数据准备：把问答库先灌进去

#### 1. 准备数据集

原始数据是一份 Excel：`data/data_download/教学问答数据集.xlsx`，工作表名 `问答初始数据`，列结构固定：

| 列名 | 说明 |
| --- | --- |
| `标准问题(80字以内，不能为空)` | 检索用的主文本 |
| `相似问法1(80字以内)` ~ `相似问法6(80字以内)` | 同一问题的不同说法，拼进主文本提高召回 |
| `答案(2000字以内，不能为空)` | 存进 metadata，检索命中后带出来 |
| `规则分类（30字以内，空为默认分类）` | 存进 metadata |

**为什么先做这一步**：学生端问答要检索"问答库"，库是空的，后面所有调试都看不到效果。先把数据灌进去，后面写检索代码时才有东西可查。

#### 2. 封装向量化模型

**做什么**：把"本地嵌入模型"封装成一个可复用的方法，模型只加载一次。

`data/model/chromadb_model.py`

```python
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_huggingface import HuggingFaceEmbeddings

class ChromaDBModel:
    def __init__(self):
        # 模型目录从 .env 读，避免写死路径
        self.model_name = os.getenv("VECTORIZE_MODEL_PATH")

    def chromadb_model(self):
        return HuggingFaceEmbeddings(
            model_name=self.model_name,
            # 本地加载：不走网络，要求目录里已有完整模型文件
            model_kwargs={
                "device": "cuda",          # 无显卡机器改为 "cpu"
                "local_files_only": True,
            },
        )
```

**为什么 `local_files_only=True`**：服务器不一定能联网，而且每次启动都去 HuggingFace 校验会拖慢启动。代价是模型必须提前放到 `VECTORIZE_MODEL_PATH`——这也是"数据准备"里最容易被忽略的一步。

**验证**：

```python
from data.model.chromadb_model import ChromaDBModel
m = ChromaDBModel().chromadb_model()
print(len(m.embed_query("测试")))   # 输出向量维度，如 1024
```

#### 3. 封装向量库连接

**做什么**：把两个 collection（问答库、课件库）的创建逻辑收敛到一个类里。

`data/util/chromadb_util.py`

```python
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_chroma import Chroma
from data.model.chromadb_model import ChromaDBModel


class ChromaDB:
    def __init__(self):
        # 问答库
        self.qa_chromadb_path = os.getenv("QA_CHROMADB_PATH")
        self.qa_vector_dataset_name = os.getenv("QA_VECTOR_DATASET_NAME")
        # 课件库
        self.cw_courseware_chromadb_path = os.getenv("CW_CHROMADB_PATH")
        self.cw_vector_dataset_name = os.getenv("CW_VECTOR_DATASET_NAME")
        # 向量化模型（两个库共用同一个嵌入模型）
        self.chromadb_model = ChromaDBModel().chromadb_model()

    def qa_chromadb(self):
        return Chroma(
            persist_directory=self.qa_chromadb_path,
            collection_name=self.qa_vector_dataset_name,
            embedding_function=self.chromadb_model,
            collection_metadata={"hnsw:space": "cosine"}   # 显式指定余弦距离
        )

    def cw_chromadb(self):
        return Chroma(
            persist_directory=self.cw_courseware_chromadb_path,
            collection_name=self.cw_vector_dataset_name,
            embedding_function=self.chromadb_model,
            collection_metadata={"hnsw:space": "cosine"}
        )
```

**为什么两个库分开**：问答库是"权威答案"，一学期改一次；课件库是"课件切片"，每上传一份课件就变一次。更新频率差三个数量级，混在一个 collection 里，任何一次课件写入都会影响问答检索的性能与稳定性。

#### 4. 写离线向量化脚本

**做什么**：Excel → DataFrame → Document → 写入 Chroma。分三步：读表清洗、组装文档、批量写入。

`data/data_processing/Teaching_QA.py`

```python
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from langchain_core.documents import Document
from data.util.chromadb_util import ChromaDB


class TeachingQA:
    def __init__(self):
        self.raw_data = os.getenv("RAW_DATA_PATH")
        self.df = self.convert_dataframe()
        self.documents = self.convert_document()

    # 1. 读表 + 清洗
    def convert_dataframe(self):
        # pandas 本身不解析 xlsx，靠 openpyxl 引擎
        df = pd.read_excel(self.raw_data, sheet_name="问答初始数据")
        # 标准问题为空的行直接丢掉，否则写进向量库会污染检索
        df.dropna(subset=["标准问题(80字以内，不能为空)"], inplace=True)
        return df

    # 2. 组装成 LangChain 的 Document
    def convert_document(self):
        documents = []
        similar_cols = [
            "相似问法1(80字以内)", "相似问法2(80字以内)", "相似问法3(80字以内)",
            "相似问法4(80字以内)", "相似问法5(80字以内)", "相似问法6(80字以内)",
        ]
        for i, row in self.df.iterrows():
            # 收集非空的相似问法
            similar_questions = []
            for s in similar_cols:
                if s in row.index and pd.notna(row[s]):
                    similar_questions.append(str(row[s]))

            # 标准问题 + 相似问法拼成一段，扩大命中面
            page_content = f"标准问题：{str(row['标准问题(80字以内，不能为空)'])}\n"
            if similar_questions:
                page_content += f"相似问法：{'；'.join(similar_questions)}\n"

            documents.append(Document(
                page_content=page_content,
                metadata={
                    "answer": str(row["答案(2000字以内，不能为空)"]),
                    "category": str(row["规则分类（30字以内，空为默认分类）"]),
                    "source": "教学问答数据集.xlsx"
                }
            ))

        print(f"【测试】数据处理完成，共加载 {len(documents)} 条问答数据。")
        return documents

    # 3. 写入向量库
    def write_to_chromadb(self):
        try:
            db = ChromaDB().qa_chromadb()
            db.add_documents(self.documents)
            print("【测试】数据向量化并存储成功！")
            print(f"【测试】当前数据库中共有 {db._collection.count()} 条数据。")
        except Exception as e:
            print(f"【测试】存入数据库时出错: {e}")


if __name__ == '__main__':
    TeachingQA().write_to_chromadb()
```

执行：

```cmd
cd IC_Server/data
python data_processing/Teaching_QA.py
```

**验证**：脚本最后打印的条数应等于 Excel 有效行数；再手动查一次：

```python
from data.util.chromadb_util import ChromaDB
db = ChromaDB().qa_chromadb()
print(db._collection.count())
print(db.similarity_search("这门课的考核方式是什么", k=3))
```

> 注意 `add_documents` 是**追加**语义。重复执行会写入重复数据；要重建就先删掉 `QA_CHROMADB_PATH` 目录再跑。

### （三）把三个"外部存储"接上

后面每个模块都要落库，先把连接层写好，业务代码就只需要调工具类。

#### 1. MySQL：账号与课件

建库建表（结构按代码里 SQL 的实际列来）：

```sql
CREATE DATABASE IF NOT EXISTS interactiveclassroom DEFAULT CHARSET utf8mb4;

CREATE TABLE IF NOT EXISTS student (
  id          VARCHAR(32)  NOT NULL PRIMARY KEY COMMENT '学号',
  name        VARCHAR(64)  NOT NULL,
  email       VARCHAR(128) NOT NULL,
  password    VARCHAR(255) NOT NULL COMMENT 'bcrypt 密文',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS teacher (
  id          VARCHAR(32)  NOT NULL PRIMARY KEY COMMENT '工号',
  name        VARCHAR(64)  NOT NULL,
  email       VARCHAR(128) NOT NULL,
  password    VARCHAR(255) NOT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS courseware (
  id                BIGINT AUTO_INCREMENT PRIMARY KEY,
  original_filename VARCHAR(255) NOT NULL,
  saved_filename    VARCHAR(255) NOT NULL,
  file_path         VARCHAR(512) NOT NULL,
  course_name       VARCHAR(255) NOT NULL,
  chapter_name      VARCHAR(255) NOT NULL,
  upload_time       DATETIME DEFAULT CURRENT_TIMESTAMP,
  file_size         BIGINT DEFAULT 0,
  file_type         VARCHAR(16),
  parse_status      TINYINT DEFAULT 2 COMMENT '0处理中 1已完成 2未处理 3失败'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

连接封装：

```python
# app/web/util/mysql_conn.py
import pymysql
import os
from dotenv import load_dotenv
load_dotenv()

class MySQLConn:
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST")
        self.port = int(os.getenv("MYSQL_PORT"))
        self.user = os.getenv("MYSQL_USER")
        self.password = os.getenv("MYSQL_PASSWORD")
        self.database = os.getenv("MYSQL_DATABASE")
        self.charset = os.getenv("MYSQL_CHARSET")

    def get_mysql_conn(self):
        try:
            return pymysql.connect(
                host=self.host, port=self.port, user=self.user,
                password=self.password, database=self.database,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor   # 查询结果直接是 dict
            )
        except Exception as e:
            print(f"【测试】获取数据库连接失败：{e}")
            return None

    def close_mysql_conn(self, cur, conn):
        # 关闭要幂等，业务里可能重复关闭
        try:
            if cur is not None: cur.close()
        except Exception as e:
            print(f"【测试】关闭cursor异常: {e}")
        try:
            if conn is not None: conn.close()
        except Exception as e:
            print(f"【测试】关闭连接异常: {e}")
```

**为什么每条 SQL 都自己开连接**：这个项目并发量小、SQL 简单，用"开连接—执行—关连接"比维护连接池更省心；连接池留给读写频繁的 PostgreSQL。

**验证**：`python -m app.web.util.mysql_conn` 能打印连接对象。

#### 2. PostgreSQL：对话与记忆

四张表不需要手工建，服务启动时会幂等创建。先写连接池：

```python
# app/web/util/postgres_conn.py（节选）
from psycopg_pool import ConnectionPool

CREATE_TABLE_SQL_LIST = [
    '''CREATE TABLE IF NOT EXISTS chat_history (
        id BIGSERIAL PRIMARY KEY,
        session_id VARCHAR(64) NOT NULL,
        user_id VARCHAR(64) NOT NULL,
        mode VARCHAR(16) NOT NULL,
        course_name VARCHAR(255) DEFAULT '',
        chapter_name VARCHAR(255) DEFAULT '',
        role VARCHAR(16) NOT NULL,
        content TEXT NOT NULL,
        create_time TIMESTAMP DEFAULT NOW()
    )''',
    'CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id)',
    'CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id)',
    '''CREATE TABLE IF NOT EXISTS conversation_summary (
        session_id VARCHAR(64) PRIMARY KEY,
        summary TEXT,
        update_time TIMESTAMP DEFAULT NOW()
    )''',
    '''CREATE TABLE IF NOT EXISTS student_profile (
        user_id VARCHAR(64) NOT NULL,
        course_name VARCHAR(255) NOT NULL,
        profile TEXT,
        update_time TIMESTAMP DEFAULT NOW(),
        PRIMARY KEY (user_id, course_name)
    )''',
    'CREATE INDEX IF NOT EXISTS idx_student_profile_user ON student_profile(user_id)',
    '''CREATE TABLE IF NOT EXISTS long_memory (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(64) NOT NULL,
        content TEXT NOT NULL,
        create_time TIMESTAMP DEFAULT NOW()
    )''',
    'CREATE INDEX IF NOT EXISTS idx_user_memory_user ON long_memory(user_id)',
]


class PostgresConn:
    # 类级共享连接池 -- 整个进程只有一份
    _pool = None

    def __init__(self):
        self.conninfo = os.getenv("POSTGRESQL_URL")

    def open_pool(self):
        if PostgresConn._pool is None:
            PostgresConn._pool = ConnectionPool(
                self.conninfo, min_size=2, max_size=10,
                open=False, kwargs={"autocommit": True}
            )
            PostgresConn._pool.open()
            self.create_tables()          # 启动即建表，幂等
            print("【测试】PostgreSQL连接池已启动，数据表已就绪")
        return PostgresConn._pool

    def close_pool(self):
        if PostgresConn._pool is not None:
            PostgresConn._pool.close()
            PostgresConn._pool = None

    def get_pool(self):
        if PostgresConn._pool is None:
            raise RuntimeError("PostgreSQL连接池未初始化，请检查服务启动流程")
        return PostgresConn._pool

    def create_tables(self):
        with PostgresConn._pool.connection() as conn:
            with conn.cursor() as cur:
                for sql in CREATE_TABLE_SQL_LIST:
                    cur.execute(sql)
```

**为什么用类属性存池**：`PostgresConn()` 在业务里会被 new 很多次（每个请求一次），如果池挂在实例上，就会变成每个请求建一个池——连接数瞬间打满。挂在类属性上，`__init__` 只读配置，真正的池全局唯一。

**验证**：启动服务后看日志"数据表已就绪"，再 `\dt` 能看到四张表。

#### 3. Neo4j 与 Redis

```python
# app/ai/util/neo4j_util.py
from py2neo import Graph
import os
from dotenv import load_dotenv
load_dotenv()

class Neo4jConn:
    def __init__(self):
        self.host = os.getenv('NEO4J_HOST')
        self.account = os.getenv('NEO4J_ACCOUNT')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.name = os.getenv('NEO4J_NAME')

    def get_neo4j_conn(self) -> Graph:
        return Graph(
            profile=self.host,                       # 连接地址
            auth=(self.account, self.password),      # 账号密码
            name=self.name,                          # 数据库名称
        )
```

业务里统一用 `Neo4jConn().get_neo4j_conn()` 拿连接，和 PostgreSQL 的 `PostgresConn().get_pool()` 保持同一种写法。

```python
# app/web/util/redis_conn.py
import os
import redis
from dotenv import load_dotenv
load_dotenv()

class RedisConn:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST")
        self.port = os.getenv("REDIS_PORT")
        self.password = os.getenv("REDIS_PASSWORD")
        self.db = os.getenv("REDIS_DB")

    def get_redis_conn(self):
        return redis.Redis(
            host=self.host, port=self.port,
            password=self.password, db=self.db,
        )

    def close_redis_conn(self, conn):
        conn.close()
```

**验证**：分别跑一次连接并执行一条简单查询（Neo4j `RETURN 1`、Redis `ping()`）。

---

## 三、系统主页

### （一）客户端

**做什么**：先把"路由 + 一个页面"跑通。主页只有两个按钮：教师登录、学生登录。

#### 1. 配置路由

`src/router/index.js`

```js
import { createRouter, createWebHistory } from 'vue-router';

// 路由表：后面每加一个页面，就往这里加一项
const routes = [
    {
        path: '',
        meta: { title: '首页', login: false, identity: null },
        component: () => import('../components/Home.vue')
    },
]

const router = createRouter({
    history: createWebHistory(),   // history 模式，访问路径没有 # 号
    routes
})

export default router
```

`meta` 里的两个字段现在还没用上，但先约定好：`login` 表示"是否要登录"、`identity` 表示"允许哪种身份"，第五章的导航守卫会读它们。

#### 2. 页面

`src/components/Home.vue`

```vue
<template>
  <div>
    <h1>欢迎来到</h1>
    <h1>AI 互动智课系统</h1>
  </div>
  <div>
    请选择教师或者学生登录<br>
    <button @click="goTeacherLogin">教师登录</button>
    <button @click="goStudentLogin">学生登录</button>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

// 点击时先记下身份，再跳登录页 —— 登录页据此决定显示"学号"还是"工号"
function goTeacherLogin() {
  sessionStorage.setItem("identity", "teacher");
  router.push('/login');
}

function goStudentLogin() {
  sessionStorage.setItem("identity", "student");
  router.push('/login');
}
</script>
```

**为什么身份要放进 `sessionStorage`**：登录页需要知道"这次是教师还是学生登录"，但又不想为它单独写一个接口。用 `sessionStorage` 传，刷新页面后仍在，关掉标签页就消失——正好符合"一次登录会话"的语义。

#### 3. 把路由挂到应用上

`src/main.js`

```js
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

const app = createApp(App)

import router from './router'
app.use(router)

app.mount('#app')
```

`src/App.vue` 用 `<router-view />` 占位，页面由路由决定：

```vue
<script setup>
</script>

<template>
  <div>
    <router-view />
  </div>
</template>
```

**验证**：`npm run dev` → 打开 `http://localhost:8080`，能显示欢迎语与两个按钮；点按钮跳到 `/login`（此时还是空白页，控制台会提示组件不存在，正常）。

---

## 四、登录页面

### （一）客户端

`src/components/Login.vue` 的关键逻辑：根据 `identity` 切换显示"学号/工号"，提交后调 `/account/login`，成功后存 token 与姓名并跳转。

```vue
<template>
  <div><h1>当前为 - {{ identity }} - 登录</h1></div>
  <div>
    <form>
      <table>
        <tbody>
          <tr>
            <td v-show="!isShow">学号：</td>
            <td v-show="isShow">工号：</td>
            <td><input type="text" v-model="id"></td>
          </tr>
          <tr>
            <td>密码：</td>
            <td><input type="password" v-model="password"></td>
          </tr>
        </tbody>
      </table>
    </form>
  </div>
  <div>
    <button @click="goSignUp">注册</button>
    <button @click="goChat">登录</button>
    <button @click="goHome">退出</button>
  </div>
</template>

<script setup>
import { ref, getCurrentInstance, onMounted } from "vue";
import { useRouter } from "vue-router";

const identity = ref("")
const isShow = ref(false)

// 页面加载后从 sessionStorage 取身份，决定显示学号还是工号
onMounted(() => {
  identity.value = sessionStorage.getItem("identity");
  isShow.value = identity.value === 'teacher';
})

const router = useRouter();
const goSignUp = () => router.push('/signup');
const goHome = () => router.push('/');

// Vue3 的 setup 里没有 this，靠 proxy 拿 main.js 挂载的 $axios
const proxy = getCurrentInstance().proxy

const id = ref('')
const password = ref('')

function goChat() {
  proxy.$axios({
    url: 'account/login',
    method: 'post',
    data: { identity: identity.value, id: id.value, name: '', email: '', password: password.value }
  }).then(res => {
    const { code, message, data, token } = res.data
    if (code === 200) {
      sessionStorage.setItem("name", data);        // 姓名，页面展示用
      sessionStorage.setItem("token", token);      // 后续请求的凭证
      ElMessage.success(message);
      setTimeout(() => router.push('/chat'), 1500)
    } else {
      ElMessage.error(message)
    }
  })
}
</script>
```

**为什么用 `getCurrentInstance().proxy`**：`main.js` 把 axios 挂在了 `app.config.globalProperties.$axios` 上，这是"全局属性"，只有组件实例能访问；而 `<script setup>` 里没有 `this`，只能用 `proxy` 绕过去。

### （二）服务器

#### 1. 入参校验

`app/web/schema/account_schema.py`

```python
from pydantic import BaseModel, Field
from typing import Optional

class AccountSchema(BaseModel):
    identity: str = Field(..., description="当前登录身份")
    id: str = Field(..., description="学号或工号")
    name: str = Field(..., description="姓名")
    # 登录时用不到，但注册/发邮件共用这一个模型，所以都可选
    email: Optional[str] = Field(default=None, description="邮箱")
    password: Optional[str] = Field(default=None, description="密码")
    captcha: Optional[str] = Field(default=None, description="验证码")
```

#### 2. 查询工具

`app/web/tool/mysql_select_tool.py`

```python
from app.web.util.mysql_conn import MySQLConn

class MySQLSelect:
    def __init__(self):
        self.mysql_conn = MySQLConn()
        self.conn = self.mysql_conn.get_mysql_conn()
        self.cur = self.conn.cursor()

    # 查单条（登录、查重）
    def verify_account(self, sql, id):
        self.cur.execute(sql, id)
        result = self.cur.fetchone()
        self.mysql_conn.close_mysql_conn(self.cur, self.conn)
        return result

    # 查多条（课件列表）
    def select_courseware(self, sql):
        self.cur.execute(sql)
        result = self.cur.fetchall()
        self.mysql_conn.close_mysql_conn(self.cur, self.conn)
        return result
```

> 后面的 `mysql_insert_tool` / `mysql_update_tool` / `mysql_delete_tool` 是同一种写法：构造时建连接，方法里执行 SQL、`commit`、`finally` 关连接。这里不再逐个贴，逻辑完全对称。

#### 3. 路由与业务

`app/web/system_router/login_router.py`

```python
from fastapi import APIRouter
login_router = APIRouter()

from app.web.schema.account_schema import AccountSchema
from app.web.system_router.login_account import LoginAccount

@login_router.post(path="/login", summary="登录账号")
def login(account_schema: AccountSchema):
    return LoginAccount(account_schema).verify()
```

`app/web/system_router/login_account.py`（这一章先用明文比对，第九章再换成 bcrypt）

```python
from app.web.schema.account_schema import AccountSchema
from app.web.tool.mysql_select_tool import MySQLSelect

class LoginAccount:
    def __init__(self, account_schema: AccountSchema):
        self.id = account_schema.id
        self.password = account_schema.password
        self.identity = account_schema.identity
        self.mysql_verify = MySQLSelect()

    def verify(self):
        # 表名由 identity 决定：student 或 teacher
        sql_verify = f"select id,name,password from {self.identity} where id = %s"
        result = self.mysql_verify.verify_account(sql_verify, self.id)

        if not result:
            return {"code": 500, "message": "账号不存在，请注册后重新登录！", "data": None}

        if result["id"] == self.id and result["password"] == self.password:
            return {"code": 200, "message": "登录成功", "data": result['name']}
        return {"code": 500, "message": "账号或密码错误", "data": None}
```

**为什么 `password` 用占位符而 `identity` 用 f-string**：参数化只能用在"值"上，表名不能参数化——这是 MySQL 协议的限制。代价是 `identity` 存在注入风险，所以第九章补了白名单校验。

#### 4. 注册路由

`main.py` 里加一行：

```python
from app.web.system_router.login_router import login_router
app.include_router(login_router, prefix="/account", tags=["account"])
```

**验证**：在 `/docs` 里调 `POST /account/login`，分别试"账号不存在 / 密码错误 / 正确"三种情况，返回结构应为 `{code, message, data}`。

---

## 五、注册页面

注册比登录多一步：**先发验证码，再校验验证码**。所以客户端要做成两态。

### （一）客户端

`src/components/SignUp.vue` 的核心是"同一个按钮，前一次是发验证码，后一次是提交注册"：

```vue
<script setup>
import { ref, getCurrentInstance } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

const proxy = getCurrentInstance().proxy;
const router = useRouter();

const id = ref('')
const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const captcha = ref("")

// 两个开关：iscaptcha 控制按钮文案，method 控制后端走"发信"还是"校验"
const iscaptcha = ref(true)
const method = ref(true)

// 第一步：验证两次密码 → 请求发验证码
function sendCaptcha() {
  if (password.value !== confirmPassword.value) {
    ElMessage.error('两次密码不一致');
    return;
  }
  proxy.$axios({
    url: '/account/email',
    method: 'post',
    data: { identity: sessionStorage.getItem("identity"), id: id.value, name: name.value,
            email: email.value, password: password.value }
  }).then(res => {
    if (res.data.code === 200) {
      iscaptcha.value = false        // 按钮变成"注册"
      ElMessage.info(res.data.msg)
    } else {
      ElMessage.error(res.data.msg)
    }
  })
}

// 第二步：带验证码提交注册
function signUp() {
  proxy.$axios({
    url: '/account/signup',
    method: 'post',
    data: { identity: sessionStorage.getItem("identity"), id: id.value, name: name.value,
            email: email.value, password: password.value }
  }).then(res => {
    if (res.data.code === 200) {
      ElMessage.success('注册成功');
      router.push('/student');
    } else {
      ElMessage.error('注册失败');
    }
  })
}
</script>
```

**为什么注册要两道请求**：验证码必须"先落 Redis、再发信"，否则用户收到验证码时后端还没存下来，校验必然失败。把"发信"和"注册"拆成两个接口，顺序就由前端控制，逻辑更直白。

### （二）服务器

#### 1. 发验证码

`app/web/system_router/send_email.py`（节选核心三步）

```python
class SendEmail:
    def __init__(self, account_schema):
        # 邮件配置
        self.sender = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_EMAIL_PASSWORD")
        self.host = os.getenv("EMAIL_HOST")
        self.port = int(os.getenv("EMAIL_PORT"))
        # 账号信息
        self.identity = account_schema.identity
        self.id = account_schema.id
        self.email = account_schema.email
        # 依赖
        self.mysql_verify = MySQLSelect()
        self.redis_conn = RedisConn()

    # 1. 生成 4 位数字验证码
    def create_captcha(self):
        return "".join(str(random.randint(0, 9)) for _ in range(4))

    # 2. 存 Redis，5 分钟过期；先删旧值，避免重复发送时旧码还能用
    def save_captcha_to_redis(self):
        conn = self.redis_conn.get_redis_conn()
        conn.delete(self.id)
        conn.setex(self.id, 300, self.captcha)
        self.redis_conn.close_redis_conn(conn)

    # 3. 发信（QQ 邮箱 465 端口必须走 SMTP_SSL）
    def captcha_email(self):
        # 已注册的账号不再发验证码
        sql = f"select id,email from {self.identity} where id = %s"
        if self.mysql_verify.verify_account(sql, self.id):
            return {"code": 500, "msg": f"用户 {self.id} 存在，无需注册"}

        context = ssl.create_default_context()
        smtp = smtplib.SMTP_SSL(host=self.host, port=self.port, context=context)
        smtp.login(self.sender, self.sender_password)
        smtp.sendmail(self.sender, self.email, self.message.as_string())
        smtp.quit()
        return {"code": 200, "msg": f"发送邮件到 {self.email} 成功", "data": self.id}
```

#### 2. 注册入库

`app/web/system_router/add_account.py`

```python
class AddAccount:
    def sign_up(self):
        # 身份白名单：只有这两种表存在
        if self.identity not in ("student", "teacher"):
            return {"code": 500, "message": "身份错误", "data": None}

        sql_verify = f"select id,name,email from {self.identity} where id = %s"
        if self.mysql_verify.verify_account(sql_verify, self.id):
            return {"code": 500, "message": "账号已存在", "data": None}

        sql_insert = f"insert into {self.identity} values(%s, %s, %s, %s, now())"
        return self.mysql_insert.insert_account(
            sql_insert, self.id, self.name, self.email, self.password
        )
```

**验证**：用真实邮箱走一遍：收到验证码 → 提交注册 → 数据库出现新记录；用同一学号再注册一次，返回"账号已存在"。

---

## 六、教师端：上传、解析与授课脚本

这是整个项目最重的一块，分成"上传"和"解析"两段：上传只负责把文件落盘 + 记一行数据库；解析是一个后台跑几分钟的智能体流水线。

### （一）客户端

`src/components/Teacher.vue` 做四件事：上传表单、课件列表、解析轮询、脚本弹窗。

```vue
<script setup>
// 上传：FormData 打包文件 + 课程名 + 章节名
function uploadFile() {
  let formData = new FormData();
  formData.append('file', selectedFile.value);
  formData.append('course_name', courseName.value);
  formData.append('chapter_name', chapterName.value);

  proxy.$axios({
    url: 'courseware/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(res => {
    if (res.data.code === 200) { fetchCoursewareList(); }
  })
}

// 解析：调接口后开始轮询
function processCourseware(item) {
  proxy.$axios({
    url: 'courseware/parse',
    method: 'post',
    data: { original_filename: item.original_filename, file_path: item.file_path,
            course_name: item.course_name, chapter_name: item.chapter_name, id: item.id }
  }).then(res => {
    if (res.data.code === 200) startPollingStatus();
  })
}

// 轮询：每 5 秒查一次列表，直到没有"处理中(0)"的课件
let pollTimer = null;
function startPollingStatus(silent = false) {
  clearInterval(pollTimer);
  pollTimer = setInterval(() => {
    fetchCoursewareList();
    if (!coursewareList.value.some(item => item.parse_status === 0)) {
      clearInterval(pollTimer);
      if (silent) return;
      const failed = coursewareList.value.some(item => item.parse_status === 3);
      failed ? ElMessage.error('有课件处理失败，请重新处理')
             : ElMessage.success('课件处理完成');
    }
  }, 5000);
}
</script>
```

**为什么用轮询而不是 WebSocket**：解析进度只有一个"状态字段"要同步，用轮询实现成本最低（一个 `setInterval` + 一个已有接口），也不需要服务端维护长连接。

### （二）服务器

#### 1. 入参模型

`app/web/schema/courseware_schema.py`

```python
from pydantic import BaseModel, Field

class CoursewareSchema(BaseModel):
    original_filename: str = Field(..., description="课件原始名称")
    file_path: str = Field(..., description="课件在服务器的路径")
    course_name: str = Field(..., description="课程名")
    chapter_name: str = Field(..., description="章节名")
    id: int = Field(..., description="课件id")

class ScriptGenerateSchema(BaseModel):
    courseware_id: int = Field(..., description="课件id")
    course_name: str = Field(..., description="课程名")
    chapter_name: str = Field(..., description="章节名")
```

#### 2. 上传：分块写盘 + 落库

`app/web/teacher_router/courseware_upload.py`

```python
class CoursewareUpload:
    def __init__(self, file, form_data):
        self.mysql_insert = MySQLInsert()
        self.file = file
        self.course_name = form_data['course_name']
        self.chapter_name = form_data['chapter_name']

        # 绝对路径，避免运行目录变化导致存错地方
        self.base_dir = Path(__file__).resolve().parents[3]
        self.save_dir = self.base_dir / "data" / "data_download"
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.allowed_extensions = {".ppt", ".pptx", ".pdf"}
        self.max_size = 100 * 1024 * 1024

        self.only_filename, self.save_path, self.file_ext = self.get_only_name()

    def get_only_name(self):
        file_ext = Path(self.file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(400, "仅支持 .ppt, .pptx, .pdf 格式的文件")
        # UUID 重命名：防重名覆盖，也作为后续删除的唯一定位依据
        only_filename = f"{uuid.uuid4().hex}{file_ext}"
        return only_filename, self.save_dir / only_filename, file_ext

    async def save_courseware(self):
        # 边读边写，每次 1MB，避免大文件占满内存
        total_size = 0
        with open(self.save_path, "wb") as buffer:
            while chunk := await self.file.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > self.max_size:
                    buffer.close()
                    self.save_path.unlink(missing_ok=True)
                    raise HTTPException(400, "文件大小不能超过 100MB")
                buffer.write(chunk)

        result = self.save_mysql()
        return JSONResponse({"code": 200, "message": "文件上传成功"})

    def save_mysql(self):
        sql = "insert into courseware values(null,%s,%s,%s,%s,%s,now(),%s,%s,%s)"
        return self.mysql_insert.insert_courseware(
            sql, self.file.filename, self.only_filename, self.save_path,
            self.course_name, self.chapter_name, self.file.size, self.file_ext
        )
```

**为什么用 UUID 重命名**：同名课件覆盖会直接毁掉旧数据；UUID 保证了"文件→数据库→图谱→向量库"这条链路有一个全局唯一的定位符，后面删除、过滤都靠它。

#### 3. 列表与解析触发

`app/web/teacher_router/courseware_get.py`

```python
class CoursewareGet:
    def get_cur_list(self):
        result = MySQLSelect().select_courseware("select * from courseware")
        return {"code": 200, "message": "获取课件列表成功", "data": result}
```

`app/web/teacher_router/courseware_parse.py`（关键：先写状态，再起后台任务）

```python
class CourseWareParse:
    def __init__(self, request, courseware_schema):
        self.agent = request.app.state.courseware_agent   # 全局唯一的解析智能体
        self.save_path = courseware_schema.file_path
        self.id = courseware_schema.id
        self.mysql_update = MySQLUpdate()
        self.sql_update = "update courseware set parse_status=%s where id=%s"

    async def parse_courseware(self):
        result_file = self._get_file()
        # 先置 0（处理中），前端轮询才有东西可看
        self.mysql_update.update_parse_status(self.sql_update, 0, self.id)
        # 关键：不 await 图执行，起一个任务就返回
        asyncio.create_task(self._run_and_update(result_file))
        return {"code": 200, "message": "课件开始处理"}

    async def _run_and_update(self, result_file):
        try:
            await self.agent.run(result_file)
            self.mysql_update.update_parse_status(self.sql_update, 1, self.id)
        except Exception as e:
            print(f"【测试】课件处理失败: {e}")
            self.mysql_update.update_parse_status(self.sql_update, 3, self.id)
```

**为什么必须先写状态**：如果先起任务再写状态，前端可能在状态为 2（未处理）时就轮询到，误以为没开始；而且任务一旦秒失败，状态会停在 2，无法区分"没点过"和"点了但挂了"。

#### 4. 授课脚本与删除

`app/web/teacher_router/courseware_script.py`

```python
class CoursewareScript:
    async def get_script(self):
        # 复用同一个图，走 manager 节点：脚本在就直接读，不在就现场生成
        result = await self.agent.run_script(self.course_name, self.chapter_name, self.courseware_id)
        status = result.get('script_status')

        if status in ('exists', 'done'):
            return {"code": 200, "message": "获取授课脚本成功",
                    "data": {"content": result.get('script_content', ''),
                             "script_path": result.get('script_path', ''),
                             "generated": status == 'done'}}
        if status == 'no_kp':
            return {"code": 400, "message": "该课件尚未解析，请先点击\"处理\"完成课件解析", "data": None}
        return {"code": 500, "message": "授课脚本获取失败", "data": None}
```

删除课件要清理六处，写成"逐项执行 + 收集结果"：

```python
# app/web/teacher_router/courseware_delete.py（节选）
def delete_courseware(self):
    results = [
        ("MySQL记录",   self._del_mysql()),
        ("原始文件",    self._del_file()),
        ("授课脚本",    self._del_script()),
        ("评价报告",    self._del_eval()),
        ("Chroma向量",  self._del_chroma()),   # 按 source_file 过滤
        ("Neo4j知识点", self._del_neo4j()),    # DETACH DELETE，按 source_file
    ]
    failed = [name for name, ok in results if not ok]
    if failed:
        return {"code": 500, "message": f"部分数据删除失败: {', '.join(failed)}"}
    return {"code": 200, "message": "课件及所有相关数据已删除"}
```

**为什么向量清理用 `source_file` 而不是课程名**：课程名是"教学内容"的维度，同一门课可能有多份课件；只有 UUID 文件名能精确定位"这份课件产生的切片"。

### （三）AI 解析流水线

#### 1. 定义状态

`app/ai/agent/teachers/state/courseware_state.py`

```python
from typing_extensions import TypedDict

class CoursewareState(TypedDict):
    # 入参
    courseware_path: str        # 课件绝对路径
    course_name: str
    chapter_name: str
    file_type: str              # ppt / pptx / pdf
    courseware_id: int          # MySQL 记录 id，用于脚本文件命名
    # 中间产物
    extracted_text: str
    slide_contents: list[dict]  # [{"page":1, "text":"...", "images":[...]}]
    extracted_images: list[str]
    img_temp_dir: str
    ocr_text: str               # 实际写入的是 list[dict]，见 ocr_node
    # 状态标记
    parse_status: str
    ocr_status: str
    vectorize_status: str
    script_status: str
    # 模式与输出
    mode: str                   # parse / script
    script_mode: str
    script_path: str
    script_content: str
```

#### 2. `read_node`：把文件拆成"页 + 文本 + 图片"

三种格式三条路径，但**输出结构统一**成 `slide_contents`，后面的节点就不用关心来源格式了。

```python
def read_node(state: CoursewareState):
    file_path = state['courseware_path']
    file_ext = state['file_type']
    file_name = os.path.splitext(os.path.basename(file_path))[0]

    img_temp_dir = img_temp(file_name)       # static/img/{课件名}/

    if file_ext == '.pptx':
        slide_contents, extracted_images = extract_pptx(file_path, img_temp_dir)
    elif file_ext == '.ppt':
        converted_path = extract_ppt(file_path)     # 先转 pptx
        slide_contents, extracted_images = extract_pptx(converted_path, img_temp_dir)
    elif file_ext == '.pdf':
        slide_contents, extracted_images = extract_pdf(file_path, img_temp_dir)
    else:
        raise ValueError(f"不支持的文件格式: {file_ext}")

    full_text = '\n'.join([slide['text'] for slide in slide_contents])

    return {
        'file_type': file_ext.lstrip('.'),
        'extracted_text': full_text,
        'slide_contents': slide_contents,
        'extracted_images': extracted_images,
        'img_temp_dir': str(img_temp_dir)
    }
```

两个容易踩坑的地方：

```python
def extract_ppt(file_path):
    pythoncom.CoInitialize()        # 没有这句，多线程下报 -2147221008
    try:
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        presentation = powerpoint.Presentations.Open(file_path)
        presentation.SaveAs(output_path, 24)    # 24 = pptx 格式常量
        presentation.Close()
        powerpoint.Quit()
        return output_path
    finally:
        pythoncom.CoUninitialize()  # 必须释放，否则后台残留 PowerPoint 进程
```

```python
# pdf 里图片是 xref 引用，要 extract_image 才能拿到二进制
for img_idx, img in enumerate(page.get_images(full=True)):
    xref = img[0]
    base_image = doc.extract_image(xref)
    image_bytes = base_image['image']
    image_ext = base_image['ext']
```

#### 3. `ocr_node`：只认图片里的字

```python
_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = PaddleOCR(
            use_angle_cls=True,      # 处理倾斜文字
            lang='ch',
            det_db_box_thresh=0.3,   # 降低检测阈值，提高召回
            device='CPU',            # 避开 CUDA 版本冲突
        )
    return _ocr_engine

def ocr_node(state: CoursewareState):
    slide_contents = state.get('slide_contents', [])
    ocr_results = []

    if not slide_contents:
        return {'ocr_status': 'done', 'ocr_text': ""}

    try:
        ocr_engine = get_ocr_engine()
    except ImportError:
        # 没装 PaddleOCR 不阻断整条流水线，标记 error 继续
        return {'ocr_status': 'error', 'ocr_text': 'PaddleOCR未安装'}

    for slide in slide_contents:
        for img_path in slide.get('images', []):
            try:
                result = ocr_engine.ocr(img_path, cls=True)
                texts = [line[1][0] for line in (result[0] or [])]
                ocr_results.append({
                    'page': slide['page'],
                    'image_path': img_path,
                    'ocr_text': '\n'.join(texts)
                })
            except Exception as e:
                # 单图失败写占位，不影响其他页
                ocr_results.append({'page': slide['page'], 'image_path': img_path,
                                    'ocr_text': f'[OCR失败: {e}]'})

    return {'ocr_text': ocr_results, 'ocr_status': 'done'}
```

**为什么把 `ocr_text` 存成列表而不是字符串**：页码信息必须保留，否则合并时无法把 OCR 文本放回对应页。代价是 `CoursewareState` 的类型声明不准确（写的是 `str`），`parse_node` 用 `isinstance` 兼容了两种形态。

#### 4. `parse_node`：分块调用大模型

```python
CHUNK_SIZE = 12   # 每块页数，78 页约 7 次调用

def _parse_with_llm(llm, prompt_template, merged_pages):
    all_kps = []
    total_chunks = (len(merged_pages) + CHUNK_SIZE - 1) // CHUNK_SIZE

    for i in range(0, len(merged_pages), CHUNK_SIZE):
        chunk = merged_pages[i:i + CHUNK_SIZE]
        chunk_text = '\n'.join(f"{p['page']}\n{p['text']}" for p in chunk)
        prompt = prompt_template.replace('$content', chunk_text)
        all_kps.extend(_invoke_and_parse(llm, prompt))

    # 不同块可能抽到同一个概念，按 name 去重
    seen, unique_kps = set(), []
    for kp in all_kps:
        name = kp.get('name', '')
        if name and name not in seen:
            seen.add(name)
            unique_kps.append(kp)
    return unique_kps
```

写图谱时用 `MERGE` 而不是 `CREATE`，并先建三个唯一约束：

```python
neo4j.run('CREATE CONSTRAINT course_name_unique IF NOT EXISTS FOR (c:Course) REQUIRE c.name IS UNIQUE')
neo4j.run('CREATE CONSTRAINT chapter_unique IF NOT EXISTS FOR (ch:Chapter) REQUIRE (ch.name, ch.course) IS UNIQUE')
neo4j.run('CREATE CONSTRAINT kp_unique IF NOT EXISTS FOR (kp:KnowledgePoint) REQUIRE (kp.name, kp.chapter, kp.course) IS UNIQUE')

# 知识点按"课程+章节+名称"唯一，不同章节的同名知识点不会互相覆盖
for kp in knowledge_points:
    neo4j.run(
        'MERGE (ch:Chapter {name: $chapter, course: $course}) '
        'MERGE (kp:KnowledgePoint {name: $name, chapter: $chapter, course: $course}) '
        'MERGE (ch)-[:HAS_KNOWLEDGE_POINT]->(kp) '
        'SET kp.content = $content, kp.type = $type, kp.page = $page, kp.source_file = $source_file',
        chapter=chapter_name, course=course_name,
        name=kp.get('name', ''), content=kp.get('content', ''),
        type=kp.get('type', 'concept'), page=kp.get('page', 0),
        source_file=source_file
    )
```

再加一层降级：如果整份课件抽出 0 个知识点，换简化提示词**逐块补跑一次**。

```python
if len(knowledge_points) == 0:
    json_template = '{"knowledge_points":[{"name":"名称","content":"内容","type":"concept","page":页码}]}'
    for i in range(0, len(merged_pages), CHUNK_SIZE):
        chunk = merged_pages[i:i + CHUNK_SIZE]
        chunk_text = '\n'.join(f"{p['page']}\n{p['text']}" for p in chunk)
        simple_prompt = (f"请从以下课件内容中提取知识点，输出JSON格式。\n"
                         f"课程：{course_name}，章节：{chapter_name}\n\n"
                         f"课件内容：\n{chunk_text}\n\n输出格式：{json_template}")
        knowledge_points.extend(_invoke_and_parse(llm, simple_prompt))
```

#### 5. `vectorize_node`：从图谱读，写进向量库

```python
def _store_vectors(cw_chroma, knowledge_points, course_name, chapter_name):
    # 先删本章旧向量：重解析幂等，不影响同课程其他章节
    cw_chroma._collection.delete(where={"$and": [
        {"course_name": {"$eq": course_name}},
        {"chapter_name": {"$eq": chapter_name}}
    ]})

    ids, documents, metadatas = [], [], []
    seen_ids = set()
    for kp in knowledge_points:
        text = f"{kp['name']}：{kp['content']}" if kp.get('content') else kp['name']
        kp_id = f"{course_name}_{kp['name']}_{kp.get('page', 0)}"
        if kp_id in seen_ids:
            continue
        seen_ids.add(kp_id)
        ids.append(kp_id)
        documents.append(text)
        metadatas.append({
            'course_name': course_name, 'chapter_name': chapter_name,
            'type': kp['type'], 'page': kp['page'],
            'source_file': kp.get('source_file', ''), 'kp_name': kp['name']
        })

    cw_chroma.add_texts(texts=documents, metadatas=metadatas, ids=ids)
```

#### 6. `script_node`：生成授课讲稿

```python
def script_node(state: CoursewareState):
    knowledge_points = _query_knowledge_points(course_name, chapter_name)
    if not knowledge_points:
        return {"script_status": "no_kp", "script_content": "", "script_path": ""}

    kp_text = '\n'.join(
        f"- [{kp['type']}] {kp['name']}（第{kp['page']}页）：{kp['content']}"
        for kp in knowledge_points
    )
    prompt = BuilderPromptYaml.get_prompt(
        "script_node.yaml", course_name=course_name,
        chapter_name=chapter_name, knowledge_points=kp_text
    )
    response = llm.invoke(prompt)
    script_content = response.content.strip()

    # 去掉模型可能带的 ```markdown 围栏
    if script_content.startswith('```'):
        script_content = script_content.split('```')[1]
        if script_content.startswith('markdown'):
            script_content = script_content[9:]
        script_content = script_content.strip()

    MD_DIR.mkdir(parents=True, exist_ok=True)
    script_path = MD_DIR / f"script_{courseware_id}.md"
    script_path.write_text(script_content, encoding='utf-8')
    return {"script_status": "done", "script_content": script_content,
            "script_path": str(script_path)}
```

#### 7. 组装图

```python
class CoursewareGraph:
    def courseware_agent(self):
        graph = StateGraph(CoursewareState)
        graph.add_node("read", read_node)
        graph.add_node("ocr", ocr_node)
        graph.add_node("parse", parse_node)
        graph.add_node("vectorize", vectorize_node)
        graph.add_node("manager", manager_node)
        graph.add_node("script", script_node)

        graph.add_edge(START, "manager")
        # 一个入口两种模式：解析走 read 链，脚本走 script 节点
        graph.add_conditional_edges(
            "manager", route_manager,
            {"read": "read", "script": "script", "end": END}
        )
        graph.add_edge("read", "ocr")
        graph.add_edge("ocr", "parse")
        graph.add_edge("parse", "vectorize")
        graph.add_edge("vectorize", END)
        graph.add_edge("script", END)

        return graph.compile(checkpointer=None)

    async def run(self, courseware):
        initial_state = {
            "mode": "parse",
            "courseware_path": courseware['saved_path'],
            "course_name": courseware['course_name'],
            "chapter_name": courseware['chapter_name'],
            "file_type": courseware['file_ext'],
            "courseware_id": courseware.get('id', 0),
            "parse_status": "parsing",
            "vectorize_status": "pending",
            "script_status": "", "script_content": "", "script_path": "",
        }
        return await self.agent.ainvoke(initial_state)
```

manager 节点的分流逻辑只有三句：

```python
def route_manager(state: CoursewareState):
    mode = state.get('mode', 'parse')
    if mode == 'script':
        if state.get('script_status') == 'exists':   # 文件已存在，manager 已读出内容
            return 'end'
        return 'script'
    return 'read'
```

#### 8. 接进 lifespan

`main.py`

```python
@asynccontextmanager
async def content_manager(app: FastAPI):
    print("【测试】欢迎进入 -- AI 互动智课系统")
    # 三个智能体全局只建一次
    app.state.courseware_agent = CoursewareGraph()
    app.state.student_agent = StudentChatGraph()
    app.state.student_test_agent = StudentTestGraph()
    # PostgreSQL 连接池
    app.state.postgres_conn = PostgresConn()
    app.state.postgres_conn.open_pool()
    yield
    # 关闭阶段：按创建逆序释放
    app.state.postgres_conn.close_pool()
    app.state.courseware_agent = None
```

`app.state` 是 FastAPI 提供的"全局命名空间"，请求处理时通过 `request.app.state.xxx` 取——这就是为什么课件解析接口能拿到智能体实例。

**验证整条流水线**：

1. 上传一份 20 页左右的 PPTX，列表里出现一行，`parse_status=2`；
2. 点"处理"，`parse_status` 立刻变 0；
3. 看后端日志依次出现 `read_node → ocr_node → parse_node → vectorize_node`；
4. 结束后状态变 1；Neo4j 里能查到该章节的知识点；Chroma 里 `count()` 增加；
5. 点"查看脚本"，返回 Markdown 讲稿并落盘 `static/md/script_{id}.md`。

---

## 七、学生端：对话与四层记忆

### （一）客户端

`src/components/Student.vue` 是整个项目最复杂的页面，拆成四块：

| 块 | 职责 |
| --- | --- |
| 课程/课件选择 | 决定 `course_name`、`chapter_name`、`courseware_id` |
| 对话区 | 两种模式（normal / qa），SSE 增量渲染 |
| 历史会话 | 列表、详情回看、删除 |
| 测试区 | 出题、逐题作答、交卷、查看报告 |

对话请求不走 axios，而是 `fetchEventSource`：

```js
await fetchEventSource('http://localhost:8000/student/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionStorage.getItem('token')}`   // 原生 EventSource 不能带 header
  },
  body: JSON.stringify({
    session_id: sessionId, user_id: name, mode: chatMode.value,
    course_name: selectedCourse.value, chapter_name: selectedChapter.value,
    question: inputText.value, courseware_id: selectedCourseware.value
  }),
  onmessage(ev) {
    if (ev.data === 'end_end') { loading.value = false; return; }   // 结束标记
    const { content } = JSON.parse(ev.data);
    answer.value += content;                                        // 逐 token 追加
  },
  onerror(err) { throw err }    // 抛错终止，避免无限重连
})
```

**为什么不用 axios**：axios 基于 XHR，拿不到流式响应体；`EventSource` 又不能带 `Authorization`。`fetch-event-source` 同时满足"POST + 自定义头 + 流式读取"。

### （二）服务器

#### 1. 入参模型

`app/web/schema/student_schema.py`

```python
from pydantic import BaseModel, Field
from typing import List

class ChatSchema(BaseModel):
    session_id: str = Field(..., description="会话id")
    user_id: str = Field(..., description="学生标识（用户名）")
    mode: str = Field(..., description="对话模式：normal/qa")
    course_name: str = Field(default="", description="课程名")
    chapter_name: str = Field(default="", description="章节名")
    question: str = Field(..., description="学生问题")
    courseware_id: int = Field(default=0, description="课件id")

class TestStartSchema(BaseModel):
    session_id: str = Field(...)
    user_id: str = Field(...)
    courseware_id: int = Field(...)
    course_name: str = Field(default="")
    chapter_name: str = Field(default="")

class TestFinishSchema(TestStartSchema):
    questions: List[str] = []
    answers: List[str] = []
```

#### 2. 路由

`app/web/student_router/student_router.py`（节选）

```python
student_router = APIRouter()

@student_router.post(path="/chat", summary="学生对话(SSE流式输出)")
def chat(request: Request, chat_schema: ChatSchema, now_user: dict = Depends(is_roles(["student"]))):
    return StudentChat(request, chat_schema).chat()

@student_router.get(path="/session/list", summary="获取学生会话列表")
def session_list(user_id: str = Query(...), now_user: dict = Depends(is_roles(["student"]))):
    return StudentSession().get_session_list(user_id)

@student_router.delete(path="/session", summary="删除历史会话")
def session_delete(session_id: str, now_user: dict = Depends(is_roles(["student"]))):
    return StudentSession().del_session(session_id)
```

#### 3. 对话入口：落库 + 跑图 + 流式

`app/web/student_router/student_chat.py`（核心 40 行）

```python
class StudentChat:
    def __init__(self, request, chat_schema):
        self.agent = request.app.state.student_agent      # 全局对话图
        self.pool = PostgresConn().get_pool()
        self.session_id = chat_schema.session_id
        self.user_id = chat_schema.user_id
        self.mode = chat_schema.mode
        self.course_name = chat_schema.course_name
        self.chapter_name = chat_schema.chapter_name
        self.question = chat_schema.question
        self.courseware_id = chat_schema.courseware_id

    def _save_message(self, role, content):
        sql = '''INSERT INTO chat_history(session_id, user_id, mode, course_name,
                                          chapter_name, role, content)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)'''
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (self.session_id, self.user_id, self.mode,
                                  self.course_name, self.chapter_name, role, content))

    def chat(self):
        # L1：取最近 6 条作为多轮上下文
        history = SessionManager.get_window(self.session_id, 6)
        # 先落 user 消息，保证审计顺序
        self._save_message("user", self.question)

        state = {
            "session_id": self.session_id, "user_id": self.user_id,
            "mode": self.mode, "course_name": self.course_name,
            "chapter_name": self.chapter_name, "courseware_id": self.courseware_id,
            "question": self.question, "history": history,
            "qa_context": "", "cw_context": "", "graph_context": "", "answer": ""
        }
        return StreamingResponse(self.generate(state), media_type="text/event-stream")

    def generate(self, state):
        answer = ""
        all_nodes = ("normal", "knowledge")     # 只把这些节点的 token 推给前端

        try:
            result = self.agent.agent.stream(
                state,
                config={"recursion_limit": 10},
                stream_mode=["messages", "values"],   # 双通道
            )
            for stream_mode, data in result:
                if stream_mode == "messages":
                    chunk, meta = data
                    if chunk.content and meta.get("langgraph_node") in all_nodes:
                        yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"
                else:
                    if data.get("answer"):
                        answer = data["answer"]        # values 里是完整回答，用于落库
        except GraphRecursionError:
            answer = "抱歉，本轮对话处理异常，请稍后重试或换个说法。"
            yield f"data: {json.dumps({'content': answer}, ensure_ascii=False)}\n\n"
        except Exception as e:
            answer = "抱歉，AI 回复生成失败，请稍后重试。"
            yield f"data: {json.dumps({'content': answer}, ensure_ascii=False)}\n\n"

        # 落 assistant 消息（用的是 values 里的完整文本）
        self._save_message("assistant", answer)

        # 记忆更新甩到后台线程，不阻塞流结束
        threading.Thread(target=SessionManager.after_round,
                         args=(self.session_id, self.user_id, self.mode, self.course_name,
                               self.chapter_name, state["question"], answer),
                         daemon=True).start()

        yield "data: end_end\n\n"
```

**为什么要"双通道"**：`messages` 给的是逐个 token，适合推给前端做打字机；但它可能被节点拼接打断，拼不出一份完整回答。`values` 给的是每个节点执行完的完整状态，拿 `answer` 字段落库最可靠。两条流各干一件事，"显示"和"存储"彻底解耦。

#### 4. 历史会话

`app/web/student_router/student_session.py`

```python
def get_mode_text(mode) -> str:
    if mode == 'test': return '测试'
    if mode == 'qa':   return '知识点提问'
    return '普通对话'

def get_title(course_name, chapter_name) -> str:
    if not course_name: return '普通对话'
    if chapter_name:    return f"{course_name} / {chapter_name}"
    return course_name

class StudentSession:
    def get_session_list(self, user_id):
        # 一个会话一行：MIN/MAX 取会话级属性，COUNT 取消息数
        sql = '''SELECT session_id, MIN(mode) AS mode, MAX(course_name) AS course_name,
                        MAX(chapter_name) AS chapter_name, COUNT(*) AS msg_count,
                        MIN(create_time) AS start_time, MAX(create_time) AS last_time
                 FROM chat_history WHERE user_id = %s
                 GROUP BY session_id ORDER BY last_time DESC'''
        rows = self._query_all(sql, (user_id,))
        return {"code": 200, "message": "获取会话列表成功", "data": [
            {"session_id": r['session_id'],
             "time": r['last_time'].strftime('%Y-%m-%d %H:%M:%S'),
             "title": get_title(r['course_name'], r['chapter_name']),
             "mode": r['mode'], "modeText": get_mode_text(r['mode']),
             "msg_count": r['msg_count'],
             "selectedCourse": r['course_name'], "selectedChapter": r['chapter_name']}
            for r in rows
        ]}
```

### （三）对话图

#### 1. 状态

`app/ai/agent/student/state/student_state.py`

```python
class StudentState(TypedDict):
    session_id: str
    user_id: str
    mode: str            # normal / qa
    course_name: str
    chapter_name: str
    question: str
    courseware_id: int
    history: List[dict]  # L1 窗口，web 层传进来
    # 各节点产出
    qa_context: str
    cw_context: str
    graph_context: str
    script_context: str
    answer: str
```

#### 2. manager：只打印，路由交给路由函数

```python
def manager_node(state: StudentState) -> dict:
    print("【测试】当前模式：", state["mode"])
    return {}

def route_chat(state: StudentState) -> str:
    return "knowledge" if state["mode"] == "qa" else "normal"
```

#### 3. normal：只用记忆，不检索

```python
def normal_node(state: StudentState) -> dict:
    summary = SessionManager.get_summary(state["session_id"])
    facts   = SessionManager.get_facts(state["user_id"])
    profile = SessionManager.get_profile(state["user_id"], state.get("course_name", "")) \
              if state.get("course_name") else ""

    # 提示词模板用 $summary/$facts/$profile 占位，空值给"（暂无）"
    system_prompt = BuilderPromptYaml.get_prompt(
        'normal_node.yaml',
        summary=summary or "（暂无）",
        facts="\n".join(f"- {f}" for f in facts) if facts else "（暂无）",
        profile=profile or "（暂无）",
    )

    messages = [SystemMessage(content=system_prompt)]
    for msg in state.get("history", []):
        messages.append(HumanMessage(content=msg["content"]) if msg["role"] == "user"
                        else AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=state["question"]))

    return {"answer": MyModel.get_model().invoke(messages).content}
```

#### 4. knowledge：四源检索 + 动态拼提示词

```python
def knowledge_node(state: StudentState) -> dict:
    question, course_name, chapter_name = state["question"], state["course_name"], state["chapter_name"]

    # 记忆三件套
    summary = SessionManager.get_summary(state["session_id"])
    facts   = SessionManager.get_facts(state["user_id"])
    profile = SessionManager.get_profile(state["user_id"], course_name)

    # 四源检索
    docs = ChromaDB().qa_chromadb().similarity_search(question, k=5)
    qa_context = "\n\n".join(f"[{i+1}] {doc.page_content}" for i, doc in enumerate(docs))

    cw_context, _ = CoursewareSearchTool().search(question, course_name, chapter_name, k=5)
    graph_context = Neo4jSearchTool().search_neo4j(course_name, chapter_name)
    script_context = _get_script(state.get("courseware_id", 0))

    # 动态拼接：有值才加段落，避免空段落污染提示词
    sys_prompt = [BuilderPromptYaml.get_prompt('knowledge_node.yaml')]
    if script_context: sys_prompt.append(f"【授课脚本】（老师本节课的讲稿）\n{script_context}")
    if cw_context:     sys_prompt.append(f"【课程知识库】（课件知识点检索结果）\n{cw_context}")
    if graph_context:
        scope = f"{course_name} - {chapter_name}" if chapter_name else course_name
        sys_prompt.append(f"【知识点结构】（{scope}）\n{graph_context}")
    if qa_context:     sys_prompt.append(f"【问答库】（检索结果）\n{qa_context}")
    if summary:        sys_prompt.append(f"【对话摘要】\n{summary}")
    if facts:          sys_prompt.append("【长期记忆】\n" + "\n".join(f"- {f}" for f in facts))
    if profile:        sys_prompt.append(f"【学生画像】\n{profile}")

    messages = [SystemMessage(content="\n\n".join(sys_prompt))]
    messages += [HumanMessage(content=m["content"]) if m["role"] == "user"
                 else AIMessage(content=m["content"]) for m in state.get("history", [])]
    messages.append(HumanMessage(content=question))

    result = MyModel.get_model().invoke(messages)
    return {"qa_context": qa_context, "cw_context": cw_context,
            "graph_context": graph_context, "script_context": script_context,
            "answer": result.content}
```

脚本读取带三级降级（没选课件 / 文件不存在 / 读失败），并对超长内容截断：

```python
script_max_len = 8000

def _get_script(courseware_id: int) -> str:
    if not courseware_id:
        return ""
    path = script_dir / f"script_{courseware_id}.md"
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8").strip()
        return content if len(content) <= script_max_len else content[:script_max_len] + "\n...（已截断）"
    except Exception:
        return ""
```

#### 5. 组装

```python
graph = StateGraph(StudentState)
graph.add_node("manager", manager_node)
graph.add_node("normal", normal_node)
graph.add_node("knowledge", knowledge_node)

graph.add_edge(START, "manager")
graph.add_conditional_edges("manager", route_chat,
                            {"normal": "normal", "knowledge": "knowledge"})
graph.add_edge("normal", END)
graph.add_edge("knowledge", END)
self.agent = graph.compile(debug=True)
```

### （四）四层记忆

#### 1. 三个存储模块（L1/L2/L3）

```python
# L1 窗口（window_memory.py）—— 只读，倒序取最近 N 条再翻回正序
def read(session_id: str, limit: int = 10, offset: int = 0) -> list:
    pool = PostgresConn().get_pool()
    sql = ("SELECT role, content FROM chat_history WHERE session_id = %s "
           "ORDER BY id DESC LIMIT %s OFFSET %s")
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (session_id, limit, offset))
            rows = cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

# L2 摘要（summary_memory.py）—— upsert，按 session_id 覆盖
def write(session_id: str, summary: str) -> None:
    pool = PostgresConn().get_pool()
    sql = """INSERT INTO conversation_summary (session_id, summary, update_time)
             VALUES (%s, %s, NOW())
             ON CONFLICT (session_id) DO UPDATE
             SET summary = EXCLUDED.summary, update_time = NOW()"""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (session_id, summary))

# L3 长期事实（long_memory.py）—— 批量追加
def add(user_id: str, facts: list) -> None:
    if not facts:
        return
    pool = PostgresConn().get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO long_memory (user_id, content) VALUES (%s, %s)",
                            [(user_id, f) for f in facts])
```

L4 画像是 `student_profile` 上的复合主键 upsert：

```python
sql = """INSERT INTO student_profile (user_id, course_name, profile, update_time)
         VALUES (%s, %s, %s, NOW())
         ON CONFLICT (user_id, course_name) DO UPDATE
         SET profile = EXCLUDED.profile, update_time = NOW()"""
```

#### 2. 三个生成器：摘要、事实、画像

```python
# L2 —— 旧摘要 + 窗口外消息 → 新摘要
def regenerate(old_summary: str, older_messages: list) -> str:
    prompt = BuilderPromptYaml.get_prompt(
        "summary_agent.yaml",
        old_summary=old_summary or "（无）",
        older_messages=format_messages(older_messages)
    )
    return MyModel.get_model().invoke(prompt).content.strip()

# L3 —— 从本轮问答里抽事实，输出 JSON 数组，失败就跳过本轮
def extract(question: str, answer: str) -> list:
    r = MyModel.get_model().invoke(
        BuilderPromptYaml.get_prompt("long_agent.yaml", question=question, answer=answer)
    ).content.strip()
    # 剥掉 ```json 围栏后 json.loads，任何异常都返回 []
    ...

# L4 —— 原画像 + L3 全部事实 → 新画像
def regenerate(old_profile: str, facts: list) -> str:
    prompt = BuilderPromptYaml.get_prompt(
        "profile_agent.yaml",
        old_profile=old_profile or "（无）",
        facts="\n".join(f"- {f}" for f in facts) if facts else "（暂无）"
    )
    return MyModel.get_model().invoke(prompt).content.strip()
```

#### 3. 调度器：一轮结束后决定更新什么

`app/ai/memory/manager/memory_manager.py`

```python
window_size = 6

def after_round(session_id, user_id, mode, course_name, chapter_name, question, answer):
    try:
        # L3 每轮都做：抽事实 → 写库
        facts = long_agent.extract(question, answer)
        if facts:
            long_memory.add(user_id, facts)

        count = summary_memory.count(session_id)

        # L2 超过窗口后每轮更新：只压窗口外的旧消息
        if count > window_size:
            older_count = count - window_size
            older_messages = window_memory.read(session_id, older_count, offset=window_size)
            old_summary = summary_memory.read(session_id) or ""
            new_summary = summary_agent.regenerate(old_summary, older_messages)
            summary_memory.write(session_id, new_summary)

        # L4 超过窗口且有课程名：用 L3 全部事实重提炼画像
        if count > window_size and course_name:
            old_profile = profile_memory.read(user_id, course_name)
            all_facts = long_memory.list(user_id)
            if all_facts:
                new_profile = profile_agent.regenerate(old_profile, all_facts)
                profile_memory.write(user_id, course_name, new_profile)
    except Exception as e:
        # 记忆是增强功能，失败不能影响对话
        print(f"【测试】记忆更新失败（不影响对话）: {e}")
```

**为什么 L2 要 `offset=window_size`**：窗口内的 6 条以原文（L1）形式已经在提示词里了，摘要只处理更早的部分。否则同一段对话既进原文又进摘要，token 白花一遍。

#### 4. 门面：一个入口读四层

`SessionManager` 把 L1~L4 的读取统一成四个静态方法，每个都 try/except 降级（`[]` / `""`），业务节点只需要调一行：

```python
summary = SessionManager.get_summary(session_id)
facts   = SessionManager.get_facts(user_id)
profile = SessionManager.get_profile(user_id, course_name)
history = SessionManager.get_window(session_id, 6)
```

**验证**：

1. 连续聊 8 轮（16 条消息），第 7 轮之后 `conversation_summary` 应出现记录；
2. 换一个会话再聊，`long_memory` 里应累积该用户的事实；
3. 选择课程后再聊，`student_profile` 出现该课程画像；
4. 断开 Neo4j 再提问，对话仍能回答（四源降级为三源）。

---

## 八、知识测试与学情点评

测试是独立的一条图，因为它的生命周期与对话完全不同：**一次请求出题、一次请求收卷**，中间隔着用户的作答时间。

### （一）状态与图

`app/ai/agent/student/state/test_state.py`

```python
class TestState(TypedDict, total=False):   # 全部可选，未注入时为缺失键
    session_id: str
    user_id: str
    courseware_id: int
    course_name: str
    chapter_name: str
    mode: str                   # start / finish
    questions: List[dict]       # [{"qno":1, "content":"..."}]
    qa_pairs: List[dict]        # [{"qno":1,"question":"...","answer":"..."}]
    evaluation_md: str
    evaluation_path: str
```

```python
graph = StateGraph(TestState)
graph.add_node("manager", test_manager_node)
graph.add_node("start", question_node)
graph.add_node("finish", finish_node)
graph.add_node("evaluation", evaluation_node)

graph.add_edge(START, "manager")
graph.add_conditional_edges("manager", route_test,
                            {"start": "start", "finish": "finish"})
graph.add_edge("start", END)
graph.add_edge("finish", "evaluation")   # 收卷必须先生成、再落盘
graph.add_edge("evaluation", END)
```

```python
def route_test(state: TestState) -> str:
    return "finish" if state["mode"] == "finish" else "start"
```

### （二）出题

`app/ai/agent/student/node/question_node.py`

```python
def question_node(state: TestState) -> dict:
    course_name, chapter_name = state["course_name"], state["chapter_name"]

    # 检索：课件库 + 图谱，保证题目"出自本章"
    cw_context, _ = CoursewareSearchTool().search(
        question=f"{course_name} - {chapter_name} 核心考点",
        course_name=course_name, chapter_name=chapter_name, k=5
    )
    kn_points = Neo4jSearchTool().search_neo4j(course_name, chapter_name)

    sys_prompt = BuilderPromptYaml.get_prompt(
        "question_node.yaml",
        course_name=course_name,
        chapter_name=chapter_name or "（不限定章节）",
        cw_context=cw_context or "（暂无）",
        points=kn_points or "（暂无）",
    )
    user_prompt = (
        "请严格输出 10 道练习题的 JSON 数组，"
        "键名固定为 qno（1~10 的整数）和 content（题目的完整陈述）。"
        "题型覆盖：概念理解 / 方法辨析 / 应用举例 / 知识联系 / 总结反思。"
        "题目应基于以上【课程内容】【知识点结构】，不要超出范围。"
        "只输出 JSON 数组本身，不要任何额外文字。"
    )

    r = MyModel.get_model().invoke([("system", sys_prompt), ("user", user_prompt)]).content.strip()
    # 剥 ```json 围栏
    if r.startswith("```"):
        r = r.split("```", 2)[1]
        if r.startswith("json"): r = r[4:]
        r = r.strip().rstrip("`").strip()

    return {"questions": json.loads(r)}
```

**为什么"只输出 JSON"要写在 user prompt 里**：system prompt 负责"考什么"，user prompt 负责"怎么输出"。分开写，调题型时不动角色设定，调格式时不动内容约束。

### （三）收卷与点评

```python
# finish_node.py
def finish_node(state: TestState) -> dict:
    points = Neo4jSearchTool().get_knowledge_points(state["course_name"], state["chapter_name"])

    qa_table = ""
    for i, pair in enumerate(state["qa_pairs"], 1):
        qa_table += f"\n### 第{i}题：{pair['question']}\n**学生回答**：{pair['answer']}\n"

    sys_prompt = BuilderPromptYaml.get_prompt(
        "evaluation_node.yaml",
        course_name=state["course_name"],
        chapter_name=state["chapter_name"] or "（不限定章节）",
        points=points or "（暂无）",
        qa_table=qa_table,
    )
    return {"evaluation_md": MyModel.get_model().invoke(sys_prompt).content}
```

```python
# evaluation_node.py —— 只做落盘，覆盖写，只留最新一版
eval_dir = Path(__file__).resolve().parents[5] / "static" / "evaluation"

def evaluation_node(state: TestState) -> dict:
    eval_dir.mkdir(parents=True, exist_ok=True)
    md_path = eval_dir / f"evaluation_{state['courseware_id']}.md"
    md_path.write_text(state["evaluation_md"], encoding="utf-8")
    return {"evaluation_path": str(md_path)}
```

### （四）业务层

```python
# student_test.py
def start(self):
    state = {..., "mode": "start", "questions": []}
    result = self._run_graph(state)
    if not result or not result.get("questions"):
        return {"code": 500, "message": "出题失败，请稍后重试", "data": {"questions": []}}
    # 只把题干给前端，qno 前端自己按顺序生成
    return {"code": 200, "message": "测试开始，题目已全部生成",
            "data": {"questions": [q["content"] for q in result["questions"]]}}

def finish(self):
    # 先交错落库，保证历史里能回放
    qa_pairs = [{"num": i + 1, "question": q, "answer": a}
                for i, (q, a) in enumerate(zip(self.questions or [], self.answers or []))]
    for pair in qa_pairs:
        self._save_msg("assistant", f"【练习题 {pair['num']}/{len(qa_pairs)}】{pair['question']}")
        self._save_msg("user", f"作答：{pair['answer']}")

    result = self._run_graph({..., "mode": "finish", "qa_pairs": qa_pairs})
    if not result or not result.get("evaluation_path"):
        # 题目答案已经落库，只有报告失败，提示语要说清楚
        return {"code": 500, "message": "测试已提交，但点评报告生成失败，请稍后重试"}
    return {"code": 200, "message": "测试完成，点评报告已生成",
            "data": {"evaluation_path": result["evaluation_path"]}}
```

查看报告直接读文件，不需要再查数据库：

```python
class StudentEvaluation:
    def eval_last(self, courseware_id: int) -> dict:
        md_path = eval_dir / f"evaluation_{courseware_id}.md"
        if not md_path.exists():
            return {"code": 500, "message": "暂无评价，请先完成测试", "data": {"content": ""}}
        return {"code": 200, "message": "获取评价成功",
                "data": {"content": md_path.read_text(encoding="utf-8")}}
```

**验证**：出题返回 10 条字符串 → 全部作答 → 收卷返回 `evaluation_path` → 打开 `static/evaluation/evaluation_{id}.md` 能看到五段式报告；中途退出再进历史，不会出现半截测试记录。

---

## 九、安全加固

前面几章为了先跑通，登录是明文比对、接口没有角色校验。这一章回头补上四件事。

### （一）密码哈希

`app/web/util/password_util.py`

```python
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password) -> str:
    return bcrypt_context.hash(password)

def verify_password(password, hash_pwd) -> bool:
    try:
        return bcrypt_context.verify(password, hash_pwd)
    except Exception as e:
        print(f'【测试】密码验证失败：{e}')
        return False
```

注册时加密、登录时校验，各改一行：

```python
# add_account.py
"password": hash_password(self.password)

# login_account.py
if result["id"] == self.id and verify_password(self.password, result["password"]):
```

**验证**：数据库里 `password` 是 `$2b$12$...` 开头的 60 字符密文；用错误密码登录返回"账号或密码错误"。

### （二）JWT

```python
# app/web/util/jwt_util.py
from jose import JWTError, jwt
from datetime import datetime, timezone, timedelta

def create_token(payload: dict) -> str:
    copy_payload = payload.copy()
    # 过期时间 + 签发时间都塞进 claims，服务端无需存储
    stop_time = datetime.now(timezone.utc) + timedelta(
        minutes=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')))
    copy_payload.update({'exp': stop_time, 'iat': datetime.now(timezone.utc)})
    return jwt.encode(claims=copy_payload, key=os.getenv('SECRET_KEY'),
                      algorithm=os.getenv('ALGORITHM'))

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token=token, key=os.getenv('SECRET_KEY'),
                          algorithms=[os.getenv('ALGORITHM')])
    except JWTError:
        raise HTTPException(status_code=401, detail="token错误或已过期，验证失败")
```

登录成功后返回 token：

```python
token = create_token({"id": self.id, "name": result["name"], "identity": self.identity})
return {"code": 200, "message": "登录成功", "data": result["name"], "token": token}
```

密钥用脚本生成一次，写进 `.env`，**不要提交到 Git**：

```python
# secret_key_util.py
import secrets
print(secrets.token_urlsafe(32))
```

### （三）登出：黑名单

JWT 签出去就撤不回，所以要补一个"吊销名单"。关键是把 TTL 设成 token 的**剩余寿命**：

```python
# logout_account.py
def logout(self) -> dict:
    try:
        payload = verify_token(self.token)
    except HTTPException:
        return {"code": 200, "message": "token已失效，直接退出", "data": None}

    remaining = int(payload.get("exp") - datetime.now(timezone.utc).timestamp())
    remaining = max(remaining, 1)     # 至少 1 秒，保证键写得进去

    if self.token_blacklist.add_token_to_blacklist(self.token, remaining):
        return {"code": 200, "message": "退出登录成功", "data": None}
    return {"code": 500, "message": "退出登录失败，请稍后重试", "data": None}
```

```python
# token_blacklist.py
def add_token_to_blacklist(self, token: str, remaining_seconds: int) -> bool:
    conn = self.redis_conn.get_redis_conn()
    conn.setex(f"token_blacklist:{token}", remaining_seconds, "1")
    self.redis_conn.close_redis_conn(conn)
    return True

def verify_token_in_blacklist(self, token: str) -> bool:
    try:
        conn = self.redis_conn.get_redis_conn()
        result = conn.exists(f"token_blacklist:{token}")
        self.redis_conn.close_redis_conn(conn)
        return bool(result)
    except Exception as e:
        # Redis 挂了就放行：可用性优先，等 Redis 恢复后自然恢复吊销能力
        print(f"【测试】黑名单查询异常，降级放行：{e}")
        return False
```

**为什么 TTL 用剩余时间而不是固定 7 天**：token 过期后黑名单条目就是垃圾。用剩余寿命做 TTL，token 失效的同一刻键也消失，不需要任何清理任务。

### （四）角色权限

```python
# app/web/util/jwt_decode.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="account/login")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    payload = verify_token(token)                       # 验签 + 验过期
    if TokenBlacklist().verify_token_in_blacklist(token):  # 验吊销
        raise HTTPException(401, "token已失效（已登出），请重新登录")
    return payload

def is_roles(*allow_roles):
    def user(now_user: dict = Depends(get_current_user)):
        if now_user.get("identity") in allow_roles[0]:
            return now_user
        raise HTTPException(403, "用户身份不被允许访问该接口")
    return user
```

然后给每个接口挂上依赖：

```python
# 学生端：全部仅学生
@student_router.post("/chat", ...)
def chat(..., now_user: dict = Depends(is_roles(["student"]))): ...

# 课件端：写操作仅教师，读操作共用
@courseware_router.post("/upload", ...)
async def upload(..., now_user: dict = Depends(is_roles(["teacher"]))): ...

@courseware_router.get("/list", ...)
def get_list(now_user: dict = Depends(is_roles(["teacher", "student"]))): ...
```

**为什么用依赖注入而不是全局中间件**：中间件只能拿到路径，做"按路径前缀判角色"的粗粒度控制；依赖注入挂在函数签名上，粒度到单个接口，Swagger 里也能直接看到。代价是"漏写就裸奔"，所以要把角色矩阵列进接口文档，逐个核对。

### （五）前端：拦截器 + 守卫

```js
// main.js —— 请求自动带 token
axios.interceptors.request.use(config => {
  const token = sessionStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 401：清登录态回登录页；403：提示无权限
axios.interceptors.response.use(res => res, err => {
  if (err.response?.status === 401) {
    sessionStorage.clear()
    ElMessage.error('登录已过期或已退出，请重新登录')
    router.push('/login')
  } else if (err.response?.status === 403) {
    ElMessage.error('当前身份无权访问该功能')
  }
  return Promise.reject(err)
})
```

```js
// main.js —— 路由守卫：未登录或身份不符都回首页
router.beforeEach((to, from, next) => {
  if (to.meta.login) {
    if (!sessionStorage.getItem('token')) { next('/'); return }
    if (to.meta.identity && to.meta.identity !== sessionStorage.getItem('identity')) {
      next('/'); return
    }
  }
  next()
})
```

**验证**：

1. 不带 token 调 `/student/chat` → 401；
2. 用学生 token 调 `/courseware/upload` → 403；
3. 登出后再用原 token 调接口 → 401（黑名单生效）；
4. 前端 token 过期 → 自动跳登录页。

---

## 十、联调与交付

### （一）启动顺序

顺序不能乱：外部服务 → 后端 → 前端。

```bash
# 1. 四个外部服务（按本机方式启动，或用 Docker Compose）
#    MySQL / PostgreSQL / Redis / Neo4j

# 2. 后端
conda activate agent_env
cd IC_Server
python main.py            # http://localhost:8000/docs

# 3. 前端
cd IC_Client
npm run dev               # http://localhost:8080
```

### （二）联调清单

按角色走一遍，每条都能验证一类问题：

| # | 操作 | 期望 | 覆盖的点 |
| --- | --- | --- | --- |
| 1 | 注册学生（邮箱验证码） | 收到邮件、入库成功 | SMTP、Redis、bcrypt |
| 2 | 学生登录 | 返回 token，跳转学生页 | JWT |
| 3 | 教师登录并上传 PPTX | 列表出现、状态 2 | 文件分块写盘、MySQL |
| 4 | 点"处理" | 状态 0 → 1，日志走完五节点 | 异步任务、LangGraph |
| 5 | 查看授课脚本 | 返回 Markdown 并落盘 | 图谱查询、LLM |
| 6 | 学生选课件提问 | 逐字输出，能引用课件内容 | 四源检索、SSE |
| 7 | 连续对话 8 轮 | 摘要、长期记忆、画像依次出现 | 四层记忆 |
| 8 | 开始测试 → 交卷 | 10 题、生成五段式报告 | 测试图、文件落盘 |
| 9 | 删除课件 | 六处数据全部清理 | 级联删除 |
| 10 | 登出后重放 token | 401 | 黑名单 |

### （三）常见问题

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 启动报 `int(None)` | `.env` 缺 `MYSQL_HOST` | 补上，值为 `127.0.0.1` |
| 启动报 CUDA 不可用 | `chromadb_model.py` 里 `device="cuda"` | 无显卡改 `"cpu"` |
| 嵌入模型加载失败 | `local_files_only=True` 但模型目录为空 | 先把模型放到 `VECTORIZE_MODEL_PATH` |
| 上传 `.ppt` 报错 | `python-pptx` 不支持旧格式 | 装 `pywin32`，走 `win32com` 转换 |
| 解析一直"处理中" | 后台任务异常但没写状态 | 查日志；手工把 `parse_status` 置 3 |
| 问答检索为空 | 没跑 `Teaching_QA.py` | 跑一遍向量化脚本，确认 `count()` |
| SSE 没有任何输出 | 反向代理缓冲 / 前端没带 token | 关代理缓冲；确认 `Authorization` |
| 登出后仍能访问 | Redis 未启动，黑名单降级放行 | 启动 Redis 再测 |
