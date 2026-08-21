# Speed Test Monitor - Raspberry Pi 3B+

## 📋 Overview
A Python script that runs periodic internet speed tests and stores results in a SQLite database for monitoring and visualization in Grafana.

## 🖥️ Environment
- **Device**: Raspberry Pi 3B+ (ARMv7l / aarch64)
- **OS**: Debian-based (Raspberry Pi OS)
- **Python**: 3.13
- **Architecture**: ARM64

## 📁 Project Structure
```
speed-check/
├── .venv/                  # Python virtual environment
├── speed_test.py           # Main speed test script
├── speedtest.db            # Local SQLite database (for reference)
├── speedtest_dashboard.json # Grafana dashboard (import this)
├── requirements.txt        # Python dependencies
├── grafana_setup.md        # Grafana installation guide
└── project.md              # This file

/opt/speed-check/data/speedtest.db  # Active database for Grafana
```

## ⚙️ Setup Instructions

### 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Grafana
See `grafana_setup.md` for complete instructions.

### 3. Configure Datasource
- Grafana datasource: **SpeedTest SQLite**
- Type: `frser-sqlite-datasource`
- Path: `/opt/speed-check/data/speedtest.db`
- Path Prefix: (leave empty)
- Path Options: `?_pragma=query_only(1)` or leave empty

### Database Directory Setup
Before running the script, set up the database directory:

```bash
# Create dedicated group
sudo groupadd --system speedtest

# Add users to group
sudo usermod -aG speedtest grafana
sudo usermod -aG speedtest admin

# Create directory (NOT in /var due to systemd PrivateTmp isolation)
sudo install -d -o admin -g speedtest -m 2770 /opt/speed-check/data
```

### 4. Import Dashboard
- In Grafana: **+ → Import**
- Upload: `speedtest_dashboard.json`
- Select datasource: **SpeedTest SQLite**

## 📊 Database Schema

**Location:** `/opt/speed-check/data/speedtest.db`

> **Important:** This follows the [official Grafana SQLite plugin recommendations](https://github.com/fr-ser/grafana-sqlite-datasource/blob/main/docs/faq.md). Do NOT use `/var/` with Grafana v8.2.0+ due to systemd PrivateTmp isolation. The `/opt/` directory is accessible to Grafana under default systemd security settings.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | INTEGER | Auto-incrementing primary key | 1, 2, 3... |
| timestamp | INTEGER | Unix timestamp (seconds since 1970) | 1787261716 |
| ping | REAL | Latency in milliseconds | 98.67 |
| download | REAL | Download speed in bits/second | 8010000.0 |
| upload | REAL | Upload speed in bits/second | 7970000.0 |

## ⏰ Automated Speed Tests

### Cron Job (Runs every 15 minutes)
```bash
*/15 * * * * cd /home/admin/speed-check && /home/admin/speed-check/.venv/bin/python speed_test.py
```

**To manage:**
```bash
# View cron jobs
crontab -l

# Edit cron jobs
crontab -e

# View logs
grep CRON /var/log/syslog | tail -20
```

## 🔧 Script Details

**File:** `speed_test.py`

- Uses `speedtest-cli` library
- Stores timestamps as **Unix epoch in seconds** (compatible with Grafana)
- Writes to: `/opt/speed-check/data/speedtest.db`
- Creates table automatically if it doesn't exist

## 📈 Grafana Queries

### Time Series Panels
```sql
-- Download Speed
SELECT timestamp as time, download/1000000.0 as value 
FROM results 
WHERE timestamp >= $__from/1000 AND timestamp <= $__to/1000 
ORDER BY timestamp

-- Upload Speed
SELECT timestamp as time, upload/1000000.0 as value 
FROM results 
WHERE timestamp >= $__from/1000 AND timestamp <= $__to/1000 
ORDER BY timestamp

-- Ping
SELECT timestamp as time, ping as value 
FROM results 
WHERE timestamp >= $__from/1000 AND timestamp <= $__to/1000 
ORDER BY timestamp
```

### Stat Panels
```sql
-- Download (latest)
SELECT download/1000000.0 as value FROM results ORDER BY timestamp DESC LIMIT 1

-- Upload (latest)
SELECT upload/1000000.0 as value FROM results ORDER BY timestamp DESC LIMIT 1

-- Ping (latest)
SELECT ping as value FROM results ORDER BY timestamp DESC LIMIT 1
```

## 💡 Tips & Troubleshooting

### Check Data
```bash
source .venv/bin/activate
python -c "import sqlite3; conn = sqlite3.connect('/opt/speed-check/data/speedtest.db'); cursor = conn.cursor(); cursor.execute('SELECT count(*), min(timestamp), max(timestamp) FROM results'); print(cursor.fetchone()); conn.close()"
```

### Manual Run
```bash
cd /home/admin/speed-check
source .venv/bin/activate
python speed_test.py
```

### Grafana Access
- URL: `http://<your-pi-ip>:3000`
- Default login: `admin` / `admin` (change on first login)

### Reset Grafana Admin Password
```bash
sudo grafana-cli admin reset-admin-password admin
sudo systemctl restart grafana-server
```

## 🎯 Maintenance

### Backup Database
```bash
cp /opt/speed-check/data/speedtest.db /opt/speed-check/data/speedtest.db.backup
```

### Restore Database
```bash
cp /opt/speed-check/data/speedtest.db.backup /opt/speed-check/data/speedtest.db
```

### Clean Old Data
```bash
# Delete data older than 30 days
source .venv/bin/activate
python -c "import sqlite3; from datetime import datetime, timedelta; conn = sqlite3.connect('/opt/speed-check/data/speedtest.db'); cursor = conn.cursor(); cutoff = int((datetime.now() - timedelta(days=30)).timestamp()); cursor.execute('DELETE FROM results WHERE timestamp < ?', (cutoff,)); conn.commit(); conn.close(); print('Old data cleaned')"
```

## 📚 Resources
- [speedtest-cli](https://github.com/sivel/speedtest-cli) - Speed test library
- [Grafana](https://grafana.com/) - Visualization platform
- [frser-sqlite-datasource Plugin](https://github.com/fr-ser/grafana-sqlite-datasource) - Official SQLite plugin (recommended)
- [SQLite Plugin FAQ](https://github.com/fr-ser/grafana-sqlite-datasource/blob/main/docs/faq.md) - Official setup guide

## 🔄 Changelog
- **v1.0**: Initial setup with MySQL
- **v2.0**: Switched to SQLite
- **v3.0**: Fixed datetime deprecation warning
- **v4.0**: Added Grafana integration
- **v5.0**: Fixed timezone issues with Unix timestamps in seconds
- **v6.0**: Added automated cron job (every 15 minutes)
