from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import sqlite3
import time
import requests

app = FastAPI()
DB_FILE = "tablets.db"
NTFY_URL = "http://localhost:3000"  # Adjust if needed

class BatteryUpdate(BaseModel):
    id: str
    battery: int

class NewDevice(BaseModel):
    id: str
    warning_threshold: int = 30
    critical_threshold: int = 15

@app.post("/add")
def add_device(device: NewDevice):
    with sqlite3.connect(DB_FILE) as conn:
        try:
            conn.execute("INSERT INTO devices (id, warning_threshold, critical_threshold, last_seen, battery) VALUES (?, ?, ?, ?, ?)",
                         (device.id, device.warning_threshold, device.critical_threshold, int(time.time()), 100))
            conn.commit()
            return {"message": "Device added"}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Device already exists")

@app.post("/update")
def update_battery(update: BatteryUpdate):
    now = int(time.time())
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT warning_threshold, critical_threshold FROM devices WHERE id = ?", (update.id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Device not found")
        warning, critical = row
        status = None
        if update.battery <= critical:
            status = "CRITICAL"
        elif update.battery <= warning:
            status = "WARNING"

        cur.execute("UPDATE devices SET battery = ?, last_seen = ? WHERE id = ?",
                    (update.battery, now, update.id))
        conn.commit()

        if status:
            requests.post(f"{NTFY_URL}/{update.id}", data=f"{status}: Device {update.id}'s battery at {update.battery}%")

    return {"message": "Battery updated", "status": status or "OK"}

@app.get("/status")
def get_all():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = cur.execute("SELECT * FROM devices ORDER BY last_seen DESC").fetchall()
        return [dict(row) for row in rows]

@app.get("/status/{device_id}")
def get_device(device_id: str):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        row = cur.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
        if row:
            return dict(row)
        else:
            raise HTTPException(status_code=404, detail="Device not found")

@app.delete("/remove/{device_id}")
def remove_device(device_id: str):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        conn.commit()
        if cur.rowcount:
            return {"message": "Device removed"}
        else:
            raise HTTPException(status_code=404, detail="Device not found")

