""""
项目状态说明：
待审核的项目：数据库的状态为1
审核通过，项目状态会变成2
审核不通过 项目的状态会变成5

"""

import unittest
import os
import jsonpath
from library.ddt import ddt, data
from common.readexcel import ReadExcel
from common.contants import DATA_DIR
from common.handle_db import HandleDB
from common.myconfig import conf
from common.handle_request import HandleRequest
from common.handle_data import TestData, replace_data
from common.mylogger import my_log

file_path = os.path.join(DATA_DIR, "apicases.xlsx")


@ddt
class TestAudit(unittest.TestCase):
    excel = ReadExcel(file_path, "audit")
    cases = excel.read_data()
    http = HandleRequest()
    db = HandleDB()

    @classmethod
    def setUpClass(cls):
        # -----------执行用例之前先进行登录-->
        # 登录，获取用户的id以及鉴权需要用到的token
        url = conf.get_str("env", "url") + "/member/login"
        data = {
            "mobile_phone": conf.get_str("test_data", 'admin_phone'),
            "pwd": conf.get_str("test_data", "admin_pwd")
        }
        headers = eval(conf.get_str("env", "headers"))
        response = cls.http.send(url=url, method="post", json=data, headers=headers)
        json_data = response.json()
        # -------登录之后，从响应结果中提取用户id和token-------------
        # 1、提取用户id
        member_id = jsonpath.jsonpath(json_data, "$..id")[0]
        setattr(TestData, "member_id", str(member_id))
        # 2、提取token
        token_type = jsonpath.jsonpath(json_data, "$..token_type")[0]
        token = jsonpath.jsonpath(json_data, "$..token")[0]
        token_data = token_type + " " + token
        setattr(TestData, "token_data", token_data)

    def setUp(self):
        # ---------每个审核的用例执行之前都加一个项目，将项目id保存起来----------
        url = conf.get_str("env", "url") + "/loan/add"
        data = {"member_id": getattr(TestData, "member_id"),
                "title": "借钱实现财富自由",
                "amount": 2000,
                "loan_rate": 12.0,
                "loan_term": 3,
                "loan_date_type": 1,
                "bidding_days": 5}
        headers = eval(conf.get_str("env", "headers"))
        headers["Authorization"] = getattr(TestData, "token_data")
        # 发送请求加标
        response = self.http.send(url=url, method="post", json=data, headers=headers)
        json_data = response.json()
        # 1、提取标id
        loan_id = jsonpath.jsonpath(json_data, "$..id")[0]
        # 2、保存为TestDate的属性
        setattr(TestData, "loan_id", str(loan_id))

    @data(*cases)
    def test_audit(self, case):
        # 拼接完整的接口地址
        url = conf.get_str("env", "url") + case["url"]
        # 请求的方法
        method = case["method"]
        # 请求参数
        # 替换用例参数
        case["data"] = replace_data(case["data"])
        data = eval(case["data"])
        # 请求头
        headers = eval(conf.get_str("env", "headers"))
        headers["Authorization"] = getattr(TestData, "token_data")

        # 预期结果
        expected = eval(case["expected"])
        # 该用例在表单的中所在行
        row = case["case_id"] + 1

        # ------第二步：发送请求到接口，获取实际结果--------

        response = self.http.send(url=url, method=method, json=data, headers=headers)
        result = response.json()


        # 如果审核通过的项目返回ok，说明该项目已审核
        if case["title"] == "审核通过" and result["msg"] == "OK":
            pass_loan_id = getattr(TestData, 'loan_id')
            # 将该项目的id保存起来
            setattr(TestData, "pass_loan_id", pass_loan_id)

        # -------第三步：比对预期结果和实际结果-----
        try:
            self.assertEqual(expected["code"], result["code"])
            self.assertEqual((expected["msg"]), result["msg"])
            if case["check_sql"]:
                sql = replace_data(case["check_sql"])
                # 获取这个标的用户id
                status = self.db.get_one(sql)[0]
                # 进行断言
                self.assertEqual(expected["status"], status)
        except AssertionError as e:
            self.excel.write_data(row=row, column=8, value="未通过")
            my_log.info("用例：{}--->执行未通过".format(case["title"]))
            raise e
        else:
            self.excel.write_data(row=row, column=8, value="通过")
            my_log.info("用例：{}--->执行通过".format(case["title"]))


