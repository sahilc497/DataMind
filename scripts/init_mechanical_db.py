"""
Mechanical Copilot — Synthetic Database Initializer
Creates the mechanical_copilot database with realistic sensor data and injected anomalies.
"""
import asyncio
import asyncpg
import random
import math
from datetime import datetime, timedelta
from config import settings

MACHINES = [
    {"name": "CNC Lathe Alpha",    "type": "CNC Lathe",       "location": "Bay A-1", "max_rpm": 3200, "max_temp": 95,  "max_load": 100},
    {"name": "Hydraulic Press B2", "type": "Hydraulic Press",  "location": "Bay A-2", "max_rpm": 1200, "max_temp": 110, "max_load": 100},
    {"name": "Milling Station C",  "type": "Milling Machine",  "location": "Bay B-1", "max_rpm": 2800, "max_temp": 90,  "max_load": 100},
    {"name": "Drill Unit D4",      "type": "Drill Press",      "location": "Bay B-2", "max_rpm": 3600, "max_temp": 85,  "max_load": 100},
    {"name": "Compressor E5",      "type": "Air Compressor",   "location": "Bay C-1", "max_rpm": 1800, "max_temp": 105, "max_load": 100},
    {"name": "Conveyor Belt F",    "type": "Conveyor System",  "location": "Bay C-2", "max_rpm": 600,  "max_temp": 60,  "max_load": 100},
    {"name": "Welding Robot G7",   "type": "Robotic Welder",   "location": "Bay D-1", "max_rpm": 2400, "max_temp": 130, "max_load": 100},
    {"name": "Pump Station H8",    "type": "Centrifugal Pump", "location": "Bay D-2", "max_rpm": 2000, "max_temp": 80,  "max_load": 100},
    {"name": "Grinder Unit J9",    "type": "Surface Grinder",  "location": "Bay E-1", "max_rpm": 3000, "max_temp": 88,  "max_load": 100},
    {"name": "Packaging Line K10", "type": "Packaging Unit",   "location": "Bay E-2", "max_rpm": 800,  "max_temp": 55,  "max_load": 100},
]

# Anomaly patterns injected into specific machines
ANOMALY_MACHINES = {
    2: "bearing_wear",       # Machine 2: High vibration + rising temp
    5: "cooling_failure",    # Machine 5: High temp + low load
    7: "misalignment",       # Machine 7: Fluctuating RPM
}

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS machines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(80) NOT NULL,
    location VARCHAR(60) NOT NULL,
    install_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'operational',
    max_rpm INTEGER NOT NULL,
    max_temp NUMERIC(5,1) NOT NULL,
    max_load NUMERIC(5,1) NOT NULL
);

CREATE TABLE IF NOT EXISTS sensor_logs (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id),
    timestamp TIMESTAMP NOT NULL,
    temperature NUMERIC(5,1) NOT NULL,
    vibration NUMERIC(5,2) NOT NULL,
    pressure NUMERIC(6,1) NOT NULL,
    rpm INTEGER NOT NULL,
    load_percent NUMERIC(5,1) NOT NULL,
    efficiency NUMERIC(5,1) NOT NULL
);

CREATE TABLE IF NOT EXISTS production_logs (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id),
    date DATE NOT NULL,
    output_units INTEGER NOT NULL,
    downtime_minutes INTEGER DEFAULT 0,
    defect_count INTEGER DEFAULT 0,
    shift VARCHAR(10) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sensor_machine_ts ON sensor_logs(machine_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_prod_machine_date ON production_logs(machine_id, date);
"""

def generate_sensor_reading(machine_id: int, machine: dict, ts: datetime, day_offset: int):
    """Generate a single sensor reading with optional anomaly injection."""
    base_temp = random.uniform(45, 70)
    base_vib = random.uniform(0.8, 2.5)
    base_pressure = random.uniform(90, 150)
    base_rpm = int(machine["max_rpm"] * random.uniform(0.6, 0.9))
    base_load = random.uniform(40, 80)
    base_efficiency = random.uniform(82, 96)
    
    anomaly = ANOMALY_MACHINES.get(machine_id)
    
    if anomaly == "bearing_wear":
        # Progressive vibration increase + temperature rise over last 10 days
        if day_offset >= 20:
            progress = (day_offset - 20) / 10.0
            base_vib += progress * 4.5  # Vibration spikes to ~7.0
            base_temp += progress * 25   # Temp rises to ~95
            base_efficiency -= progress * 15
    
    elif anomaly == "cooling_failure":
        # High temperature despite low load (cooling system issue)
        if day_offset >= 15:
            base_temp = random.uniform(90, 115)
            base_load = random.uniform(20, 40)
            base_efficiency = random.uniform(55, 72)
    
    elif anomaly == "misalignment":
        # RPM fluctuations and intermittent vibration spikes
        if day_offset >= 18:
            base_rpm = int(base_rpm * random.uniform(0.7, 1.3))  # Wild fluctuations
            if random.random() > 0.6:
                base_vib += random.uniform(2.0, 4.0)
            base_efficiency -= random.uniform(5, 15)
    
    # Add natural noise
    temp = round(base_temp + random.gauss(0, 2), 1)
    vib = round(max(0.3, base_vib + random.gauss(0, 0.3)), 2)
    pressure = round(base_pressure + random.gauss(0, 5), 1)
    rpm = max(100, int(base_rpm + random.gauss(0, 50)))
    load = round(min(100, max(5, base_load + random.gauss(0, 5))), 1)
    efficiency = round(min(99, max(30, base_efficiency + random.gauss(0, 2))), 1)
    
    return (machine_id, ts, temp, vib, pressure, rpm, load, efficiency)


def generate_production_log(machine_id: int, date, shift: str):
    """Generate a production log entry."""
    anomaly = ANOMALY_MACHINES.get(machine_id)
    
    base_output = random.randint(80, 200)
    base_downtime = random.randint(0, 15)
    base_defects = random.randint(0, 3)
    
    if anomaly and (date - datetime(2026, 3, 26).date()).days > 15:
        base_downtime += random.randint(15, 60)
        base_defects += random.randint(2, 8)
        base_output -= random.randint(20, 60)
    
    return (machine_id, date, max(10, base_output), base_downtime, base_defects, shift)


async def init_database():
    """Create the mechanical_copilot database and populate with synthetic data."""
    # Connect to default postgres to create the new DB
    base_dsn = settings.DATABASE_URL
    base_url = base_dsn.rsplit("/", 1)[0] + "/postgres"
    
    print("🔧 Connecting to PostgreSQL...")
    conn = await asyncpg.connect(base_url)
    
    # Create database if not exists
    db_name = settings.MECHANICAL_DB
    exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    if not exists:
        await conn.execute(f'CREATE DATABASE {db_name}')
        print(f"✅ Created database: {db_name}")
    else:
        print(f"ℹ️  Database {db_name} already exists")
    await conn.close()
    
    # Connect to the new database
    mech_dsn = base_dsn.rsplit("/", 1)[0] + f"/{db_name}"
    conn = await asyncpg.connect(mech_dsn)
    
    # Create tables
    await conn.execute(CREATE_TABLES_SQL)
    print("✅ Tables created: machines, sensor_logs, production_logs")
    
    # Check if data already exists
    count = await conn.fetchval("SELECT COUNT(*) FROM machines")
    if count > 0:
        print(f"ℹ️  Data already exists ({count} machines). Skipping insert.")
        await conn.close()
        return
    
    # Insert machines
    print("📊 Inserting machines...")
    for i, m in enumerate(MACHINES, 1):
        install_date = datetime(2023, 1, 1).date() + timedelta(days=random.randint(0, 365))
        status = "warning" if i in ANOMALY_MACHINES else "operational"
        await conn.execute(
            """INSERT INTO machines (name, type, location, install_date, status, max_rpm, max_temp, max_load) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            m["name"], m["type"], m["location"], install_date, status,
            m["max_rpm"], m["max_temp"], m["max_load"]
        )
    
    # Generate sensor data (30 days, ~500 readings per machine)
    print("📈 Generating sensor data (this may take a moment)...")
    sensor_data = []
    now = datetime(2026, 4, 25, 12, 0, 0)
    
    for machine_id in range(1, 11):
        machine = MACHINES[machine_id - 1]
        for day_offset in range(30):
            day = now - timedelta(days=30 - day_offset)
            # ~16 readings per day (every 1.5 hours)
            for hour_frac in range(16):
                ts = day + timedelta(hours=hour_frac * 1.5, minutes=random.randint(0, 20))
                reading = generate_sensor_reading(machine_id, machine, ts, day_offset)
                sensor_data.append(reading)
    
    # Bulk insert sensor data
    await conn.executemany(
        """INSERT INTO sensor_logs (machine_id, timestamp, temperature, vibration, pressure, rpm, load_percent, efficiency)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        sensor_data
    )
    print(f"✅ Inserted {len(sensor_data)} sensor readings")
    
    # Generate production logs (30 days, 3 shifts per day per machine)
    print("🏭 Generating production logs...")
    prod_data = []
    for machine_id in range(1, 11):
        for day_offset in range(30):
            date = (now - timedelta(days=30 - day_offset)).date()
            for shift in ["morning", "afternoon", "night"]:
                log = generate_production_log(machine_id, date, shift)
                prod_data.append(log)
    
    await conn.executemany(
        """INSERT INTO production_logs (machine_id, date, output_units, downtime_minutes, defect_count, shift)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        prod_data
    )
    print(f"✅ Inserted {len(prod_data)} production logs")
    
    await conn.close()
    print("\n🎉 Mechanical Copilot database initialized successfully!")
    print(f"   Database: {db_name}")
    print(f"   Machines: {len(MACHINES)}")
    print(f"   Sensor Readings: {len(sensor_data)}")
    print(f"   Production Logs: {len(prod_data)}")
    print(f"\n   ⚠️  Anomaly machines: {', '.join(f'Machine {k} ({v})' for k, v in ANOMALY_MACHINES.items())}")


if __name__ == "__main__":
    asyncio.run(init_database())
