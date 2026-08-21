# Grafana Setup for SQLite (Raspberry Pi 3B+)

## 📊 Overview
Visualize your speed test data from SQLite in Grafana using the **official** SQLite datasource plugin.

> **⚠️ IMPORTANT:** This guide uses the **frser-sqlite-datasource** plugin, which is the actively maintained and officially recommended plugin. Do NOT use `marcusolsson-sqlite-datasource` as it is deprecated.

## ✅ Prerequisites
- Raspberry Pi 3B+ running Raspberry Pi OS
- Your speed test script (`speed_test.py`) already configured

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

# Install the OFFICIAL SQLite datasource plugin
sudo grafana-cli plugins install frser-sqlite-datasource

# Restart Grafana
sudo systemctl start grafana-server
```

> **Note:** The plugin will be installed to `/var/lib/grafana/plugins/`
> 
> **Why frser-sqlite-datasource?** This is the actively maintained plugin recommended by Grafana. See: https://github.com/fr-ser/grafana-sqlite-datasource

## ⚙️ Step 3: Set Up Database Directory

**⚠️ CRITICAL:** Do this BEFORE configuring Grafana. The `/var/lib/grafana/databases/` directory is NOT standard and will not persist across reboots.

```bash
# 1. Create dedicated group for the database
sudo groupadd --system speedtest

# 2. Add both Grafana and your user to the group
sudo usermod -aG speedtest grafana
sudo usermod -aG speedtest admin

# 3. Create directory with proper permissions
sudo install -d -o admin -g speedtest -m 2770 /var/lib/speed-check/data

# 4. Run your script once to create the database
cd /home/admin/speed-check
source .venv/bin/activate
python speed_test.py

# 5. Set file permissions
sudo chown admin:speedtest /var/lib/speed-check/data/speedtest.db
sudo chmod 660 /var/lib/speed-check/data/speedtest.db

# 6. Restart Grafana to pick up group changes
sudo systemctl restart grafana-server
```

> **Why this matters:** This follows the [official plugin recommendations](https://github.com/fr-ser/grafana-sqlite-datasource/blob/main/docs/faq.md) which state: "Avoid storing the file under `/home/...`; systemd hardening can prevent Grafana from accessing home directories. Moving the file under `/var/lib` or `/opt` is safer and simpler."

## 📊 Step 4: Configure SQLite Datasource in Grafana

1. Log in to Grafana (`http://<your-pi-ip>:3000`)
2. Go to **Configuration** → **Data Sources**
3. Click **"Add data source"**
4. Search for and select **"SQLite"**
5. Configure the datasource:
   - **Name:** `SpeedTest SQLite` (or any name you prefer)
   - **Path:** `/var/lib/speed-check/data/speedtest.db` (full absolute path)
   - **Path Prefix:** **(leave EMPTY - do NOT use `file:`)**
   - **Path Options:** `?_pragma=query_only(1)` **OR leave empty** (plugin adds it automatically)
   - **Access:** Proxy
   - Click **"Save & Test"**

> **⚠️ CRITICAL:** If you use Path Options, you **MUST** include the `?` prefix (e.g., `?_pragma=query_only(1)`). Without it, the plugin will look for a file named `speedtest.db_pragma=query_only(1)` which doesn't exist, resulting in the error: "no file exists at the file path".

## 📈 Step 5: Create a Dashboard

### Option A: Import the Pre-made Dashboard
1. In Grafana: **+ → Import**
2. Upload: `speedtest_dashboard.json` (included in this project)
3. Select datasource: **SpeedTest SQLite**
4. Click **Import**

### Option B: Create Manually
1. Click **"+" → Create → Dashboard**
2. Click **"Add new panel"**
3. In the query editor:
   - Select your SQLite datasource
   - Write SQL queries (see examples below)
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

- **Verify Grafana can access the database:**
  ```bash
  sudo -u grafana sqlite3 /var/lib/speed-check/data/speedtest.db 'SELECT COUNT(*) FROM results;'
  ```
  If this fails, check permissions and group membership.

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

- **After making permission changes:** Always restart Grafana with `sudo systemctl restart grafana-server` to ensure the service picks up new group memberships.

## 🔄 Automating Data Collection

To run tests automatically, add a cron job:
```bash
# Edit crontab
crontab -e

# Add this line to run every 15 minutes (recommended)
*/15 * * * * cd /home/admin/speed-check && /home/admin/speed-check/.venv/bin/python speed_test.py
```

> **Note:** The cron job runs as your user (admin), which is in the `speedtest` group, so it can write to `/var/lib/speed-check/data/speedtest.db`.

## 📚 Resources
- **Official Plugin:** https://grafana.com/grafana/plugins/frser-sqlite-datasource/
- **Plugin Documentation:** https://github.com/fr-ser/grafana-sqlite-datasource
- **FAQ & Best Practices:** https://github.com/fr-ser/grafana-sqlite-datasource/blob/main/docs/faq.md
- Grafana Documentation: https://grafana.com/docs/
