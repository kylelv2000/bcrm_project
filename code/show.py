import os
import sys
import json
import pandas as pd
import sqlite3
import datetime

from pyecharts.charts import Bar, Line, Grid, Timeline, Gauge, Page
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

# 过去*天早中晚餐峰值时间
# 当天人数变化+预测，各个食堂当前拥挤度


# 生成折线图
part1 = (Timeline(init_opts=opts.InitOpts(width='3600px',
                                          height='700px',
                                          page_title="食堂实时拥挤度变化")
                  )
         .add_schema(pos_left='3%',
                     pos_right='3%',
                     is_auto_play=False,
                     label_opts=opts.LabelOpts(is_show=True,
                                               position="bottom")
                     )
         )

c = []
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
    time_list = ["%02d:%02d" % ((dt_begin+datetime.timedelta(minutes=2*i)).hour,
                                (dt_begin+datetime.timedelta(minutes=2*i)).minute) for i in range(540)]

    # 读取当天真实访问数据 6:00-now
    SQL = "SELECT * FROM canteens WHERE DATETIME >= '%s' AND DATETIME <= '%s' AND NAME = '%s';" % (
        str(dt_begin), str(dt_now), canteen)
    result = curs.execute(SQL)

    t_time = dt_begin
    for row in result:
        while datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') > t_time:
            if t_time == dt_begin:
                real_data.append(0.0)
            else:
                real_data.append(real_data[-1])
            t_time += datetime.timedelta(minutes=2)
        real_data.append(row[2]*100.0/row[4])
        t_time += datetime.timedelta(minutes=2)

    # 读取当天预测数据 6:00-23:58
    SQL = "SELECT * FROM forecast WHERE DATETIME >= '%s' AND DATETIME <= '%s' AND NAME = '%s';" % (
        str(dt_begin), str(dt_begin+datetime.timedelta(hours=18)), canteen)
    result = curs.execute(SQL)

    t_time = dt_begin
    for row in result:
        while datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') > t_time:
            if t_time == dt_begin:
                forecast_data.append(0.0)
            else:
                forecast_data.append(forecast_data[-1])
            t_time += datetime.timedelta(minutes=2)
        if(row[3]>10):
            forecast_data.append((row[3]*100.0/row[4])*(1.0+row[5]))
        else:
            forecast_data.append((row[3]*100.0/row[4]))
        t_time += datetime.timedelta(minutes=2)
    # print(real_data)
    line = (
        Line()
        .add_xaxis(time_list)
        .add_yaxis("拥挤度变化",
                   y_axis=real_data,
                   color='gray',
                   label_opts=opts.LabelOpts(is_show=False),
                   is_smooth=True)
        .add_yaxis("拥挤度预测",
                   y_axis=forecast_data,
                   color='red',
                   label_opts=opts.LabelOpts(is_show=False),
                   is_smooth=True)

        .set_global_opts(
            title_opts=opts.TitleOpts(title="{}实时拥挤度变化（就餐人数/总座位数*100%）".format(canteen),
                                      pos_left='center', pos_top='5%'),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            datazoom_opts=opts.DataZoomOpts(range_start=int(50.0*len(real_data)/len(forecast_data)+0.5),
                                            range_end=100,
                                            pos_bottom='11%'),
        )
    )
    grid = (
        Grid(init_opts=opts.InitOpts(width='3600px',
                                     height='700px',
                                     page_title="食堂实时拥挤度变化")).add(line, grid_opts=opts.GridOpts(pos_bottom="20%"))
    )
    c.append(grid)
    part1.add(grid, canteen)


conn.close()


# 统计实时拥挤程度
extent = []
names = []

for i in range(len(df)):
    extent.append(int(100.0*df.iloc[i, 0]/df.iloc[i, 2]+0.5))
    names.append(df.iloc[i, 1])
    # 分页储存

    g = (
        Gauge(
            init_opts=opts.InitOpts(width="600px",
                                    height="600px",
                                    page_title="{}实时数据分析".format(df.iloc[i, 1])
                                    )
        )
        .add("", [("", int(100.0*df.iloc[i, 0]/df.iloc[i, 2]+0.5))])
        .set_global_opts(
            title_opts=opts.TitleOpts(title="{}实时拥挤度".format(df.iloc[i, 1]),
                                      pos_left='center',
                                      pos_top='5%'),
            tooltip_opts=opts.TooltipOpts(
                is_show=True, formatter="{a} <br/>{b} : {c}%"),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    page = Page(page_title="{}食堂实时数据分析".format(
        df.iloc[i, 1]), layout=Page.SimplePageLayout)
    page.add(g, c[i])
    page.render("../web/c%d.html" % i)


# 实时数据柱状图
bar = (Bar(init_opts=opts.InitOpts(width='2500px',
                                   height='800px'))
       .add_xaxis(names)
       .add_yaxis("", extent)
       .set_global_opts(
    title_opts=opts.TitleOpts(title="{} 实时各食堂饱和度（就餐人数/总座位数*100%）".format(df.index[i]),
                              pos_left='center', pos_top='10%'),
    xaxis_opts=opts.AxisOpts(
        axislabel_opts={"rotate": 30},
        split_number=1
    ),
    visualmap_opts=opts.VisualMapOpts(
        min_=0, max_=100, is_piecewise=True)
)
)

pages = Page(page_title="北大各食堂实时数据分析", layout=Page.SimplePageLayout)
pages.add(part1, bar)
pages.render("../web/shows.html")
