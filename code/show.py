import os
import sys
import json
import pandas as pd
import sqlite3
import datetime

from pyecharts.charts import WordCloud, Line, Pie, Timeline
from pyecharts import options as opts


os.chdir(sys.path[0])

# 得到食堂数据（名字）
f = open('../data/latest.json', 'r')
a = json.loads(f.read())
f.close()
df = pd.DataFrame(a['rows'], index=[a['time']]*len(a['rows']))
df.drop(df.columns[3], axis=1, inplace=True)

conn = sqlite3.connect(
    sys.path[0]+'/../data/shows.db', check_same_thread=False)
curs = conn.cursor()

# 过去*天早中晚餐峰值时间，
# 当天人数变化+预测，各个食堂当前拥挤度
# 读取数据


for rows in df.itertuples():
    real_data = []
    forecast_data = []
    canteen = rows.name
    seat = rows.seat
    today = datetime.date.today()
    dt_begin = datetime.datetime(today.year, today.month, today.day, 6)
    dt_now = datetime.datetime.today()
    # print(dt_begin)

    # 读取当天真实访问数据 6:00-now
    SQL = "SELECT * FROM canteens WHERE DATETIME >= '%s' AND DATETIME <= '%s' AND NAME = '%s';" % (
        str(dt_begin), str(dt_now), canteen)
    result = curs.execute(SQL)
    for tmp in result:
        real_data.append(tmp)

    # 读取当天预测数据 6:00-23:58
    SQL = "SELECT * FROM forecast WHERE DATETIME >= '%s' AND DATETIME <= '%s' AND NAME = '%s';" % (
        str(dt_begin), str(dt_begin+datetime.timedelta(hours=18)), canteen)
    result = curs.execute(SQL)
    for tmp in result:
        forecast_data.append(tmp)
    
    #for i in :


conn.close()
