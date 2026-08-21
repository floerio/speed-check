from speedtest import Speedtest
import sqlite3
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

# Run speed test
st = Speedtest()
st.get_best_server()
st.download()
st.upload()
results = st.results.dict()

# Insert results into the database (store as Unix timestamp in SECONDS)
sql = "INSERT INTO results (timestamp, ping, download, upload) VALUES (?, ?, ?, ?)"
val = (int(datetime.now().timestamp()), results['ping'], results['download'], results['upload'])
cursor.execute(sql, val)

conn.commit()
conn.close()