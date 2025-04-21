"""
DB wrapper for snake_case‑skjemaet.
"""
import time
import pymysql
from pymysql.err import OperationalError, InterfaceError
from utils.config import DB_CFG
from utils.logger import log

RETRY    = 3
T_TEMP   = "temperature_readings"
T_ACCEL  = "acceleration_readings"

class DB:
    def __init__(self):
        self._connect()

    # ---------- INSERT ---------- #
    def insert_temperature(self, sensor_id: int, temp: float):
        self._exec(
            f"INSERT INTO {T_TEMP}(sensor_id,temperature) VALUES (%s,%s)",
            (sensor_id, temp)
        )

    def insert_accel(self, sensor_id: int, x: float, y: float, z: float):
        self._exec(
            f"INSERT INTO {T_ACCEL}(sensor_id,x,y,z) VALUES (%s,%s,%s,%s)",
            (sensor_id, x, y, z)
        )

    # ---------- FETCH HISTORY ---------- #
    def fetch_last_hours(self, table: str, hours: int = 1) -> list[tuple]:
        """
        Return all rows from `table` whose `created_at` timestamp
        is within the last `hours` hours, ordered ascending.
        Returns an empty list on error.
        """
        try:
            sql = (
                f"SELECT * "
                f"FROM {table} "
                f"WHERE created_at >= NOW() - INTERVAL %s HOUR "
                f"ORDER BY created_at ASC"
            )
            self.cur.execute(sql, (hours,))
            return self.cur.fetchall()
        except Exception as exc:
            log(f"DB fetch_last_hours error: {exc}")
            return []

    # ---------- INTERNAL HELPERS ---------- #
    def _connect(self):
        """Attempt to connect (with retries) and set up cursor."""
        while True:
            try:
                self.cnx = pymysql.connect(**DB_CFG, autocommit=True)
                self.cur = self.cnx.cursor()
                log("DB connected")
                return
            except Exception as exc:
                log(f"DB connect failed: {exc} – retrying in {RETRY}s")
                time.sleep(RETRY)

    def _exec(self, sql: str, params: tuple):
        """Execute an INSERT/UPDATE, reconnecting once on connection loss."""
        try:
            self.cur.execute(sql, params)
        except (OperationalError, InterfaceError):
            # Lost connection → reconnect and retry once
            self._connect()
            try:
                self.cur.execute(sql, params)
            except Exception as exc:
                log(f"DB exec error after reconnect: {exc}")
        except Exception as exc:
            log(f"DB exec error: {exc}")
