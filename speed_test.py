import sqlite3
import subprocess
import json
from datetime import datetime

# Initialize SQLite database (location accessible by Grafana)
# NOTE: Do NOT use /var/ with Grafana v8.2.0+ due to systemd PrivateTmp isolation
DB_PATH = '/opt/speed-check/data/speedtest.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table if it doesn't exist (using INTEGER for Unix timestamp)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        ping REAL,
        download REAL,
        upload REAL
    )
''')
conn.commit()

# Run speed test using Ookla CLI
try:
    # Run the test with JSON output
    output = subprocess.check_output(
        ['/usr/local/bin/speedtest', '-f', 'json'],
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Parse JSON output - Ookla outputs multiple JSON objects, we need the result type
    data = None
    for line in output.strip().split('\n'):
        if line.strip():
            try:
                parsed = json.loads(line)
                if parsed.get('type') == 'result':
                    data = parsed
                    break
            except json.JSONDecodeError:
                continue
    
    if data is None:
        print(f"No result data found in output")
        exit(1)
    
    # Extract metrics
    ping = data['ping']['latency']
    download = data['download']['bandwidth'] * 8  # Convert bytes/sec to bits/sec
    upload = data['upload']['bandwidth'] * 8      # Convert bytes/sec to bits/sec
    timestamp = int(datetime.now().timestamp())
    
    # Insert results into the database
    sql = "INSERT INTO results (timestamp, ping, download, upload) VALUES (?, ?, ?, ?)"
    val = (timestamp, ping, download, upload)
    cursor.execute(sql, val)
    conn.commit()
    
    print("Speed test results saved successfully!")
    
except subprocess.CalledProcessError as e:
    print(f"Error running speedtest (code {e.returncode}): {e.output}")
    exit(1)
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# Close database connection
conn.close()