import atexit
import time
import os

class Logger:
  os.path.dirname(__file__)
  def __init__(self, name=None, cutoff=1024):
    fname = os.path.join(os.path.dirname(__file__), "x.log")
    self.file = open(fname, 'a', buffering=1)
    self.name = name
    self.cutoff = cutoff
    self.queue = []
    atexit.register(self._cleanup)

  def _log(self, msg, quietly=False):
    now = time.time()
    msg = msg.strip()
    line = f"{now} {self.name} {msg}"
    print(line, file=self.file)
    if not quietly:
      print(msg[:self.cutoff])
      if len(msg) > self.cutoff:
        print("\n...")

  def __call__(self, msg, **kwargs):
    return self._log(msg, **kwargs)

  def later(self, fn_or_str, **kwargs):
    self.queue.append((fn_or_str, kwargs))

  def _cleanup(self):
    for (fn_or_str, kwargs) in self.queue:
      if callable(fn_or_str):
        msg = fn_or_str()
      else:
        msg = fn_or_str
      self._log(msg, **kwargs)
    self.file.close()
