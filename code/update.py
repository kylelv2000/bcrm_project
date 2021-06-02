import os
import sys
import json
import requests
import pandas as pd
import sqlite3
import datetime

conn = sqlite3.connect(sys.path[0]+'/../data/shows.db', check_same_thread=False)
curs = conn.cursor()

#过去*天早中晚餐峰值时间，当天人数变换+预测，各个食堂当前拥挤度
#读取数据
#for 
