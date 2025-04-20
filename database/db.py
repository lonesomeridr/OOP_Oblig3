"""
DB wrapper for snake_case‑skjemaet.
"""
import time, pymysql
from pymysql.err import OperationalError, InterfaceError
from utils.config import DB_CFG
from utils.logger import log

RETRY = 3
T_TEMP  = "temperature_readings"
T_ACCEL = "acceleration_readings"

class DB:
    def __init__(self):
        self._connect()

    # ---------- insert ---------- #
    def insert_temperature(self, sensor_id:int, temp:float):
        self._exec(f"INSERT INTO {T_TEMP}(sensor_id,temperature) VALUES (%s,%s)",
                   (sensor_id,temp))

    def insert_accel(self, sensor_id:int, x:float,y:float,z:float):
        self._exec(
            f"INSERT INTO {T_ACCEL}(sensor_id,x,y,z) VALUES (%s,%s,%s,%s)",
            (sensor_id,x,y,z)
        )

    # ---------- intern ---------- #
    def _connect(self):
        while True:
            try:
                self.cnx = pymysql.connect(**DB_CFG, autocommit=True)
                self.cur = self.cnx.cursor()
                log("DB connected")
                return
            except Exception as exc:
                log(f"DB connect failed: {exc} – retrying in {RETRY}s")
                time.sleep(RETRY)

    def _exec(self, sql:str, params:tuple):
        try:
            self.cur.execute(sql, params)
        except (OperationalError, InterfaceError):
            self._connect()
            try:
                self.cur.execute(sql, params)
            except Exception as exc:
                log(f"DB exec error after reconnect: {exc}")
        except Exception as exc:
            log(f"DB exec error: {exc}")
