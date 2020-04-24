import unittest
import os
import random
from common.readexcel import ReadExcel
from common.contants import DATA_DIR
from library.ddt import ddt, data
from common.myconfig import conf
from common.handle_request import HandleRequest
from common.mylogger import my_log
from common.handle_db import HandleDB

data_file_path = os.path.join(DATA_DIR, "apicases.xlsx")


@ddt
class TestRegister(unittest.TestCase):
    excel = ReadExcel(data_file_path, "register")
    cases = excel.read_data()
    http = HandleRequest()
    db = HandleDB()

    @data(*cases)
    def test_register(self, case):
        # ------第一步：准备用例数据------------
        # 拼接完整的接口地址
        url = conf.get_str("env", "url") + case["url"]
        # 请求的方法
        method = case["method"]
        # 请求参数
        # 判断是否有有手机号码需要替换
        if "#phone#" in case["data"]:
            # 生成一个手机号码
            phone = self.random_phone()
            print(type(phone))
            # 进行替换
            case["data"] = case["data"].replace("#phone#", phone)

        data = eval(case["data"])
        # 请求头
        headers = eval(conf.get_str("env", "headers"))
        # 预期结果
        expected = eval(case["expected"])
        # 该用例在表单的中所在行
        row = case["case_id"] + 1

        # ------第二步：发送请求到接口，获取实际结果-------

        response = self.http.send(url=url, method=method, json=data, headers=headers)
        result = response.json()
        # --------------------以下内容为扩展内容----------------
        # 先判断是否注册成功，如果是注册成功
        # self.phone = "注册成功的手机号码"  # 没有注册成功就设置未None
        # ---------------------------------------------------

        # -------第三步：比对预期结果和实际结果-----
        try:
            self.assertEqual(expected["code"], result["code"])
            self.assertEqual((expected["msg"]), result["msg"])
            if result["msg"] == "OK":
                # 去数据库查询当前注册的账号是否存在
                sql = "SELECT * FROM futureloan.member where mobile_phone={}".format(phone)
                # 获取数据库中没有没有该用户的信息
                count = self.db.count(sql)
                # 数据库中返回的数据做断言，判断是否有一条数据
                self.assertEqual(1, count)

        except AssertionError as e:
            self.excel.write_data(row=row, column=8, value="未通过")
            my_log.info("用例：{}--->执行未通过".format(case["title"]))
            print("预取结果：{}".format(expected))
            print("实际结果：{}".format(result))
            raise e
        else:
            self.excel.write_data(row=row, column=8, value="通过")

            my_log.info("用例：{}--->执行通过".format(case["title"]))

    @staticmethod
    def random_phone():
        """生成随机的手机号码"""
        phone = "133"
        for i in range(8):
            phone += str(random.randint(0, 9))

        return phone

    @classmethod
    def tearDownClass(cls):
        # 关闭数据的连接和游标对象
        cls.db.close()







