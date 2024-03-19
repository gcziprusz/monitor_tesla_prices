# crontab content 

```
MONITOR_SENDER_EMAIL=
MONITOR_RECIPIENT_EMAIL=
MONITOR_RECIPIENT_CC=
MONITOR_EMAIL_PASSWORD=
MONITOR_PROCESS_FILE={ADD DIR}/processed_ids.txt
* * * * * /usr/bin/python3 {ADD DIR}/monitor.py >>{ADD DIR}/out.log 2>&1
```
