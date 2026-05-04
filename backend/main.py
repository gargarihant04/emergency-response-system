from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import uuid
from datetime import datetime
import os
app = FastAPI(title="SOS API for Women's Safety")

# Database connection details (connecting via your Kubernetes tunnel)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "sos_db"),
    "user": os.getenv("DB_USER", "sos_admin"),
    "password": os.getenv("DB_PASSWORD", "admin123")
}

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database connection failed.")

# --- Pydantic Models for Data Validation ---

class SOSPayload(BaseModel):
    user_id: str
    latitude: float
    longitude: float

class EscalatePayload(BaseModel):
    latitude: float
    longitude: float
    medical_required: bool

# --- API Endpoints ---

@app.post("/api/v1/sos")
async def trigger_sos(payload: SOSPayload):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Verify the user exists
        cur.execute("SELECT full_name, emergency_contact FROM users WHERE user_id = %s", (payload.user_id,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User ID not found in database.")
        
        # 2. PostGIS Magic: Find the absolute nearest POLICE STATION
        # The <-> operator calculates 2D distance instantly
        cur.execute("""
            SELECT id, name, contact_number 
            FROM emergency_facilities 
            WHERE amenity_type = 'police' 
            ORDER BY location <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326) 
            LIMIT 1;
        """, (payload.longitude, payload.latitude))
        
        police_station = cur.fetchone()
        
        if not police_station:
            raise HTTPException(status_code=404, detail="No police stations found in the area.")

        # 3. Log the Alert
        alert_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO active_alerts (alert_id, user_id, status, facility_id) 
            VALUES (%s, %s, %s, %s)
        """, (alert_id, payload.user_id, 'police_dispatched', police_station[0]))
        
        conn.commit()

        return {
            "message": "SOS Triggered. Police Dispatched.",
            "alert_id": alert_id,
            "user": {"name": user[0], "emergency_contact": user[1]},
            "dispatched_to": {"facility_name": police_station[1], "contact": police_station[2]}
        }

    finally:
        cur.close()
        conn.close()


@app.put("/api/v1/sos/{alert_id}/escalate")
async def escalate_to_medical(alert_id: str, payload: EscalatePayload):
    if not payload.medical_required:
        return {"message": "Escalation logged, no medical required."}

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. PostGIS Magic: Find the absolute nearest HOSPITAL
        cur.execute("""
            SELECT id, name, contact_number 
            FROM emergency_facilities 
            WHERE amenity_type = 'hospital' 
            ORDER BY location <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326) 
            LIMIT 1;
        """, (payload.longitude, payload.latitude))
        
        hospital = cur.fetchone()
        
        if not hospital:
            raise HTTPException(status_code=404, detail="No hospitals found in the area.")

        # 2. Update the existing alert status
        cur.execute("""
            UPDATE active_alerts 
            SET status = 'medical_dispatched', facility_id = %s 
            WHERE alert_id = %s
        """, (hospital[0], alert_id))
        
        conn.commit()

        return {
            "message": "Alert Escalated. Ambulance Dispatched.",
            "alert_id": alert_id,
            "dispatched_to": {"facility_name": hospital[1], "contact": hospital[2]}
        }

    finally:
        cur.close()
        conn.close()