#!/usr/bin/env python

# pyclmc
# PYthon Curses Listen.Moe Client
#
# Released under GNU GPLv3 https://www.gnu.org/licenses/gpl-3.0.en.html
# Maintained by and Copyright 2020 - 2021, Emily <elishikawa@jagudev.net>

from time import sleep
import curses
from subprocess import Popen, PIPE, DEVNULL
import errno
import asyncio
import threading
from random import choice, randint
import colorsys
from math import floor

import listenmoe_websocket

# Variables describing the current program state
HEADER_TEXT = ""
PLAYING_STATE = True
MUTED_STATE = False
VOLUME = 75
CURRENT_META = { "title": "Loading title...", "album": "Loading album...", "artist": "Loading artist...", "cover": None }
CURRENT_FOOTER = ""
COVER_ANIM_MODES = [ "SPECTRUM", "WAVE", "SPIN", "OUTLINESPIN", "PULSE" ]
COVER_ANIM_MODE_INDEX = 0
COVER_ANIM_FRAME = 0

# Config Variables
QUIT = [ord('q'), curses.KEY_CANCEL, curses.KEY_END, curses.KEY_EXIT, 27]
VOLUME_UP = [ord('+'), ord('0'), curses.KEY_UP]
VOLUME_DOWN = [ord('-'), ord('9'), curses.KEY_DOWN]
MUTE = [ord('m')]
PLAYPAUSE = [ord(' '), ord('p'), curses.KEY_ENTER]
CLEARSCREEN = [ord('c'), ord('r')]
VOLUMESTEP = 5

# Footers
FOOTERS = [[ "#    # #### ##### ##### #   #    #   #  ###  #####",
             "#    # #      #   #     ##  #    ## ## #   # #    ",
             "#    # ####   #   ##### # # #    # # # #   # #####",
             "#    #    #   #   #     #  ## ## #   # #   # #    ",
             "#### # ####   #   ##### #   # ## #   #  ###  #####" ],
           [ "###  #   #  ### #    #   #  ###",
             "#  # #   # #    #    ## ## #   ",
             "###   # #  #    #    # # # #   ",
             "#      #   #    #    #   # #   ",
             "#      #    ### #### #   #  ###" ],
           [ " ### #  # # #   #  ###  #  #  ### ",
             "#    #  # # #   # #   # # #  #   #",
             "#    #### #  # #  #   # ##   #   #",
             "#    #  # #   #   #   # # #  #   #",
             " ### #  # #   #    ###  #  #  ### " ]]

def main():
    stdscr = _init_curses()

    set_header_text(stdscr, "Initializing...")

    mplayer_process = _init_mplayer_with_pipe()
    set_header_text(stdscr, "Playing")
    update_meta_display(stdscr)

    wsthread = _init_metadata_websocket(stdscr)
    footerthread = _init_footer(stdscr)
    coverthread = _init_cover(stdscr)
    
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
        elif key_event in CLEARSCREEN:
            full_redraw(stdscr, True)

    set_header_text(stdscr, "Quitting...")
    # _quit_metadata_websocket()  # This is no longer needed. It is still kept just in case something breaks
    _quit_mplayer(mplayer_process)
    _quit_curses(stdscr)

def _init_curses():
    stdscr = curses.initscr()  # Init screen
    curses.noecho()  # No echo-ing characters
    curses.cbreak()  # Instant key handling
    stdscr.keypad(True)  # Conversion of special characters
    stdscr.clear()  # Clear screen
    curses.curs_set(0)  # Make cursor invisible
    curses.start_color()
    # stdscr.addstr(curses.LINES-1, 0, curses.COLS * " ", curses.A_REVERSE)  # Add white line at bottom (doesn't work)
    return stdscr

def _quit_curses(stdscr):  # Revert to terminal-friendly mode
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

def _init_metadata_websocket(stdscr):  # Starts a thread which runs the Listen.Moe Metadata Websocket.
    loop = asyncio.get_event_loop()    # See comments in listenmoe_websocket.py
    wsthread = threading.Thread(target=listenmoe_websocket.run_mainloop, args=(loop, update_meta_variables, stdscr,), daemon=True)
    wsthread.start()
    return wsthread

def _quit_metadata_websocket():  # Sets the cancel variable of the websocket manager to true, resulting in the websocket shutting down
    listenmoe_websocket.cancel = True

def set_header_text(stdscr, text):  # Change the text of the window header
    global HEADER_TEXT
    HEADER_TEXT = f'{text} - pyclmc'
    stdscr.addstr(0, 0, int(curses.COLS/2-(len(HEADER_TEXT)/2))*" " + HEADER_TEXT + int(curses.COLS/2-(len(HEADER_TEXT)/2)) * " ",
              curses.A_REVERSE)
    stdscr.refresh()

def full_redraw(stdscr, redraw_meta):
    stdscr.clear()
    if redraw_meta:
        update_meta_display(stdscr)
    set_header_text(stdscr, HEADER_TEXT[:-9])
    update_footer(stdscr)
    generate_and_show_image(None, curses.LINES - 24, 12, int(curses.COLS / 2) - ((curses.LINES - 24) * 2) - 2, stdscr)
    stdscr.refresh()

def _init_footer(stdscr):
    global CURRENT_FOOTER
    CURRENT_FOOTER = choice(FOOTERS)
    footerthread = threading.Thread(target=_footer_thread_runner, args=(stdscr,), daemon=True)
    footerthread.start()
    return footerthread

def _footer_thread_runner(stdscr):
    sleep(0.1)
    while True:
        update_footer(stdscr)
        sleep(1)

def update_footer(stdscr):
    y = 0
    for line in CURRENT_FOOTER:
        color = randint(1, 7)
        curses.init_pair(color, color, 0)
        stdscr.addstr(curses.LINES - 6 + y, int((stdscr.getmaxyx()[1] - len(line)) / 2), line, curses.color_pair(color))
        y += 1
    stdscr.refresh()

def update_meta_variables(data, stdscr):  # Updates the metadata variables and then calls update_meta_display(stdscr)
    global CURRENT_META
    if data['t'] == 'TRACK_UPDATE':
        CURRENT_META["title"] = data['d']['song']['title']
        if data['d']['song']['albums']:
            CURRENT_META["album"] = data['d']['song']['albums'][0]['name']  # Although albums is technically an array, why would you want to display multiple albums?
            CURRENT_META["cover"] = data['d']['song']['albums'][0]['image']
        else:
            CURRENT_META["album"] = "No album"
            CURRENT_META["cover"] = None
        if data['d']['song']['artists']:
            CURRENT_META["artist"] = ""
            for artist in data['d']['song']['artists']:
                CURRENT_META["artist"] += artist['name'] + "  "
        else:
            CURRENT_META["album"] = "No artist"
        full_redraw(stdscr, False)
        update_meta_display(stdscr)

def update_meta_display(stdscr):  # Updates the metadata display
    stdscr.addstr(int(curses.LINES/2)-2, int(curses.COLS/2), _fill_spaces(CURRENT_META["title"]))
    stdscr.addstr(int(curses.LINES/2)-1, int(curses.COLS/2), _fill_spaces(CURRENT_META["album"]))
    stdscr.addstr(int(curses.LINES/2), int(curses.COLS/2), _fill_spaces(CURRENT_META["artist"]))
    volume = f'Volume: {str(VOLUME)}% {"(muted)  " if MUTED_STATE else "         "}'
    stdscr.addstr(int(curses.LINES/2)+1, int(curses.COLS/2), volume)
    if PLAYING_STATE:
        stdscr.addstr(int(curses.LINES/2)+2, int(curses.COLS/2), "Playing")
    else:
        stdscr.addstr(int(curses.LINES/2)+2, int(curses.COLS/2), "Paused ")
    stdscr.refresh()

def _init_cover(stdscr):
#    global COVER_ANIM_MODE_INDEX
#    COVER_ANIM_MODE_INDEX = randint(0, len(COVER_ANIM_MODES) - 1)
    coverthread = threading.Thread(target=_cover_thread_runner, args=(stdscr,), daemon=True)
    coverthread.start()
    return coverthread

def _cover_thread_runner(stdscr):
    sleep(0.156)
    while True:
        redraw_cover_display(stdscr)
        sleep(0.1)

def redraw_cover_display(stdscr):  # Redraws the cover display
#    if CURRENT_META["cover"] is None:
#        return
#    full_url = f'https://cdn.listen.moe/covers/{CURRENT_META["cover"]}'
    generate_and_show_image(None, curses.LINES - 24, 12, int(curses.COLS / 2) - ((curses.LINES - 24) * 2) - 2, stdscr)
    stdscr.refresh()

def generate_and_show_image(url, dim, y_start, x_start, window):
    img_arr = _gen_img_arr_frame(dim)
    for y in range(dim):
        for x in range(dim * 2): # monospace fix
            pix = img_arr[y][floor(x / 2)]
            color = int((pix[0]*6/256)*36 + (pix[1]*6/256)*6 + (pix[2]*6/256) - 1)
            curses.init_color(color, floor(pix[0] * 4), floor(pix[1] * 4), floor(pix[2] * 4))
            curses.init_pair(color, color, color)
            window.addstr(y_start + y, x_start + x, "#", curses.color_pair(color))

def _gen_img_arr_frame(dim):
    global COVER_ANIM_FRAME
    COVER_ANIM_FRAME = (COVER_ANIM_FRAME + 1) % 1001
    mode = COVER_ANIM_MODES[COVER_ANIM_MODE_INDEX]
    if mode == "SPECTRUM":
        col = colorsys.hsv_to_rgb(COVER_ANIM_FRAME / 1000.0, 0.8, 0.6)
        specarr = [[col[0] * 250, col[1] * 250, col[2] * 250]] * dim
        return [specarr] * dim
    else:
        noarr = [[0, 0, 0]] * dim
        return [noarr] * dim

def _fill_spaces(text):  # Fills spaces after text until window end
    return text + (int(curses.COLS/2-(len(text))) * " ")

def _init_mplayer_with_pipe():  # Start mplayer and return the stdin as a pipe
    p = Popen(['mplayer', '-volume', str(VOLUME), '-volstep', str(VOLUMESTEP), 'https://listen.moe/stream'], stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
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
