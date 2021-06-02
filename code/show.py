import os
import sys
import json
import pandas as pd
import sqlite3
import datetime

from pyecharts.charts import Bar, Line, Pie, Timeline, Geo, Page, Map
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


# 生成折线图
part1 = Timeline(init_opts=opts.InitOpts(width='3600px',
                                         height='500px',
                                         page_title="食堂实时拥挤度变化"))


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
    time_list = ["%02d:%02d"%((dt_begin+datetime.timedelta(minutes=2*i)).hour,
                            (dt_begin+datetime.timedelta(minutes=2*i)).minute) for i in range(540)]

    # 读取当天真实访问数据 6:00-now
    SQL = "SELECT * FROM canteens WHERE DATETIME >= '%s' AND DATETIME <= '%s' AND NAME = '%s';" % (
        str(dt_begin), str(dt_now), canteen)
    result = curs.execute(SQL)

    t_time=dt_begin
    for row in result:
        while datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')>t_time:
            t_time+=datetime.timedelta(minutes=2)
            if t_time == dt_begin:
                real_data.append(0.0)
            else:
                real_data.append(real_data[-1])
        real_data.append(row[2]*100.0/row[4])
        t_time+=datetime.timedelta(minutes=2)

    # 读取当天预测数据 6:00-23:58
    SQL = "SELECT * FROM forecast WHERE DATETIME >= '%s' AND DATETIME <= '%s' AND NAME = '%s';" % (
        str(dt_begin), str(dt_begin+datetime.timedelta(hours=18)), canteen)
    result = curs.execute(SQL)
    
    t_time=dt_begin
    for row in result:
        while datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')>t_time:
            t_time+=datetime.timedelta(minutes=2)
            if t_time == dt_begin:
                forecast_data.append(0.0)
            else:
                forecast_data.append(real_data[-1])
        forecast_data.append((row[3]*100.0/row[4])*(1.0+row[5]))
        t_time+=datetime.timedelta(minutes=2)
    #print(real_data)
    line = (
        Line()
        .add_xaxis(time_list)
        .add_yaxis("拥挤度变化",
                   y_axis=real_data,
                   is_symbol_show=False,
                   color="red",
                   label_opts=opts.LabelOpts(is_show=False),
                   is_smooth=True)
        .add_yaxis("拥挤度预测",
                   y_axis=forecast_data,
                   is_symbol_show=False,
                   color="grey",
                   label_opts=opts.LabelOpts(is_show=False),
                   is_smooth=True)
        .set_global_opts(
            title_opts=opts.TitleOpts(title="{}实时拥挤度变化".format(canteen),
                                      pos_left='center', pos_top='5%'),
        )
    )
    part1.add(line, canteen)


conn.close()


pages = Page(page_title="人口自然增长率", layout=Page.SimplePageLayout)
pages.add(part1)
pages.render("../web/show.html")
