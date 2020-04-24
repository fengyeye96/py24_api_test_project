

import unittest
import os
import jsonpath
from library.ddt import ddt, data
from common.readexcel import ReadExcel
from common.contants import DATA_DIR
from common.myconfig import conf
from common.handle_data import replace_data, TestData
from common.handle_request import HandleRequest
from common.mylogger import my_log
from common.handle_db import HandleDB
file_path = os.path.join(DATA_DIR, "apicases.xlsx")


@ddt
class TestAdd(unittest.TestCase):
    excel = ReadExcel(file_path, "add")
    cases = excel.read_data()
    http = HandleRequest()
    db = HandleDB()
    @data(*cases)
    def test_add(self, case):
        # 第一步：准备用例数据
        # 获取url
        url = conf.get_str("env", "url") + case["url"]
        # 获取数据
        case["data"] = replace_data(case["data"])
        data = eval(case["data"])
        # 请求头
        headers = eval(conf.get_str("env", "headers"))
        if case["interface"] != "login":
            headers["Authorization"] = getattr(TestData, "token_data")
        # 预期结果
        expected = eval(case["expected"])
        # 请求方法
        method = case["method"]
        # 用例所在的行
        row = case["case_id"] + 1
        # 第二步：发送请求
        print(url, method, data, headers)
        res = self.http.send(url=url, method=method, json=data, headers=headers)
        json_data = res.json()
        print("json_data=", json_data)
        if case["interface"] == "login":
            # 如果是登录的用例，提取对应的token,和用户id,保存为TestData这个类的类属性，用来给后面的用例替换
            token_type = jsonpath.jsonpath(json_data, "$..token_type")[0]
            token = jsonpath.jsonpath(json_data, "$..token")[0]
            token_data = token_type + " " + token
            setattr(TestData, "token_data", token_data)
            id = jsonpath.jsonpath(json_data, "$..id")[0]
            setattr(TestData, "admin_member_id", str(id))
        # 第三步：断言
        try:
            self.assertEqual(expected["code"], json_data["code"])
            self.assertEqual(expected["msg"], json_data["msg"])

        except AssertionError as e:
            self.excel.write_data(row=row, column=8, value="未通过")
            my_log.info("用例：{}--->执行未通过".format(case["title"]))
            print("预取结果：{}".format(expected))
            print("实际结果：{}".format(json_data))
            raise e
        else:
            self.excel.write_data(row=row, column=8, value="通过")
            my_log.info("用例：{}--->执行通过".format(case["title"]))



