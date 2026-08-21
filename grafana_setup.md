# Grafana Setup for SQLite (Raspberry Pi 3B+)

## 📊 Overview
Visualize your speed test data from SQLite in Grafana using the **official** SQLite datasource plugin.

> **⚠️ IMPORTANT:** This guide uses the **frser-sqlite-datasource** plugin, which is the actively maintained and officially recommended plugin. Do NOT use `marcusolsson-sqlite-datasource` as it is deprecated.

> **⚠️ CRITICAL:** Do NOT use `/var/` for your database with Grafana v8.2.0+ due to systemd PrivateTmp isolation. Use `/opt/` instead.

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

**⚠️ CRITICAL:** Do NOT use `/var/` with Grafana v8.2.0+ due to systemd PrivateTmp isolation. Use `/opt/` instead.

```bash
# 1. Create dedicated group for the database
sudo groupadd --system speedtest

# 2. Add both Grafana and your user to the group
sudo usermod -aG speedtest grafana
sudo usermod -aG speedtest admin

# 3. Create directory with proper permissions (NOT in /var)
sudo install -d -o admin -g speedtest -m 2770 /opt/speed-check/data

# 4. Run your script once to create the database
cd /home/admin/speed-check
source .venv/bin/activate
python speed_test.py

# 5. Set file permissions
sudo chown admin:speedtest /opt/speed-check/data/speedtest.db
sudo chmod 660 /opt/speed-check/data/speedtest.db
```

> **Why this matters:** Grafana v8.2.0+ runs with `PrivateTmp=true` by default, which isolates `/var`, `/tmp`, and other system directories. The `/opt/` directory is NOT isolated and remains accessible. See: https://github.com/fr-ser/grafana-sqlite-datasource/blob/main/docs/faq.md

## 📄 Step 4: Configure Provisioning File

To ensure your datasource persists across reboots, configure it via provisioning:

```bash
# Create provisioning file with correct permissions
sudo bash -c 'cat > /etc/grafana/provisioning/datasources/sqlite.yaml << "EOF"
apiVersion: 1

datasources:
  - name: SpeedTest SQLite
    uid: P1DED9D3A955C8195
    type: frser-sqlite-datasource
    access: proxy
    orgId: 1
    isDefault: true
    editable: true
    jsonData:
      path: /opt/speed-check/data/speedtest.db
EOF'

# Set ownership so Grafana can read it
sudo chown grafana:grafana /etc/grafana/provisioning/datasources/sqlite.yaml
sudo chmod 644 /etc/grafana/provisioning/datasources/sqlite.yaml
```

> **⚠️ CRITICAL NOTES:**
> - Use **`path:`** not `database:` - the frser-sqlite-datasource plugin expects `path` in jsonData
> - Include the **UID** to ensure Grafana updates the existing datasource instead of creating a duplicate
> - The file **must be readable** by the Grafana user (grafana:grafana)

## 📊 Step 5: Configure SQLite Datasource in Grafana

1. Log in to Grafana (`http://<your-pi-ip>:3000`)
2. Go to **Configuration** → **Data Sources**
3. Your datasource **"SpeedTest SQLite"** should appear automatically from provisioning
4. Click on it to verify:
   - **Path:** `/opt/speed-check/data/speedtest.db` (full absolute path)
   - **Path Prefix:** **(leave EMPTY - do NOT use `file:`)**
   - **Path Options:** `?_pragma=query_only(1)` **OR leave empty** (plugin adds it automatically)
   - **Access:** Proxy

> **⚠️ CRITICAL:** If you use Path Options, you **MUST** include the `?` prefix (e.g., `?_pragma=query_only(1)`). Without it, the plugin will look for a file named `speedtest.db_pragma=query_only(1)` which doesn't exist, resulting in the error: "no file exists at the file path".

## 📈 Step 6: Create a Dashboard

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
  sudo -u grafana sqlite3 /opt/speed-check/data/speedtest.db 'SELECT COUNT(*) FROM results;'
  ```
  If this fails, check permissions and group membership.

- **Verify provisioning file permissions:**
  ```bash
  ls -la /etc/grafana/provisioning/datasources/sqlite.yaml
  ```
  Should show: `-rw-r--r-- 1 grafana grafana ...`

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

> **Note:** The cron job runs as your user (admin), which is in the `speedtest` group, so it can write to `/opt/speed-check/data/speedtest.db`.

## 📚 Resources
- **Official Plugin:** https://grafana.com/grafana/plugins/frser-sqlite-datasource/
- **Plugin Documentation:** https://github.com/fr-ser/grafana-sqlite-datasource
- **FAQ & Best Practices:** https://github.com/fr-ser/grafana-sqlite-datasource/blob/main/docs/faq.md
- Grafana Documentation: https://grafana.com/docs/
