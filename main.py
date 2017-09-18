#!/usr/bin/python
# coding=utf-8

import re
import datetime
import ast
import time
import math
import urllib, urllib.request, urllib.error
import http.cookiejar
from multiprocessing.pool import Pool
from Oper_Mysql_Class import mysqlExe, paramInfo
from Comm_Func import *

# 模拟访问的主机头
headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
    'Content-type': 'application/x-www-form-urlencoded',
    'Host': 'vip.stock.finance.sina.com.cn',
    'Proxy-Connection': 'keep-alive',
    'Referer': 'http://vip.stock.finance.sina.com.cn/mkt/',
    'Cookie': 'U_TRS1=00000003.60b950d2.59a4315b.94e8025d; UOR=www.baidu.com,blog.sina.com.cn,; SINAGLOBAL=60.168.196.3_1503932765.188387; Apache=172.16.92.24_1504977455.437036; ULV=1505043151282:3:2:1:172.16.92.24_1504977455.437036:1504716602899; U_TRS2=0000003c.eac0b52.59b522d8.4ef968fe; SR_SEL=1_511; SGUID=1505577900705_10744876; rotatecount=5; lxlrttp=1504173940; FINANCE2=188db5c668e55e32add7da9187ae8f9b; SUB=_2AkMu4e_4f8NxqwJRmP4Qz23rb4RwyQ7EieKYvR4jJRMyHRl-yD83qhYotRCO5GBdtFrd7wPNry7ETE9MvrOUew..',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
}  # 虚拟主机头信息

# 格式化打印调试信息
def prtlog(printstr):
    return  print(str(datetime.datetime.now()) + " DEBUG INFO" +  " : " + printstr)

# 返回sina行情里的总记录数
def __GetSina_Stock_Count(stockCntUrl):
    request = urllib.request.Request(url=stockCntUrl, headers=headers)

    request = urllib.request.urlopen(request)  # 这里是要读取内容的url
    content = request.read().decode("unicode_escape", "ignore")  # 读取，一般会在这里报异常

    # stockCnt = re.findall(r'\w*([0-9]+)\w*',content)[0]
    stockCnt = re.sub("\D", "", content)
    return stockCnt

# 将sina行情返回的数据格式化为标准的python数组
def __Format_Stock_List(stockInfoContent,stockType):

    try:
        currDate = time.strftime('%Y%m%d', time.localtime(time.time()))
        stockInfoRegex = re.compile(r'''{(.+?)}''')
        sinaStockInfoList = stockInfoRegex.findall(stockInfoContent)

        # 定义一个汇总数组 用于保存所有的股票信息
        allStockInfoList = []

        cnt = 0

        for tempSinaStockInfo in sinaStockInfoList:
            cnt += 1

            # 分割取回的全部股票信息，使之成为单一股票信息为一个字符端
            sinaSingStockInfo = tempSinaStockInfo.split(",")
            # print(tmpinfo(str(cnt)),sinaSingStockInfo)

            # 定义一个单一股票字典
            singStockDictExt = {}

            # 把单一股票字符串按字段分割
            for sinaSingStockField in sinaSingStockInfo:
                singStockDict = {}

                singStockDict["date"] = currDate
                singStockDict["class"] = stockType
                singStockDictExt.update(singStockDict) # 追加有一个日期字段

                if '"' in sinaSingStockField:
                    # 字段字符中存在两种情况，一种是字符型 有双引号 需要用正则表达式区分
                    reField = re.compile(r'''(.+?):"(.+?)"''')
                    sinaSingStockFieldSub = reField.findall(sinaSingStockField)[0]
                    singStockDict[sinaSingStockFieldSub[0]] = sinaSingStockFieldSub[1]
                else:
                    # 一种是字段值为数字，没有双引号，用字符分割方式即可
                    sinaSingStockFieldSub = sinaSingStockField.split(":")
                    # 字典模式 字段名为字典key 值为value
                    singStockDict[sinaSingStockFieldSub[0]] = sinaSingStockFieldSub[1]
                singStockDictExt.update(singStockDict)

            # 把字典写入到汇总数组中,并返回给其他函数使用
            allStockInfoList.append(singStockDictExt)

        return allStockInfoList

    except Exception as e:
        print(e)

def __Get_Sina_Stock(queryParam):

    currDate = time.strftime('%Y%m%d', time.localtime(time.time()))

    rtnListUrl = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=%s&num=%d&sort=symbol&asc=1&node=%s&symbol=&_s_r_a=page' % (queryParam["pageNum"], queryParam["pageMaxRows"], queryParam["stockType"])

    request = urllib.request.Request(url=rtnListUrl, headers=headers)
    request = urllib.request.urlopen(request)  # 这里是要读取内容的url
    stockInfoContent = request.read().decode("gbk", "ignore")  # 读取，一般会在这里报异常


    if stockInfoContent == "null":
        print(errinfo(),rtnListUrl)
        return False

    stockInfoList = __Format_Stock_List(stockInfoContent, queryParam["stockType"])

    for stockInfo in stockInfoList:
        # print("xx ",currDate,len(stockInfo),stockInfo)

        strSql = "select count(*) from sina_stock_quotes where 0=0 and code='%s' and date='%s';" % (stockInfo["code"], currDate)
        rtnCnt = mysqlExe.ExecQuery(strSql)[0][0]
        # print(tmpinfo("11"),strSql)

        if rtnCnt == 0:
            strSqlExe = "INSERT INTO sina_stock_quotes (date, symbol, code, name, trade, pricechange, changepercent, buy, sell, settlement, open, high, low, volume, " \
                        "amount, ticktime, per, pb, mktcap, nmc, turnoverratio, class) VALUES (" \
                        "'%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % \
                        (stockInfo["date"], stockInfo["symbol"], stockInfo["code"], stockInfo["name"],
                         stockInfo["trade"], stockInfo["pricechange"], stockInfo["changepercent"],
                         stockInfo["buy"], stockInfo["sell"], stockInfo["settlement"],
                         stockInfo["open"], stockInfo["high"], stockInfo["low"], stockInfo["volume"],
                         stockInfo["amount"],
                         stockInfo["ticktime"], stockInfo["per"], stockInfo["pb"], stockInfo["mktcap"],
                         stockInfo["nmc"], stockInfo["turnoverratio"], stockInfo["class"])
        else:
            strSqlExe = "UPDATE sina_stock_quotes SET name='%s', trade='%s', pricechange='%s', changepercent='%s', buy='%s', sell='%s', settlement='%s', open='%s', high='%s', low='%s', volume='%s', " \
                        "amount='%s', ticktime='%s', per='%s', pb='%s', mktcap='%s', nmc='%s', turnoverratio='%s', class='%s' WHERE 0=0 and code='%s' and date = '%s';" % \
                        (stockInfo["name"], stockInfo["trade"],
                         stockInfo["pricechange"], stockInfo["changepercent"], stockInfo["buy"],
                         stockInfo["sell"], stockInfo["settlement"], stockInfo["open"],
                         stockInfo["high"], stockInfo["low"],
                         stockInfo["volume"], stockInfo["amount"], stockInfo["ticktime"],
                         stockInfo["per"], stockInfo["pb"], stockInfo["mktcap"], stockInfo["nmc"],
                         stockInfo["turnoverratio"],stockInfo["class"],
                         stockInfo["code"],stockInfo["date"])

        print(debug(),strSqlExe)
        mysqlExe.ExecNonQuery(strSqlExe.encode('utf-8'))

def __Get_Sina_Crawker_Param(stockTypeList) :

    sinaStockQueryParam = []

    for stockType in stockTypeList:
        stockCntUrl = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount?node=%s' % (stockType)
        rtnCnt = __GetSina_Stock_Count(stockCntUrl)

        pageUpperLimit = math.ceil(int(rtnCnt)/pageMaxRows)

        for i in range(1, pageUpperLimit+1):
            dictStockQueryParam = {}
            dictStockQueryParam["stockType"] = stockType
            dictStockQueryParam["pageNum"] = i
            dictStockQueryParam["pageMaxRows"] = pageMaxRows
            sinaStockQueryParam.append(dictStockQueryParam)

    return sinaStockQueryParam

def __Push_Sina_Cookies(rootUrl):

    # 模拟访问的主机头
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Content-type': 'application/x-www-form-urlencoded',
        'Host': 'vip.stock.finance.sina.com.cn',
        'Proxy-Connection': 'keep-alive',
        'Referer': 'http://vip.stock.finance.sina.com.cn/mkt/',
        'Cookie':'U_TRS1=00000003.60b950d2.59a4315b.94e8025d; UOR=www.baidu.com,blog.sina.com.cn,; SINAGLOBAL=60.168.196.3_1503932765.188387; Apache=172.16.92.24_1504977455.437036; ULV=1505043151282:3:2:1:172.16.92.24_1504977455.437036:1504716602899; U_TRS2=0000003c.eac0b52.59b522d8.4ef968fe; SR_SEL=1_511; SGUID=1505577900705_10744876; rotatecount=5; lxlrttp=1504173940; FINANCE2=188db5c668e55e32add7da9187ae8f9b; SUB=_2AkMu4e_4f8NxqwJRmP4Qz23rb4RwyQ7EieKYvR4jJRMyHRl-yD83qhYotRCO5GBdtFrd7wPNry7ETE9MvrOUew..',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
    }  # 虚拟主机头信息

    # request = urllib.request.Request(url=rootUrl, headers=headers)
    # request = urllib.request.urlopen(request)  # 这里是要读取内容的url
    # # content = request.read().decode("unicode_escape", "ignore")  # 读取，一般会在这里报异常
    # content = request.read().decode("gb2312", "ignore")  # 读取，一般会在这里报异常

    # cj = http.cookiejar.CookieJar()
    # opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    # urllib.request.install_opener(opener)
    # r = opener.open(rootUrl)
    # print(r.read().decode("unicode_escape", "ignore"))
    # print(cj)

    return headers

if __name__ == "__main__":

    # headers = __Push_Sina_Cookies("http://vip.stock.finance.sina.com.cn/mkt")

    # strSql = "select count(*) from sina_stock_quotes;"
    # rtnCnt = mysqlExe.ExecQuery(strSql)
    # print(rtnCnt)

    startRunTime = time.clock()  # 记录脚本运行起始时间

    pageMaxRows = int(paramInfo["PAGE_MAX_RTN_ROWS"])

    # node = ["hs_a", "hs_b", "hs_z", "zxqy", "cyb", "shfxjs", "hs_s"]
    stockTypeList = ["sh_a", "sh_b", "sz_a", "sz_b","sh_z","sz_z"]

    sinaStockQueryParam = __Get_Sina_Crawker_Param(stockTypeList)

    pool = Pool(processes=int(paramInfo["PROC_NUM"]))
    for queryParam in sinaStockQueryParam:
        pool.apply_async(__Get_Sina_Stock, (queryParam,))  # 启用线程池机制
        # __Get_Sina_Stock(queryParam)

    pool.close()
    pool.join()

    endRunTime = time.clock()  # 记录程序运行结束时间
    print()
    print(debug(),"read: %f s" % (endRunTime - startRunTime))



