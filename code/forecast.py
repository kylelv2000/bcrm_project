import os
import sys
import json
import time
import requests
import pandas as pd
import sqlite3
import datetime

os.chdir(sys.path[0])

#得到最新数据
f = open('../data/latest.json', 'r')
a = json.loads(f.read())
f.close()
df = pd.DataFrame(a['rows'], index=[a['time']]*len(a['rows']))
df.drop(df.columns[3], axis=1, inplace=True)

conn = sqlite3.connect(sys.path[0]+'/../data/shows.db')
curs = conn.cursor()

# 预测数据

#若不存在则新建
SQL = "CREATE TABLE if not exists forecast(NAME CHAR[20],IP DOUBLE,SEAT INTEGER);"
curs.execute(SQL)

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
