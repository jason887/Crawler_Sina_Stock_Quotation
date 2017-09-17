import pymysql
import os
import platform
from Comm_Func import *

class MySQL:

    def __init__(self, host, user, pwd, db, port):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.db = db
        self.port = port

    def __GetConnect(self):
        if not self.db:
            raise (NameError, "没有设置数据库信息")
        self.conn = pymysql.connect(host=self.host, user=self.user, password=self.pwd, database=self.db, port=self.port, charset="utf8")
        cur = self.conn.cursor()
        if not cur:
            raise (NameError, "连接数据库失败")
        else:
            return cur

    def ExecQuery(self, sql):
        cur = self.__GetConnect()
        cur.execute(sql)
        resList = cur.fetchall()

        # 查询完毕后必须关闭连接
        # self.conn.close()
        return resList

    def ExecNonQuery(self, sql):
        cur = self.__GetConnect()
        rtn = cur.execute(sql)
        self.conn.commit()
        # self.conn.close()
        return rtn


def Get_Param_Info(Config):

    if os.path.isfile(Config) == False:
        raise Exception("错误，全局参数配置文件不存在")

    paramInfo = {}
    for line in open(Config,"r",encoding= 'UTF-8'):
        if line != "\n" :
            info = line.strip("\n")
            # 首字符为 # ; 等符号 视为注释
            if info.strip()[0] != "#" and info.strip()[0] != ";" and info.strip()[0] != "[" :
                # print(info.strip()[0])
                info = info.split("=")
                if len(info) == 2:
                    paramName = info[0].strip()
                    paramValue = info[1].strip()
                    paramInfo[paramName]=paramValue
    return paramInfo

sysType = platform.system()

if sysType == "Windows":
    configFile = r".\Config.ini"
elif sysType == "Linux":
    configFile = r"/my_workspace/python/Oper_Qnap_Transmission/Config.ini"
elif sysType == "Darwin":  # mac
    configFile = r"./Config.ini"

paramInfo = Get_Param_Info(configFile)

# 引入mysql操作函数
mysqlExe = MySQL(
    host = paramInfo["DB_HOST"],
    user = paramInfo["USER_NAME"],
    pwd = paramInfo["USER_PWD"],
    db = paramInfo["DB_NAME"],
    port = int(paramInfo["DB_PORT"])
)

