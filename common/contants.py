import os

"""
该模块用来处理整个项目目录的路径

"""

#
# res = os.path.dirname(__file__)
# BASEDIR = os.path.dirname(res)

# 获取当前文件的绝对路径
# dir = os.path.abspath(__file__)
# print(dir)
# print(__file__)


# 项目目录的路径 | 如果运行的时候项目目录路径出错，使用上面abspath的方式来获取当前文件的绝对路径
BASEDIR = os.path.dirname(os.path.dirname(__file__))
# 配置文件的路径
CONF_DIR = os.path.join(BASEDIR, "conf")
# 用例数据的目录
DATA_DIR = os.path.join(BASEDIR, "data")
# 日志文件目录
LOG_DIR = os.path.join(BASEDIR, "log")
# 测试报告的目录
REPORT_DIR = os.path.join(BASEDIR, "reports")
# 测试用例模块所在的目录
CASE_DIR = os.path.join(BASEDIR, "testcases")