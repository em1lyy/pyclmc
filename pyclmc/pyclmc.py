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

QUIT = [ord('q'), curses.KEY_CANCEL, curses.KEY_END, curses.KEY_EXIT, 27]
VOLUME_UP = [ord('+'), ord('0'), curses.KEY_UP]
VOLUME_DOWN = [ord('-'), ord('9'), curses.KEY_DOWN]
MUTE = [ord('m')]
PLAYPAUSE = [ord(' '), ord('p'), curses.KEY_ENTER]
DEFAULT_VOLUME = 100
VOLUMESTEP = 5

def main():
    stdscr = _init_curses()

    set_header_text(stdscr, "Initializing...")

    mplayer_process = _init_mplayer_with_pipe()
    set_header_text(stdscr, "Playing")

    key_event = -1
    while key_event not in QUIT:  # Handle keys
        key_event = stdscr.getch()
        if key_event in VOLUME_UP:
            mplayer_incvol(mplayer_process)
        elif key_event in VOLUME_DOWN:
            mplayer_decvol(mplayer_process)
        elif key_event in MUTE:
            mplayer_mutetoggle(mplayer_process)
        elif key_event in PLAYPAUSE:
            mplayer_playpause(mplayer_process)

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

def set_header_text(stdscr, text):  # Change the text of the window header
    HEADER_TEXT = f'{text} - pyclmc'
    stdscr.addstr(0, 0, int(curses.COLS/2-(len(HEADER_TEXT)/2))*" " + HEADER_TEXT + int(curses.COLS/2-(len(HEADER_TEXT)/2)) * " ",
              curses.A_REVERSE)
    stdscr.refresh()

def _init_mplayer_with_pipe():  # Start mplayer and return the stdin as a pipe
    p = Popen(f'mplayer -volume {DEFAULT_VOLUME} -volstep {VOLUMESTEP} https://listen.moe/stream', stdin=PIPE, stdout=DEVNULL)
    return p

def _quit_mplayer(proc):  # Send q character to mplayer to quit
    line = b'q'
    try:
        proc.stdin.write(line)
    except IOError as e:
        proc.kill()
    proc.stdin.flush()
    proc.stdin.close()
    proc.wait()

def mplayer_incvol(proc):  # Increase mplayer volume
    line = b'0'
    try:
        proc.stdin.write(line)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            return
        else:
            raise
    proc.stdin.flush()

def mplayer_decvol(proc):  # Decrease mplayer volume
    line = b'9'
    try:
        proc.stdin.write(line)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            return
        else:
            raise
    proc.stdin.flush()

def mplayer_playpause(proc):  # Play/Pause mplayer
    line = b' '
    try:
        proc.stdin.write(line)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            return
        else:
            raise
    proc.stdin.flush()

def mplayer_mutetoggle(proc):  # Toggle mplayer mute state
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
