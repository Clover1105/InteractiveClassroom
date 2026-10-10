import os
import yaml
from string import Template

class BuilderPromptYaml:
    @staticmethod
    def get_prompt(file_name: str, **kwargs) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, file_name)

        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 模板变量替换（用 $变量名 语法，安全不冲突）
        def _substitute(value) -> object:
            if isinstance(value, str):
                if kwargs:
                    try:
                        return Template(value).safe_substitute(kwargs)
                    except KeyError:
                        return value
                return value
            elif isinstance(value, list):
                return [_substitute(item) for item in value]
            elif isinstance(value, dict):  # ← 新增：处理字典类型
                return {k: _substitute(v) for k, v in value.items()}
            return value

        config = _substitute(config)

        if "prompt" in config:
            # 自由格式
            prompt = config["prompt"]
        else:
            # 结构化
            prompt = (
                f"一 角色:{config['role']}\n"
                f"二 任务:\n{chr(10).join(config['task'])}\n"
                f"三 规则:\n{chr(10).join(config['rule'])}\n"
                f"四 输出:\n{chr(10).join(config['output'])}\n"
                # f"五 示例:\n{chr(10).join(config['example'])}\n"
            )
        return prompt.strip()

if __name__ == '__main__':
    bp = BuilderPromptYaml()
    rs = bp.get_prompt("parse_node.yaml")
    print(rs)
