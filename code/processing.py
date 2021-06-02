import os
import sys
import json
import requests
import pandas as pd
import sqlite3
import datetime

os.chdir(sys.path[0])
# 得到json文件
r = requests.get(
    'https://portal.pku.edu.cn/portal2017/publicsearch/canteen/retrCarteenInfos.do')
a = json.loads(r.text)
# 似乎到23：58会停止更新（判断一下和之前是否相同
f1 = open('../data/latest.json', 'r')
fro_a = json.loads(f1.read())
if(a['time'] == fro_a['time']):
    f1.close()
    sys.exit()
f1.close()

f2 = open('../data/latest.json', 'w')
f2.write(json.dumps(a))
f2.close()


# 转成dataframe
df = pd.DataFrame(a['rows'], index=[a['time']]*len(a['rows']))
df.drop(df.columns[3], axis=1, inplace=True)  # 删除多余信息
# print(df)

# 连接数据库
conn = sqlite3.connect(
    sys.path[0]+'/../data/shows.db', check_same_thread=False)
#print("Opened database successfully")
# 创建游标
curs = conn.cursor()
SQL = "CREATE TABLE if not exists canteens(\
        ID INTEGER PRIMARY KEY AUTOINCREMENT,\
        DATETIME TEXT,\
        IP INTEGER,\
        NAME CHAR(20),\
        SEAT INTEGER\
        );"
curs.execute(SQL)

# 数据存入数据库
for i in range(len(df)):
    dateTime_p = datetime.datetime.strptime(df.index[i], '%Y-%m-%d %H:%M')

    # ip,name,seat
    SQL = "INSERT INTO canteens (DATETIME,IP,NAME,SEAT) VALUES("\
        + "'"+str(dateTime_p)+"',"\
        + str(df.iloc[i, 0])+","\
        + "'"+df.iloc[i, 1]+"',"\
        + str(df.iloc[i, 2]) +\
        ")"
    # print(SQL)
    curs.execute(SQL)

conn.commit()
conn.close()
