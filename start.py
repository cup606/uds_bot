import subprocess
import time

subprocess.Popen(["python", "uds_bot.py"])
subprocess.Popen(["python", "discord_bot.py"])

while True:
    time.sleep(3600)
