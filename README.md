# Speed Test Monitor 📊

A **Raspberry Pi** project that monitors internet connection speed and visualizes data in **Grafana**.

[![Grafana Dashboard](https://img.shields.io/badge/Grafana-Dashboard-green)](https://grafana.com)
[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-3B%2B-red)](https://raspberrypi.org)

---

## 🚀 Features

- ✅ **Automated speed tests** every 15 minutes via cron
- ✅ **SQLite database** storage (lightweight, no server required)
- ✅ **Grafana dashboards** for beautiful visualization
- ✅ **Real-time monitoring** of download, upload, and ping latency
- ✅ **Zero external dependencies** (except speedtest-cli)

---

## 🖥️ Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Raspberry Pi | 3B+ | ARMv7/ARM64 |
| Python | 3.13 | Included in Raspberry Pi OS |
| Grafana | 13.2.0 | Installed via apt |
| SQLite | 3 | Built into Python |

---

## ⚙️ Quick Start

### 1️⃣ Clone & Setup
```bash
# Clone the repository
git clone https://github.com/floerio/speed-check.git
cd speed-check

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Run a Test
```bash
python speed_test.py
```

### 3️⃣ Set Up Grafana
See **[grafana_setup.md](grafana_setup.md)** for complete installation and configuration.

### 4️⃣ Import Dashboard
1. In Grafana: **+ → Import**
2. Upload: `speedtest_dashboard.json`
3. Select datasource: **SpeedTest SQLite**
4. Click **Import**

---

## 📊 Database Schema

**Location:** `/var/lib/speed-check/data/speedtest.db`

> **Important:** This follows the [official Grafana SQLite plugin recommendations](https://github.com/fr-ser/grafana-sqlite-datasource/blob/main/docs/faq.md). Do NOT use `/var/lib/grafana/databases/` as it is not a standard Grafana directory and will not persist across reboots.

| Column | Type | Description | Unit |
|--------|------|-------------|------|
| `id` | INTEGER | Auto-incrementing primary key | - |
| `timestamp` | INTEGER | Unix timestamp (seconds since 1970) | seconds |
| `ping` | REAL | Latency | milliseconds |
| `download` | REAL | Download speed | bits/second |
| `upload` | REAL | Upload speed | bits/second |

---

## ⏰ Automated Testing

### Cron Job (Every 15 Minutes)
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
grep CRON /var/log/syslog
```

---

## 📈 Grafana Queries

### Time Series Panels
```sql
-- Download Speed (Mbps)
SELECT timestamp as time, download/1000000.0 as value 
FROM results 
WHERE timestamp >= $__from/1000 AND timestamp <= $__to/1000 
ORDER BY timestamp

-- Upload Speed (Mbps)
SELECT timestamp as time, upload/1000000.0 as value 
FROM results 
WHERE timestamp >= $__from/1000 AND timestamp <= $__to/1000 
ORDER BY timestamp

-- Ping (ms)
SELECT timestamp as time, ping as value 
FROM results 
WHERE timestamp >= $__from/1000 AND timestamp <= $__to/1000 
ORDER BY timestamp
```

### Stat Panels (Latest Values)
```sql
-- Download
SELECT download/1000000.0 as value FROM results ORDER BY timestamp DESC LIMIT 1

-- Upload
SELECT upload/1000000.0 as value FROM results ORDER BY timestamp DESC LIMIT 1

-- Ping
SELECT ping as value FROM results ORDER BY timestamp DESC LIMIT 1
```

---

## 📁 Project Structure

```
speed-check/
├── .gitignore              # Git exclusions
├── .venv/                  # Python virtual environment
├── README.md               # This file
├── grafana_setup.md        # Grafana installation guide
├── project.md              # Detailed project documentation
├── requirements.txt        # Python dependencies
├── speed_test.py           # Main speed test script
├── speedtest_dashboard.json # Grafana dashboard template
└── speedtest.db            # Local SQLite (reference only)

/var/lib/speed-check/data/speedtest.db  # Active database for Grafana
```

---

## 🔧 Configuration

### Datasource Configuration
- **Name:** SpeedTest SQLite
- **Type:** `frser-sqlite-datasource`
- **Path:** `/var/lib/speed-check/data/speedtest.db`
- **Path Prefix:** (leave empty)
- **Path Options:** `?_pragma=query_only(1)` or leave empty (plugin adds it automatically)
- **Access:** Proxy

### Database Setup
```bash
# 1. Create dedicated group for the database
sudo groupadd --system speedtest

# 2. Add both users to the group
sudo usermod -aG speedtest grafana
sudo usermod -aG speedtest admin

# 3. Create directory with proper permissions
sudo install -d -o admin -g speedtest -m 2770 /var/lib/speed-check/data

# 4. Set file permissions (after first run)
sudo chown admin:speedtest /var/lib/speed-check/data/speedtest.db
sudo chmod 660 /var/lib/speed-check/data/speedtest.db
```

---

## 📊 Example Dashboard

![Speed Test Dashboard](https://via.placeholder.com/800x400?text=Speed+Test+Dashboard+Screenshot)

The dashboard includes:
- Download speed over time (line chart)
- Upload speed over time (line chart)
- Ping latency over time (line chart)
- Current download speed (stat)
- Current upload speed (stat)
- Current ping (stat)

---

## 💡 Tips

### Check Data
```bash
source .venv/bin/activate
python -c "import sqlite3; conn = sqlite3.connect('/var/lib/speed-check/data/speedtest.db'); cursor = conn.cursor(); cursor.execute('SELECT count(*), min(timestamp), max(timestamp) FROM results'); print(cursor.fetchone()); conn.close()"
```

### Manual Test
```bash
cd /home/admin/speed-check
source .venv/bin/activate
python speed_test.py
```

### Clean Old Data
```bash
# Delete data older than 30 days
source .venv/bin/activate
python -c "import sqlite3; from datetime import datetime, timedelta; conn = sqlite3.connect('/var/lib/speed-check/data/speedtest.db'); cursor = conn.cursor(); cutoff = int((datetime.now() - timedelta(days=30)).timestamp()); cursor.execute('DELETE FROM results WHERE timestamp < ?', (cutoff,)); conn.commit(); conn.close(); print('Old data cleaned')"
```

---

## 🔄 Changelog
- **v1.0**: Initial setup with MySQL
- **v2.0**: Switched to SQLite
- **v3.0**: Fixed datetime deprecation warning
- **v4.0**: Added Grafana integration
- **v5.0**: Fixed timezone issues with Unix timestamps in seconds
- **v6.0**: Added automated cron job (every 15 minutes)
- **v7.0**: Fixed database path to `/var/lib/speed-check/data/speedtest.db` following [official Grafana SQLite plugin recommendations](https://github.com/fr-ser/grafana-sqlite-datasource/blob/main/docs/faq.md). Added proper group-based permissions (speedtest group) and corrected Path Options format (requires `?` prefix). Removed reference to non-standard `/var/lib/grafana/databases/` directory.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

[MIT License](https://choosealicense.com/licenses/mit/)

---

## 🙏 Acknowledgments

- [speedtest-cli](https://github.com/sivel/speedtest-cli) - Speed test library
- [Grafana](https://grafana.com/) - Visualization platform
- [frser-sqlite-datasource](https://github.com/fr-ser/grafana-sqlite-datasource) - Official SQLite plugin for Grafana (recommended)
