from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from typing import Any
import os
load_dotenv()

"""
基于单例模式的模型封装
"""

class MyModel:
    # 定义私有属性
    _model = None
    # 定义本地模型私有属性
    _local_model = None
    # 定义语音模型
    _vosk_model = None
    # 定义静态函数，在线模型
    @staticmethod   # 静态方法，不需要实例化对象就可以调用
    def get_model() -> Any:
        # 判断_model是否为空
        if MyModel._model is None:
            # 为空，创建模型
            MyModel._model = ChatOpenAI(
                model=os.getenv("MODEL_ONLINE_NAME"),
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                streaming=True,
                # 是否开启思考模式
                extra_body={
                    "enable_thinking": False
                }
            )
        return MyModel._model

    # 本地模型创建
    @staticmethod
    def get_local_model() -> Any:
        # 判断_local_model是否为空，为空，创建模型
        if MyModel._local_model is None:
            MyModel._local_model = ChatOpenAI(
                model=os.getenv("MODEL_LOCAL_NAME"),
                api_key="22",
                base_url=os.getenv("LOCAL_URL"),
                streaming=True,
                # 是否开启思考模式
                extra_body={
                    "enable_thinking": False
                }
            )
        return MyModel._local_model


if __name__ == '__main__':
    model = MyModel.get_model()
    # model = MyModel.get_local_model()
    rs = model.invoke("你好")
    print(rs)



























