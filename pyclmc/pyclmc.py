#!/usr/bin/env python

# pyclmc
# PYthon Curses Listen.Moe Client
#
# Released under GNU GPLv3 https://www.gnu.org/licenses/gpl-3.0.en.html
# Maintained by Jonas Jaguar <jonasjaguar@jagudev.net>, 2020

import curses
from time import sleep

HEADER_TEXT = "Not playing - pyclmc"

def main():
    stdscr = _init_curses()
    stdscr.addstr(0, 0, int(curses.COLS/2-(len(HEADER_TEXT)/2))*" " + HEADER_TEXT + int(curses.COLS/2-(len(HEADER_TEXT)/2)) * " ",
              curses.A_REVERSE)
    stdscr.refresh()
    sleep(5)
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

if __name__ == '__main__':
    main()
