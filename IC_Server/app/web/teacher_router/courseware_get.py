from app.web.tool.mysql_select_tool import MySQLSelect

class CoursewareGet:
    def __init__(self) -> None:
        self.mysql_select = MySQLSelect()

    def get_cur_list(self) -> dict:
        sql_select = "select * from courseware"
        result = self.mysql_select.select_courseware(sql_select) # 字典
        return {
            "code":200,
            "message":"获取课件列表成功",
            "data":result
        }