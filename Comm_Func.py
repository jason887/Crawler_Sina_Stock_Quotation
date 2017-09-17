
import re
import datetime
import os
from Oper_Mysql_Class import *

# def PrintDebugLog(msg=""):
#     logFile = open(("XY_%s_%s_ADD_LOG.txt" % (orgCode, strDate)), "w+", encoding='utf8')
#
#     now = datetime.datetime.now()
#     print("\033[1;34mDEBUG INFO: " + now.strftime("%Y-%m-%d %H:%M:%S") + ":\033[0m",msg)
#     logFile.write(now.strftime("%Y-%m-%d %H:%M:%S") +": "+ msg+"\n")
#
# def PrintErrorLog(msg=""):
#     logFile = open(("XY_%s_%s_ADD_LOG.txt" % (orgCode, strDate)), "w+", encoding='utf8')
#     now = datetime.datetime.now()
#     print("\033[1;31mERROR INFO: " + now.strftime("%Y-%m-%d %H:%M:%S") + ":\033[0m",msg)
#     logFile.write(now.strftime("%Y-%m-%d %H:%M:%S") +": "+ msg+"\n")

def debug():
    now = datetime.datetime.now()
    return "\033[1;34mDEBUG INFO: " + now.strftime("%Y-%m-%d %H:%M:%S")+":\033[0m"

def errinfo():
    now = datetime.datetime.now()
    return "\033[1;31mERROR INFO: " + now.strftime("%Y-%m-%d %H:%M:%S")+":\033[0m"

def tmpinfo(msg=""):
    now = datetime.datetime.now()
    if msg != "":
        msg = " " + msg
    return "\033[1;32mTEMP INFO: " + now.strftime("%Y-%m-%d %H:%M:%S") + msg + ":\033[0m"

# print(tmpinfo(),"swerwrwe")


def Get_Now_Date(dateFormat):

    nowDate = datetime.datetime.now()
    Y = nowDate.strftime("%Y")
    M = nowDate.strftime("%m")
    D = nowDate.strftime("%d")

    if dateFormat == "y-m-d":
        strDate = str(Y)+"-"+str(int(M))+"-"+str(int(D))
    elif dateFormat == "yyyy-mm-dd":
        strDate = str(Y)+"-"+str(M)+"-"+str(D)
    elif dateFormat == "yyyymmdd":
        strDate = str(Y)+str(M)+str(D)
    elif dateFormat == "yyyymmdd_HHMMSS":
        strDate = nowDate.strftime("%Y%m%d_%H%M%S")
    else:
        return 'Get_Now_Date("%s"),入参无效' % dateFormat

    return strDate

def format_datetime(up_datetime):
    # 11-22&nbsp;2016
    # 02-06&nbsp;18:05
    # Y-day&nbsp;23:36
    # Today&nbsp;02:02
    # <b>7&nbsp;mins&nbsp;ago</b>
    # 10-17&nbsp;2008
    if 'Y-day' in up_datetime:
        today = datetime.date.today()
        oneday = datetime.timedelta(days=1)
        yesterday = today - oneday
        up_datetime = yesterday.strftime('%Y-%m-%d') + " " + up_datetime[-5:]+":00"
    elif 'ago' in up_datetime:
        today = datetime.datetime.now()
        oneday = datetime.timedelta(hours=8)
        yesterday = today - oneday
        mins = re.sub("\D", "",up_datetime[0:9])
        oneday = datetime.timedelta(minutes=int(mins))
        yesterday = yesterday-oneday
        up_datetime = yesterday.strftime('%Y-%m-%d %H:%M:%S')
    elif 'Today' in up_datetime:
        up_datetime = datetime.datetime.now().strftime('%Y-%m-%d') + " " + up_datetime[-5:]+":00"
    elif '&nbsp;201' in up_datetime:
        up_datetime = up_datetime[-4:] + "-" + up_datetime[0:2] + "-" + up_datetime[3:5] + " " + "00:00:00"
    elif '&nbsp;202' in up_datetime:
        up_datetime = up_datetime[-4:] + "-" + up_datetime[0:2] + "-" + up_datetime[3:5] + " " + "00:00:00"
    elif '&nbsp;200' in up_datetime:
        up_datetime = up_datetime[-4:] + "-" + up_datetime[0:2] + "-" + up_datetime[3:5] + " " + "00:00:00"
    else:
        up_datetime = datetime.datetime.now().strftime('%Y') + "-" + up_datetime[0:2] + "-" + up_datetime[3:5] + " " + up_datetime[-5:]+":00"
    return up_datetime

def Get_Mian_Site_Info(siteName):
    strSql = "select site_url from get_tpb_main_site where site_name = '%s';" % siteName
    siteWeb = mysqlExe.ExecQuery(strSql.encode('utf-8'))[0][0]
    return siteWeb

def Get_TPB_Dict_2_DB_Dict(driver,siteWeb):

    siteWeb = "%s/browse" % siteWeb
    driver.get(siteWeb)

    pageSourceScript = driver.page_source
    # print(pageSourceScript)

    dataReg = re.compile(r'''<select id="category" name="category" onchange="javascript:setAll\(\);">(.+?)</select>''', re.S)
    rawDatas = dataReg.findall(pageSourceScript)[0]
    # print("",rawDatas)

    dataReg = re.compile(r'''<optgroup(.+?)</optgroup>''', re.S)
    subDatas = dataReg.findall(rawDatas)
    for subNode in subDatas :
        dataReg = re.compile(r'''label="(.+?)">''')
        labelName = dataReg.findall(subNode)[0]

        dataReg = re.compile(r'''<option value="(.+?)">(.+?)</option>''')
        subNodeNames = dataReg.findall(subNode)

        for subNodeName in subNodeNames:

            strSql = "select count(*) from sys_dict where dict_the = 'tpb' and dict_id = '%s' and dict_item='%s' and dict_item_sl='%s';" % (subNodeName[0],labelName,subNodeName[1])
            rtnCnt = mysqlExe.ExecQuery(strSql.encode('utf-8'))[0][0]

            if rtnCnt == 0:

                strSql = "INSERT INTO sys_dict (dict_the, dict_id, dict_item, dict_item_sl, dict_item_spf) VALUES ('tpb', '%s', '%s', '%s', '');" % (subNodeName[0],labelName,subNodeName[1])
                mysqlExe.ExecNonQuery(strSql.encode('utf-8'))

def Get_DB_Dict(rs_group):
    if rs_group == "ALL":
        sqlStr = "select dict_id from sys_dict where dict_the = 'tpb';"
    else:
        sqlStr = "select dict_id from sys_dict where dict_the = 'tpb' and dict_item = '"+rs_group+"';"
    listDatas = mysqlExe.ExecQuery(sqlStr.encode('utf-8'))
    groupList = []
    for singData in listDatas:
        groupList.append(singData[0])
    return groupList

def isElementExist(driver):
    flag = True
    try:
        driver.find_element_by_class_name("info").is_displayed()
        return flag
    except:
        flag = False
        return flag

def Get_SEQ_Next_Val(seq_name):
    getSeqNextVal = "select nextval('"+seq_name+"');"
    listsql = mysqlExe.ExecQuery(getSeqNextVal.encode('utf-8'))
    seqVal = int(listsql[0][0])
    return seqVal

def Set_SEQ_Init_Val(seq_name):
    setSeqInitVal = "select setval('"+seq_name+"',0);"
    mysqlExe.ExecNonQuery(setSeqInitVal.encode('utf-8'))

def Get_Search_Name():
    sqlStr = "select like_name from get_tpb_down_search where flag=1;"
    listDatas = mysqlExe.ExecQuery(sqlStr.encode('utf-8'))
    nameList = []
    for singData in listDatas:
        nameList.append(singData[0])
    return nameList

def Get_User_Name():
    sqlStr = "select us_name from get_tpb_down_user where flag=1;"
    listDatas = mysqlExe.ExecQuery(sqlStr.encode('utf-8'))
    nameList = []
    for singData in listDatas:
        nameList.append(singData[0])
    return nameList

# def Set_SEQ_Init_Val_Py(seq_name,value):
#     setSeqInitVal = "update py_sequence set current_value = " + value + " WHERE seq_name = '" + seq_name + "';"
#     mysqlExe.ExecNonQuery(setSeqInitVal.encode('utf-8'))

def Get_Param_In_DB(paraDomain=""):
    if paraDomain == "" :
        sqlStr = "select para_domain,para_name,para_value from sys_parameter where 0=0;"
    else:
        sqlStr = "select para_domain,para_name,para_value from sys_parameter where 0=0 and para_domain='%s';" % paraDomain

    rtnDatas = mysqlExe.ExecQuery(sqlStr.encode('utf-8'))
    if len(rtnDatas) == 0:
        raise ZeroDivisionError("没有取到任何参数信息，请检查参数域等设置！！")
    else:
        dbParamInfo = {}
        for data in rtnDatas:
            paramName = data[1].strip()
            paramValue = data[2].strip()
            dbParamInfo[paramName] = paramValue

        return dbParamInfo