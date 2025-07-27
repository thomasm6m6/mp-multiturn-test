#!/bin/sh

case $1 in
test) shift; python3 -u test.py "$@" | tee -a logs/test.out.log ;;
auto) shift; python3 -u auto.py "$@" | tee -a logs/auto.out.log ;;
# XXX can we pipe output from this without breaking interactive input?
chat)  shift; python3 chat.py "$@" ;;
*) printf 'Invalid command %s\n' "$1"; exit 1
esac
