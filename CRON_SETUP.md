# Cron Job Setup for Scheduled Publisher

## Option 1: Linux Crontab

Add to crontab (`crontab -e`):

```bash
# Run every 15 minutes
*/15 * * * * /usr/bin/python3 -m backend.jobs.scheduled_publisher >> /var/log/scheduled_publisher.log 2>&1
```

## Option 2: Systemd Timer (Recommended for Production)

Create `/etc/systemd/system/scheduled-publisher.service`:

```ini
[Unit]
Description=VintedBot Scheduled Publisher
After=network.target

[Service]
Type=oneshot
User=vintedbot
WorkingDirectory=/home/user/vintedbot
ExecStart=/usr/bin/python3 -m backend.jobs.scheduled_publisher
Environment="PYTHONPATH=/home/user/vintedbot"
```

Create `/etc/systemd/system/scheduled-publisher.timer`:

```ini
[Unit]
Description=Run VintedBot Scheduled Publisher every 15 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Unit=scheduled-publisher.service

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable scheduled-publisher.timer
sudo systemctl start scheduled-publisher.timer
sudo systemctl status scheduled-publisher.timer
```

## Option 3: Python APScheduler (In-app)

Already integrated in `backend/jobs.py` if you want to run it within the FastAPI app:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.jobs.scheduled_publisher import publish_scheduled_items

scheduler = AsyncIOScheduler()
scheduler.add_job(publish_scheduled_items, 'interval', minutes=15)
scheduler.start()
```

## Monitoring

Check logs:
```bash
# Cron logs
tail -f /var/log/scheduled_publisher.log

# Systemd logs
journalctl -u scheduled-publisher.service -f
```
