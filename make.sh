#!/bin/sh

now=$(date +%s)

# load vars from .env
set -a; . .env; set +a

if script --version >/dev/null 2>&1; then # GNU script
    script() { command script; }
else # BSD script
    script() { command script "$@"; }
fi

case $1 in
test) shift; script python3 test.py "$@" ;;
auto) shift; python3 auto.py "$@" ;;
chat) shift; python3 chat.py "$@" ;;
*) printf 'Invalid command %s\n' "$1"; exit 1
esac
