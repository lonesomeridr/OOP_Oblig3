"""
DB wrapper for the updated schema (Sensors, Readings, Alarms).
"""
import time
import datetime
import pymysql
from pymysql.err import OperationalError, InterfaceError
from utils.config import DB_CFG  # Assuming DB_CFG contains host, user, password, db
from utils.logger import log

RETRY_DELAY_SECONDS = 3
TABLE_TEMP_READINGS = "TemperatureReadings"
TABLE_ACCEL_READINGS = "AccelerationReadings"

# --- Default Sensor ID ---
DEFAULT_SENSOR_ID = 1 # <<< THIS LINE MUST BE PRESENT HERE


class DB:
    def __init__(self):
        """Initializes the DB connection."""
        self.cnx = None
        self.cur = None
        self._connect()

    # ---------- Insert Reading Methods ---------- #

    def insert_temperature(self, sensor_id: int, temp: float):
        """Inserts a single temperature reading into the TemperatureReadings table."""
        # Note: Using NOW() for timestamp automatically uses the DB server's time
        sql = f"""
            INSERT INTO {TABLE_TEMP_READINGS} (sensor_id, timestamp, temperature)
            VALUES (%s, NOW(), %s)
        """
        self._exec(sql, (sensor_id, temp))

    def insert_accel(self, sensor_id: int, x: float, y: float, z: float,
                       diff_x: float, diff_y: float, diff_z: float):
        """
        Inserts a single acceleration reading including differentials
        into the AccelerationReadings table.
        """
        # Note: Using NOW() for timestamp automatically uses the DB server's time
        sql = f"""
            INSERT INTO {TABLE_ACCEL_READINGS}
            (sensor_id, timestamp, acceleration_x, acceleration_y, acceleration_z,
             diff_acceleration_x, diff_acceleration_y, diff_acceleration_z)
            VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s)
        """
        self._exec(sql, (sensor_id, x, y, z, diff_x, diff_y, diff_z))

    # ---------- Fetch Methods (Example for History Tab) ---------- #

    def fetch_last_n_temp_readings(self, sensor_id: int, n: int) -> list[tuple]:
        """Fetches the last N temperature readings for a given sensor."""
        sql = f"""
            SELECT timestamp, temperature
            FROM {TABLE_TEMP_READINGS}
            WHERE sensor_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        return self._fetch(sql, (sensor_id, n), fetch_all=True)

    def fetch_last_n_accel_readings(self, sensor_id: int, n: int) -> list[tuple]:
        """Fetches the last N acceleration readings for a given sensor."""
        sql = f"""
            SELECT timestamp, acceleration_x, acceleration_y, acceleration_z,
                   diff_acceleration_x, diff_acceleration_y, diff_acceleration_z
            FROM {TABLE_ACCEL_READINGS}
            WHERE sensor_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        return self._fetch(sql, (sensor_id, n), fetch_all=True)


    # ---------- Internal Connection & Execution Logic ---------- #

    def _connect(self):
        """Establishes a connection to the database with retry logic."""
        while True:
            try:
                self.cnx = pymysql.connect(**DB_CFG, autocommit=True)
                self.cur = self.cnx.cursor()
                log("DB connected successfully.")
                return # Exit loop on successful connection
            except OperationalError as exc:
                log(f"DB connection failed (OperationalError): {exc} – Retrying in {RETRY_DELAY_SECONDS}s")
                time.sleep(RETRY_DELAY_SECONDS)
            except Exception as exc: # Catch other potential connection errors
                log(f"DB connection failed (General Exception): {exc} – Retrying in {RETRY_DELAY_SECONDS}s")
                time.sleep(RETRY_DELAY_SECONDS)


    def _exec(self, sql: str, params: tuple = None):
        """Executes a SQL command (INSERT, UPDATE, DELETE) with reconnect logic."""
        try:
            if not self.cnx or not self.cnx.open:
                log("DB connection lost. Reconnecting...")
                self._connect() # Try to reconnect
            self.cur.execute(sql, params or ())
            # log(f"Executed SQL: {self.cur._last_executed}") # Optional: Log executed query
        except (OperationalError, InterfaceError) as db_exc:
             log(f"DB execution error ({type(db_exc).__name__}), attempting reconnect: {db_exc}")
             self._connect() # Connection likely lost, reconnect
             try:
                 # Retry execution after reconnecting
                 self.cur.execute(sql, params or ())
                 log("DB command executed successfully after reconnect.")
             except Exception as retry_exc:
                 log(f"DB exec error persists after reconnect: {retry_exc}")
                 # Consider raising an exception here if critical
        except Exception as exc:
            log(f"General DB exec error: {exc}")
            log(f"Failed SQL: {sql} with params {params}")
            # Consider raising an exception here if critical

    def _fetch(self, sql: str, params: tuple = None, fetch_all: bool = True) -> list[tuple] | tuple | None:
        """Executes a SELECT query and fetches results with reconnect logic."""
        try:
            if not self.cnx or not self.cnx.open:
                log("DB connection lost. Reconnecting...")
                self._connect() # Try to reconnect
            self.cur.execute(sql, params or ())
            # log(f"Executed SQL: {self.cur._last_executed}") # Optional: Log executed query
            if fetch_all:
                return self.cur.fetchall()
            else:
                return self.cur.fetchone()
        except (OperationalError, InterfaceError) as db_exc:
             log(f"DB fetch error ({type(db_exc).__name__}), attempting reconnect: {db_exc}")
             self._connect() # Connection likely lost, reconnect
             try:
                 # Retry execution after reconnecting
                 self.cur.execute(sql, params or ())
                 log("DB fetch executed successfully after reconnect.")
                 if fetch_all:
                     return self.cur.fetchall()
                 else:
                    return self.cur.fetchone()
             except Exception as retry_exc:
                 log(f"DB fetch error persists after reconnect: {retry_exc}")
                 return [] if fetch_all else None # Return empty on error after retry
        except Exception as exc:
            log(f"General DB fetch error: {exc}")
            log(f"Failed SQL: {sql} with params {params}")
            return [] if fetch_all else None # Return empty on error

    def close(self):
        """Closes the database connection."""
        if self.cur:
            self.cur.close()
            self.cur = None
        if self.cnx:
            self.cnx.close()
            self.cnx = None
        log("DB connection closed.")

# Example usage (outside the class, for testing):
# if __name__ == "__main__":
#     db = DB()
#     try:
#         # Make sure sensor_id 1 exists in your Sensors table first!
#         # Use MySQL Workbench: INSERT INTO Sensors (type) VALUES ('TestSensor');
#         sensor_id = 1
#
#         print("Inserting sample data...")
#         db.insert_temperature(sensor_id, 25.5)
#         db.insert_accel(sensor_id, 0.1, -0.2, 9.8, 0.01, -0.01, 0.0)
#         print("Sample data inserted.")
#
#         print("\nFetching last 5 temp readings:")
#         temps = db.fetch_last_n_temp_readings(sensor_id, 5)
#         for row in temps:
#             print(row)
#
#         print("\nFetching last 5 accel readings:")
#         accels = db.fetch_last_n_accel_readings(sensor_id, 5)
#         for row in accels:
#             print(row)
#
#     finally:
#         db.close()
