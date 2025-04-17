"""
Super‑enkel DB‑wrapper. Ingen ORM – bare rå INSERT/SELECT.
"""
import pymysql
from utils.config import DB_CFG
from utils.logger import log

class DB:
    def __init__(self):
        self.cnx = pymysql.connect(**DB_CFG)
        self.cur = self.cnx.cursor()

    # ---------- INSERT ---------- #
    def insert_temperature(self, sensor_id, temp):
        self.cur.execute(
            "INSERT INTO temperature_readings(sensor_id, temperature) VALUES (%s, %s)",
            (sensor_id, temp))
        self.cnx.commit()

    def insert_accel(self, sensor_id, x, y, z):
        self.cur.execute(
            "INSERT INTO acceleration_readings(sensor_id,x,y,z) VALUES (%s,%s,%s,%s)",
            (sensor_id, x, y, z))
        self.cnx.commit()

    # ---------- SELECT ---------- #
    def fetch_last_hours(self, table, hours=1):
        self.cur.execute(
            f"SELECT * FROM {table} WHERE timestamp >= NOW()-INTERVAL %s HOUR",
            (hours,))
        return self.cur.fetchall()
