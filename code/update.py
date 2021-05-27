import os
import sys
import time
import pandas as pd
import sqlite3
import datetime

os.chdir(sys.path[0])

conn = sqlite3.connect(sys.path[0]+'/../data/shows.db')
curs = conn.cursor()
#SQL = "CREATE TABLE if not exists forecast(
conn.close()

