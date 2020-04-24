import pymysql
from common.myconfig import conf

class HandleDB:

      # def __init__(self):
      #     # 连接到数据库

    def __init__(self):
        host = conf.get_str("mysql","host")
        user = conf.get_str("mysql","user")
        password = conf.get_str("mysql","password")
        port= conf.get_int("mysql","port")
        self.con = pymysql.connect(host = host,
                                 user = user ,
                                 password = password ,
                                 port = port,
                                 charset="utf8")
        self.cur  = self.con.cursor()

    def get_one(self,sql):
        try:
            self.con.commit()
            self.cur.execute(sql)
            return self.cur.fetchone()
        except Exception as e:
            print('查询语句错误', e)
            raise e



    def get_all(self,sql):
        try:
            self.con.commit()
            self.cur.execute(sql)
            return self.cur.fetchall()
        except Exception as e:
            print('查询语句错误', e)
            raise e


    def count(self,sql):
        self.con.commit()
        res = self.cur.execute(sql)
        return res


    def close(self):
        # 关闭游标对象
        self.cur.close()
        # 断开连接
        self.con.close()
if __name__ == '__main__':
    s = HandleDB()
    sql = "SELECT * from futureloan.invest where member_id = 146"
    s.get_one(sql)




