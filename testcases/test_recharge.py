"""
============================
Author:柠檬班-木森
Time:2019/12/6
E-mail:3247119728@qq.com
Company:湖南零檬信息技术有限公司
============================
"""

import unittest
import os
import decimal
import jsonpath
from common.readexcel import ReadExcel
from common.contants import DATA_DIR
from library.ddt import ddt, data
from common.myconfig import conf
from common.handle_request import HandleRequest
from common.mylogger import my_log
from common.handle_db import HandleDB
from common.handle_data import TestData,replace_data

data_file_path = os.path.join(DATA_DIR, "apicases.xlsx")

"""
方式一：
setupclass中提取的用户id和token,如何在用例方法中使用？
1、设为全局变量

2、保存为类属性

3、写入到配置文件

4、保存在临时变量的类中（后面会讲的，先不要去研究）

方式二：
在excel中，第一条用例设计为登录，
# 然后在用例方法中，请求之后去判断否是登录的用例：如果是的就去提取数据，对数据进行保存
1、设为全局变量

2、保存为类属性

3、写入到配置文件

4、保存在临时变量的类中（后面会讲的，先不要去研究）


"""



@ddt
class TestRecharge(unittest.TestCase):
    excel = ReadExcel(data_file_path, "recharge")
    cases = excel.read_data()
    http = HandleRequest()
    db = HandleDB()
    @classmethod
    def setUpClass(cls):
        # # 创建操作数据库的对象
        # cls.db = HandleDB()
        # 登录，获取用户的id以及鉴权需要用到的token
        url = conf.get_str("env", "url") + "/member/login"
        data = {
            "mobile_phone": conf.get_str("test_data", 'user'),
            "pwd": conf.get_str("test_data", "pwd")
        }
        headers = eval(conf.get_str("env", "headers"))
        response = cls.http.send(url=url, method="post", json=data, headers=headers)
        json_data = response.json()
        # -------登录之后，从响应结果中提取用户id和token-------------
        # 1、用户id
        member_id = jsonpath.jsonpath(json_data,"$..id")[0]
        setattr(TestData,"member_id",str(member_id))
        # 2、提取token
        token_type = jsonpath.jsonpath(json_data, "$..token_type")[0]
        token = jsonpath.jsonpath(json_data, "$..token")[0]
        token_data = token_type + " " + token
        setattr(TestData,"token_data",token_data)

    @data(*cases)
    def test_recharge(self, case):
        # ------第一步：准备用例数据------------
        # 拼接完整的接口地址
        url = conf.get_str("env", "url") + case["url"]
        # 请求的方法
        method = case["method"]
        # 请求参数
        # 替换用例参数
        case["data"]= replace_data(case["data"])

        data = eval(case["data"])
        # 请求头
        headers = eval(conf.get_str("env", "headers"))
        headers["Authorization"] = getattr(TestData,"token_data")

        # 预期结果
        expected = eval(case["expected"])
        # 该用例在表单的中所在行
        row = case["case_id"] + 1

        # ------第二步：发送请求到接口，获取实际结果--------

        if case["check_sql"]:
            sql = case["check_sql"].format(conf.get_str("test_data","user"))
            # 获取充值之前的余额
            start_money = self.db.get_one(sql)[0]

        response = self.http.send(url=url, method=method, json=data, headers=headers)
        result = response.json()
        # -------第三步：比对预期结果和实际结果-----
        try:
            self.assertEqual(expected["code"], result["code"])
            self.assertEqual((expected["msg"]), result["msg"])
            if case["check_sql"]:
               sql = case["check_sql"].format(conf.get_str("test_data","user"))
               # 获取充值之后的余额
               end_money = self.db.get_one(sql)[0]
               # 充值的金额
               recharge_money = decimal.Decimal(str(data["amount"]))
               my_log.info("充值之前金额为{}\n,充值金额:{}\n,充值之后金额为{},".format(start_money,recharge_money,end_money))
               # 数据库中返回的数据做断言，判断是否有一条数据
               self.assertEqual(recharge_money, end_money-start_money)

        except AssertionError as e:
            self.excel.write_data(row=row, column=8, value="未通过")
            my_log.info("用例：{}--->执行未通过".format(case["title"]))
            print("预取结果：{}".format(expected))
            print("实际结果：{}".format(result))
            raise e
        else:
            self.excel.write_data(row=row, column=8, value="通过")
            my_log.info("用例：{}--->执行通过".format(case["title"]))

    @classmethod
    def tearDownClass(cls):
        # 关闭数据的连接和游标对象
        cls.db.close()