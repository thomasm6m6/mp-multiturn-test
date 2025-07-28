#!/usr/bin/env python3

import os
import pty
import tty
import sys
import time
import termios
import subprocess
import select
import shutil
import fcntl
import struct
import signal
from pathlib import Path
from dotenv import load_dotenv

COMMANDS = {
    'auto': 'auto.py',
    'test': 'test.py',
    'chat': 'chat.py',
}

# basic clone of script(1)
def script(args, *, logfile):
    parent_fd, child_fd = pty.openpty()

    def resize_pty():
        try:
            cols, rows = shutil.get_terminal_size()
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(parent_fd, termios.TIOCSWINSZ, winsize)
        except (OSError, NameError):
            pass

    def sigwinch_handler(signum, frame):
        resize_pty()

    resize_pty()

    signal.signal(signal.SIGWINCH, sigwinch_handler)

    term_settings = termios.tcgetattr(sys.stdin.fileno())
    log_handle = open(logfile, 'ab')

    proc = None

    try:
        tty.setraw(sys.stdin.fileno())
        proc = subprocess.Popen(
            args,
            stdin=child_fd,
            stdout=child_fd,
            stderr=child_fd,
            preexec_fn=os.setsid
        )
        os.close(child_fd)

        while proc.poll() is None:
            try:
                ready_fds, _, _ = select.select([sys.stdin, parent_fd], [], [])
            except InterruptedError:
                continue

            if sys.stdin in ready_fds:
                user_input = os.read(sys.stdin.fileno(), 1024)
                if user_input:
                    os.write(parent_fd, user_input)
                else:
                    break   # EOF

            if parent_fd in ready_fds:
                try:
                    child_output = os.read(parent_fd, 1024)
                except OSError:
                    child_output = b''

                if child_output:
                    os.write(sys.stdout.fileno(), child_output)
                    log_handle.write(child_output)
                else:
                    break   # PTY closed

    finally:
        if proc and proc.poll() is None:
            proc.kill()
        log_handle.close()
        os.close(parent_fd)
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, term_settings)


if __name__ == '__main__':
    now = time.time()
    load_dotenv()

    if len(sys.argv) < 2:
        print(f'Usage: python3 {sys.argv[0]} <command> [args...]', file=sys.stderr)
        print('Commands: ' + ', '.join(COMMANDS.keys()), file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Unknown command '{sys.argv[1]}'")
        sys.exit(1)

    filename = COMMANDS[cmd]
    args = sys.argv[2:]

    if not os.path.exists(filename):
        print(f'Error: cannot find {filename}')
        sys.exit(1)

    script_logfile = Path('logs') / cmd / f'{int(now)}.log'
    logfile = Path('logs') / cmd / f'{int(now)}.out.log'
    os.makedirs(logfile.parent, exist_ok=True)
    os.environ['LOGFILE'] = str(script_logfile)

    script(['python3', filename] + args, logfile=logfile)
