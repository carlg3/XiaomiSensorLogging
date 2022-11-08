from django.http import HttpResponse
import sqlite3
import json
import os.path
from pathlib import PurePath

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
MY_PATH = PurePath(SCRIPT_PATH)

DBNAME = MY_PATH/'../../t_h_readings.db'

def index(request):
    con  = sqlite3.connect(DBNAME)
    with con:
        cur = con.cursor()
        con.row_factory = sqlite3.Row

        res = cur.execute('''SELECT timestamp, temperature FROM reading LIMIT 10000;''').fetchall()
        colonne = [d[0] for d in cur.description]
        colonne = ['x', 'y']
        j = json.dumps([dict(zip(colonne, ix)) for ix in res])
    return HttpResponse(j)
