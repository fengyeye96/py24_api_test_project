import unittest
import os
import jsonpath
from library.ddt import ddt,data
from common.readexcel import ReadExcel
from common.contants import DATA_DIR
from common.handle_request import HandleRequest
from common.myconfig import conf
from common.mylogger import my_log
from common.handle_data import TestData,replace_data
from common.handle_db import HandleDB

data_file_path = os.path.join(DATA_DIR,"apicases.xlsx")
@ddt
class TestInvest(unittest.TestCase):
    excel = ReadExcel(data_file_path,"invest")
    cases = excel.read_data()
    http = HandleRequest()
    db = HandleDB()
    @data(*cases)
    def test_invest(self,case):
        # 第一步：准备用例数据
        # 获取URL
        url = conf.get_str("env","url")+case["url"]
        # 获取请求的方法
        method = case["method"]
        # 获取请求的参数
        # 替换用例参数
        case["data"] = replace_data(case["data"])
        data = eval(case["data"])
        # 获取请求头
        headers = eval(conf.get_str("env","headers"))
        if case["interface"] != "login":
            headers["Authorization"] = getattr(TestData, "token_data")
            # 添加请求头中的token
        # 预期结果
        expected = eval(case["expected"])
        # 获取所在行
        row = case["case_id"]+ 1
        # ------第二步：发送请求到接口，获取实际结果--------
        response = self.http.send(url=url,method=method,headers=headers,json=data)
        result = response.json()
        if case["interface"] == "login":
            # 提取用户id和token
            id = jsonpath.jsonpath(result,"$..id")[0]
            token_type = jsonpath.jsonpath(result,"$..token_type")[0]
            token = jsonpath.jsonpath(result,"$..token")[0]
            token_data = token_type + " " + token
            setattr(TestData,"token_data",token_data)
            setattr(TestData,"member_id",str(id))

        elif case["interface"]=="add":
            # 提取项目id
            loan_id = jsonpath.jsonpath(result,"$..id")[0]
            setattr(TestData,"loan_id",str(loan_id))
        #  -------第三步：比对预期结果和实际结果-----
        try:
            self.assertEqual(expected["code"],result["code"])
            self.assertEqual(expected["msg"],result["msg"])
            # 判断是否需要sql校验
            if case["check_sql"]:
                sql = replace_data(case["check_sql"])
                count = self.db.count(sql)[0]
                # 判断数据库表中是否有一条新数据
                self.assertEqual(1, count)

        except AssertionError as e:
            self.excel.write_data(row =row,column=8,value="未通过")
            my_log.info("用例：{}--->执行未通过".format(case["title"]))
            raise e

        else:
            self.excel.write_data(row=row,column=8,value="通过")
            my_log.info(my_log.info("用例：{}--->执行通过".format(case["title"])))






