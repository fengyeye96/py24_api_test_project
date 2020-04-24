
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
from common.handle_data import replace_data,TestData

data_file_path = os.path.join(DATA_DIR, "apicases.xlsx")

"""
方式二：
在excel中，第一条用例设计为登录，
# 然后在用例方法中，请求之后去判断否是登录的用例：如果是的就去提取数据，对数据进行保存
1、设为全局变量
2、保存为类属性
3、写入到配置文件
4、保存在临时变量的类中（后面会讲的，先不要去研究）
"""

@ddt
class TestWithdraw(unittest.TestCase):
    excel = ReadExcel(data_file_path, "withdraw")
    cases = excel.read_data()
    http = HandleRequest()
    db = HandleDB()

    @classmethod
    def setUpClass(cls):
        # 获取登录用户手机号和密码
        # cls.mobile_phone = conf.get_str("test_data", 'user')
        # cls.pwd = conf.get_str("test_data", "pwd")
       pass




    @data(*cases)
    def test_withdraw(self, case):
        # ------第一步：准备用例数据------------
        # 拼接完整的接口地址
        url = conf.get_str("env", "url") + case["url"]
        # 请求的方法
        method = case["method"]
        # 请求参数
        # 判断是否有用户id需要替换
        case["data"] = replace_data(case["data"])
        data = eval(case["data"])

        # 请求头
        headers = eval(conf.get_str("env", "headers"))
        if case["interface"] != "login":
            headers["Authorization"] = getattr(TestData,"token_data")
        # 预期结果
        expected = eval(case["expected"])
        # 该用例在表单的中所在行
        row = case["case_id"] + 1

        # ------第二步：发送请求到接口，获取实际结果--------
        # 判断是否需要sql校验
        if case["check_sql"]:
            sql = case["check_sql"].format(conf.get_str("test_data", 'user'))
            # 获取取充值之前的余额
            start_money = self.db.get_one(sql)[0]
        # 发送请求，获取结果
        response = self.http.send(url=url, method=method, json=data, headers=headers)
        result = response.json()


        if case["interface"] == "login":
            # -------如果是登录接口，从响应结果中提取用户id和token-------------
            # 1、用户id
            member_id = jsonpath.jsonpath(result, "$..id")[0]
            setattr(TestData,"member_id",str(member_id))

            # 2、提取token
            token_type = jsonpath.jsonpath(result, "$..token_type")[0]

            token = jsonpath.jsonpath(result, "$..token")[0]
            token_data = token_type + " " + token

            # 下面这行代码和上面哪行代码是一个意思，都是将token设为类属性

            setattr(TestData, "token_data",token_data)
        # -------第三步：比对预期结果和实际结果-----
        try:
            self.assertEqual(expected["code"], result["code"])
            self.assertEqual((expected["msg"]), result["msg"])
            # 判断是否需要数据库校验
            if case["check_sql"]:
                sql = case["check_sql"].format(conf.get_str("test_data", 'user'))
                # 获取取充值之前的余额
                end_money = self.db.get_one(sql)[0]
                recharge_money = decimal.Decimal(str(data["amount"]))
                my_log.info("取现之前金额为{}\n，取现金额为：{}\n，取现之后金额为{}，".format(start_money, recharge_money, end_money))
                # 进行断言(开始的金额减去结束的金额)
                self.assertEqual(recharge_money, start_money - end_money)

        except AssertionError as e:
            self.excel.write_data(row=row, column=8, value="未通过")
            my_log.info("用例：{}--->执行未通过".format(case["title"]))
            print("预取结果：{}".format(expected))
            print("实际结果：{}".format(result))
            raise e
        else:
            self.excel.write_data(row=row, column=8, value="通过")
            my_log.info("用例：{}--->执行通过".format(case["title"]))









