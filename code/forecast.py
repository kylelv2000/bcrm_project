import os
import sys
import json
import pandas as pd
import sqlite3
import datetime

os.chdir(sys.path[0])

# 得到最新数据
f = open('../data/latest.json', 'r')
a = json.loads(f.read())
f.close()
df = pd.DataFrame(a['rows'], index=[a['time']]*len(a['rows']))
df.drop(df.columns[3], axis=1, inplace=True)

# 连接数据库
conn = sqlite3.connect(
    sys.path[0]+'/../data/shows.db', check_same_thread=False)
curs = conn.cursor()


# 预测数据

# 若不存在则新建
SQL = "CREATE TABLE if not exists forecast(ID INTEGER PRIMARY KEY AUTOINCREMENT,\
        DATETIME TEXT,NAME CHAR[20],IP DOUBLE,SEAT INTEGER,delta DOUBLE);"
curs.execute(SQL)

# 得到目前数据时间
now_dt = datetime.datetime.strptime(df.index[0], '%Y-%m-%d %H:%M')

# 删除历史预测数据


def delOldData():
    delta = datetime.timedelta(days=1)  # 我们保存1天内的数据
    perlen = 19  # 19个食堂，因此一个时间有19条数据
    while True:
        SQL = "select * from forecast limit 0,%d" % perlen
        result = curs.execute(SQL)
        cnt = 0
        mx_id = 0
        for row in result:
            # print(row)
            dateTime_p = datetime.datetime.strptime(
                row[1], '%Y-%m-%d %H:%M:%S')
            if(dateTime_p+delta > now_dt):
                # 如果当前数据时间以及到达应该保存就停止，将之前的全部删除
                curs.execute("DELETE FROM forecast WHERE ID < %d;" % row[0])
                conn.commit()
                return
            cnt = cnt+1
            mx_id = max(mx_id, row[0])

        if cnt < perlen:
            return
        else:
            curs.execute("DELETE FROM forecast WHERE ID <= %d;" % mx_id)
            conn.commit()


delOldData()
# 删除未来预测信息，重新预测
curs.execute("DELETE FROM forecast WHERE DATETIME > '%s';" % str(now_dt))
conn.commit()

# 对于未来获取历史信息来预测
for rows in df.itertuples():
    canteen = rows.name
    seat = rows.seat
    # print(canteen)

    # 数据矫正偏移(前10次的误差)
    sum_3 = 0.0
    cnt_3 = 0
    for j in range(10):
        fro_dt = now_dt-datetime.timedelta(minutes=j*2)
        result = curs.execute(
            "SELECT IP FROM canteens WHERE NAME = '%s' AND DATETIME = '%s';" % (canteen, str(fro_dt)))
        real_ip = 0.0
        for tmp in result:
            real_ip += tmp[0]
            break
        if real_ip > 0:  # 如果存在记录
            result = curs.execute(
                "SELECT IP FROM forecast WHERE NAME = '%s' AND DATETIME = '%s';" % (canteen, str(fro_dt)))
            for tmp in result:
                sum_3 += (real_ip-(tmp[0]*1.0))/real_ip  # 相对误差
                cnt_3 += 1
    delta = 0.0
    # 取均值
    if cnt_3 > 0:
        delta = sum_3/cnt_3
    delta /= 2  # 将偏移量减半（防止矫正过度）

    # 前5天同一时间
    sum_1 = [0.0 for _ in range(720)]  # 对于每一时刻记录均值
    cnt_1 = [0 for _ in range(720)]
    for j in range(1, 6):
        fro_dt = now_dt-datetime.timedelta(days=j)
        # 得到该24h内所有数据
        result = curs.execute("SELECT * FROM canteens WHERE NAME = '%s' \
            AND DATETIME > '%s' AND DATETIME < '%s';" % (canteen, str(fro_dt), str(fro_dt+datetime.timedelta(days=1))))
        i = 0
        for row in result:
            # 如果数据和现在枚举不对，即可能数据丢失或者重复
            if datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') < fro_dt:
                continue
            while datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') > fro_dt:
                i += 1
                fro_dt = fro_dt+datetime.timedelta(minutes=2)
            sum_1[i] += row[2]
            cnt_1[i] += 1
            i += 1
            fro_dt = fro_dt+datetime.timedelta(minutes=2)

    # 前4周同一星期和时间
    sum_2 = [0.0 for _ in range(720)]  # 对于每一时刻记录均值
    cnt_2 = [0 for _ in range(720)]
    for j in range(1, 5):
        fro_dt = now_dt-datetime.timedelta(weeks=j)
        # 得到该24h内所有数据
        result = curs.execute("SELECT * FROM canteens WHERE NAME = '%s' \
            AND DATETIME > '%s' AND DATETIME < '%s';" % (canteen, str(fro_dt), str(fro_dt+datetime.timedelta(days=1))))
        i = 0
        for row in result:
            # 如果数据和现在枚举不对，即可能数据丢失或者重复
            if datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') < fro_dt:
                continue
            while datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') > fro_dt:
                i += 1
                fro_dt = fro_dt+datetime.timedelta(minutes=2)
            sum_2[i] += row[2]
            cnt_2[i] += 1
            i += 1
            fro_dt = fro_dt+datetime.timedelta(minutes=2)

    # 数据预测
    for i in range(1, 720):
        # 枚举没一时刻（2分钟为间隔）
        nxt_dt = now_dt+datetime.timedelta(minutes=2*i)

        forcast_ip = 0.0
        # 对于历史数据加权赋值，我们认为影响当前预测的有两个：1是前面连续几天的数据，2是每周当天的数据（一般每周的课大致都不变的）
        if cnt_1[i] > 0:
            forcast_ip += (sum_1[i]/cnt_1[i])*0.4
        if cnt_2[i] > 0:
            forcast_ip += (sum_2[i]/cnt_2[i])*0.6
        elif cnt_1[i] > 0:
            forcast_ip += (sum_1[i]/cnt_1[i])*0.6

        SQL = "INSERT INTO forecast (DATETIME,NAME,IP,SEAT,delta) VALUES("\
            + "'"+str(nxt_dt)+"',"\
            + "'"+canteen+"',"\
            + str(forcast_ip)+","\
            + str(seat)+","\
            + str(delta) +\
            ")"
        curs.execute(SQL)

conn.commit()
conn.close()
