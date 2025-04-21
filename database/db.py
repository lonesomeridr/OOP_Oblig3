import time
import pymysql
from pymysql.err import OperationalError, InterfaceError
from utils.config import DB_CFG
from utils.logger import log
from datetime import date

# table names
T_TEMP    = "temperature_readings"
T_ACCEL   = "acceleration_readings"
T_SENSORS = "sensors"
T_ACCG    = "acceleration_config"

RETRY = 3  # seconds between reconnect attempts

class DB:
    def __init__(self):
        self._connect()

    # ---------- INSERTS ---------- #
    def insert_temperature(self, sensor_id: int, temp: float):
        self._exec(
            f"INSERT INTO {T_TEMP}(sensor_id,temperature) VALUES (%s,%s)",
            (sensor_id, temp),
        )

    def insert_accel(self, sensor_id: int, x: float, y: float, z: float):
        self._exec(
            f"INSERT INTO {T_ACCEL}(sensor_id,x,y,z) VALUES (%s,%s,%s,%s)",
            (sensor_id, x, y, z),
        )

    # ---------- HISTORY FETCH ----------
    def fetch_last_hours(self, table: str, hours: int = 1) -> list[tuple]:
        """
        Return all rows from `table` whose `created_at` column is within
        the last `hours` hours, ordered ascending. Returns empty on error.
        """
        try:
            sql = (
                f"SELECT * "
                f"FROM {table} "
                f"WHERE `created_at` >= NOW() - INTERVAL %s HOUR "
                f"ORDER BY `created_at` ASC"
            )
            self.cur.execute(sql, (hours,))
            return self.cur.fetchall()
        except Exception as exc:
            log(f"DB fetch_last_hours error: {exc}")
            return []


    # ---------- SENSORS CRUD ---------- #
    def get_sensors(self) -> list[tuple]:
        self.cur.execute(f"SELECT sensor_id, type, location, installation_date FROM {T_SENSORS}")
        return self.cur.fetchall()

    def add_sensor(self, type: str, location: str, installation_date: date):
        self._exec(
            f"INSERT INTO {T_SENSORS}(type,location,installation_date) VALUES (%s,%s,%s)",
            (type, location, installation_date),
        )

    def update_sensor(self, sensor_id: int, type: str, location: str, installation_date: date):
        self._exec(
            f"UPDATE {T_SENSORS} "
            f"SET type=%s, location=%s, installation_date=%s "
            f"WHERE sensor_id=%s",
            (type, location, installation_date, sensor_id),
        )

    # ---------- ACCEL CONFIG UP/DOWN ---------- #
    def get_accel_config(self, sensor_id: int) -> dict:
        self.cur.execute(
            f"SELECT zero_x, zero_y, zero_z, deadband FROM {T_ACCG} WHERE sensor_id=%s",
            (sensor_id,),
        )
        row = self.cur.fetchone()
        if row:
            return {"zero_x": row[0], "zero_y": row[1], "zero_z": row[2], "deadband": row[3]}
        # defaults
        return {"zero_x":0.0, "zero_y":0.0, "zero_z":0.0, "deadband":0.1}

    def upsert_accel_config(self, sensor_id: int, zx: float, zy: float, zz: float, dbnd: float):
        # Attempt UPDATE first
        self.cur.execute(
            f"UPDATE {T_ACCG} SET zero_x=%s, zero_y=%s, zero_z=%s, deadband=%s WHERE sensor_id=%s",
            (zx, zy, zz, dbnd, sensor_id),
        )
        if self.cur.rowcount == 0:
            # no row updated, so INSERT
            self.cur.execute(
                f"INSERT INTO {T_ACCG}(sensor_id,zero_x,zero_y,zero_z,deadband) VALUES (%s,%s,%s,%s,%s)",
                (sensor_id, zx, zy, zz, dbnd),
            )

    # ---------- INTERNAL HELPERS ---------- #
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

    def _exec(self, sql: str, params: tuple):
        try:
            self.cur.execute(sql, params)
        except (OperationalError, InterfaceError):
            # lost connection → reconnect then retry once
            self._connect()
            try:
                self.cur.execute(sql, params)
            except Exception as ex2:
                log(f"DB exec error after reconnect: {ex2}")
        except Exception as exc:
            log(f"DB exec error: {exc}")
