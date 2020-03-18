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
import asyncio
import threading

import listenmoe_websocket

HEADER_TEXT = ""

QUIT = [ord('q'), curses.KEY_CANCEL, curses.KEY_END, curses.KEY_EXIT, 27]
VOLUME_UP = [ord('+'), ord('0'), curses.KEY_UP]
VOLUME_DOWN = [ord('-'), ord('9'), curses.KEY_DOWN]
MUTE = [ord('m')]
PLAYPAUSE = [ord(' '), ord('p'), curses.KEY_ENTER]
VOLUME = 100
VOLUMESTEP = 5
PLAYING_STATE = True
MUTED_STATE = False
CURRENT_META = { "title": "Loading title...", "album": "Loading album...", "artist": "Loading artist...", "cover": None }

def main():
    stdscr = _init_curses()

    set_header_text(stdscr, "Initializing...")

    mplayer_process = _init_mplayer_with_pipe()
    set_header_text(stdscr, "Playing")
    update_meta_display(stdscr)

    wsthread = _init_metadata_websocket(stdscr)

    key_event = -1
    while key_event not in QUIT:  # Handle keys
        key_event = stdscr.getch()
        if key_event in VOLUME_UP:
            mplayer_incvol(stdscr, mplayer_process)
        elif key_event in VOLUME_DOWN:
            mplayer_decvol(stdscr, mplayer_process)
        elif key_event in MUTE:
            mplayer_mutetoggle(stdscr, mplayer_process)
        elif key_event in PLAYPAUSE:
            mplayer_playpause(stdscr, mplayer_process)

    set_header_text(stdscr, "Quitting...")
    _quit_metadata_websocket()
    _quit_mplayer(mplayer_process)
    _quit_curses(stdscr)

def _init_curses():
    stdscr = curses.initscr()  # Init screen
    curses.noecho()  # No echo-ing characters
    curses.cbreak()  # Instant key handling
    stdscr.keypad(True)  # Conversion of special characters
    stdscr.clear()  # Clear screen
    curses.curs_set(0)  # Make cursor invisible
    return stdscr

def _quit_curses(stdscr):  # Revert to terminal-friendly mode
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

def _init_metadata_websocket(stdscr):
    loop = asyncio.get_event_loop()
    wsthread = threading.Thread(target=listenmoe_websocket.run_mainloop, args=(loop, update_meta_variables, stdscr,))
    wsthread.start()
    return wsthread

def _quit_metadata_websocket():
    loop = asyncio.get_event_loop()
    loop.stop()

def set_header_text(stdscr, text):  # Change the text of the window header
    HEADER_TEXT = f'{text} - pyclmc'
    stdscr.addstr(0, 0, int(curses.COLS/2-(len(HEADER_TEXT)/2))*" " + HEADER_TEXT + int(curses.COLS/2-(len(HEADER_TEXT)/2)) * " ",
              curses.A_REVERSE)
    stdscr.refresh()

def update_meta_variables(data, stdscr):
    if data['t'] == 'TRACK_UPDATE':
        CURRENT_META["title"] = data['d']['song']['title']
        if data['d']['song']['albums']:
            CURRENT_META["album"] = data['d']['song']['albums'][0]['name']  # Although albums is technically an array, why would you want to display multiple albums?
        else:
            CURRENT_META["album"] = "No album"
        if data['d']['song']['artists']:
            CURRENT_META["artist"] = ""
            for artist in data['d']['song']['artists']:
                CURRENT_META["artist"] += artist['name'] + "　"
        else:
            CURRENT_META["album"] = "No artist"
        update_meta_display(stdscr)

def update_meta_display(stdscr):  # Updates the metadata display
    stdscr.addstr(int(curses.LINES/2)-2, int(curses.COLS/2), _fill_spaces(CURRENT_META["title"]))
    stdscr.addstr(int(curses.LINES/2)-1, int(curses.COLS/2), _fill_spaces(CURRENT_META["album"]))
    stdscr.addstr(int(curses.LINES/2), int(curses.COLS/2), _fill_spaces(CURRENT_META["artist"]))
    volume = f'Volume: {str(VOLUME)}% {" (muted)  " if MUTED_STATE else "          "}'
    stdscr.addstr(int(curses.LINES/2)+1, int(curses.COLS/2), volume)
    if PLAYING_STATE:
        stdscr.addstr(int(curses.LINES/2)+2, int(curses.COLS/2), "Playing")
    else:
        stdscr.addstr(int(curses.LINES/2)+2, int(curses.COLS/2), "Paused ")
    stdscr.refresh()

def _fill_spaces(text):  # Fills spaces after text until window end
    return text + int(curses.COLS/2-(len(text)/2)) * " "

def _init_mplayer_with_pipe():  # Start mplayer and return the stdin as a pipe
    p = Popen(f'mplayer -volume {VOLUME} -volstep {VOLUMESTEP} https://listen.moe/stream', stdin=PIPE, stdout=DEVNULL)
    return p

def _quit_mplayer(proc):  # Send q character to mplayer to quit
    _mplayer_sendkey(proc, b'q')
    proc.stdin.close()
    proc.wait()

def _mplayer_sendkey(proc, key):  # Send a key to the mplayer process proc
    try:
        proc.stdin.write(key)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            return
        else:
            raise
    proc.stdin.flush()

def mplayer_incvol(stdscr, proc):  # Increase mplayer volume
    _mplayer_sendkey(proc, b'0')
    global VOLUME
    VOLUME = min(VOLUME + VOLUMESTEP, 100)
    update_meta_display(stdscr)

def mplayer_decvol(stdscr, proc):  # Decrease mplayer volume
    _mplayer_sendkey(proc, b'9')
    global VOLUME
    VOLUME = max(VOLUME - VOLUMESTEP, 0)
    update_meta_display(stdscr)

def mplayer_playpause(stdscr, proc):  # Play/Pause mplayer
    _mplayer_sendkey(proc, b' ')
    global PLAYING_STATE
    PLAYING_STATE = not PLAYING_STATE
    if PLAYING_STATE:
        set_header_text(stdscr, "Playing")
    else:
        set_header_text(stdscr, "Paused")
    update_meta_display(stdscr)

def mplayer_mutetoggle(stdscr, proc):  # Toggle mplayer mute state
    _mplayer_sendkey(proc, b'm')
    global MUTED_STATE
    MUTED_STATE = not MUTED_STATE
    update_meta_display(stdscr)

if __name__ == '__main__':
    main()
