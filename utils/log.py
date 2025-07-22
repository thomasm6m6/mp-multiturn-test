import os
import time
import atexit
from .globals import shared_state

log_queue = []

os.makedirs("logs", exist_ok=True)
LOGFILE = open(f"logs/{int(time.time())}.txt", 'w')

def cleanup():
  log("\nCleanup messages:")
  for (msg, kwargs) in log_queue:
    log(msg, **kwargs)
  log(f"Total cost used: ${round(shared_state['total_cost'], 3)}")
  LOGFILE.close()

atexit.register(cleanup)

def log(msg, file_only=False):
  print(msg, file=LOGFILE)
  if not file_only:
    cutoff = 1024
    print(msg[:cutoff])
    if len(msg) > cutoff:
      print("\n[output elided for length. see log file]\n")

def log_later(msg, **kwargs):
  log_queue.append((msg, kwargs))

def flush_log():
  LOGFILE.flush()
