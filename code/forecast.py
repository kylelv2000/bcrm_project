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


conn = sqlite3.connect(
    sys.path[0]+'/../data/shows.db', check_same_thread=False)
curs = conn.cursor()


# 预测数据

# 若不存在则新建
SQL = "CREATE TABLE if not exists forecast(ID INTEGER PRIMARY KEY AUTOINCREMENT,\
        DATETIME TEXT,NAME CHAR[20],IP DOUBLE,SEAT INTEGER,delta DOUBLE);"
curs.execute(SQL)

now_dt = datetime.datetime.strptime(df.index[0], '%Y-%m-%d %H:%M')

# 删除历史预测数据


def delOldData():
    delta = datetime.timedelta(hours=12)
    perlen = 19
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

    # 数据矫正偏移(前6次的误差)
    sum_3 = 0.0
    cnt_3 = 0
    for j in range(6):
        fro_dt = now_dt-datetime.timedelta(minutes=j*2)
        result = curs.execute(
            "SELECT IP FROM canteens WHERE NAME = '%s' AND DATETIME = '%s';" % (canteen, str(fro_dt)))
        real_ip = 0.0
        for tmp in result:
            real_ip = tmp[0]
            break
        if real_ip > 0:  # 如果存在记录
            result = curs.execute(
                "SELECT IP FROM forecast WHERE NAME = '%s' AND DATETIME = '%s';" % (canteen, str(fro_dt)))
            for tmp in result:
                sum_3 += (real_ip-(tmp[0]*1.0))/real_ip  # 相对误差
                cnt_3 += 1
    delta = 0.0
    if cnt_3 > 0:
        delta = sum_3/cnt_3

    for i in range(1, 720):
        nxt_dt = now_dt+datetime.timedelta(minutes=2*i)
        # 前5天同一时间
        sum_1 = 0.0
        cnt_1 = 0
        for j in range(1, 6):
            fro_dt = nxt_dt-datetime.timedelta(days=j)
            result = curs.execute(
                "SELECT IP FROM canteens WHERE NAME = '%s' AND DATETIME = '%s';" % (canteen, str(fro_dt)))
            for tmp in result:
                sum_1 += tmp[0]
                cnt_1 += 1
                break
        # 前4周同一星期和时间
        sum_2 = 0.0
        cnt_2 = 0
        for j in range(1, 5):
            fro_dt = nxt_dt-datetime.timedelta(weeks=j)
            result = curs.execute(
                "SELECT IP FROM canteens WHERE NAME = '%s' AND DATETIME = '%s';" % (canteen, str(fro_dt)))
            for tmp in result:
                sum_2 += tmp[0]
                cnt_2 += 1
                break

        # 数据预测
        forcast_ip = 0.0
        if cnt_1 > 0:
            forcast_ip += (sum_1/cnt_1)*0.4
        if cnt_2 > 0:
            forcast_ip += (sum_2/cnt_2)*0.6
        elif cnt_1 > 0:
            forcast_ip += (sum_1/cnt_1)*0.6

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
