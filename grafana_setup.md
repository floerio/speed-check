# Grafana Setup for SQLite (Raspberry Pi 3B+)

## 📊 Overview
Visualize your speed test data from SQLite in Grafana using the SQLite datasource plugin.

## ✅ Prerequisites
- Raspberry Pi 3B+ running Raspberry Pi OS
- Your speed test script already running with SQLite (`speedtest.db`)

## 🚀 Step 1: Install Grafana

```bash
# Add Grafana repository
sudo apt-get install -y apt-transport-https
sudo apt-get install -y software-properties-common wget
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list

# Install Grafana
sudo apt update
sudo apt install grafana -y

# Start and enable Grafana service
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Verify it's running
sudo systemctl status grafana-server
```

**Access Grafana:** Open `http://<your-pi-ip>:3000` in your browser
- Default login: `admin` / `admin` (you'll be prompted to change password)

## 🔌 Step 2: Install SQLite Datasource Plugin

```bash
# Stop Grafana service
sudo systemctl stop grafana-server

# Install the SQLite datasource plugin (community plugin)
sudo grafana-cli plugins install marcusolsson-sqlite-datasource

# Restart Grafana
sudo systemctl start grafana-server
```

> **Note:** The plugin will be installed to `/var/lib/grafana/plugins/`

## ⚙️ Step 3: Configure SQLite Datasource in Grafana

1. Log in to Grafana (`http://<your-pi-ip>:3000`)
2. Go to **Configuration** → **Data Sources**
3. Click **"Add data source"**
4. Search for and select **"SQLite"**
5. Configure the datasource:
   - **Name:** `SpeedTest SQLite` (or any name you prefer)
   - **Path:** `/home/admin/speed-check/speedtest.db` (full absolute path to your database)
   - Click **"Save & Test"**

## 📈 Step 4: Create a Dashboard

### Option A: Import a Pre-made Dashboard
I can create a JSON dashboard file for you to import.

### Option B: Create Manually
1. Click **"+" → Create → Dashboard**
2. Click **"Add new panel"**
3. In the query editor:
   - Select your SQLite datasource
   - Write SQL queries like:
     ```sql
     SELECT timestamp, download FROM results ORDER BY timestamp
     ```
4. Set visualization type to **Time series** or **Stat**

## 🎨 Suggested Panels

1. **Download Speed (Time Series)**
   ```sql
   SELECT timestamp, download/1000000 as download_mbps FROM results ORDER BY timestamp
   ```

2. **Upload Speed (Time Series)**
   ```sql
   SELECT timestamp, upload/1000000 as upload_mbps FROM results ORDER BY timestamp
   ```

3. **Ping (Time Series)**
   ```sql
   SELECT timestamp, ping FROM results ORDER BY timestamp
   ```

4. **Current Stats (Stat Panel)**
   ```sql
   SELECT 
     download/1000000 as download_mbps,
     upload/1000000 as upload_mbps,
     ping as ping_ms
   FROM results ORDER BY timestamp DESC LIMIT 1
   ```

## 💡 Tips for Raspberry Pi 3B+

- **Reduce Grafana memory usage:** Edit `/etc/grafana/grafana.ini` and set:
  ```
  [server]
  http_port = 3000
  
  [auth.anonymous]
  enabled = true
  ```

- **Limit data retention:** Your SQLite file will grow over time. Consider:
  - Running a weekly cleanup script
  - Or adding a `DELETE` query to remove old data

- **Access from other devices:** Make sure your Pi's firewall allows port 3000

## 🔄 Automating Data Collection

To run tests automatically, add a cron job:
```bash
# Edit crontab
crontab -e

# Add this line to run every hour
0 * * * * cd /home/admin/speed-check && /home/admin/.venv/bin/python speed_test.py
```

## 📚 Resources
- Grafana SQLite Plugin: https://grafana.com/grafana/plugins/marcusolsson-sqlite-datasource/
- Grafana Documentation: https://grafana.com/docs/
