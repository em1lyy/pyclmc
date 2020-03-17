#!/usr/bin/env python

# pyclmc
# PYthon Curses Listen.Moe Client
#
# Released under GNU GPLv3 https://www.gnu.org/licenses/gpl-3.0.en.html
# Maintained by Jonas Jaguar <jonasjaguar@jagudev.net>, 2020

from time import sleep
import curses
from subprocess import Popen, PIPE, DEVNULL
import errno

HEADER_TEXT = ""

def main():
    stdscr = _init_curses()

    set_header_text(stdscr, "Initializing...")

    mplayer_process = _init_mplayer_with_pipe()
    set_header_text(stdscr, "Playing")
    sleep(60)

    set_header_text(stdscr, "Quitting...")
    _quit_mplayer(mplayer_process)
    _quit_curses(stdscr)

def _init_curses():
    stdscr = curses.initscr()  # Init screen
    curses.noecho()  # No echo-ing characters
    curses.cbreak()  # Instant key handling
    stdscr.keypad(True)  # Conversion of special characters
    stdscr.clear()
    return stdscr

def _quit_curses(stdscr):  # Revert to terminal-friendly mode
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

def set_header_text(stdscr, text):
    HEADER_TEXT = f'{text} - pyclmc'
    stdscr.addstr(0, 0, int(curses.COLS/2-(len(HEADER_TEXT)/2))*" " + HEADER_TEXT + int(curses.COLS/2-(len(HEADER_TEXT)/2)) * " ",
              curses.A_REVERSE)
    stdscr.refresh()

def _init_mplayer_with_pipe():
    p = Popen('mplayer https://listen.moe/stream', stdin=PIPE, stdout=DEVNULL)
    return p

def _quit_mplayer(proc):
    line = b'q'
    try:
        proc.stdin.write(line)
    except IOError as e:
        proc.kill()
    proc.stdin.flush()
    proc.stdin.close()
    proc.wait()

def mplayer_incvol(proc):
    line = b'0'
    try:
        proc.stdin.write(line)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            return
        else:
            raise
    proc.stdin.flush()

def mplayer_decvol(proc):
    line = b'9'
    try:
        proc.stdin.write(line)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            return
        else:
            raise
    proc.stdin.flush()

def mplayer_playpause(proc):
    line = b' '
    try:
        proc.stdin.write(line)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            return
        else:
            raise
    proc.stdin.flush()

def mplayer_mutetoggle(proc):
    line = b'm'
    try:
        proc.stdin.write(line)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            return
        else:
            raise
    proc.stdin.flush()

if __name__ == '__main__':
    main()
